import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger("config")

load_dotenv()

REQUIRED_FOR_LIVE = [
    "INSTAGRAM_ACCOUNT_ID",
    "INSTAGRAM_ACCESS_TOKEN",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_S3_BUCKET",
    "AWS_REGION",
]

OPTIONAL_KEYS = [
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "GROQ_API_KEY",
]


def load_config() -> dict:
    cfg = {}
    for key in REQUIRED_FOR_LIVE + OPTIONAL_KEYS:
        cfg[key] = os.getenv(key, "")

    present_ai = [k for k in OPTIONAL_KEYS if cfg.get(k)]
    if not present_ai:
        logger.warning("No AI provider API keys found — all responses will use fallback messages")
    else:
        logger.info(f"AI providers configured: {[k.replace('_API_KEY','') for k in present_ai]}")

    return cfg