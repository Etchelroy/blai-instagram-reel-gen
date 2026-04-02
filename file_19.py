import logging
import os
import time

import boto3
import requests

import config

logger = logging.getLogger(__name__)

INSTAGRAM_API = "https://graph.facebook.com/v19.0"


def upload_to_s3(file_path: str) -> str:
    s3 = boto3.client(
        "s3",
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
        region_name=config.AWS_REGION,
    )
    key = f"reels/{os.path.basename(file_path)}"
    logger.info("Uploading %s to s3://%s/%s", file_path, config.S3_BUCKET_NAME, key)
    s3.upload_file(
        file_path,
        config.S3_BUCKET_NAME,
        key,
        ExtraArgs={"ContentType": "video/mp4", "ACL": "public-read"},
    )
    url = f"https://{config.S3_BUCKET_NAME}.s3.{config.AWS_REGION}.amazonaws.com/{key}"
    logger.info("S3 upload complete: %s", url)
    return url


def _create_media_container(video_url: str, caption: str) -> str:
    resp = requests.post(
        f"{INSTAGRAM_API}/{config.INSTAGRAM_USER_ID}/media",
        params={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": config.INSTAGRAM_ACCESS_TOKEN,
        },
        timeout=30,
    )
    resp.raise_for_status()
    container_id = resp.json()["id"]
    logger.info("Media container created: %s", container_id)
    return container_id


def _wait_for_container(container_id: str, max_wait: int = 120) -> None:
    for _ in range(max_wait // 5):
        resp = requests.get(
            f"{INSTAGRAM_API}/{container_id}",
            params={
                "fields": "status_code",
                "access_token": config.INSTAGRAM_ACCESS_TOKEN,
            },
            timeout=15,
        )
        resp.raise_for_status()
        status = resp.json().get("status_code", "")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError(f"Container {container_id} failed processing")
        time.sleep(5)
    raise TimeoutError(f"Container {container_id} not ready after {max_wait}s")


def _publish_container(container_id: str) -> str:
    resp = requests.post(
        f"{INSTAGRAM_API}/{config.INSTAGRAM_USER_ID}/media_publish",
        params={
            "creation_id": container_id,
            "access_token": config.INSTAGRAM_ACCESS_TOKEN,
        },
        timeout=30,
    )
    resp.raise_for_status()
    media_id = resp.json()["id"]
    logger.info("Published to Instagram: %s", media_id)
    return media_id


def publish_reel(video_path: str, caption: str, dry_run: bool = False) -> dict:
    payload = {
        "video_path": video_path,
        "caption": caption,
        "instagram_user_id": config.INSTAGRAM_USER_ID,
        "mode": "dry_run" if dry_run else "live",
    }

    if dry_run:
        logger.info("DRY RUN — Instagram API payload: %s", payload)
        return {"dry_run": True, "payload": payload}

    video_url = upload_to_s3(video_path)
    payload["s3_url"] = video_url

    container_id = _create_media_container(video_url, caption)
    _wait_for_container(container_id)
    media_id = _publish_container(container_id)

    return {"media_id": media_id, "s3_url": video_url}