import logging
from pathlib import Path
from typing import List, Dict
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class ReelRenderer:
    """Render Instagram reel with intro card and AI response cards."""

    WIDTH = 1080
    HEIGHT = 1920
    FPS = 30
    CARD_DURATION = 3  # seconds per card
    INTRO_DURATION = 2  # seconds for intro card
    FADE_DURATION = 0.5  # seconds for transitions

    def __init__(self, config):
        self.config = config
        self.output_dir = Path('output')
        self.output_dir.mkdir(exist_ok=True)

    def render(self, prompt: str, ai_responses: List[Dict[str, str]]) -> str:
        """Render reel video with intro and AI response cards."""
        logger.info(f'Starting reel render for prompt: {prompt}')

        # Calculate total duration
        total_frames = int(
            (self.INTRO_DURATION + len(ai_responses) * self.CARD_DURATION + 
             len(ai_responses) * self.FADE_DURATION) * self.FPS
        )
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        output_path = self.output_dir / 'reel.mp4'
        out = cv2.VideoWriter(str(output_path), fourcc, self.FPS, (self.WIDTH, self.HEIGHT))

        frame_idx = 0

        # Intro card
        intro_frames = int(self.INTRO_DURATION * self.FPS)
        intro_img = self._create_intro_card(prompt)
        for _ in range(intro_frames):
            frame = cv2.cvtColor(np.array(intro_img), cv2.COLOR_RGB2BGR)
            out.write(frame)
            frame_idx += 1

        # AI response cards
        for i, response in enumerate(ai_responses):
            # Fade in
            fade_frames = int(self.FADE_DURATION * self.FPS)
            card_img = self._create_response_card(response)
            for j in range(fade_frames):
                alpha = j / fade_frames
                frame = self._blend_frames(
                    self._get_black_frame(),
                    np.array(card_img),
                    alpha
                )
                out.write(frame)
                frame_idx += 1

            # Display card
            card_frames = int(self.CARD_DURATION * self.FPS)
            for _ in range(card_frames):
                frame = cv2.cvtColor(np.array(card_img), cv2.COLOR_RGB2BGR)
                out.write(frame)
                frame_idx += 1

            # Fade out
            for j in range(fade_frames):
                alpha = 1 - (j / fade_frames)
                frame = self._blend_frames(
                    np.array(card_img),
                    self._get_black_frame(),
                    alpha
                )
                out.write(frame)
                frame_idx += 1

        out.release()
        logger.info(f'Reel saved to {output_path}')
        return str(output_path)

    def _create_intro_card(self, prompt: str) -> Image.Image:
        """Create intro card with prompt text."""
        img = Image.new('RGB', (self.WIDTH, self.HEIGHT), color=self._hex_to_rgb(self.config.brand_primary_color))
        draw = ImageDraw.Draw(img)

        # Add title
        title = "AI Perspectives"
        font_size = 80
        try:
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), title, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (self.WIDTH - text_width) // 2
        draw.text((text_x, 400), title, fill=(255, 255, 255), font=font)

        # Add prompt
        try:
            font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 40)
        except:
            font_small = ImageFont.load_default()

        wrapped_prompt = self._wrap_text(prompt, 40)
        y_offset = 700
        for line in wrapped_prompt:
            bbox = draw.textbbox((0, 0), line, font=font_small)
            text_width = bbox[2] - bbox[0]
            text_x = (self.WIDTH - text_width) // 2
            draw.text((text_x, y_offset), line, fill=(255, 255, 255), font=font_small)
            y_offset += 60

        return img

    def _create_response_card(self, response: Dict[str, str]) -> Image.Image:
        """Create card for AI response."""
        img = Image.new('RGB', (self.WIDTH, self.HEIGHT), color=self._hex_to_rgb(self.config.brand_secondary_color))
        draw = ImageDraw.Draw(img)

        # Provider header
        try:
            font_provider = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 50)
        except:
            font_provider = ImageFont.load_default()

        provider = response.get('provider', 'Unknown')
        draw.text((60, 200), provider, fill=self._hex_to_rgb(self.config.brand_accent_color), font=font_provider)

        # Response text
        try:
            font_text = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 32)
        except:
            font_text = ImageFont.load_default()

        text = response.get('text', '')[:200]
        wrapped_text = self._wrap_text(text, 35)
        y_offset = 400
        for line in wrapped_text:
            draw.text((60, y_offset), line, fill=(255, 255, 255), font=font_text)
            y_offset += 60

        return img

    def _wrap_text(self, text: str, max_chars: int) -> List[str]:
        """Wrap text to fit within max characters per line."""
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            if len(' '.join(current_line + [word])) <= max_chars:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        return lines

    def _get_black_frame(self) -> np.ndarray:
        """Get black frame as numpy array."""
        return np.zeros((self.HEIGHT, self.WIDTH, 3), dtype=np.uint8)

    def _blend_frames(self, frame1: np.ndarray, frame2: np.ndarray, alpha: float) -> np.ndarray:
        """Blend two frames with alpha."""
        return cv2.cvtColor(
            np.array(Image.fromarray(
                (frame1 * (1 - alpha) + frame2 * alpha).astype(np.uint8)
            )), 
            cv2.COLOR_RGB2BGR
        )

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))