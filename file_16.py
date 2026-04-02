import asyncio
import logging
from typing import Dict

import anthropic
import openai
from groq import Groq
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

import config

logger = logging.getLogger(__name__)

PROVIDERS = ["claude", "gpt4o", "gemini", "groq"]

BRAND_COLORS = {
    "claude":  "#D97757",
    "gpt4o":   "#10A37F",
    "gemini":  "#4285F4",
    "groq":    "#F55036",
}

PROVIDER_LABELS = {
    "claude": "Claude (Anthropic)",
    "gpt4o":  "GPT-4o (OpenAI)",
    "gemini": "Gemini (Google)",
    "groq":   "Llama 3 (Groq)",
}

FALLBACK = "This AI provider is currently unavailable. Please try again later."


async def _query_claude(prompt: str) -> str:
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8),
           retry=retry_if_exception_type(Exception))
    def _call():
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text.strip()
    try:
        return await asyncio.wait_for(asyncio.to_thread(_call), timeout=30)
    except Exception as e:
        logger.error("Claude failed: %s", e)
        return FALLBACK


async def _query_gpt4o(prompt: str) -> str:
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8),
           retry=retry_if_exception_type(Exception))
    def _call():
        client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content.strip()
    try:
        return await asyncio.wait_for(asyncio.to_thread(_call), timeout=30)
    except Exception as e:
        logger.error("GPT-4o failed: %s", e)
        return FALLBACK


async def _query_gemini(prompt: str) -> str:
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8),
           retry=retry_if_exception_type(Exception))
    def _call():
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content(prompt)
        return resp.text.strip()
    try:
        return await asyncio.wait_for(asyncio.to_thread(_call), timeout=30)
    except Exception as e:
        logger.error("Gemini failed: %s", e)
        return FALLBACK


async def _query_groq(prompt: str) -> str:
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8),
           retry=retry_if_exception_type(Exception))
    def _call():
        client = Groq(api_key=config.GROQ_API_KEY)
        resp = client.chat.completions.create(
            model="llama3-8b-8192",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content.strip()
    try:
        return await asyncio.wait_for(asyncio.to_thread(_call), timeout=30)
    except Exception as e:
        logger.error("Groq failed: %s", e)
        return FALLBACK


async def query_all(prompt: str) -> Dict[str, str]:
    results = await asyncio.gather(
        _query_claude(prompt),
        _query_gpt4o(prompt),
        _query_gemini(prompt),
        _query_groq(prompt),
        return_exceptions=False,
    )
    return {
        "claude": results[0],
        "gpt4o":  results[1],
        "gemini": results[2],
        "groq":   results[3],
    }