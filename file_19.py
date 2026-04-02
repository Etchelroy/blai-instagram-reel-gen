# tests/test_renderer.py
import pytest
import os
from pathlib import Path
from PIL import Image
from renderer import RendererModule
from config import Config


@pytest.fixture
def mock_config():
    config = Config()
    config.brand_primary_color = "#FF6B6B"
    config.brand_secondary_color = "#4ECDC4"
    config.output_dir = "./test_output"
    os.makedirs(config.output_dir, exist_ok=True)
    return config


@pytest.fixture
def renderer(mock_config):
    return RendererModule(mock_config)


def test_parse_color(renderer):
    """Test color parsing."""
    color = renderer._parse_color("#FF6B6B")
    assert color == (255, 107, 107)


def test_parse_color_no_hash(renderer):
    """Test color parsing without hash."""
    color = renderer._parse_color("FF6B6B")
    assert color == (255, 107, 107)


def test_create_intro_card(renderer):
    """Test intro card creation."""
    img = renderer._create_intro_card()
    
    assert isinstance(img, Image.Image)
    assert img.size == (1080, 1920)


def test_create_ai_card(renderer):
    """Test AI card creation."""
    img = renderer._create_ai_card("TestAI", "This is a test response about something interesting.")
    
    assert isinstance(img, Image.Image)
    assert img.size == (1080, 1920)


def test_render_full_reel(renderer):
    """Test full reel rendering."""
    ai_responses = [
        {"provider": "Claude", "response": "Response 1 from Claude about the topic"},
        {"provider": "GPT-4o", "response": "Response 2 from GPT-4o with insights"},
        {"provider": "Gemini", "response": "Response 3 from Gemini with analysis"},
        {"provider": "Llama", "response": "Response 4 from Llama with perspective"}
    ]
    
    output_path = renderer.render("Test prompt", ai_responses)
    
    assert Path(output_path).exists()
    assert output_path.endswith(".mp4")
    
    # Cleanup
    if Path(output_path).exists():
        Path(output_path).unlink()


def test_render_with_empty_responses(renderer):
    """Test rendering with empty responses."""
    ai_responses = []
    
    output_path = renderer.render("Test prompt", ai_responses)
    
    assert Path(output_path).exists()
    
    if Path(output_path).exists():
        Path(output_path).unlink()