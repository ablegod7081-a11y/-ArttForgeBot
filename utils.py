import time
from typing import Dict, Tuple
from datetime import datetime
import hashlib
import json

# User session storage (in production, use Redis or database)
user_sessions = {}
user_rate_limits = {}

class SessionManager:
    """Manage user sessions and settings"""
    
    @staticmethod
    def get_settings(user_id: int) -> Dict:
        """Get user settings or create default"""
        if user_id not in user_sessions:
            user_sessions[user_id] = {
                'size': '1024x1024',
                'quality': 'standard',
                'style': 'natural',
                'created_at': datetime.now().isoformat()
            }
        return user_sessions[user_id]
    
    @staticmethod
    def update_setting(user_id: int, key: str, value: str) -> Dict:
        """Update a user setting"""
        settings = SessionManager.get_settings(user_id)
        settings[key] = value
        user_sessions[user_id] = settings
        return settings
    
    @staticmethod
    def reset_settings(user_id: int) -> Dict:
        """Reset settings to default"""
        user_sessions[user_id] = {
            'size': '1024x1024',
            'quality': 'standard',
            'style': 'natural',
            'created_at': datetime.now().isoformat()
        }
        return user_sessions[user_id]
    
    @staticmethod
    def format_settings(settings: Dict) -> str:
        """Format settings for display"""
        return (
            f"📐 Size: {settings.get('size', '1024x1024')}\n"
            f"✨ Quality: {settings.get('quality', 'standard').upper()}\n"
            f"🎨 Style: {settings.get('style', 'natural').upper()}"
        )

class RateLimiter:
    """Simple rate limiter for user requests"""
    
    @staticmethod
    def check_limit(user_id: int) -> Tuple[bool, int]:
        """
        Check if user is within rate limit
        Returns: (is_allowed, remaining_requests)
        """
        current_time = time.time()
        
        if user_id not in user_rate_limits:
            user_rate_limits[user_id] = {
                'count': 0,
                'reset_time': current_time + 3600  # 1 hour from now
            }
            return True, 29  # 30 - 1 = 29 remaining
        
        user_data = user_rate_limits[user_id]
        
        # Check if window has expired
        if current_time > user_data['reset_time']:
            user_rate_limits[user_id] = {
                'count': 1,
                'reset_time': current_time + 3600
            }
            return True, 29
        
        # Check if limit is exceeded
        if user_data['count'] >= 30:
            time_left = int(user_data['reset_time'] - current_time)
            return False, time_left
        
        # Increment count
        user_data['count'] += 1
        remaining = 30 - user_data['count']
        return True, remaining

def format_prompt(prompt: str, max_length: int = 50) -> str:
    """Format prompt for display"""
    if len(prompt) > max_length:
        return prompt[:max_length] + '...'
    return prompt

def generate_request_id() -> str:
    """Generate unique request ID"""
    timestamp = str(time.time())
    return hashlib.md5(timestamp.encode()).hexdigest()[:8]

def parse_command_args(text: str) -> str:
    """Extract prompt from command"""
    parts = text.split()
    if len(parts) > 1:
        return ' '.join(parts[1:])
    return ""
