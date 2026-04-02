import asyncio
import logging
import json
from pathlib import Path
import aiohttp
import boto3

logger = logging.getLogger(__name__)


class InstagramPoster:
    """Post reels to Instagram and upload to S3."""

    def __init__(self, config):
        self.config = config
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
            region_name=config.s3_region,
        ) if config.aws_access_key_id else None

    async def post(self, video_path: str, caption: str, dry_run: bool = False) -> dict:
        """Post reel to Instagram."""
        try:
            if dry_run:
                logger.info(f'[DRY RUN] Would post video: {video_path}')
                logger.info(f'[DRY RUN] Caption: {caption}')
                return {'status': 'dry_run', 'message': 'Dry run completed'}
            
            # Upload to S3
            if self.s3_client and self.config.s3_bucket:
                s3_url = await self._upload_to_s3(video_path)
                logger.info(f'Uploaded to S3: {s3_url}')
            else:
                logger.warning('S3 credentials not configured, skipping S3 upload')
                s3_url = None
            
            # Post to Instagram
            if self.config.instagram_access_token and self.config.instagram_business_account_id:
                result = await self._post_to_instagram(s3_url, caption)
                logger.info(f'Posted to Instagram: {result}')
                return result
            else:
                logger.warning('Instagram credentials not configured')
                return {'status': 'error', 'message': 'Instagram credentials not configured'}
        
        except Exception as e:
            logger.error(f'Posting error: {e}')
            raise

    async def _upload_to_s3(self, video_path: str) -> str:
        """Upload video to S3."""
        try:
            file_name = Path(video_path).name
            self.s3_client.upload_file(
                video_path,
                self.config.s3_bucket,
                file_name,
                ExtraArgs={'ContentType': 'video/mp4'}
            )
            return f"s3://{self.config.s3_bucket}/{file_name}"
        except Exception as e:
            logger.error(f'S3 upload error: {e}')
            raise

    async def _post_to_instagram(self, video_url: str, caption: str) -> dict:
        """Post to Instagram using Graph API."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://graph.instagram.com/v18.0/{self.config.instagram_business_account_id}/media"
                
                data = {
                    'media_type': 'REELS',
                    'video_url': video_url or 'local_file',
                    'caption': caption,
                    'access_token': self.config.instagram_access_token,
                }
                
                async with session.post(url, json=data) as resp:
                    result = await resp.json()
                    if resp.status in [200, 201]:
                        return {'status': 'success', 'media_id': result.get('id')}
                    else:
                        return {'status': 'error', 'message': result}
        except Exception as e:
            logger.error(f'Instagram posting error: {e}')
            raise