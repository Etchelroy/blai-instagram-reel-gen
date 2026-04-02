import asyncio
import argparse
import sys
import logging
from pathlib import Path
from config import Config
from ai_query import AIQuery
from renderer import ReelRenderer
from audio import AudioMixer
from poster import InstagramPoster

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(description='Instagram Reel Generator')
    parser.add_argument('--prompt', required=True, help='Prompt to query AI models')
    parser.add_argument('--dry-run', action='store_true', help='Run without posting to Instagram')
    args = parser.parse_args()

    try:
        # Load config
        config = Config()
        logger.info('Config loaded successfully')

        # Query AI models in parallel
        logger.info(f'Querying AI models with prompt: {args.prompt}')
        ai_query = AIQuery(config)
        ai_responses = await ai_query.query_all(args.prompt)
        logger.info(f'Received {len(ai_responses)} AI responses')

        # Render reel
        logger.info('Rendering reel...')
        renderer = ReelRenderer(config)
        reel_path = renderer.render(args.prompt, ai_responses)
        logger.info(f'Reel rendered: {reel_path}')

        # Add audio
        logger.info('Adding audio...')
        audio_mixer = AudioMixer(config)
        final_reel_path = audio_mixer.mix(reel_path)
        logger.info(f'Audio mixed: {final_reel_path}')

        # Post to Instagram
        logger.info('Posting to Instagram...')
        poster = InstagramPoster(config)
        result = await poster.post(final_reel_path, args.prompt, args.dry_run)
        logger.info(f'Posting result: {result}')

        logger.info('✓ Reel generation complete')
        return 0

    except Exception as e:
        logger.error(f'Fatal error: {e}', exc_info=True)
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)