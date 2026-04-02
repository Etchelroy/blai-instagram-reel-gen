# renderer.py
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import moviepy.editor as mpy
import textwrap

logger = logging.getLogger(__name__)


class RendererModule:
    def __init__(self, config):
        self.config = config
        self.width = 1080
        self.height = 1920
        self.fps = 30
        self.bg_color = (20, 20, 30)  # Dark background

    def _parse_color(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _create_intro_card(self) -> Image.Image:
        """Create intro card with prompt."""
        img = Image.new("RGB", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
            subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()

        accent_color = self._parse_color(self.config.brand_primary_color)
        
        # Draw accent line
        draw.rectangle([(0, 300), (self.width, 350)], fill=accent_color)
        
        # Draw title
        draw.text((540, 960), "AI Insights", font=title_font, fill=(255, 255, 255), anchor="mm")
        draw.text((540, 1100), "Multiple perspectives on one question", font=subtitle_font, fill=(180, 180, 180), anchor="mm")

        return img

    def _create_ai_card(self, provider: str, response: str) -> Image.Image:
        """Create card for single AI provider response."""
        img = Image.new("RGB", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        try:
            provider_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
        except:
            provider_font = ImageFont.load_default()
            text_font = ImageFont.load_default()

        accent_color = self._parse_color(self.config.brand_primary_color)
        
        # Draw accent bar
        draw.rectangle([(0, 0), (self.width, 120)], fill=accent_color)
        draw.text((540, 60), provider, font=provider_font, fill=(255, 255, 255), anchor="mm")
        
        # Wrap and draw response text
        wrapped_text = textwrap.fill(response, width=50)
        draw.multiline_text(
            (540, 600),
            wrapped_text,
            font=text_font,
            fill=(220, 220, 220),
            anchor="mm",
            align="center"
        )

        return img

    def render(self, prompt: str, ai_responses: list) -> str:
        """Render full reel with intro + AI cards + transitions."""
        logger.info(f"Rendering reel with {len(ai_responses)} AI responses")
        
        clips = []
        
        # Intro card (2 seconds)
        intro_img = self._create_intro_card()
        intro_path = f"{self.config.output_dir}/intro.png"
        intro_img.save(intro_path)
        intro_clip = mpy.ImageClip(intro_path).set_duration(2)
        clips.append(intro_clip)
        
        # AI cards (3 seconds each with fade)
        card_duration = 3
        fade_duration = 0.5
        
        for response in ai_responses[:4]:  # Limit to 4 providers
            card_img = self._create_ai_card(response.get("provider", "Unknown"), response.get("response", ""))
            card_path = f"{self.config.output_dir}/card_{len(clips)}.png"
            card_img.save(card_path)
            card_clip = mpy.ImageClip(card_path).set_duration(card_duration)
            card_clip = card_clip.crossfadeout(fade_duration)
            clips.append(card_clip)
        
        # Concatenate all clips
        final_clip = mpy.concatenate_videoclips(clips)
        
        # Set target duration (15-25s)
        target_duration = min(25, max(15, final_clip.duration))
        if final_clip.duration < target_duration:
            final_clip = final_clip.speedx(final_clip.duration / target_duration)
        elif final_clip.duration > target_duration:
            final_clip = final_clip.speedx(final_clip.duration / target_duration)
        
        # Write video
        output_path = f"{self.config.output_dir}/reel.mp4"
        final_clip.write_videofile(
            output_path,
            fps=self.fps,
            codec="libx264",
            audio=False,
            verbose=False,
            logger=None
        )
        
        logger.info(f"Reel rendered: {output_path} ({final_clip.duration:.1f}s)")
        return output_path