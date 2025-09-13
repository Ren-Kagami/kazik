"""
Configuration settings for the Slot Machine application.
"""

import os
import logging
from typing import List, Dict, Any
from pathlib import Path

# Application settings
APP_NAME = "Slot Machine Probability Research"
APP_VERSION = "1.0.0"
API_PREFIX = "/api/v1"

# Environment settings
DEBUG_MODE = os.getenv("DEBUG", "true").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Game settings
INITIAL_CREDITS = int(os.getenv("INITIAL_CREDITS", "100"))
MAX_BET_AMOUNT = int(os.getenv("MAX_BET_AMOUNT", "100"))
MIN_BET_AMOUNT = int(os.getenv("MIN_BET_AMOUNT", "1"))

# Session settings
SESSION_TIMEOUT_HOURS = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
MAX_SESSIONS_PER_USER = int(os.getenv("MAX_SESSIONS_PER_USER", "5"))

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./slot_machine.db")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

# Admin settings
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "slot_admin_2025")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO" if not DEBUG_MODE else "DEBUG")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = os.getenv("LOG_FILE", "slot_machine.log")

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(logs_dir / LOG_FILE, encoding='utf-8')
    ]
)

logger = logging.getLogger(APP_NAME)

# Default slot machine configuration
DEFAULT_SYMBOLS = ["🍒", "🍋", "🍊", "🍇", "🔔", "⭐", "💎"]
DEFAULT_WEIGHTS = [30, 25, 20, 15, 5, 3, 2]  # Higher weight = more frequent
DEFAULT_PAYOUTS = {
    "🍒": 2,
    "🍋": 3,
    "🍊": 4,
    "🍇": 5,
    "🔔": 10,
    "⭐": 20,
    "💎": 50
}

# Slot machine settings
NUM_REELS = int(os.getenv("NUM_REELS", "3"))
SIMULATION_BATCH_SIZE = int(os.getenv("SIMULATION_BATCH_SIZE", "1000"))
MAX_SIMULATION_SPINS = int(os.getenv("MAX_SIMULATION_SPINS", "100000"))

# CORS settings
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# Rate limiting settings
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
REQUESTS_PER_MINUTE = int(os.getenv("REQUESTS_PER_MINUTE", "60"))

# Cache settings
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))

def get_settings() -> Dict[str, Any]:
    """
    Get all configuration settings as a dictionary.

    Returns:
        Dict containing all configuration values
    """
    return {
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "debug_mode": DEBUG_MODE,
        "environment": ENVIRONMENT,
        "initial_credits": INITIAL_CREDITS,
        "max_bet_amount": MAX_BET_AMOUNT,
        "min_bet_amount": MIN_BET_AMOUNT,
        "num_reels": NUM_REELS,
        "default_symbols": DEFAULT_SYMBOLS,
        "default_weights": DEFAULT_WEIGHTS,
        "default_payouts": DEFAULT_PAYOUTS,
        "session_timeout_hours": SESSION_TIMEOUT_HOURS,
        "database_url": DATABASE_URL,
        "log_level": LOG_LEVEL
    }

def validate_config():
    """
    Validate configuration settings.
    Raises ValueError if configuration is invalid.
    """
    if INITIAL_CREDITS <= 0:
        raise ValueError("Initial credits must be positive")

    if MAX_BET_AMOUNT <= 0 or MIN_BET_AMOUNT <= 0:
        raise ValueError("Bet amounts must be positive")

    if MIN_BET_AMOUNT > MAX_BET_AMOUNT:
        raise ValueError("Min bet amount cannot exceed max bet amount")

    if NUM_REELS < 1 or NUM_REELS > 10:
        raise ValueError("Number of reels must be between 1 and 10")

    if len(DEFAULT_SYMBOLS) != len(DEFAULT_WEIGHTS):
        raise ValueError("Symbols and weights must have same length")

    if not all(weight > 0 for weight in DEFAULT_WEIGHTS):
        raise ValueError("All symbol weights must be positive")

    if not all(symbol in DEFAULT_PAYOUTS for symbol in DEFAULT_SYMBOLS):
        raise ValueError("All symbols must have payout multipliers")

    logger.info("Configuration validation passed")

# Validate configuration on import
try:
    validate_config()
except ValueError as e:
    logger.error(f"Configuration validation failed: {e}")
    raise