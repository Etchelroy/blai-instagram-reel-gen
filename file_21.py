# tests/conftest.py
import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'test-claude-key')
    monkeypatch.setenv('OPENAI_API_KEY', 'test-gpt4-key')
    monkeypatch.setenv('GOOGLE_API_KEY', 'test-gemini-key')
    monkeypatch.setenv('GROQ_API_KEY', 'test-groq-key')
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'test-aws-key')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'test-aws-secret')
    monkeypatch.setenv('AWS_S3_BUCKET', 'test-bucket')
    monkeypatch.setenv('AWS_S3_REGION', 'us-east-1')
    monkeypatch.setenv('INSTAGRAM_ACCESS_TOKEN', 'test-ig-token')
    monkeypatch.setenv('INSTAGRAM_BUSINESS_ACCOUNT_ID', 'test-ig-account')
    monkeypatch.setenv('BRAND_ACCENT_COLOR', '#FF6B35')
    monkeypatch.setenv('LOG_LEVEL', 'INFO')
    return monkeypatch

@pytest.fixture
def mock_async_client():
    """Mock async HTTP client."""
    return AsyncMock()

@pytest.fixture
def sample_prompt():
    """Sample prompt for testing."""
    return "Is AI conscious?"

@pytest.fixture
def sample_ai_responses():
    """Sample AI responses for testing."""
    return {
        'Claude': 'Claude response about consciousness.',
        'GPT-4o': 'GPT-4o response about consciousness.',
        'Gemini': 'Gemini response about consciousness.',
        'Llama': 'Llama response about consciousness.'
    }