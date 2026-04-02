import os
import shutil
import pytest
from unittest.mock import patch, MagicMock


def test_overlay_audio_missing_music(tmp_path):
    import audio
    src = tmp_path / "input.mp4"
    src.write_bytes(b"fake")
    out = str(tmp_path / "output.mp4")

    with patch("audio.config.BACKGROUND_MUSIC_PATH", str(tmp_path / "missing.mp3")):
        result = audio.overlay_audio(str(src), output_path=out)

    assert result == out
    assert os.path.exists(out)


def test_overlay_audio_with_music(tmp_path):
    import audio
    src = tmp_path / "input.mp4"
    src.write_bytes(b"fake")
    music = tmp_path / "bg.mp3"
    music.write_bytes(b"fake_audio")
    out = str(tmp_path / "output.mp4")

    mock_video = MagicMock()
    mock_video.duration = 20.0
    mock_audio = MagicMock()
    mock_audio.duration = 30.0
    mock_audio.volumex.return_value = mock_audio
    mock_audio.subclip.return_value = mock_audio
    mock_video.set_audio.return_value = mock_video

    with patch("audio.config.BACKGROUND_MUSIC_PATH", str(music)), \
         patch("audio.VideoFileClip", return_value=mock_video), \
         patch("audio.AudioFileClip", return_value=mock_audio):
        result = audio.overlay_audio(str(src), output_path=out)

    mock_video.write_videofile.assert_called_once()
    assert result == out


def test_overlay_audio_exception_fallback(tmp_path):
    import audio
    src = tmp_path / "input.mp4"
    src.write_bytes(b"fake")
    music = tmp_path / "bg.mp3"
    music.write_bytes(b"fake")
    out = str(tmp_path / "output.mp4")

    with patch("audio.config.BACKGROUND_MUSIC_PATH", str(music)), \
         patch("audio.VideoFileClip", side_effect=Exception("crash")):
        result = audio.overlay_audio(str(src), output_path=out)

    assert result == out