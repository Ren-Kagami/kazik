#!/bin/bash

# Enhanced Slot Machine FastAPI Project Creator with Animations
# Creates complete project with Russian translation and enhanced animations

echo "🎰 Создание улучшенного проекта Игровые Автоматы с анимациями..."

# Create main project directory
mkdir -p slot_machine
cd slot_machine

echo "📁 Создание структуры директорий..."

# Create directories
mkdir -p app/{models,api,core,static}
mkdir -p tests

echo "📄 Создание файлов с полным содержимым..."

# Create requirements.txt
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pytest==7.4.3
pytest-cov==4.1.0
pytest-asyncio==0.21.1
httpx==0.25.2
EOF

# Create app/__init__.py
cat > app/__init__.py << 'EOF'
"""
Игровые Автоматы - Веб Приложение.

FastAPI приложение для изучения теории вероятности через игровые автоматы.
"""

__version__ = "1.0.0"
EOF

# Create app/core/config.py
cat > app/core/config.py << 'EOF'
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
EOF

# Create enhanced JavaScript with animations
cat > app/static/script.js << 'EOF'
// Игровые Автоматы с Анимациями и Русской Локализацией

class SlotMachine {
    constructor() {
        this.sessionId = null;
        this.credits = 100;
        this.isSpinning = false;
        this.symbols = ['🍒', '🍋', '🍊', '🍇', '🔔', '⭐', '💎'];
        this.symbolWeights = [30, 25, 20, 15, 5, 3, 2];
        this.payoutMultipliers = {
            '🍒': 2, '🍋': 3, '🍊': 4, '🍇': 5,
            '🔔': 10, '⭐': 20, '💎': 50
        };

        // Настройки анимации
        this.spinDuration = 2000; // 2 секунды
        this.reelDelays = [0, 200, 400]; // Задержки остановки барабанов

        this.init();