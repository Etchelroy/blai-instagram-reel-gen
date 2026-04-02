import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Load and validate configuration from environment variables."""

    def __init__(self):
        # AI API Keys
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.groq_api_key = os.getenv('GROQ_API_KEY')

        # Instagram & S3
        self.instagram_access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
        self.instagram_business_account_id = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.s3_bucket = os.getenv('S3_BUCKET')
        self.s3_region = os.getenv('S3_REGION', 'us-east-1')

        # Audio
        self.music_file = os.getenv('MUSIC_FILE', 'background_music.mp3')

        # Output
        self.output_dir = Path(os.getenv('OUTPUT_DIR', './output'))
        self.output_dir.mkdir(exist_ok=True)

        # Brand
        self.brand_name = os.getenv('BRAND_NAME', 'AI Insights')
        self.brand_accent_color = os.getenv('BRAND_ACCENT_COLOR', '#FF6B6B')
        self.brand_text_color = os.getenv('BRAND_TEXT_COLOR', '#FFFFFF')

        # Validation
        self._validate()

    def _validate(self):
        """Validate required config."""
        required = [
            'ANTHROPIC_API_KEY',
            'OPENAI_API_KEY',
            'GOOGLE_API_KEY',
            'GROQ_API_KEY',
        ]
        missing = [key for key in required if not os.getenv(key)]
        if missing:
            raise ValueError(f'Missing required env vars: {", ".join(missing)}')