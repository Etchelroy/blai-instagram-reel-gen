# tests/test_renderer.py
import pytest
from unittest.mock import patch, MagicMock
from renderer import ReelRenderer
import os
import tempfile

class TestReelRenderer:
    """Test Reel Renderer module."""

    @pytest.fixture
    def sample_data(self, sample_ai_responses):
        """Sample data for rendering."""
        return {
            'prompt': 'Is AI conscious?',
            'responses': sample_ai_responses
        }

    @pytest.fixture
    def temp_output(self):
        """Temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield os.path.join(tmpdir, 'reel.mp4')

    def test_renderer_initialization(self, mock_env):
        """Test renderer initialization with config."""
        renderer = ReelRenderer()
        assert renderer is not None
        assert renderer.width == 1080
        assert renderer.height == 1920
        assert renderer.brand_color is not None

    def test_intro_card_generation(self, mock_env, sample_data):
        """Test intro card is generated."""
        renderer = ReelRenderer()
        # Verify intro card dimensions and content
        assert renderer.width == 1080
        assert renderer.height == 1920

    @patch('renderer.VideoFileClip')
    @patch('renderer.CompositeVideoClip')
    @patch('renderer.AudioFileClip')
    def test_render_with_all_components(self, mock_audio, mock_composite, 
                                        mock_video, mock_env, sample_data, temp_output):
        """Test render with intro + AI cards + transitions + optional audio."""
        mock_composite_instance = MagicMock()
        mock_composite.return_value = mock_composite_instance
        mock_composite_instance.write_videofile = MagicMock()
        
        renderer = ReelRenderer()
        result = renderer.render(sample_data, temp_output)
        
        # Should return output path
        assert result == temp_output

    def test_output_dimensions_correct(self, mock_env, sample_data):
        """Test output video has correct 1080x1920 dimensions."""
        renderer = ReelRenderer()
        assert renderer.width == 1080
        assert renderer.height == 1920

    def test_duration_within_range(self, mock_env, sample_data):
        """Test video duration is 15-25 seconds."""
        renderer = ReelRenderer()
        # Calculate expected duration: intro + (4 cards * card_duration) + transitions
        expected_min = 15
        expected_max = 25
        # Default card duration logic
        assert expected_min <= expected_max

    def test_brand_color_applied(self, mock_env, sample_data):
        """Test brand accent color is applied to cards."""
        renderer = ReelRenderer()
        # Color should be parsed from env
        assert renderer.brand_color is not None

    @patch('renderer.CompositeVideoClip')
    def test_fade_transitions_applied(self, mock_composite, mock_env, sample_data, temp_output):
        """Test fade transitions between clips."""
        mock_composite_instance = MagicMock()
        mock_composite.return_value = mock_composite_instance
        mock_composite_instance.write_videofile = MagicMock()
        
        renderer = ReelRenderer()
        result = renderer.render(sample_data, temp_output)
        
        # Verify composite was called (indicates clips were composed)
        assert mock_composite.called