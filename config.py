import os
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class Config:
    """Configuration class for environment variables"""
    
    @staticmethod
    def get_telegram_token() -> str:
        """Get Telegram bot token from environment"""
        token = os.environ.get('TELEGRAM_TOKEN')
        if not token:
            raise ValueError("TELEGRAM_TOKEN environment variable not set")
        return token
    
    @staticmethod
    def get_openai_key() -> str:
        """Get OpenAI API key from environment"""
        key = os.environ.get('OPENAI_API_KEY')
        if not key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        return key
    
    @staticmethod
    def get_port() -> int:
        """Get port for Railway deployment"""
        return int(os.environ.get('PORT', 8080))
    
    @staticmethod
    def is_production() -> bool:
        """Check if running in production"""
        return os.environ.get('RAILWAY_ENVIRONMENT') == 'production'
    
    # Default settings
    DEFAULT_SIZE = "1024x1024"
    DEFAULT_QUALITY = "standard"
    DEFAULT_STYLE = "natural"
    
    IMAGE_SIZES = {
        'square': '1024x1024',
        'portrait': '1024x1792',
        'landscape': '1792x1024'
    }
    
    IMAGE_QUALITY = {
        'standard': 'standard',
        'hd': 'hd'
    }
    
    IMAGE_STYLES = {
        'natural': 'natural',
        'vivid': 'vivid'
    }
    
    # Rate limiting (30 requests per hour per user)
    RATE_LIMIT = 30
    RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds

# Create global config instance
config = Config()
