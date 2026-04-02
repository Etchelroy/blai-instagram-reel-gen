# config.py
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class Config:
    def __init__(self):
        load_dotenv()
        
        # AI Providers
        self.claude_api_key = os.getenv("CLAUDE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        
        # Instagram / AWS
        self.instagram_access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.instagram_business_account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.s3_bucket = os.getenv("S3_BUCKET")
        self.s3_region = os.getenv("S3_REGION", "us-east-1")
        
        # Renderer
        self.brand_primary_color = os.getenv("BRAND_PRIMARY_COLOR", "#FF6B6B")
        self.brand_secondary_color = os.getenv("BRAND_SECONDARY_COLOR", "#4ECDC4")
        self.brand_font = os.getenv("BRAND_FONT", "Arial")
        
        # Audio
        self.background_music_path = os.getenv("BACKGROUND_MUSIC_PATH", "")
        
        # Timeouts & Retries
        self.ai_timeout_seconds = int(os.getenv("AI_TIMEOUT_SECONDS", "30"))
        self.ai_max_retries = int(os.getenv("AI_MAX_RETRIES", "3"))
        
        # Output
        self.output_dir = os.getenv("OUTPUT_DIR", "./output")
        os.makedirs(self.output_dir, exist_ok=True)


def load_config() -> Config:
    """Load and validate configuration."""
    config = Config()
    logger.info("Configuration loaded from .env")
    return config