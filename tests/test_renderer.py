import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from renderer import ReelRenderer


@pytest.fixture
def mock_config():
    config = Mock()
    config.output_dir = Path('./test_output')
    config.output_dir.mkdir(exist_ok=True)
    config.brand_name = 'Test Brand'
    config.brand_accent_color = '#FF0000'
    config.brand_text_color = '#FFFFFF'
    return config


def test_renderer_init(mock_config):
    """Test renderer initialization."""
    renderer = ReelRenderer(mock_config)
    assert renderer.width == 1080
    assert renderer.height == 1920
    assert renderer.fps == 30


def test_hex_to_rgb_conversion():
    """Test hex to RGB conversion."""
    rgb = ReelRenderer._hex_to_rgb('#FF0000')
    assert rgb == (255, 0, 0)

    rgb = ReelRenderer._hex_to_rgb('#00FF00')
    assert rgb == (0, 255, 0)

    rgb = ReelRenderer._hex_to_rgb('#0000FF')
    assert rgb == (0, 0, 255)


@patch('renderer.concatenate_videoclips')
@patch('renderer.ColorClip')
def test_render_creates_output_file(mock_color_clip, mock_concat, mock_config):
    """Test that render creates output file."""
    mock_clip = Mock()
    mock_clip.write_videofile = Mock()
    mock_concat.return_value = mock_clip
    mock_color_clip.return_value = Mock()

    renderer = ReelRenderer(mock_config)
    prompt = 'Test prompt'
    ai_responses = [
        {'provider': 'Claude', 'text': 'Response 1'},
        {'provider': 'GPT-4o', 'text': 'Response 2'},
    ]

    with patch.object(renderer, '_create_intro_card', return_value=mock_clip), \
         patch.object(renderer, '_create_response_card', return_value=mock_clip):
        result = renderer.render(prompt, ai_responses)
        assert 'reel.mp4' in result