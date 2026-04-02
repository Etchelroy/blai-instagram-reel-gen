import argparse
import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def parse_args():
    p = argparse.ArgumentParser(description="Instagram Reel Generator")
    p.add_argument("--prompt", required=True, help="Question/prompt for AI providers")
    p.add_argument("--dry-run", action="store_true", help="Log payload without posting")
    return p.parse_args()


async def run(prompt: str, dry_run: bool):
    from ai_query import query_all
    from renderer import render_video
    from audio import overlay_audio
    from poster import publish_reel

    logger.info("Querying AI providers for: %r", prompt)
    answers = await query_all(prompt)
    for provider, answer in answers.items():
        logger.info("[%s] %.80s...", provider, answer)

    logger.info("Rendering video...")
    raw_video = render_video(prompt, answers, output_path="reel_raw.mp4")

    logger.info("Overlaying audio...")
    final_video = overlay_audio(raw_video, output_path="reel.mp4")

    caption = (
        f"🤖 4 AIs answer: \"{prompt}\"\n\n"
        "Claude • GPT-4o • Gemini • Llama\n"
        "#AI #ArtificialIntelligence #ChatGPT #Claude #Gemini"
    )

    result = publish_reel(final_video, caption, dry_run=dry_run)
    logger.info("Done: %s", result)
    return result


def main():
    args = parse_args()
    asyncio.run(run(args.prompt, args.dry_run))


if __name__ == "__main__":
    main()