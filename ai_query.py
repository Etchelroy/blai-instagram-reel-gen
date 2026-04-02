import asyncio
import logging
import os
from typing import Dict

logger = logging.getLogger("ai_query")

TIMEOUT = 30
MAX_RETRIES = 3

FALLBACK = "This AI provider did not return a response within the allowed time."

PROVIDER_COLORS = {
    "Claude": "#D4A574",
    "GPT-4o": "#74C0FC",
    "Gemini": "#A9D18E",
    "Groq/Llama": "#C9B1FF",
}


async def query_claude(prompt: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set, returning fallback for Claude")
        return FALLBACK
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=api_key)
            async with asyncio.timeout(TIMEOUT):
                message = await client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=150,
                    messages=[{"role": "user", "content": prompt}],
                )
            return message.content[0].text.strip()
        except asyncio.TimeoutError:
            logger.warning(f"Claude attempt {attempt} timed out")
        except Exception as e:
            logger.warning(f"Claude attempt {attempt} failed: {e}")
        if attempt < MAX_RETRIES:
            await asyncio.sleep(2 ** attempt)
    return FALLBACK


async def query_gpt4o(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set, returning fallback for GPT-4o")
        return FALLBACK
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key)
            async with asyncio.timeout(TIMEOUT):
                response = await client.chat.completions.create(
                    model="gpt-4o",
                    max_tokens=150,
                    messages=[{"role": "user", "content": prompt}],
                )
            return response.choices[0].message.content.strip()
        except asyncio.TimeoutError:
            logger.warning(f"GPT-4o attempt {attempt} timed out")
        except Exception as e:
            logger.warning(f"GPT-4o attempt {attempt} failed: {e}")
        if attempt < MAX_RETRIES:
            await asyncio.sleep(2 ** attempt)
    return FALLBACK


async def query_gemini(prompt: str) -> str:
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        logger.warning("GOOGLE_API_KEY not set, returning fallback for Gemini")
        return FALLBACK
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            async with asyncio.timeout(TIMEOUT):
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(max_output_tokens=150),
                    ),
                )
            return response.text.strip()
        except asyncio.TimeoutError:
            logger.warning(f"Gemini attempt {attempt} timed out")
        except Exception as e:
            logger.warning(f"Gemini attempt {attempt} failed: {e}")
        if attempt < MAX_RETRIES:
            await asyncio.sleep(2 ** attempt)
    return FALLBACK


async def query_groq(prompt: str) -> str:
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        logger.warning("GROQ_API_KEY not set, returning fallback for Groq/Llama")
        return FALLBACK
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            from groq import AsyncGroq
            client = AsyncGroq(api_key=api_key)
            async with asyncio.timeout(TIMEOUT):
                response = await client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    max_tokens=150,
                    messages=[{"role": "user", "content": prompt}],
                )
            return response.choices[0].message.content.strip()
        except asyncio.TimeoutError:
            logger.warning(f"Groq attempt {attempt} timed out")
        except Exception as e:
            logger.warning(f"Groq attempt {attempt} failed: {e}")
        if attempt < MAX_RETRIES:
            await asyncio.sleep(2 ** attempt)
    return FALLBACK


async def query_all_providers(prompt: str) -> Dict[str, str]:
    tasks = {
        "Claude": query_claude(prompt),
        "GPT-4o": query_gpt4o(prompt),
        "Gemini": query_gemini(prompt),
        "Groq/Llama": query_groq(prompt),
    }
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    output = {}
    for provider, result in zip(tasks.keys(), results):
        if isinstance(result, Exception):
            logger.error(f"{provider} raised exception: {result}")
            output[provider] = FALLBACK
        else:
            output[provider] = result
    return output