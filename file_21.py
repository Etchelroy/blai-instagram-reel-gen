import asyncio
import pytest
from unittest.mock import patch, MagicMock

import ai_query


def make_mock_message(text):
    m = MagicMock()
    m.content = [MagicMock(text=text)]
    return m


def make_mock_choice(text):
    m = MagicMock()
    m.choices = [MagicMock(message=MagicMock(content=text))]
    return m


@pytest.mark.asyncio
async def test_query_claude_success():
    with patch("ai_query.anthropic.Anthropic") as mock_cls:
        mock_cls.return_value.messages.create.return_value = make_mock_message("Claude answer")
        result = await ai_query._query_claude("test?")
    assert result == "Claude answer"


@pytest.mark.asyncio
async def test_query_claude_fallback():
    with patch("ai_query.anthropic.Anthropic") as mock_cls:
        mock_cls.return_value.messages.create.side_effect = Exception("API down")
        result = await ai_query._query_claude("test?")
    assert result == ai_query.FALLBACK


@pytest.mark.asyncio
async def test_query_gpt4o_success():
    with patch("ai_query.openai.OpenAI") as mock_cls:
        mock_cls.return_value.chat.completions.create.return_value = make_mock_choice("GPT answer")
        result = await ai_query._query_gpt4o("test?")
    assert result == "GPT answer"


@pytest.mark.asyncio
async def test_query_gpt4o_fallback():
    with patch("ai_query.openai.OpenAI") as mock_cls:
        mock_cls.return_value.chat.completions.create.side_effect = Exception("fail")
        result = await ai_query._query_gpt4o("test?")
    assert result == ai_query.FALLBACK


@pytest.mark.asyncio
async def test_query_gemini_fallback():
    with patch("ai_query.genai.GenerativeModel") as mock_cls:
        mock_cls.return_value.generate_content.side_effect = Exception("fail")
        result = await ai_query._query_gemini("test?")
    assert result == ai_query.FALLBACK


@pytest.mark.asyncio
async def test_query_groq_fallback():
    with patch("ai_query.Groq") as mock_cls:
        mock_cls.return_value.chat.completions.create.side_effect = Exception("fail")
        result = await ai_query._query_groq("test?")
    assert result == ai_query.FALLBACK


@pytest.mark.asyncio
async def test_query_all_returns_all_providers():
    with patch("ai_query._query_claude", return_value="c"), \
         patch("ai_query._query_gpt4o", return_value="g"), \
         patch("ai_query._query_gemini", return_value="ge"), \
         patch("ai_query._query_groq", return_value="gr"):
        results = await ai_query.query_all("test?")
    assert set(results.keys()) == {"claude", "gpt4o", "gemini", "groq"}
    assert results["claude"] == "c"