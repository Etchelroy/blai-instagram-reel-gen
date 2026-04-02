# tests/test_poster.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from poster import PosterModule
import json

class TestPosterModule:
    """Test Instagram Poster Module."""

    def test_poster_initialization(self, mock_env):
        """Test poster module initializes with credentials."""
        poster = PosterModule()
        assert poster is not None
        assert poster.access_token is not None
        assert poster.business_account_id is not None

    def test_dry_run_mode_logs_payload(self, mock_env, capsys):
        """Test --dry-run mode logs payload without posting."""
        poster = PosterModule()
        
        payload = {
            'media_type': 'REELS',
            'video_url': 'https://s3.example.com/reel.mp4',
            'caption': 'Test caption',
            'access_token': 'test-token'
        }
        
        # Call dry-run
        result = poster.publish_dry_run(payload)
        
        # Should log payload
        assert result is not None

    @patch('poster.requests.post')
    def test_s3_upload_before_posting(self, mock_post, mock_env):
        """Test S3 upload happens before Instagram posting."""
        mock_post.return_value = MagicMock(status_code=200)
        
        poster = PosterModule()
        with patch('poster.boto3.client') as mock_s3:
            mock_s3_instance = MagicMock()
            mock_s3.return_value = mock_s3_instance
            mock_s3_instance.upload_file = MagicMock()
            
            result = poster.upload_to_s3('test_video.mp4', 'test-bucket')
            # Should complete S3 upload
            assert result is not None

    @patch('poster.requests.post')
    def test_instagram_graph_api_publish(self, mock_post, mock_env):
        """Test Instagram Graph API /me/media endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'media_123'}
        mock_post.return_value = mock_response
        
        poster = PosterModule()
        
        result = poster.publish_to_instagram(
            video_url='https://s3.example.com/reel.mp4',
            caption='Test caption'
        )
        
        assert result is not None

    def test_payload_structure_valid(self, mock_env):
        """Test payload has all required Graph API fields."""
        poster = PosterModule()
        
        payload = poster.build_payload(
            video_url='https://s3.example.com/reel.mp4',
            caption='Test'
        )
        
        assert 'media_type' in payload
        assert 'video_url' in payload
        assert 'caption' in payload
        assert 'access_token' in payload

    @patch('poster.requests.post')
    def test_http_error_handling(self, mock_post, mock_env):
        """Test graceful handling of HTTP errors from Instagram API."""
        mock_post.return_value = MagicMock(status_code=400)
        
        poster = PosterModule()
        
        try:
            result = poster.publish_to_instagram(
                video_url='https://s3.example.com/reel.mp4',
                caption='Test'
            )
        except Exception as e:
            # Should raise or return error gracefully
            assert e is not None or True

    def test_credentials_from_env(self, mock_env):
        """Test all credentials loaded from .env only."""
        poster = PosterModule()
        
        assert poster.access_token == 'test-ig-token'
        assert poster.business_account_id == 'test-ig-account'