import os
import logging

logger = logging.getLogger(__name__)


class Config:
    """Load configuration from environment variables."""

    def __init__(self):
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.s3_bucket = os.getenv('S3_BUCKET', 'reel-generator-bucket')
        self.s3_region = os.getenv('S3_REGION', 'us-east-1')
        self.instagram_access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
        self.instagram_business_account_id = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
        self.music_file_path = os.getenv('MUSIC_FILE_PATH', None)
        self.brand_primary_color = os.getenv('BRAND_PRIMARY_COLOR', '#FF6B35')
        self.brand_secondary_color = os.getenv('BRAND_SECONDARY_COLOR', '#004E89')
        self.brand_accent_color = os.getenv('BRAND_ACCENT_COLOR', '#F7B801')

        self._validate()

    def _validate(self):
        """Validate required environment variables."""
        required_keys = [
            'ANTHROPIC_API_KEY',
            'OPENAI_API_KEY',
            'GOOGLE_API_KEY',
            'GROQ_API_KEY',
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'INSTAGRAM_ACCESS_TOKEN',
            'INSTAGRAM_BUSINESS_ACCOUNT_ID',
        ]
        missing = [key for key in required_keys if not os.getenv(key)]
        if missing:
            logger.warning(f'Missing environment variables: {", ".join(missing)}')