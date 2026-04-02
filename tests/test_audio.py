import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from audio import AudioMixer


@pytest.fixture
def mock_config():
    config = Mock()
    config.music_file = 'background_music.mp3'
    config.output_dir = Path('./test_output')
    config.output_dir.mkdir(exist_ok=True)
    return config


def test_audio_mixer_init(mock_config):
    """Test AudioMixer initialization."""
    mixer = AudioMixer(mock_config)
    assert mixer.config == mock_config
    assert mixer.music_file == Path('background_music.mp3')


@patch('audio.VideoFileClip')
def test_mix_returns_output_path_when_music_missing(mock_video_clip, mock_config):
    """Test that mix returns silent video when music file is missing."""
    mock_video = Mock()
    mock_video.duration = 10
    mock_video.audio = None
    mock_video.write_videofile = Mock()
    mock_video_clip.return_value = mock_video

    mixer = AudioMixer(mock_config)
    result = mixer.mix('test_video.mp4')

    assert 'reel_final.mp4' in result


@patch('audio.VideoFileClip')
@patch('audio.AudioFileClip')
def test_mix_with_music_file_present(mock_audio_clip, mock_video_clip, mock_config):
    """Test mix when music file is present."""
    mock_video = Mock()
    mock_video.duration = 10
    mock_video.audio = Mock()
    mock_video.write_videofile = Mock()
    mock_video.set_audio = Mock(return_value=mock_video)
    mock_video_clip.return_value = mock_video

    mock_music = Mock()
    mock_music.duration = 5
    mock_music.subclipped = Mock(return_value=mock_music)
    mock_music.volumex = Mock(return_value=mock_music)
    mock_audio_clip.return_value = mock_music

    with patch('audio.Path.exists', return_value=True), \
         patch('audio.CompositeAudioClip'):
        mixer = AudioMixer(mock_config)
        result = mixer.mix('test_video.mp4')
        assert 'reel_final.mp4' in result