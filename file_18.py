import logging
import os

from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

import config

logger = logging.getLogger(__name__)


def overlay_audio(video_path: str, output_path: str = "reel_audio.mp4") -> str:
    music_path = config.BACKGROUND_MUSIC_PATH

    if not os.path.exists(music_path):
        logger.warning("Music file not found at %s — exporting silent video", music_path)
        if video_path != output_path:
            import shutil
            shutil.copy(video_path, output_path)
        return output_path

    try:
        video = VideoFileClip(video_path)
        audio = AudioFileClip(music_path).volumex(config.MUSIC_VOLUME)

        if audio.duration < video.duration:
            loops = int(video.duration / audio.duration) + 1
            from moviepy.editor import concatenate_audioclips
            audio = concatenate_audioclips([audio] * loops)

        audio = audio.subclip(0, video.duration)
        video_with_audio = video.set_audio(audio)
        video_with_audio.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="fast",
            logger=None,
        )
        logger.info("Audio overlay complete: %s", output_path)
        return output_path
    except Exception as e:
        logger.error("Audio overlay failed: %s — falling back to silent", e)
        if video_path != output_path:
            import shutil
            shutil.copy(video_path, output_path)
        return output_path