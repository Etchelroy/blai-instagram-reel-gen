import asyncio
import json
import logging
from pathlib import Path
import requests
import boto3

logger = logging.getLogger(__name__)


class InstagramPoster:
    """Post reel to Instagram via Graph API and S3."""

    def __init__(self, config):
        self.config = config
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
            region_name=config.s3_region,
        )

    async def post(self, reel_path: str, prompt: str, dry_run: bool = False) -> dict:
        """Post reel to Instagram."""
        try:
            # Upload to S3
            s3_url = await self._upload_to_s3(reel_path)
            logger.info(f'Uploaded to S3: {s3_url}')

            # Prepare Instagram payload
            payload = {
                'media_type': 'REELS',
                'video_url': s3_url,
                'caption': f'{prompt}\n\n#AI #Insights #Tech',
                'access_token': self.config.instagram_access_token,
            }

            if dry_run:
                logger.info(f'DRY RUN: Instagram API payload: {json.dumps(payload, indent=2)}')
                return {'status': 'dry_run', 'payload': payload}

            # Post to Instagram
            response = await self._post_to_instagram(payload)
            logger.info(f'Posted to Instagram: {response}')
            return response

        except Exception as e:
            logger.error(f'Posting error: {e}', exc_info=True)
            raise

    async def _upload_to_s3(self, file_path: str) -> str:
        """Upload reel to S3 and return URL."""
        loop = asyncio.get_event_loop()
        file_key = Path(file_path).name

        def upload():
            self.s3_client.upload_file(
                file_path,
                self.config.s3_bucket,
                file_key,
                ExtraArgs={'ContentType': 'video/mp4'},
            )
            return f'https://{self.config.s3_bucket}.s3.{self.config.s3_region}.amazonaws.com/{file_key}'

        return await loop.run_in_executor(None, upload)

    async def _post_to_instagram(self, payload: dict) -> dict:
        """Post to Instagram Graph API."""
        loop = asyncio.get_event_loop()

        def post():
            url = f'https://graph.instagram.com/v18.0/{self.config.instagram_business_account_id}/media'
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()

        return await loop.run_in_executor(None, post)