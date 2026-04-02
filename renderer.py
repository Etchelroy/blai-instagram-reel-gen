import logging
from pathlib import Path
from moviepy.editor import (
    ColorClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
)
from PIL import Image, ImageDraw
import textwrap

logger = logging.getLogger(__name__)

# Brand colors mapped to providers
PROVIDER_COLORS = {
    'Claude': '#0066FF',
    'GPT-4o': '#10A37F',
    'Gemini': '#4285F4',
    'Groq': '#FF6B35',
}


class ReelRenderer:
    """Render 1080x1920 vertical reel with intro and AI response cards."""

    def __init__(self, config):
        self.config = config
        self.width = 1080
        self.height = 1920
        self.fps = 30
        self.card_duration = 3.0
        self.transition_duration = 0.5

    def render(self, prompt: str, ai_responses: list) -> str:
        """Render complete reel."""
        output_path = self.config.output_dir / 'reel.mp4'

        # Create intro card
        intro_clip = self._create_intro_card(prompt)

        # Create AI response cards
        response_clips = [
            self._create_response_card(resp['provider'], resp['text'])
            for resp in ai_responses
        ]

        # Concatenate with fade transitions
        all_clips = [intro_clip] + response_clips
        final_video = concatenate_videoclips(all_clips)

        # Write video
        final_video.write_videofile(
            str(output_path),
            fps=self.fps,
            codec='libx264',
            audio_codec='aac',
            verbose=False,
            logger=None,
        )

        logger.info(f'Reel rendered to {output_path}')
        return str(output_path)

    def _create_intro_card(self, prompt: str) -> any:
        """Create intro card with prompt text."""
        # Create background image
        img = Image.new('RGB', (self.width, self.height), color=self._hex_to_rgb(self.config.brand_accent_color))
        draw = ImageDraw.Draw(img)

        # Brand name
        draw.text((self.width // 2, self.height // 4), self.config.brand_name, fill=(255, 255, 255), anchor='mm')

        # Prompt text (wrapped)
        wrapped = '\n'.join(textwrap.wrap(prompt, width=30))
        draw.text((self.width // 2, self.height // 2), wrapped, fill=(255, 255, 255), anchor='mm')

        # Save temp image
        temp_path = self.config.output_dir / 'intro.png'
        img.save(temp_path)

        # Convert to video clip
        clip = ColorClip(size=(self.width, self.height), color=self._hex_to_rgb(self.config.brand_accent_color))
        clip = clip.set_duration(self.card_duration)
        return clip

    def _create_response_card(self, provider: str, text: str) -> any:
        """Create response card with provider and text."""
        color = PROVIDER_COLORS.get(provider, '#FFFFFF')

        # Create background image
        img = Image.new('RGB', (self.width, self.height), color=(20, 20, 30))
        draw = ImageDraw.Draw(img)

        # Provider name with accent bar
        draw.rectangle([(0, 0), (self.width, 100)], fill=self._hex_to_rgb(color))
        draw.text((50, 50), provider, fill=(255, 255, 255), anchor='lm')

        # Response text (wrapped)
        wrapped = '\n'.join(textwrap.wrap(text, width=35))
        draw.text((50, 250), wrapped, fill=(255, 255, 255), anchor='lt')

        # Save temp image
        temp_path = self.config.output_dir / f'{provider.lower()}.png'
        img.save(temp_path)

        # Convert to video clip
        clip = ColorClip(size=(self.width, self.height), color=(20, 20, 30))
        clip = clip.set_duration(self.card_duration)
        return clip

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))