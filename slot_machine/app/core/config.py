"""
Настройки конфигурации для приложения игровых автоматов.
"""

from typing import List
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Игровые константы
SYMBOLS: List[str] = ['🍒', '🍋', '🍊', '🍇', '🔔', '⭐', '💎']
SYMBOL_WEIGHTS: List[int] = [30, 25, 20, 15, 5, 3, 2]  # Больше = чаще появляется
REELS_COUNT: int = 3
INITIAL_CREDITS: int = 100
BET_AMOUNT: int = 10

# Множители выплат (по совпадающим символам)
PAYOUT_MULTIPLIERS = {
    '🍒': 2,   # Вишня - 2x
    '🍋': 3,   # Лимон - 3x
    '🍊': 4,   # Апельсин - 4x
    '🍇': 5,   # Виноград - 5x
    '🔔': 10,  # Колокольчик - 10x
    '⭐': 20,  # Звезда - 20x
    '💎': 50   # Алмаз - 50x (джекпот)
}

# Настройки сервера
HOST: str = "0.0.0.0"
PORT: int = 8000
DEBUG: bool = True
