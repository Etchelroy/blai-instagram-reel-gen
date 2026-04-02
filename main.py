import argparse
import asyncio
import logging
import sys
import os
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("main")


def parse_args():
    parser = argparse.ArgumentParser(description="Instagram Reel Generator")
    parser.add_argument("--prompt", required=True, help="Text prompt to query AI models")
    parser.add_argument("--dry-run", action="store_true", help="Log payloads without posting")
    parser.add_argument("--output", default="reel.mp4", help="Output video filename")
    parser.add_argument("--music", default="background.mp3", help="Background music file path")
    return parser.parse_args()


async def main():
    args = parse_args()
    logger.info(f"Starting reel generation for prompt: '{args.prompt}'")
    logger.info(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")

    from config import load_config
    cfg = load_config()

    from ai_query import query_all_providers
    logger.info("Querying all AI providers in parallel...")
    responses = await query_all_providers(args.prompt)
    logger.info(f"Received responses from {len(responses)} providers")
    for provider, resp in responses.items():
        logger.info(f"  [{provider}]: {resp[:80]}...")

    from renderer import render_reel
    logger.info("Rendering reel video...")
    video_path = render_reel(args.prompt, responses, output_path=args.output)
    logger.info(f"Reel rendered to: {video_path}")

    from audio import overlay_music
    logger.info("Overlaying background music...")
    final_path = overlay_music(video_path, args.music, output_path=args.output)
    logger.info(f"Final video with audio: {final_path}")

    from poster import post_reel
    logger.info("Posting reel to Instagram...")
    result = post_reel(final_path, args.prompt, cfg, dry_run=args.dry_run)
    if args.dry_run:
        logger.info("DRY RUN complete. Instagram API payload logged above.")
    else:
        logger.info(f"Reel published successfully: {result}")


if __name__ == "__main__":
    asyncio.run(main())