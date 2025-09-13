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
