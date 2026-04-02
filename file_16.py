# poster.py
import logging
import json
import asyncio
from pathlib import Path
import boto3
import requests

logger = logging.getLogger(__name__)


class PosterModule:
    def __init__(self, config):
        self.config = config
        self.s3_client = None
        if config.aws_access_key_id:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=config.aws_access_key_id,
                aws_secret_access_key=config.aws_secret_access_key,
                region_name=config.s3_region
            )

    async def post(self, video_path: str, prompt: str, dry_run: bool = False) -> dict:
        """Upload to S3 and publish via Instagram Graph API."""
        try:
            file_size = Path(video_path).stat().st_size
            logger.info(f"Video size: {file_size / (1024*1024):.2f} MB")

            if dry_run:
                return self._log_dry_run_payload(video_path, prompt)

            if not self.config.instagram_access_token:
                logger.warning("No Instagram access token; running in dry-run mode")
                return self._log_dry_run_payload(video_path, prompt)

            # Upload to S3
            s3_url = await self._upload_s3(video_path)
            logger.info(f"Uploaded to S3: {s3_url}")

            # Publish to Instagram
            result = await self._publish_instagram(s3_url, prompt)
            logger.info(f"Published to Instagram: {result}")
            return result

        except Exception as e:
            logger.error(f"Post failed: {e}")
            return {"status": "error", "message": str(e)}

    async def _upload_s3(self, video_path: str) -> str:
        """Upload video to S3."""
        if not self.s3_client:
            raise ValueError("S3 client not configured")

        file_name = Path(video_path).name
        try:
            self.s3_client.upload_file(
                video_path,
                self.config.s3_bucket,
                f"reels/{file_name}",
                ExtraArgs={"ContentType": "video/mp4"}
            )
            s3_url = f"https://{self.config.s3_bucket}.s3.{self.config.s3_region}.amazonaws.com/reels/{file_name}"
            logger.info(f"S3 upload complete: {s3_url}")
            return s3_url
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            raise

    async def _publish_instagram(self, video_url: str, caption: str) -> dict:
        """Publish reel via Instagram Graph API."""
        try:
            # Step 1: Create media object
            create_url = f"https://graph.instagram.com/v18.0/{self.config.instagram_business_account_id}/media"
            payload = {
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption[:2200],  # Instagram limit
                "access_token": self.config.instagram_access_token
            }

            logger.info(f"Creating media object at {create_url}")
            logger.debug(f"Payload: {json.dumps({**payload, 'access_token': '***'}, indent=2)}")

            response = requests.post(create_url, data=payload)
            response.raise_for_status()
            media_result = response.json()
            media_id = media_result.get("id")

            if not media_id:
                raise ValueError(f"No media ID in response: {media_result}")

            logger.info(f"Media created: {media_id}")

            # Step 2: Publish media
            publish_url = f"https://graph.instagram.com/v18.0/{self.config.instagram_business_account_id}/media_publish"
            publish_payload = {
                "creation_id": media_id,
                "access_token": self.config.instagram_access_token
            }

            logger.info(f"Publishing media at {publish_url}")
            response = requests.post(publish_url, data=publish_payload)
            response.raise_for_status()
            publish_result = response.json()

            logger.info(f"✓ Published to Instagram: {publish_result}")
            return publish_result

        except requests.exceptions.RequestException as e:
            logger.error(f"Instagram API error: {e}")
            raise

    def _log_dry_run_payload(self, video_path: str, prompt: str) -> dict:
        """Log dry-run payload without posting."""
        payload = {
            "mode": "dry-run",
            "video_path": video_path,
            "video_size_mb": Path(video_path).stat().st_size / (1024*1024),
            "prompt": prompt,
            "instagram_api": {
                "endpoint": f"https://graph.instagram.com/v18.0/{self.config.instagram_business_account_id}/media",
                "media_type": "REELS",
                "caption": prompt[:2200]
            }
        }
        logger.info(f"DRY-RUN PAYLOAD:\n{json.dumps(payload, indent=2)}")
        return payload