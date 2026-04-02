import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_query_claude_no_key():
    with patch.dict("os.environ", {}, clear=True):
        import importlib
        import ai_query
        importlib.reload(ai_query)
        result = await ai_query.query_claude("test prompt")
        assert result == ai_query.FALLBACK


@pytest.mark.asyncio
async def test_query_gpt4o_no_key():
    with patch.dict("os.environ", {}, clear=True):
        import importlib
        import ai_query
        importlib.reload(ai_query)
        result = await ai_query.query_gpt4o("test prompt")
        assert result == ai_query.FALLBACK


@pytest.mark.asyncio
async def test_query_gemini_no_key():
    with patch.dict("os.environ", {}, clear=True):
        import importlib
        import ai_query
        importlib.reload(ai_query)
        result = await ai_query.query_gemini("test prompt")
        assert result == ai_query.FALLBACK


@pytest.mark.asyncio
async def test_query_groq_no_key():
    with patch.dict("os.environ", {}, clear=True):
        import importlib
        import ai_query
        importlib.reload(ai_query)
        result = await ai_query.query_groq("test prompt")
        assert result == ai_query.FALLBACK


@pytest.mark.asyncio
async def test_query_all_providers_returns_four_keys():
    with patch.dict("os.environ", {}, clear=True):
        import importlib
        import ai_query
        importlib.reload(ai_query)
        results = await ai_query.query_all_providers("Is AI conscious?")
        assert set(results.keys()) == {"Claude", "GPT-4o", "Gemini", "Groq/Llama"}


@pytest.mark.asyncio
async def test_query_claude_with_key_success():
    mock_content = MagicMock()
    mock_content.text = "AI is not conscious."
    mock_message = MagicMock()
    mock_message.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_message)

    mock_anthropic = MagicMock()
    mock_anthropic.AsyncAnthropic.return_value = mock_client

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
        with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
            import importlib
            import ai_query
            importlib.reload(ai_query)
            result = await ai_query.query_claude("test")
            assert result == "AI is not conscious."


@pytest.mark.asyncio
async def test_query_all_providers_exception_returns_fallback():
    import ai_query
    with patch.object(ai_query, "query_claude", side_effect=Exception("boom")):
        with patch.object(ai_query, "query_gpt4o", return_value="gpt response"):
            with patch.object(ai_query, "query_gemini", return_value="gemini response"):
                with patch.object(ai_query, "query_groq", return_value="groq response"):
                    results = await ai_query.query_all_providers("test")
                    assert results["Claude"] == ai_query.FALLBACK
                    assert results["GPT-4o"] == "gpt response"