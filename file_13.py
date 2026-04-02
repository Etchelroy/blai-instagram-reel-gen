# ai_query.py
import asyncio
import logging
from typing import Dict, List
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential
from anthropic import Anthropic
from openai import AsyncOpenAI
import google.generativeai as genai
from groq import Groq

logger = logging.getLogger(__name__)


class AIQueryModule:
    def __init__(self, config):
        self.config = config
        self.timeout = config.ai_timeout_seconds
        self.max_retries = config.ai_max_retries

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _query_claude(self, prompt: str) -> Dict[str, str]:
        """Query Claude via Anthropic API."""
        try:
            client = Anthropic(api_key=self.config.claude_api_key)
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            return {
                "provider": "Claude",
                "response": message.content[0].text,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Claude query failed: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _query_gpt4o(self, prompt: str) -> Dict[str, str]:
        """Query GPT-4o via OpenAI API."""
        try:
            client = AsyncOpenAI(api_key=self.config.openai_api_key)
            response = await client.chat.completions.create(
                model="gpt-4o",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            return {
                "provider": "GPT-4o",
                "response": response.choices[0].message.content,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"GPT-4o query failed: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _query_gemini(self, prompt: str) -> Dict[str, str]:
        """Query Gemini via Google API."""
        try:
            genai.configure(api_key=self.config.gemini_api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return {
                "provider": "Gemini",
                "response": response.text,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Gemini query failed: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _query_groq(self, prompt: str) -> Dict[str, str]:
        """Query Llama via Groq API."""
        try:
            client = Groq(api_key=self.config.groq_api_key)
            response = client.chat.completions.create(
                model="llama3-70b-8192",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            return {
                "provider": "Llama (Groq)",
                "response": response.choices[0].message.content,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Groq query failed: {e}")
            raise

    async def query_all(self, prompt: str) -> List[Dict[str, str]]:
        """Query all providers in parallel with timeout."""
        tasks = [
            asyncio.wait_for(self._query_claude(prompt), timeout=self.timeout),
            asyncio.wait_for(self._query_gpt4o(prompt), timeout=self.timeout),
            asyncio.wait_for(self._query_gemini(prompt), timeout=self.timeout),
            asyncio.wait_for(self._query_groq(prompt), timeout=self.timeout),
        ]
        
        results = []
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                results.append(result)
                logger.info(f"✓ {result['provider']} responded")
            except asyncio.TimeoutError:
                logger.warning(f"Provider timeout (30s)")
                results.append({
                    "provider": "Unknown",
                    "response": "Response timeout - AI service unavailable",
                    "status": "timeout"
                })
            except Exception as e:
                logger.warning(f"Provider error: {e}")
                results.append({
                    "provider": "Unknown",
                    "response": "Failed to retrieve response - service error",
                    "status": "error"
                })
        
        return results if results else self._fallback_responses()

    def _fallback_responses(self) -> List[Dict[str, str]]:
        """Return graceful fallback when all providers fail."""
        return [
            {
                "provider": "Claude",
                "response": "Service temporarily unavailable. Please try again.",
                "status": "fallback"
            },
            {
                "provider": "GPT-4o",
                "response": "Service temporarily unavailable. Please try again.",
                "status": "fallback"
            },
            {
                "provider": "Gemini",
                "response": "Service temporarily unavailable. Please try again.",
                "status": "fallback"
            },
            {
                "provider": "Llama (Groq)",
                "response": "Service temporarily unavailable. Please try again.",
                "status": "fallback"
            },
        ]