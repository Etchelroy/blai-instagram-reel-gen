import os
import logging
import textwrap
from pathlib import Path
from typing import Dict

import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("renderer")

WIDTH, HEIGHT = 1080, 1920
FPS = 30
CARD_DURATION = 4.0
FADE_DURATION = 0.5
INTRO_DURATION = 4.0

BG_COLOR = (10, 10, 20)
TEXT_COLOR = (240, 240, 240)
SUBTITLE_COLOR = (180, 180, 180)
ACCENT_COLORS = {
    "Claude":     (212, 165, 116),
    "GPT-4o":    (116, 192, 252),
    "Gemini":    (169, 209, 142),
    "Groq/Llama": (201, 177, 255),
}

FONT_SIZE_TITLE = 72
FONT_SIZE_PROVIDER = 52
FONT_SIZE_BODY = 40
FONT_SIZE_PROMPT = 44


def _get_font(size: int):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _get_font_regular(size: int):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _draw_rounded_rect(draw, xy, radius, fill, outline=None, outline_width=4):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill,
                            outline=outline, width=outline_width)


def _wrap_text(text: str, font, max_width: int, draw: ImageDraw.ImageDraw) -> list:
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _make_intro_frame(prompt: str, alpha: float = 1.0) -> np.ndarray:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # gradient-like background bars
    for i in range(0, HEIGHT, 4):
        shade = int(10 + 8 * abs((i / HEIGHT) - 0.5))
        draw.line([(0, i), (WIDTH, i)], fill=(shade, shade, shade + 10))

    # top accent line
    draw.rectangle([(0, 0), (WIDTH, 8)], fill=(100, 100, 220))

    # center card
    card_x1, card_y1 = 80, HEIGHT // 2 - 400
    card_x2, card_y2 = WIDTH - 80, HEIGHT // 2 + 400
    _draw_rounded_rect(draw, [card_x1, card_y1, card_x2, card_y2],
                       radius=40, fill=(25, 25, 45), outline=(80, 80, 160), outline_width=3)

    font_title = _get_font(FONT_SIZE_TITLE)
    font_sub = _get_font_regular(FONT_SIZE_PROMPT)
    font_tag = _get_font_regular(36)

    # AI DEBATE label
    tag = "⚡ AI DEBATE"
    bbox = draw.textbbox((0, 0), tag, font=font_tag)
    tw = bbox[2] - bbox[0]
    draw.text(((WIDTH - tw) // 2, card_y1 + 60), tag, font=font_tag, fill=(140, 140, 220))

    # divider
    draw.rectangle([(card_x1 + 60, card_y1 + 120), (card_x2 - 60, card_y1 + 124)],
                   fill=(60, 60, 100))

    # prompt text
    prompt_lines = _wrap_text(prompt, font_sub, card_x2 - card_x1 - 120, draw)
    y_text = card_y1 + 160
    for line in prompt_lines[:6]:
        bbox = draw.textbbox((0, 0), line, font=font_sub)
        tw = bbox[2] - bbox[0]
        draw.text(((WIDTH - tw) // 2, y_text), line, font=font_sub, fill=TEXT_COLOR)
        y_text += bbox[3] - bbox[1] + 16

    # footer
    footer = "4 AI Models Answer"
    bbox = draw.textbbox((0, 0), footer, font=font_tag)
    tw = bbox[2] - bbox[0]
    draw.text(((WIDTH - tw) // 2, card_y2 - 80), footer, font=font_tag, fill=(120, 120, 180))

    # bottom accent
    draw.rectangle([(0, HEIGHT - 8), (WIDTH, HEIGHT)], fill=(100, 100, 220))

    frame = np.array(img).astype(np.float32)
    frame = (frame * alpha).clip(0, 255).astype(np.uint8)
    return frame


def _make_ai_card_frame(provider: str, response: str, prompt: str,
                         alpha: float = 1.0) -> np.ndarray:
    accent = ACCENT_COLORS.get(provider, (180, 180, 180))
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    for i in range(0, HEIGHT, 4):
        shade = int(10 + 6 * abs((i / HEIGHT) - 0.5))
        draw.line([(0, i), (WIDTH, i)], fill=(shade, shade, shade + 8))

    # top accent bar
    draw.rectangle([(0, 0), (WIDTH, 10)], fill=accent)

    # provider header area
    draw.rectangle([(0, 10), (WIDTH, 200)], fill=(20, 20, 35))
    font_provider = _get_font(FONT_SIZE_PROVIDER)
    font_body = _get_font_regular(FONT_SIZE_BODY)
    font_small = _get_font_regular(34)

    # provider name with color dot
    dot_x, dot_y = 80, 90
    draw.ellipse([(dot_x, dot_y - 20), (dot_x + 40, dot_y + 20)], fill=accent)
    draw.text((140, 65), provider, font=font_provider, fill=accent)

    # prompt reminder
    prompt_short = (prompt[:55] + "…") if len(prompt) > 55 else prompt
    draw.text((80, 155), f'"{prompt_short}"', font=font_small, fill=(130, 130, 160))

    # response card
    card_margin = 60
    card_top = 230
    card_bottom = HEIGHT - 200
    _draw_rounded_rect(draw,
                       [card_margin, card_top, WIDTH - card_margin, card_bottom],
                       radius=36,
                       fill=(22, 22, 40),
                       outline=accent,
                       outline_width=3)

    # response text
    padding = 60
    text_x1 = card_margin + padding
    text_width = WIDTH - card_margin * 2 - padding * 2
    y_pos = card_top + padding

    response_lines = _wrap_text(response, font_body, text_width, draw)
    max_lines = 14
    if len(response_lines) > max_lines:
        response_lines = response_lines[:max_lines - 1]
        response_lines.append("…")

    for line in response_lines:
        if y_pos > card_bottom - 60:
            break
        draw.text((text_x1, y_pos), line, font=font_body, fill=TEXT_COLOR)
        bbox = draw.textbbox((0, 0), line, font=font_body)
        y_pos += bbox[3] - bbox[1] + 14

    # bottom accent
    draw.rectangle([(0, HEIGHT - 10), (WIDTH, HEIGHT)], fill=accent)

    # page indicator dots
    providers_list = ["Claude", "GPT-4o", "Gemini", "Groq/Llama"]
    dot_spacing = 30
    total_dots = len(providers_list)
    start_x = WIDTH // 2 - (total_dots * dot_spacing) // 2
    current_idx = providers_list.index(provider) if provider in providers_list else 0
    for i, _ in enumerate(providers_list):
        color = accent if i == current_idx else (60, 60, 80)
        r = 8 if i == current_idx else 6
        cx = start_x + i * dot_spacing
        cy = HEIGHT - 60
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=color)

    frame = np.array(img).astype(np.float32)
    frame = (frame * alpha).clip(0, 255).astype(np.uint8)
    return frame


def render_reel(prompt: str, responses: Dict[str, str], output_path: str = "reel.mp4") -> str:
    try:
        from moviepy.editor import VideoClip, concatenate_videoclips
    except ImportError:
        from moviepy import VideoClip, concatenate_videoclips

    providers = ["Claude", "GPT-4o", "Gemini", "Groq/Llama"]
    clips = []

    logger.info("Rendering intro card...")

    def make_intro_frame(t):
        if t < FADE_DURATION:
            alpha = t / FADE_DURATION
        elif t > INTRO_DURATION - FADE_DURATION:
            alpha = (INTRO_DURATION - t) / FADE_DURATION
        else:
            alpha = 1.0
        return _make_intro_frame(prompt, alpha=alpha)

    intro_clip = VideoClip(make_intro_frame, duration=INTRO_DURATION)
    intro_clip = intro_clip.set_fps(FPS)
    clips.append(intro_clip)

    for provider in providers:
        response = responses.get(provider, "No response available.")
        logger.info(f"Rendering card for {provider}...")

        # capture for closure
        _provider = provider
        _response = response

        def make_card_frame(t, p=_provider, r=_response):
            if t < FADE_DURATION:
                alpha = t / FADE_DURATION
            elif t > CARD_DURATION - FADE_DURATION:
                alpha = (CARD_DURATION - t) / FADE_DURATION
            else:
                alpha = 1.0
            return _make_ai_card_frame(p, r, prompt, alpha=alpha)

        card_clip = VideoClip(make_card_frame, duration=CARD_DURATION)
        card_clip = card_clip.set_fps(FPS)
        clips.append(card_clip)

    logger.info("Concatenating clips...")
    final = concatenate_videoclips(clips, method="compose")

    total_duration = INTRO_DURATION + CARD_DURATION * len(providers)
    logger.info(f"Total video duration: {total_duration:.1f}s (target: 15-25s)")
    assert 15 <= total_duration <= 25, f"Duration {total_duration} out of 15-25s range"

    output_path = str(output_path)
    logger.info(f"Writing video to {output_path}...")
    final.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio=False,
        verbose=False,
        logger=None,
    )
    logger.info(f"Video written: {output_path}")
    return output_path