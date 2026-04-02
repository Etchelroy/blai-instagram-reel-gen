import asyncio
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from poster import InstagramPoster


@pytest.fixture
def mock_config():
    config = Mock()
    config.aws_access_key_id = 'test-key'
    config.aws_secret_access_key = 'test-secret'
    config.s3_region = 'us-east-1'
    config.s3_bucket = 'test-bucket'
    config.instagram_access_token = 'test-token'
    config.instagram_business_account_id = '123456'
    return config


@patch('poster.boto3.client')
def test_poster_init(mock_boto_client, mock_config):
    """Test InstagramPoster initialization."""
    poster = InstagramPoster(mock_config)
    assert poster.config == mock_config


@pytest.mark.asyncio
@patch('poster.boto3.client')
async def test_post_dry_run(mock_boto_client, mock_config):
    """Test dry-run mode returns payload without posting."""
    poster = InstagramPoster(mock_config)
    poster._upload_to_s3 = AsyncMock(return_value='https://test-bucket.s3.us-east-1.amazonaws.com/reel.mp4')

    result = await poster.post('test_reel.mp4', 'Test prompt', dry_run=True)

    assert result['status'] == 'dry_run'
    assert 'payload' in result
    assert result['payload']['media_type'] == 'REELS'


@pytest.mark.asyncio
@patch('poster.boto3.client')
@patch('poster.requests.post')
async def test_post_live_mode(mock_post, mock_boto_client, mock_config):
    """Test live mode posts to Instagram."""
    mock_post.return_value = Mock(json=lambda: {'id': '12345'}, status_code=200)

    poster = InstagramPoster(mock_config)
    poster._upload_to_s3 = AsyncMock(return_value='https://test-bucket.s3.us-east-1.amazonaws.com/reel.mp4')

    with patch('poster.requests.post'):
        result = await poster.post('test_reel.mp4', 'Test prompt', dry_run=False)
        assert result is not None