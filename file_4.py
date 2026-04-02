import logging
from pathlib import Path
from moviepy.editor import (
    TextClip, ImageClip, CompositeVideoClip, concatenate_videoclips,
    ColorClip, CompositeAudioFileClip
)
from PIL import Image, ImageDraw, ImageFont
import numpy as np

logger = logging.getLogger(__name__)


class ReelRenderer:
    """Render Instagram Reels (1080x1920) with AI responses."""

    def __init__(self, config):
        self.config = config
        self.width = 1080
        self.height = 1920
        self.fps = 30
        self.duration_per_slide = 5

    def render(self, prompt: str, ai_responses: list) -> str:
        """Render reel from prompt and AI responses."""
        try:
            output_path = self.config.output_dir / 'reel.mp4'
            
            # Create slides
            slides = []
            
            # Title slide
            title_slide = self._create_text_slide(
                prompt, 
                'Title',
                self.duration_per_slide
            )
            slides.append(title_slide)
            
            # AI response slides
            for response in ai_responses:
                response_slide = self._create_text_slide(
                    f"{response['provider']}\n{response['text']}",
                    response['provider'],
                    self.duration_per_slide
                )
                slides.append(response_slide)
            
            # Concatenate and save
            final_video = concatenate_videoclips(slides)
            final_video.write_videofile(
                str(output_path),
                fps=self.fps,
                verbose=False,
                logger=None
            )
            
            logger.info(f'Reel rendered to {output_path}')
            return str(output_path)
        except Exception as e:
            logger.error(f'Render error: {e}')
            raise

    def _create_text_slide(self, text: str, title: str, duration: float):
        """Create a text slide with fade effect."""
        try:
            # Create background
            bg = ColorClip(size=(self.width, self.height), color=(10, 10, 10)).set_duration(duration)
            
            # Create text
            txt = TextClip(
                text,
                fontsize=40,
                color=self.config.brand_text_color,
                size=(self.width - 60, self.height - 300),
                method='caption',
                font='Arial'
            ).set_duration(duration)
            
            txt = txt.set_position('center')
            
            # Composite
            video = CompositeVideoClip([bg, txt])
            return video
        except Exception as e:
            logger.error(f'Slide creation error: {e}')
            raise