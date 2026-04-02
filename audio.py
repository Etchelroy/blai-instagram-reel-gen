import logging
from pathlib import Path
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

logger = logging.getLogger(__name__)


class AudioMixer:
    """Mix background music with video or fallback to silent."""

    def __init__(self, config):
        self.config = config
        self.music_file = Path(config.music_file)

    def mix(self, video_path: str) -> str:
        """Mix audio or return silent video."""
        try:
            # Load video
            video = VideoFileClip(video_path)

            # Check if music file exists
            if not self.music_file.exists():
                logger.warning(f'Music file not found: {self.music_file}. Returning silent video.')
                output_path = self.config.output_dir / 'reel_final.mp4'
                video.write_videofile(
                    str(output_path),
                    fps=30,
                    codec='libx264',
                    audio_codec='aac',
                    verbose=False,
                    logger=None,
                )
                return str(output_path)

            # Load background music
            music = AudioFileClip(str(self.music_file))

            # Loop music to match video duration
            if music.duration < video.duration:
                num_loops = int(video.duration / music.duration) + 1
                music_list = [music] * num_loops
                from moviepy.editor import concatenate_audioclips
                music = concatenate_audioclips(music_list).subclipped(0, video.duration)
            else:
                music = music.subclipped(0, video.duration)

            # Reduce music volume (mix at 30% volume)
            music = music.volumex(0.3)

            # Composite audio (video original + background music)
            if video.audio:
                audio_composite = CompositeAudioClip([video.audio, music])
            else:
                audio_composite = music

            video = video.set_audio(audio_composite)

            # Export
            output_path = self.config.output_dir / 'reel_final.mp4'
            video.write_videofile(
                str(output_path),
                fps=30,
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None,
            )

            logger.info(f'Audio mixed successfully: {output_path}')
            return str(output_path)

        except Exception as e:
            logger.error(f'Audio mixing error: {e}. Returning silent video.')
            # Fallback: return silent video
            video = VideoFileClip(video_path)
            output_path = self.config.output_dir / 'reel_final.mp4'
            video.write_videofile(
                str(output_path),
                fps=30,
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None,
            )
            return str(output_path)