import logging
from pathlib import Path
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioFileClip

logger = logging.getLogger(__name__)


class AudioMixer:
    """Mix background music with reel video."""

    def __init__(self, config):
        self.config = config

    def mix(self, video_path: str) -> str:
        """Mix audio into video."""
        try:
            output_path = self.config.output_dir / 'reel_with_audio.mp4'
            
            video = VideoFileClip(video_path)
            
            # Try to add background music if file exists
            music_path = Path(self.config.music_file)
            if music_path.exists():
                try:
                    music = AudioFileClip(str(music_path))
                    
                    # Loop music to match video duration
                    if music.duration < video.duration:
                        # Simple repeat by creating composite
                        music = music.loop(n=int(video.duration / music.duration) + 1)
                    
                    music = music.subclipped(0, video.duration)
                    
                    # Mix audio
                    final_audio = CompositeAudioFileClip([video.audio, music])
                    final_video = video.set_audio(final_audio)
                except Exception as e:
                    logger.warning(f'Could not add music: {e}, using video audio only')
                    final_video = video
            else:
                logger.info(f'Music file not found at {music_path}, using video audio only')
                final_video = video
            
            # Write output
            final_video.write_videofile(
                str(output_path),
                verbose=False,
                logger=None
            )
            
            logger.info(f'Audio mixed to {output_path}')
            return str(output_path)
        except Exception as e:
            logger.error(f'Audio mix error: {e}')
            raise