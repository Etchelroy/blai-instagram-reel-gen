import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
from ai_query import AIQuery


@pytest.fixture
def mock_config():
    config = Mock()
    config.anthropic_api_key = 'test-key'
    config.openai_api_key = 'test-key'
    config.google_api_key = 'test-key'
    config.groq_api_key = 'test-key'
    return config


@pytest.mark.asyncio
async def test_query_all_returns_four_responses(mock_config):
    """Test that query_all returns responses from all four providers."""
    with patch('ai_query.Anthropic'), \
         patch('ai_query.AsyncOpenAI'), \
         patch('ai_query.genai'), \
         patch('ai_query.Groq'):
        ai = AIQuery(mock_config)
        ai._query_claude = AsyncMock(return_value='Claude response')
        ai._query_gpt4o = AsyncMock(return_value='GPT-4o response')
        ai._query_gemini = AsyncMock(return_value='Gemini response')
        ai._query_groq = AsyncMock(return_value='Groq response')

        results = await ai.query_all('test prompt')

        assert len(results) == 4
        assert results[0]['provider'] == 'Claude'
        assert results[1]['provider'] == 'GPT-4o'
        assert results[2]['provider'] == 'Gemini'
        assert results[3]['provider'] == 'Groq'


@pytest.mark.asyncio
async def test_query_claude_returns_text(mock_config):
    """Test Claude query returns text."""
    mock_response = Mock()
    mock_response.content = [Mock(text='Test response')]

    with patch('ai_query.Anthropic') as MockAnthropic:
        MockAnthropic.return_value.messages.create.return_value = mock_response
        ai = AIQuery(mock_config)
        result = await ai._query_claude('test')
        assert 'Test response' in result


@pytest.mark.asyncio
async def test_query_handles_timeout(mock_config):
    """Test that timeout errors are handled gracefully."""
    with patch('ai_query.Anthropic'), \
         patch('ai_query.AsyncOpenAI'), \
         patch('ai_query.genai'), \
         patch('ai_query.Groq'):
        ai = AIQuery(mock_config)
        ai._query_claude = AsyncMock(side_effect=asyncio.TimeoutError())
        ai._query_gpt4o = AsyncMock(return_value='GPT response')
        ai._query_gemini = AsyncMock(return_value='Gemini response')
        ai._query_groq = AsyncMock(return_value='Groq response')

        results = await ai.query_all('test')
        assert len(results) == 4
        assert 'Error' in results[0]['text'] or 'timeout' in results[0]['text'].lower()