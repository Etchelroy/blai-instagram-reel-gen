# tests/test_ai_query.py
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from ai_query import AIQueryModule
from config import Config


@pytest.fixture
def mock_config():
    config = Config()
    config.claude_api_key = "test-claude-key"
    config.openai_api_key = "test-openai-key"
    config.gemini_api_key = "test-gemini-key"
    config.groq_api_key = "test-groq-key"
    config.ai_timeout_seconds = 30
    config.ai_max_retries = 3
    return config


@pytest.fixture
def ai_module(mock_config):
    return AIQueryModule(mock_config)


@pytest.mark.asyncio
async def test_query_all_success(ai_module):
    """Test successful parallel queries."""
    with patch.object(ai_module, '_query_claude', new_callable=AsyncMock) as mock_claude, \
         patch.object(ai_module, '_query_gpt4o', new_callable=AsyncMock) as mock_gpt, \
         patch.object(ai_module, '_query_gemini', new_callable=AsyncMock) as mock_gemini, \
         patch.object(ai_module, '_query_groq', new_callable=AsyncMock) as mock_groq:
        
        mock_claude.return_value = {"provider": "Claude", "response": "Test response", "status": "success"}
        mock_gpt.return_value = {"provider": "GPT-4o", "response": "Test response", "status": "success"}
        mock_gemini.return_value = {"provider": "Gemini", "response": "Test response", "status": "success"}
        mock_groq.return_value = {"provider": "Llama (Groq)", "response": "Test response", "status": "success"}

        results = await ai_module.query_all("Test prompt")
        
        assert len(results) == 4
        assert all(r["status"] in ["success", "timeout"] for r in results)


@pytest.mark.asyncio
async def test_query_all_timeout_fallback(ai_module):
    """Test fallback when all providers timeout."""
    with patch.object(ai_module, '_query_claude', new_callable=AsyncMock) as mock_claude, \
         patch.object(ai_module, '_query_gpt4o', new_callable=AsyncMock) as mock_gpt, \
         patch.object(ai_module, '_query_gemini', new_callable=AsyncMock) as mock_gemini, \
         patch.object(ai_module, '_query_groq', new_callable=AsyncMock) as mock_groq:
        
        async def timeout_side_effect(*args, **kwargs):
            await asyncio.sleep(100)
        
        mock_claude.side_effect = timeout_side_effect
        mock_gpt.side_effect = timeout_side_effect
        mock_gemini.side_effect = timeout_side_effect
        mock_groq.side_effect = timeout_side_effect

        results = await ai_module.query_all("Test prompt")
        
        assert len(results) >= 1
        assert any("timeout" in str(r.get("status", "")).lower() or "error" in str(r.get("response", "")).lower() for r in results)


@pytest.mark.asyncio
async def test_query_claude(ai_module):
    """Test Claude query with retry."""
    with patch('anthropic.Anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Claude response")]
        mock_client.messages.create.return_value = mock_message

        result = await ai_module._query_claude("Test prompt")
        
        assert result["provider"] == "Claude"
        assert result["status"] == "success"
        assert "response" in result


def test_fallback_responses(ai_module):
    """Test fallback response generation."""
    responses = ai_module._fallback_responses()
    
    assert len(responses) == 4
    assert all(r["status"] == "fallback" for r in responses)
    assert all("unavailable" in r["response"].lower() for r in responses)