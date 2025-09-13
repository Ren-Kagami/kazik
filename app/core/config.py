"""
Configuration settings for the slot machine application.
"""

from typing import List
import logging

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Game constants
SYMBOLS: List[str] = ['🍒', '🍋', '🍊', '🍇', '🔔', '⭐', '💎']
SYMBOL_WEIGHTS: List[int] = [30, 25, 20, 15, 5, 3, 2]  # Higher = more common
REELS_COUNT: int = 3
INITIAL_CREDITS: int = 100
BET_AMOUNT: int = 10

# Payout multipliers (based on matching symbols)
PAYOUT_MULTIPLIERS = {
    '🍒': 2,   # Cherry - 2x
    '🍋': 3,   # Lemon - 3x
    '🍊': 4,   # Orange - 4x
    '🍇': 5,   # Grape - 5x
    '🔔': 10,  # Bell - 10x
    '⭐': 20,  # Star - 20x
    '💎': 50   # Diamond - 50x (jackpot)
}

# Server settings
HOST: str = "0.0.0.0"
PORT: int = 8000
DEBUG: bool = True
