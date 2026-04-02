import asyncio
import logging
from typing import List, Dict
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

from anthropic import Anthropic
from openai import AsyncOpenAI
import google.generativeai as genai
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class AIQuery:
    """Query multiple AI models in parallel with retry logic."""

    def __init__(self, config):
        self.config = config
        self.anthropic_client = Anthropic(api_key=config.anthropic_api_key)
        self.openai_client = AsyncOpenAI(api_key=config.openai_api_key)
        self.groq_client = Groq(api_key=config.groq_api_key)
        genai.configure(api_key=config.google_api_key)

    async def query_all(self, prompt: str) -> List[Dict[str, str]]:
        """Query all models in parallel."""
        tasks = [
            self._query_claude(prompt),
            self._query_gpt4o(prompt),
            self._query_gemini(prompt),
            self._query_groq(prompt),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [
            {
                'provider': name,
                'text': text if not isinstance(text, Exception) else f'Error: {str(text)[:100]}',
            }
            for name, text in zip(['Claude', 'GPT-4o', 'Gemini', 'Groq'], results)
        ]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _query_claude(self, prompt: str) -> str:
        """Query Claude with retry."""
        try:
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.anthropic_client.messages.create(
                        model='claude-3-5-sonnet-20241022',
                        max_tokens=150,
                        messages=[{'role': 'user', 'content': prompt}],
                    ),
                ),
                timeout=30,
            )
            return response.content[0].text[:250]
        except asyncio.TimeoutError:
            logger.warning('Claude query timed out')
            return 'Claude response timed out.'
        except Exception as e:
            logger.error(f'Claude query error: {e}')
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _query_gpt4o(self, prompt: str) -> str:
        """Query GPT-4o with retry."""
        try:
            response = await asyncio.wait_for(
                self.openai_client.chat.completions.create(
                    model='gpt-4o',
                    max_tokens=150,
                    messages=[{'role': 'user', 'content': prompt}],
                ),
                timeout=30,
            )
            return response.choices[0].message.content[:250]
        except asyncio.TimeoutError:
            logger.warning('GPT-4o query timed out')
            return 'GPT-4o response timed out.'
        except Exception as e:
            logger.error(f'GPT-4o query error: {e}')
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _query_gemini(self, prompt: str) -> str:
        """Query Gemini with retry."""
        try:
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: genai.GenerativeModel('gemini-pro').generate_content(prompt),
                ),
                timeout=30,
            )
            return response.text[:250]
        except asyncio.TimeoutError:
            logger.warning('Gemini query timed out')
            return 'Gemini response timed out.'
        except Exception as e:
            logger.error(f'Gemini query error: {e}')
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _query_groq(self, prompt: str) -> str:
        """Query Groq with retry."""
        try:
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.groq_client.chat.completions.create(
                        model='mixtral-8x7b-32768',
                        max_tokens=150,
                        messages=[{'role': 'user', 'content': prompt}],
                    ),
                ),
                timeout=30,
            )
            return response.choices[0].message.content[:250]
        except asyncio.TimeoutError:
            logger.warning('Groq query timed out')
            return 'Groq response timed out.'
        except Exception as e:
            logger.error(f'Groq query error: {e}')
            raise