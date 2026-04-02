import logging
import os
import textwrap
from typing import Dict

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    ImageClip, concatenate_videoclips, VideoFileClip,
    CompositeVideoClip, ColorClip,
)

import config
from ai_query import BRAND_COLORS, PROVIDER_LABELS

logger = logging.getLogger(__name__)

W, H = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
CARD_DUR = config.CARD_DURATION
FADE = config.FADE_DURATION

BG_COLOR = (15, 15, 25)
TEXT_COLOR = (240, 240, 240)
ACCENT_BG = (30, 30, 45)


def _hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _get_font(size: int):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _make_intro_frame(prompt: str) -> np.ndarray:
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # gradient bar at top
    for y in range(120):
        alpha = int(255 * (1 - y / 120))
        draw.line([(0, y), (W, y)], fill=(80, 60, 180))

    font_title = _get_font(64)
    font_sub = _get_font(40)
    font_prompt = _get_font(48)

    draw.text((W // 2, 200), "AI PERSPECTIVES", font=font_title,
              fill=(220, 200, 255), anchor="mm")
    draw.text((W // 2, 290), "4 AIs answer one question", font=font_sub,
              fill=(160, 160, 200), anchor="mm")

    # divider
    draw.rectangle([(120, 360), (W - 120, 365)], fill=(80, 60, 180))

    # prompt box
    draw.rounded_rectangle([(80, 400), (W - 80, 700)], radius=32, fill=ACCENT_BG)
    wrapped = textwrap.fill(prompt, width=28)
    draw.text((W // 2, 550), wrapped, font=font_prompt,
              fill=TEXT_COLOR, anchor="mm", align="center")

    # bottom label
    draw.text((W // 2, H - 100), "Swipe to see answers →", font=font_sub,
              fill=(140, 140, 180), anchor="mm")

    return np.array(img)


def _make_ai_card_frame(provider: str, answer: str) -> np.ndarray:
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    accent = _hex_to_rgb(BRAND_COLORS[provider])
    label = PROVIDER_LABELS[provider]

    # top accent bar
    draw.rectangle([(0, 0), (W, 16)], fill=accent)

    # provider badge
    draw.rounded_rectangle([(80, 80), (W - 80, 220)], radius=24, fill=accent)
    font_label = _get_font(60)
    draw.text((W // 2, 150), label, font=font_label, fill=(255, 255, 255), anchor="mm")

    # answer box
    draw.rounded_rectangle([(60, 280), (W - 60, H - 200)], radius=28, fill=ACCENT_BG)

    font_ans = _get_font(42)
    wrapped = textwrap.fill(answer, width=30)
    lines = wrapped.split("\n")
    # truncate if too long
    max_lines = 14
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:40] + "..."

    y_start = 380
    line_h = 56
    for i, line in enumerate(lines):
        draw.text((W // 2, y_start + i * line_h), line, font=font_ans,
                  fill=TEXT_COLOR, anchor="mm", align="center")

    # accent dot bottom
    draw.ellipse([(W // 2 - 12, H - 130), (W // 2 + 12, H - 106)], fill=accent)

    return np.array(img)


def render_video(prompt: str, answers: Dict[str, str], output_path: str = "reel.mp4") -> str:
    logger.info("Rendering video to %s", output_path)

    clips = []

    intro_frame = _make_intro_frame(prompt)
    intro_clip = (ImageClip(intro_frame)
                  .set_duration(CARD_DUR)
                  .fadein(FADE)
                  .fadeout(FADE))
    clips.append(intro_clip)

    for provider in ["claude", "gpt4o", "gemini", "groq"]:
        answer = answers.get(provider, "No response available.")
        frame = _make_ai_card_frame(provider, answer)
        clip = (ImageClip(frame)
                .set_duration(CARD_DUR)
                .fadein(FADE)
                .fadeout(FADE))
        clips.append(clip)

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio=False,
        preset="fast",
        logger=None,
    )
    logger.info("Video rendered: %s (%.1fs)", output_path, final.duration)
    return output_path