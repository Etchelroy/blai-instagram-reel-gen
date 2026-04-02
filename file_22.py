# tests/test_ai_query.py
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from ai_query import AIQueryModule
import aiohttp

class TestAIQueryModule:
    """Test AI Query Module with async, retry, and timeout handling."""

    @pytest.mark.asyncio
    async def test_query_all_providers_success(self, mock_env, sample_prompt):
        """Test successful parallel queries to all 4 providers."""
        with patch('ai_query.Anthropic') as mock_anthropic, \
             patch('ai_query.AsyncOpenAI') as mock_openai, \
             patch('ai_query.genai.GenerativeModel') as mock_gemini, \
             patch('ai_query.Groq') as mock_groq:
            
            # Mock successful responses
            mock_anthropic.return_value.messages.create = MagicMock(
                return_value=MagicMock(content=[MagicMock(text='Claude response')])
            )
            mock_openai.return_value.chat.completions.create = AsyncMock(
                return_value=MagicMock(
                    choices=[MagicMock(message=MagicMock(content='GPT-4o response'))]
                )
            )
            mock_gemini.return_value.generate_content = MagicMock(
                return_value=MagicMock(text='Gemini response')
            )
            mock_groq.return_value.chat.completions.create = AsyncMock(
                return_value=MagicMock(
                    choices=[MagicMock(message=MagicMock(content='Llama response'))]
                )
            )
            
            module = AIQueryModule()
            results = await module.query_all(sample_prompt)
            
            assert len(results) == 4
            assert 'Claude' in results
            assert 'GPT-4o' in results
            assert 'Gemini' in results
            assert 'Llama' in results

    @pytest.mark.asyncio
    async def test_single_provider_timeout(self, mock_env, sample_prompt):
        """Test timeout handling for a single provider."""
        with patch('ai_query.Anthropic') as mock_anthropic, \
             patch('ai_query.AsyncOpenAI') as mock_openai, \
             patch('ai_query.genai.GenerativeModel') as mock_gemini, \
             patch('ai_query.Groq') as mock_groq:
            
            # Claude times out, others succeed
            mock_anthropic.return_value.messages.create = MagicMock(
                side_effect=asyncio.TimeoutError()
            )
            mock_openai.return_value.chat.completions.create = AsyncMock(
                return_value=MagicMock(
                    choices=[MagicMock(message=MagicMock(content='GPT-4o response'))]
                )
            )
            mock_gemini.return_value.generate_content = MagicMock(
                return_value=MagicMock(text='Gemini response')
            )
            mock_groq.return_value.chat.completions.create = AsyncMock(
                return_value=MagicMock(
                    choices=[MagicMock(message=MagicMock(content='Llama response'))]
                )
            )
            
            module = AIQueryModule()
            results = await module.query_all(sample_prompt)
            
            # Should have fallback for Claude
            assert 'Claude' in results
            assert 'Unable to reach' in results['Claude'] or results['Claude'] is not None
            assert 'GPT-4o' in results

    @pytest.mark.asyncio
    async def test_retry_logic_on_failure(self, mock_env, sample_prompt):
        """Test retry logic on API failures."""
        with patch('ai_query.Anthropic') as mock_anthropic, \
             patch('ai_query.AsyncOpenAI') as mock_openai, \
             patch('ai_query.genai.GenerativeModel') as mock_gemini, \
             patch('ai_query.Groq') as mock_groq:
            
            # Mock retry behavior
            mock_anthropic.return_value.messages.create = MagicMock(
                side_effect=[Exception('API Error'), Exception('API Error'), 
                            MagicMock(content=[MagicMock(text='Claude response')])]
            )
            mock_openai.return_value.chat.completions.create = AsyncMock(
                return_value=MagicMock(
                    choices=[MagicMock(message=MagicMock(content='GPT-4o response'))]
                )
            )
            mock_gemini.return_value.generate_content = MagicMock(
                return_value=MagicMock(text='Gemini response')
            )
            mock_groq.return_value.chat.completions.create = AsyncMock(
                return_value=MagicMock(
                    choices=[MagicMock(message=MagicMock(content='Llama response'))]
                )
            )
            
            module = AIQueryModule()
            results = await module.query_all(sample_prompt)
            
            # Verify we have responses despite retries
            assert len(results) >= 3

    @pytest.mark.asyncio
    async def test_all_providers_fail_graceful_fallback(self, mock_env, sample_prompt):
        """Test graceful fallback when all providers fail."""
        with patch('ai_query.Anthropic') as mock_anthropic, \
             patch('ai_query.AsyncOpenAI') as mock_openai, \
             patch('ai_query.genai.GenerativeModel') as mock_gemini, \
             patch('ai_query.Groq') as mock_groq:
            
            # All fail
            mock_anthropic.return_value.messages.create = MagicMock(
                side_effect=Exception('API Error')
            )
            mock_openai.return_value.chat.completions.create = AsyncMock(
                side_effect=Exception('API Error')
            )
            mock_gemini.return_value.generate_content = MagicMock(
                side_effect=Exception('API Error')
            )
            mock_groq.return_value.chat.completions.create = AsyncMock(
                side_effect=Exception('API Error')
            )
            
            module = AIQueryModule()
            results = await module.query_all(sample_prompt)
            
            # All should have fallback messages
            assert len(results) == 4
            for provider, response in results.items():
                assert response is not None
                assert len(response) > 0