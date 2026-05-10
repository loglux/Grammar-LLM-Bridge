"""
Configuration and environment variables.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration (provider-agnostic)
# Support both new generic names and legacy OpenAI-specific names for backward compatibility
LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4.1-mini")

# Legacy aliases (deprecated, use LLM_* instead)
OPENAI_API_KEY = LLM_API_KEY  # For backward compatibility in imports
OPENAI_BASE_URL = LLM_BASE_URL  # For backward compatibility in imports
MODEL = LLM_MODEL  # Alias for MODEL

DEFAULT_BASE_URL = LLM_BASE_URL or "https://api.openai.com/v1"

# Feature Flags
GRAMMAR_ONLY = os.getenv("GRAMMAR_ONLY", "false").lower() == "true"
TYPOGRAPHY_CHECK = os.getenv("TYPOGRAPHY_CHECK", "true").lower() == "true"

# LLM Client Settings
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))
LLM_RETRIES = int(os.getenv("LLM_RETRIES", "2"))
MAX_CONNECTIONS = int(os.getenv("MAX_CONNECTIONS", "20"))
MAX_KEEPALIVE_CONNECTIONS = int(os.getenv("MAX_KEEPALIVE_CONNECTIONS", "10"))

# Chunking Settings
LLM_CHUNKING = os.getenv("LLM_CHUNKING", "true").lower() == "true"
LLM_CHUNK_SIZE = int(os.getenv("LLM_CHUNK_SIZE", "600"))
LLM_CHUNK_OVERLAP = int(os.getenv("LLM_CHUNK_OVERLAP", "60"))
LLM_CHUNK_THRESHOLD = int(os.getenv("LLM_CHUNK_THRESHOLD", "1200"))
