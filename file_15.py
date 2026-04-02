# audio.py
import logging
from pathlib import Path
import moviepy.editor as mpy

logger = logging.getLogger(__name__)


class AudioModule:
    def __init__(self, config):
        self.config = config

    def add_audio(self, video_path: str) -> str:
        """Add background music to video with fallback to silent."""
        try:
            video = mpy.VideoFileClip(video_path)
            
            if not self.config.background_music_path or not Path(self.config.background_music_path).exists():
                logger.warning(f"Music file not found or not configured: {self.config.background_music_path}")
                logger.info("Returning video without audio overlay")
                output_path = f"{self.config.output_dir}/reel_final.mp4"
                video.write_videofile(
                    output_path,
                    fps=video.fps,
                    codec="libx264",
                    audio=False,
                    verbose=False,
                    logger=None
                )
                return output_path
            
            # Load music and loop it
            music = mpy.AudioFileClip(self.config.background_music_path)
            
            # Loop music to match video duration
            if music.duration < video.duration:
                n_loops = int(video.duration / music.duration) + 1
                music = mpy.concatenate_audioclips([music] * n_loops)
                music = music.subclipped(0, video.duration)
            else:
                music = music.subclipped(0, video.duration)
            
            # Reduce music volume (20% of original)
            music = music.volumex(0.2)
            
            # Composite audio
            final_audio = mpy.CompositeAudioClip([music])
            final_video = video.set_audio(final_audio)
            
            output_path = f"{self.config.output_dir}/reel_final.mp4"
            final_video.write_videofile(
                output_path,
                fps=video.fps,
                codec="libx264",
                audio_codec="aac",
                verbose=False,
                logger=None
            )
            
            logger.info(f"Audio added successfully: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error adding audio: {e}")
            logger.info("Falling back to silent video")
            video = mpy.VideoFileClip(video_path)
            output_path = f"{self.config.output_dir}/reel_final.mp4"
            video.write_videofile(
                output_path,
                fps=video.fps,
                codec="libx264",
                audio=False,
                verbose=False,
                logger=None
            )
            return output_path