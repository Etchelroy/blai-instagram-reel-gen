import logging
import os
from pathlib import Path

logger = logging.getLogger("audio")

MUSIC_VOLUME = 0.15


def overlay_music(video_path: str, music_path: str, output_path: str = None) -> str:
    if output_path is None:
        p = Path(video_path)
        output_path = str(p.parent / (p.stem + "_audio" + p.suffix))

    if not os.path.exists(music_path):
        logger.warning(
            f"Music file '{music_path}' not found. Outputting silent video. "
            "See README for music sourcing guidance."
        )
        # just copy video as-is
        import shutil
        if video_path != output_path:
            shutil.copy2(video_path, output_path)
        return output_path

    try:
        try:
            from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
        except ImportError:
            from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip

        video = VideoFileClip(video_path)
        audio = AudioFileClip(music_path)

        # loop or trim music to video length
        video_duration = video.duration
        if audio.duration < video_duration:
            loops = int(video_duration / audio.duration) + 1
            from moviepy.audio.AudioClip import concatenate_audioclips
            audio = concatenate_audioclips([audio] * loops)
        audio = audio.subclip(0, video_duration)
        audio = audio.volumex(MUSIC_VOLUME)

        final = video.set_audio(audio)
        final.write_videofile(
            output_path,
            fps=video.fps,
            codec="libx264",
            audio_codec="aac",
            verbose=False,
            logger=None,
        )
        video.close()
        audio.close()
        logger.info(f"Audio overlaid successfully: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Failed to overlay audio: {e}. Falling back to silent video.")
        import shutil
        if video_path != output_path:
            shutil.copy2(video_path, output_path)
        return output_path