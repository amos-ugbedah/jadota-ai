import re
from typing import Optional, Any
from fastapi import HTTPException, status

class InputValidator:
    """Validate and sanitize user inputs."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    @staticmethod
    def validate_password(password: str) -> bool:
        """Validate password strength."""
        if len(password) < 8:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'[0-9]', password):
            return False
        return True
    
    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """Validate trading symbol."""
        symbol_pattern = r'^[A-Z]{2,10}$'
        return bool(re.match(symbol_pattern, symbol))
    
    @staticmethod
    def validate_amount(amount: Any) -> bool:
        """Validate amount is a positive number."""
        try:
            amount = float(amount)
            return amount > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Sanitize string input."""
        if not value:
            return ""
        # Remove HTML tags
        import html
        value = html.escape(value)
        # Remove excessive whitespace
        value = ' '.join(value.split())
        return value
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username format."""
        username_pattern = r'^[a-zA-Z0-9_]{3,20}$'
        return bool(re.match(username_pattern, username))
    
    @staticmethod
    def validate_percentage(value: float, min_val: float = 0, max_val: float = 100) -> bool:
        """Validate percentage value."""
        return min_val <= value <= max_val

def validate_input(func):
    """Decorator to validate inputs."""
    async def wrapper(*args, **kwargs):
        # Validate inputs
        for key, value in kwargs.items():
            if isinstance(value, str):
                kwargs[key] = InputValidator.sanitize_string(value)
        
        return await func(*args, **kwargs)
    return wrapper
