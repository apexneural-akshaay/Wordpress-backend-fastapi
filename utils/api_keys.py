"""Utility for managing multiple API keys with automatic rotation on rate limits"""

import os
import random
from typing import Optional, List
# from google import genai # Comment out direct Gemini import
import requests # Import requests for OpenRouter

class OpenAIKeyManager:
    """Manages multiple OpenAI API keys with automatic rotation on 429 errors"""
    
    def __init__(self):
        self.keys: List[str] = []
        self.current_key_index = 0
        self._load_keys()
    
    def _load_keys(self):
        """Load all available API keys from environment variables"""
        keys_env = os.getenv('OPENAI_API_KEYS', '')
        if keys_env:
            additional_keys = [k.strip() for k in keys_env.split(',') if k.strip()]
            for key in additional_keys:
                if key and key not in self.keys:
                    self.keys.append(key)
        
        primary_key = os.getenv('OPENAI_API_KEY')
        # print(f"[DEBUG] Raw OPENAI_API_KEY from environment: {primary_key}") # Added for debugging
        if primary_key and primary_key not in self.keys:
            self.keys.append(primary_key)
        
        key_index = 1
        while True:
            key = os.getenv(f'OPENAI_API_KEY_{key_index}')
            if key and key not in self.keys:
                self.keys.append(key)
                key_index += 1
            elif not key:
                break
            else:
                key_index += 1  # Skip if duplicate
        
        if len(self.keys) > 1:
            random.shuffle(self.keys)
        
        # print(f"[LOG] Loaded {len(self.keys)} OpenAI API key(s)")
        for i, key in enumerate(self.keys):
            print(f"[DEBUG] Key Present") # Print partial key for security
        if len(self.keys) > 1:
            print("Keys will be rotated automatically on rate limit errors")
            # print(f"[LOG] Keys will be rotated automatically on rate limit errors")
    
    def get_key(self) -> Optional[str]:
        """Get the current API key"""
        if not self.keys:
            return None
        return self.keys[self.current_key_index]
    
    def get_all_keys(self) -> List[str]:
        """Get all available API keys"""
        return self.keys.copy()
    
    def rotate_key(self):
        """Switch to the next API key (call this when getting 429 error)"""
        if len(self.keys) <= 1:
            # print("[WARN] Only one key available, cannot rotate")
            return False
        
        self.current_key_index = (self.current_key_index + 1) % len(self.keys)
        print(f"[LOG] Rotated to API key {self.current_key_index + 1}/{len(self.keys)}")
        return True
    
    def has_multiple_keys(self) -> bool:
        # """Check if multiple keys are available"""
        return len(self.keys) > 1
    
    def is_rate_limit_error(self, error: Exception) -> bool:
        """Check if the error is a 429 rate limit error"""
        error_str = str(error)
        error_lower = error_str.lower()
        error_type = type(error).__name__.lower()
        
        # Check for 429 status code in error string
        if '429' in error_str:
            return True
        
        # Check for OpenAI's rate limit error (specific message or type)
        if 'rate limit exceeded' in error_lower or 'openai_ratelimit_error' in error_type:
            return True
        
        # Check HTTP status if available
        if hasattr(error, 'status_code') and error.status_code == 429:
            return True
        
        if hasattr(error, 'status') and error.status == 429:
            return True
        
        # Check error.args for rate limit information
        if hasattr(error, 'args') and error.args:
            for arg in error.args:
                arg_str = str(arg).lower()
                if '429' in str(arg) or 'rate limit' in arg_str or 'quota' in arg_str:
                    return True
                if isinstance(arg, dict):
                    if 'error' in arg:
                        nested = arg.get('error', {})
                        if isinstance(nested, dict):
                            code = nested.get('code')
                            message = nested.get('message', '')
                            if code == 429 or 'rate limit' in message.lower():
                                return True
        
        # Check error message/args for 429
        if hasattr(error, 'message'):
            msg_str = str(error.message).lower()
            if '429' in str(error.message) or 'rate limit' in msg_str:
                return True
        
        return False

class GeminiKeyManager:
    """Manages multiple Gemini API keys with automatic rotation on 429 errors"""
    
    def __init__(self):
        self.keys: List[str] = []
        self.current_key_index = 0
        self._load_keys()
    
    def _load_keys(self):
        """Load all available API keys from environment variables"""
        keys_env = os.getenv('GEMINI_API_KEYS', '')
        if keys_env:
            additional_keys = [k.strip() for k in keys_env.split(',') if k.strip()]
            for key in additional_keys:
                if key and key not in self.keys:
                    self.keys.append(key)
        
        primary_key = os.getenv('GEMINI_API_KEY')
        # print(f"[DEBUG] Raw GEMINI_API_KEY from environment: {primary_key}") # Added for debugging
        if primary_key and primary_key not in self.keys:
            self.keys.append(primary_key)
        
        key_index = 1
        while True:
            key = os.getenv(f'GEMINI_API_KEY_{key_index}')
            if key and key not in self.keys:
                self.keys.append(key)
                key_index += 1
            elif not key:
                break
            else:
                key_index += 1  # Skip if duplicate
        
        if len(self.keys) > 1:
            random.shuffle(self.keys)
        
        # print(f"[LOG] Loaded {len(self.keys)} Gemini API key(s)")
        for i, key in enumerate(self.keys):
            print(f"[DEBUG] Key Present") # Print partial key for security
        if len(self.keys) > 1:
            print(f"[LOG] Keys will be rotated automatically on rate limit errors")
    
    def get_key(self) -> Optional[str]:
        """Get the current API key"""
        if not self.keys:
            return None
        return self.keys[self.current_key_index]
    
    def get_all_keys(self) -> List[str]:
        """Get all available API keys"""
        return self.keys.copy()
    
    def rotate_key(self):
        """Switch to the next API key (call this when getting 429 error)"""
        if len(self.keys) <= 1:
            print("[WARN] Only one key available, cannot rotate")
            return False
        
        self.current_key_index = (self.current_key_index + 1) % len(self.keys)
        print(f"[LOG] Rotated to API key {self.current_key_index + 1}/{len(self.keys)}")
        return True
    
    def has_multiple_keys(self) -> bool:
        """Check if multiple keys are available"""
        return len(self.keys) > 1
    
    def is_rate_limit_error(self, error: Exception) -> bool:
        """Check if the error is a 429 rate limit error"""
        error_str = str(error)
        error_lower = error_str.lower()
        error_type = type(error).__name__.lower()
        
        # Check for 429 status code in error string
        if '429' in error_str:
            return True
        
        # Check for Google's RESOURCE_EXHAUSTED error (case-insensitive)
        if 'resource_exhausted' in error_lower:
            return True
        
        # Check for quota/rate limit keywords
        if 'rate limit' in error_lower or 'quota' in error_lower or 'exceeded' in error_lower:
            return True
        
        # Check for specific exception types that might indicate rate limits
        if '429' in error_type or 'ratelimit' in error_type or 'resourceexhausted' in error_type:
            return True
        
        # Check HTTP status if available
        if hasattr(error, 'status_code') and error.status_code == 429:
            return True
        
        if hasattr(error, 'status') and error.status == 429:
            return True
        
        # Check error.args (Google API exceptions often have error info in args)
        if hasattr(error, 'args') and error.args:
            for arg in error.args:
                arg_str = str(arg).lower()
                if '429' in str(arg) or 'resource_exhausted' in arg_str or 'quota' in arg_str:
                    return True
                if isinstance(arg, dict):
                    if 'error' in arg:
                        nested = arg.get('error', {})
                        if isinstance(nested, dict):
                            code = nested.get('code')
                            status = nested.get('status', '')
                            if code == 429 or status == 'RESOURCE_EXHAUSTED':
                                return True
        
        # Check error message/args for 429
        if hasattr(error, 'message'):
            msg_str = str(error.message).lower()
            if '429' in str(error.message) or 'resource_exhausted' in msg_str:
                return True
        
        return False

class OpenRouterKeyManager:
    """Manages multiple OpenRouter API keys with automatic rotation on 429 errors"""

    def __init__(self):
        self.keys: List[str] = []
        self.current_key_index = 0
        self._load_keys()

    def _load_keys(self):
        """Load all available API keys from environment variables"""
        keys_env = os.getenv('OPENROUTER_API_KEYS', '')
        if keys_env:
            additional_keys = [k.strip() for k in keys_env.split(',') if k.strip()]
            for key in additional_keys:
                if key and key not in self.keys:
                    self.keys.append(key)

        primary_key = os.getenv('OPENROUTER_API_KEY')
        # print(f"[DEBUG] Raw OPENROUTER_API_KEY from environment: {primary_key}")
        if primary_key and primary_key not in self.keys:
            self.keys.append(primary_key)

        key_index = 1
        while True:
            key = os.getenv(f'OPENROUTER_API_KEY_{key_index}')
            if key and key not in self.keys:
                self.keys.append(key)
                key_index += 1
            elif not key:
                break
            else:
                key_index += 1

        if len(self.keys) > 1:
            random.shuffle(self.keys)

        # print(f"[LOG] Loaded {len(self.keys)} OpenRouter API key(s)")
        for i, key in enumerate(self.keys):
            print(f"[DEBUG] Key Present")
        if len(self.keys) > 1:
            print(f"[LOG] Keys will be rotated automatically on rate limit errors")

    def get_key(self) -> Optional[str]:
        """Get the current API key"""
        if not self.keys:
            return None
        return self.keys[self.current_key_index]
    
    def get_all_keys(self) -> List[str]:
        """Get all available API keys"""
        return self.keys.copy()

    def rotate_key(self):
        """Switch to the next API key (call this when getting 429 error)"""
        if len(self.keys) <= 1:
            print("[WARN] Only one key available, cannot rotate")
            return False

        self.current_key_index = (self.current_key_index + 1) % len(self.keys)
        print(f"[LOG] Rotated to API key {self.current_key_index + 1}/{len(self.keys)}")
        return True

    def has_multiple_keys(self) -> bool:
        """Check if multiple keys are available"""
        return len(self.keys) > 1

    def is_rate_limit_error(self, error: Exception) -> bool:
        """Check if the error is a 429 rate limit error"""
        error_str = str(error)
        error_lower = error_str.lower()
        
        # Check for 429 status code in error string (from requests.exceptions.HTTPError)
        if '429 client error' in error_lower or 'rate limit exceeded' in error_lower:
            return True

        # If error is a requests.Response object, check status code directly
        if hasattr(error, 'response') and hasattr(error.response, 'status_code') and error.response.status_code == 429:
            return True
        
        # Also check for common OpenRouter specific error messages if any
        if 'x-ratelimit-remaining' in error_lower or 'openrouter_ratelimit' in error_lower:
            return True

        return False

# Global key managers
openai_key_manager: Optional[OpenAIKeyManager] = None
gemini_key_manager: Optional[GeminiKeyManager] = None
openrouter_key_manager: Optional[OpenRouterKeyManager] = None

def get_openai_key() -> Optional[str]:
    global openai_key_manager
    if openai_key_manager is None:
        openai_key_manager = OpenAIKeyManager()
    return openai_key_manager.get_key()

def rotate_openai_key() -> bool:
    global openai_key_manager
    if openai_key_manager is None:
        openai_key_manager = OpenAIKeyManager()
    return openai_key_manager.rotate_key()

def get_gemini_key() -> Optional[str]:
    global gemini_key_manager
    if gemini_key_manager is None:
        gemini_key_manager = GeminiKeyManager()
    return gemini_key_manager.get_key()

def rotate_gemini_key() -> bool:
    global gemini_key_manager
    if gemini_key_manager is None:
        gemini_key_manager = GeminiKeyManager()
    return gemini_key_manager.rotate_key()

def has_multiple_keys_openai() -> bool:
    global openai_key_manager
    if openai_key_manager is None:
        openai_key_manager = OpenAIKeyManager()
    return openai_key_manager.has_multiple_keys()

def has_multiple_keys_gemini() -> bool:
    global gemini_key_manager
    if gemini_key_manager is None:
        gemini_key_manager = GeminiKeyManager()
    return gemini_key_manager.has_multiple_keys()

def is_rate_limit_error_openai(error: Exception) -> bool:
    global openai_key_manager
    if openai_key_manager is None:
        openai_key_manager = OpenAIKeyManager()
    return openai_key_manager.is_rate_limit_error(error)

def is_rate_limit_error_gemini(error: Exception) -> bool:
    global gemini_key_manager
    if gemini_key_manager is None:
        gemini_key_manager = GeminiKeyManager()
    return gemini_key_manager.is_rate_limit_error(error)

def get_openrouter_key() -> Optional[str]:
    global openrouter_key_manager
    if openrouter_key_manager is None:
        openrouter_key_manager = OpenRouterKeyManager()
    return openrouter_key_manager.get_key()

def rotate_openrouter_key() -> bool:
    global openrouter_key_manager
    if openrouter_key_manager is None:
        openrouter_key_manager = OpenRouterKeyManager()
    return openrouter_key_manager.rotate_key()

def has_multiple_keys_openrouter() -> bool:
    global openrouter_key_manager
    if openrouter_key_manager is None:
        openrouter_key_manager = OpenRouterKeyManager()
    return openrouter_key_manager.has_multiple_keys()

def is_rate_limit_error_openrouter(error: Exception) -> bool:
    global openrouter_key_manager
    if openrouter_key_manager is None:
        openrouter_key_manager = OpenRouterKeyManager()
    return openrouter_key_manager.is_rate_limit_error(error)

# Consolidated _key_manager for backward compatibility (defaults to OpenAI for existing calls)
class ConsolidatedKeyManager:
    def __init__(self):
        self.openai_manager = OpenAIKeyManager()
        self.gemini_manager = GeminiKeyManager() # Keep Gemini manager for now, but will transition calls
        self.openrouter_manager = OpenRouterKeyManager()

    def get_key(self) -> Optional[str]:
        # Default to OpenAI if not specified, or implement logic to choose
        return self.openai_manager.get_key()

    def get_all_keys(self) -> List[str]:
        # Combine or prioritize keys, for now, just OpenAI
        return self.openai_manager.get_all_keys()
    
    def rotate_key(self):
        return self.openai_manager.rotate_key()

    def has_multiple_keys(self) -> bool:
        return self.openai_manager.has_multiple_keys() or self.gemini_manager.has_multiple_keys() or self.openrouter_manager.has_multiple_keys()
    
    def is_rate_limit_error(self, error: Exception) -> bool:
        # Check all for rate limits
        return self.openai_manager.is_rate_limit_error(error) or self.gemini_manager.is_rate_limit_error(error) or self.openrouter_manager.is_rate_limit_error(error)

_key_manager = ConsolidatedKeyManager()

