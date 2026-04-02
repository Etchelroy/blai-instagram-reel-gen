import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import tempfile

from config import Config
from ai_query import AIQuery
from renderer import ReelRenderer
from audio import AudioMixer
from poster import InstagramPoster


class TestConfig:
    """Test Config module."""

    def test_config_loads_env_vars(self):
        """Test that config loads environment variables."""
        with patch.dict('os.environ', {
            'ANTHROPIC_API_KEY': 'test-anthropic',
            'OPENAI_API_KEY': 'test-openai',
            'GOOGLE_API_KEY': 'test-google',
            'GROQ_API_KEY': 'test-groq',
            'AWS_ACCESS_KEY_ID': 'test-aws-id',
            'AWS_SECRET_ACCESS_KEY': 'test-aws-key',
            'INSTAGRAM_ACCESS_TOKEN': 'test-ig-token',
            'INSTAGRAM_BUSINESS_ACCOUNT_ID': 'test-ig-account',
        }):
            config = Config()
            assert config.anthropic_api_key == 'test-anthropic'
            assert config.openai_api_key == 'test-openai'
            assert config.s3_bucket == 'reel-generator-bucket'
            assert config.s3_region == 'us-east-1'

    def test_config_brand_colors_default(self):
        """Test that brand colors have defaults."""
        with patch.dict('os.environ', {
            'ANTHROPIC_API_KEY': 'test',
            'OPENAI_API_KEY': 'test',
            'GOOGLE_API_KEY': 'test',
            'GROQ_API_KEY': 'test',
            'AWS_ACCESS_KEY_ID': 'test',
            'AWS_SECRET_ACCESS_KEY': 'test',
            'INSTAGRAM_ACCESS_TOKEN': 'test',
            'INSTAGRAM_BUSINESS_ACCOUNT_ID': 'test',
        }):
            config = Config()
            assert config.brand_primary_color == '#FF6B35'
            assert config.brand_secondary_color == '#004E89'
            assert config.brand_accent_color == '#F7B801'


class TestAIQuery:
    """Test AIQuery module."""

    @pytest.mark.asyncio
    async def test_query_all_returns_four_responses(self):
        """Test that query_all returns 4 responses."""
        config = Mock()
        config.anthropic_api_key = 'test'
        config.openai_api_key = 'test'
        config.google_api_key = 'test'
        config.groq_api_key = 'test'

        with patch('ai_query.Anthropic'), \
             patch('ai_query.AsyncOpenAI'), \
             patch('ai_query.genai'), \
             patch('ai_query.Groq'):
            ai_query = AIQuery(config)
            ai_query._query_claude = AsyncMock(return_value='Claude response')
            ai_query._query_gpt4o = AsyncMock(return_value='GPT-4o response')
            ai_query._query_gemini = AsyncMock(return_value='Gemini response')
            ai_query._query_groq = AsyncMock(return_value='Groq response')

            responses = await ai_query.query_all('Test prompt')
            assert len(responses) == 4
            assert responses[0]['provider'] == 'Claude'
            assert responses[1]['provider'] == 'GPT-4o'
            assert responses[2]['provider'] == 'Gemini'
            assert responses[3]['provider'] == 'Groq'

    @pytest.mark.asyncio
    async def test_query_all_handles_exceptions(self):
        """Test that query_all handles exceptions gracefully."""
        config = Mock()
        config.anthropic_api_key = 'test'
        config.openai_api_key = 'test'
        config.google_api_key = 'test'
        config.groq_api_key = 'test'

        with patch('ai_query.Anthropic'), \
             patch('ai_query.AsyncOpenAI'), \
             patch('ai_query.genai'), \
             patch('ai_query.Groq'):
            ai_query = AIQuery(config)
            ai_query._query_claude = AsyncMock(side_effect=Exception('Test error'))
            ai_query._query_gpt4o = AsyncMock(return_value='GPT-4o response')
            ai_query._query_gemini = AsyncMock(return_value='Gemini response')
            ai_query._query_groq = AsyncMock(return_value='Groq response')

            responses = await ai_query.query_all('Test prompt')
            assert len(responses) == 4
            assert 'Error' in responses[0]['text']


class TestReelRenderer:
    """Test ReelRenderer module."""

    def test_renderer_initializes(self):
        """Test that renderer initializes with config."""
        config = Mock()
        config.brand_primary_color = '#FF6B35'
        config.brand_secondary_color = '#004E89'
        config.brand_accent_color = '#F7B801'

        renderer = ReelRenderer(config)
        assert renderer.WIDTH == 1080
        assert renderer.HEIGHT == 1920
        assert renderer.FPS == 30

    def test_hex_to_rgb_conversion(self):
        """Test hex to RGB conversion."""
        config = Mock()
        config.brand_primary_color = '#FF6B35'
        config.brand_secondary_color = '#004E89'
        config.brand_accent_color = '#F7B801'

        renderer = ReelRenderer(config)
        rgb = renderer._hex_to_rgb('#FF6B35')
        assert rgb == (255, 107, 53)

    def test_wrap_text(self):
        """Test text wrapping."""
        config = Mock()
        config.brand_primary_color = '#FF6B35'
        config.brand_secondary_color = '#004E89'
        config.brand_accent_color = '#F7B801'

        renderer = ReelRenderer(config)
        text = 'This is a long text that should be wrapped'
        wrapped = renderer._wrap_text(text, 15)
        assert len(wrapped) > 1
        assert all(len(line) <= 15 for line in wrapped)

    def test_create_intro_card(self):
        """Test intro card creation."""
        config = Mock()
        config.brand_primary_color = '#FF6B35'
        config.brand_secondary_color = '#004E89'
        config.brand_accent_color = '#F7B801'

        renderer = ReelRenderer(config)
        card = renderer._create_intro_card('Test prompt')
        assert card.size == (1080, 1920)
        assert card.mode == 'RGB'

    def test_create_response_card(self):
        """Test response card creation."""
        config = Mock()
        config.brand_primary_color = '#FF6B35'
        config.brand_secondary_color = '#004E89'
        config.brand_accent_color = '#F7B801'

        renderer = ReelRenderer(config)
        response = {'provider': 'Claude', 'text': 'Test response text'}
        card = renderer._create_response_card(response)
        assert card.size == (1080, 1920)
        assert card.mode == 'RGB'


class TestAudioMixer:
    """Test AudioMixer module."""

    def test_audio_mixer_initializes(self):
        """Test that audio mixer initializes with config."""
        config = Mock()
        config.music_file_path = None

        mixer = AudioMixer(config)
        assert mixer.config == config

    def test_audio_mixer_without_music_file(self):
        """Test audio mixer handles missing music file."""
        config = Mock()
        config.music_file_path = None

        mixer = AudioMixer(config)
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp_path = tmp.name

        result = mixer.mix(tmp_path)
        assert result == tmp_path


class TestInstagramPoster:
    """Test InstagramPoster module."""

    def test_poster_initializes(self):
        """Test that poster initializes with config."""
        config = Mock()
        config.instagram_access_token = 'test-token'
        config.instagram_business_account_id = 'test-account-id'
        config.s3_bucket = 'test-bucket'
        config.s3_region = 'us-east-1'
        config.aws_access_key_id = 'test-aws-id'
        config.aws_secret_access_key = 'test-aws-key'

        poster = InstagramPoster(config)
        assert poster.config == config

    @pytest.mark.asyncio
    async def test_poster_dry_run(self):
        """Test poster dry run mode."""
        config = Mock()
        config.instagram_access_token = 'test-token'
        config.instagram_business_account_id = 'test-account-id'
        config.s3_bucket = 'test-bucket'
        config.s3_region = 'us-east-1'
        config.aws_access_key_id = 'test-aws-id'
        config.aws_secret_access_key = 'test-aws-key'

        with patch('poster.boto3'), \
             patch('poster.requests'):
            poster = InstagramPoster(config)
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                tmp_path = tmp.name
                with open(tmp_path, 'w') as f:
                    f.write('fake video')

            result = await poster.post(tmp_path, 'Test prompt', dry_run=True)
            assert 'DRY RUN' in result or result is not None