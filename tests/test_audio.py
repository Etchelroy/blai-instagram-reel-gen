import pytest
import os
import shutil
from unittest.mock import patch, MagicMock
from pathlib import Path


def test_overlay_music_missing_file(tmp_path):
    # Create a dummy video file
    video_path = str(tmp_path / "input.mp4")
    output_path = str(tmp_path / "output.mp4")
    Path(video_path).write_bytes(b"fake video data")

    from audio import overlay_music
    result = overlay_music(video_path, str(tmp_path / "nonexistent.mp3"), output_path=output_path)
    assert result == output_path
    assert os.path.exists(output_path)


def test_overlay_music_missing_file_same_path(tmp_path):
    video_path = str(tmp_path / "reel.mp4")
    Path(video_path).write_bytes(b"fake video data")

    from audio import overlay_music
    result = overlay_music(video_path, "nonexistent_music.mp3", output_path=video_path)
    assert result == video_path


def test_overlay_music_with_file(tmp_path):
    video_path = str(tmp_path / "input.mp4")
    music_path = str(tmp_path / "music.mp3")
    output_path = str(tmp_path / "output.mp4")
    Path(video_path).write_bytes(b"fake video data")
    Path(music_path).write_bytes(b"fake audio data")

    mock_video = MagicMock()
    mock_video.duration = 20.0
    mock_video.fps = 30

    mock_audio = MagicMock()
    mock_audio.duration = 30.0
    mock_audio.subclip.return_value = mock_audio
    mock_audio.volumex.return_value = mock_audio

    mock_final = MagicMock()
    mock_video.set_audio.return_value = mock_final
    mock_final.write_videofile = MagicMock()

    import sys
    mock_moviepy_editor = MagicMock()
    mock_moviepy_editor.VideoFileClip.return_value = mock_video
    mock_moviepy_editor.AudioFileClip.return_value = mock_audio

    with patch.dict(sys.modules, {"moviepy.editor": mock_moviepy_editor}):
        with patch("audio.VideoFileClip", return_value=mock_video):
            with patch("audio.AudioFileClip", return_value=mock_audio):
                from audio import overlay_music
                result = overlay_music(video_path, music_path, output_path=output_path)
                assert isinstance(result, str)


def test_overlay_music_exception_fallback(tmp_path):
    video_path = str(tmp_path / "input.mp4")
    music_path = str(tmp_path / "music.mp3")
    output_path = str(tmp_path / "output.mp4")
    Path(video_path).write_bytes(b"fake video data")
    Path(music_path).write_bytes(b"fake audio data")

    with patch("audio.VideoFileClip", side_effect=Exception("moviepy error")):
        from audio import overlay_music
        result = overlay_music(video_path, music_path, output_path=output_path)
        assert result == output_path
        assert os.path.exists(output_path)