import json
import logging
import os
import time
from pathlib import Path

import requests

logger = logging.getLogger("poster")


def upload_to_s3(file_path: str, cfg: dict) -> str:
    import boto3
    bucket = cfg["AWS_S3_BUCKET"]
    region = cfg.get("AWS_REGION", "us-east-1")
    key = f"reels/{Path(file_path).name}"

    s3 = boto3.client(
        "s3",
        region_name=region,
        aws_access_key_id=cfg["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=cfg["AWS_SECRET_ACCESS_KEY"],
    )
    logger.info(f"Uploading {file_path} to s3://{bucket}/{key}")
    s3.upload_file(
        file_path,
        bucket,
        key,
        ExtraArgs={"ContentType": "video/mp4", "ACL": "public-read"},
    )
    url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
    logger.info(f"S3 upload complete: {url}")
    return url


def publish_instagram_reel(video_url: str, caption: str, cfg: dict) -> dict:
    account_id = cfg["INSTAGRAM_ACCOUNT_ID"]
    access_token = cfg["INSTAGRAM_ACCESS_TOKEN"]
    base = "https://graph.facebook.com/v19.0"

    # Step 1: Create media container
    container_payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "share_to_feed": True,
        "access_token": access_token,
    }
    logger.info(f"Creating Instagram media container...")
    resp = requests.post(
        f"{base}/{account_id}/media",
        data=container_payload,
        timeout=30,
    )
    resp.raise_for_status()
    container_id = resp.json()["id"]
    logger.info(f"Container created: {container_id}")

    # Step 2: Poll until ready
    for attempt in range(20):
        time.sleep(5)
        status_resp = requests.get(
            f"{base}/{container_id}",
            params={"fields": "status_code,status", "access_token": access_token},
            timeout=15,
        )
        status_resp.raise_for_status()
        status_data = status_resp.json()
        status_code = status_data.get("status_code", "")
        logger.info(f"Container status [{attempt+1}/20]: {status_code}")
        if status_code == "FINISHED":
            break
        if status_code == "ERROR":
            raise RuntimeError(f"Instagram container processing error: {status_data}")
    else:
        raise TimeoutError("Instagram container did not finish processing in time")

    # Step 3: Publish
    publish_payload = {
        "creation_id": container_id,
        "access_token": access_token,
    }
    pub_resp = requests.post(
        f"{base}/{account_id}/media_publish",
        data=publish_payload,
        timeout=30,
    )
    pub_resp.raise_for_status()
    result = pub_resp.json()
    logger.info(f"Reel published: {result}")
    return result


def post_reel(video_path: str, prompt: str, cfg: dict, dry_run: bool = False) -> dict:
    caption = (
        f"🤖 AI Debate: {prompt}\n\n"
        "#AI #ArtificialIntelligence #ChatGPT #Claude #Gemini #Llama "
        "#AIDebate #TechTok #FutureTech"
    )

    if dry_run:
        # simulate S3 URL
        bucket = cfg.get("AWS_S3_BUCKET") or "my-bucket"
        region = cfg.get("AWS_REGION") or "us-east-1"
        video_url = f"https://{bucket}.s3.{region}.amazonaws.com/reels/{Path(video_path).name}"

        payload_container = {
            "endpoint": f"https://graph.facebook.com/v19.0/{cfg.get('INSTAGRAM_ACCOUNT_ID','<ACCOUNT_ID>')}/media",
            "method": "POST",
            "body": {
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "share_to_feed": True,
                "access_token": "<INSTAGRAM_ACCESS_TOKEN>",
            },
        }
        payload_publish = {
            "endpoint": f"https://graph.facebook.com/v19.0/{cfg.get('INSTAGRAM_ACCOUNT_ID','<ACCOUNT_ID>')}/media_publish",
            "method": "POST",
            "body": {
                "creation_id": "<container_id_from_step_1>",
                "access_token": "<INSTAGRAM_ACCESS_TOKEN>",
            },
        }
        dry_run_output = {
            "dry_run": True,
            "video_path": str(video_path),
            "s3_upload_payload": {
                "bucket": bucket,
                "key": f"reels/{Path(video_path).name}",
                "region": region,
                "simulated_url": video_url,
            },
            "instagram_step1_container": payload_container,
            "instagram_step2_publish": payload_publish,
            "caption": caption,
        }
        logger.info("=" * 60)
        logger.info("DRY RUN — Instagram API Payload:")
        logger.info(json.dumps(dry_run_output, indent=2))
        logger.info("=" * 60)
        return dry_run_output

    # Live mode
    missing = [k for k in ["INSTAGRAM_ACCOUNT_ID", "INSTAGRAM_ACCESS_TOKEN",
                            "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
                            "AWS_S3_BUCKET"] if not cfg.get(k)]
    if missing:
        raise EnvironmentError(f"Missing required env vars for live posting: {missing}")

    video_url = upload_to_s3(video_path, cfg)
    result = publish_instagram_reel(video_url, caption, cfg)
    return result