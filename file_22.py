import os
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

import renderer


ANSWERS = {
    "claude": "Consciousness remains one of the deepest mysteries.",
    "gpt4o": "AI does not experience subjective awareness.",
    "gemini": "The question depends on how we define consciousness.",
    "groq": "Current AI systems lack phenomenal experience.",
}


def test_make_intro_frame_shape():
    frame = renderer._make_intro_frame("Is AI conscious?")
    assert isinstance(frame, np.ndarray)
    assert frame.shape == (renderer.H, renderer.W, 3)


def test_make_ai_card_frame_shape():
    for provider in ["claude", "gpt4o", "gemini", "groq"]:
        frame = renderer._make_ai_card_frame(provider, ANSWERS[provider])
        assert frame.shape == (renderer.H, renderer.W, 3)


def test_hex_to_rgb():
    assert renderer._hex_to_rgb("#D97757") == (217, 119, 87)
    assert renderer._hex_to_rgb("#10A37F") == (16, 163, 127)


def test_render_video_creates_file(tmp_path):
    out = str(tmp_path / "test.mp4")
    with patch("renderer.ImageClip") as mock_clip_cls:
        mock_clip = MagicMock()
        mock_clip.set_duration.return_value = mock_clip
        mock_clip.fadein.return_value = mock_clip
        mock_clip.fadeout.return_value = mock_clip
        mock_clip_cls.return_value = mock_clip

        with patch("renderer.concatenate_videoclips") as mock_concat:
            mock_final = MagicMock()
            mock_final.duration = 20.0
            mock_concat.return_value = mock_final

            result = renderer.render_video("test?", ANSWERS, output_path=out)

    mock_final.write_videofile.assert_called_once()
    assert result == out