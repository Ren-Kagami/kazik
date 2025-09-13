// Slot Machine Game JavaScript with Animations and Russian Localization

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

        // Animation settings
        this.spinDuration = 2000; // 2 seconds
        this.reelDelays = [0, 200, 400]; // Staggered stop times

        this.init();
    }

    init() {
        this.initializeElements();
        this.createSession();
        this.loadProbabilityData();
        this.updateDisplay();
    }

    initializeElements() {
        // Game elements
        this.spinBtn = document.getElementById('spin-btn');
        this.newSessionBtn = document.getElementById('new-session-btn');
        this.betAmountInput = document.getElementById('bet-amount');
        this.simulateBtn = document.getElementById('simulate-btn');

        // Display elements
        this.creditsDisplay = document.getElementById('credits');
        this.lastWinDisplay = document.getElementById('last-win');
        this.totalSpinsDisplay = document.getElementById('total-spins');
        this.totalWinningsDisplay = document.getElementById('total-winnings');
        this.rtpDisplay = document.getElementById('rtp');
        this.theoreticalRtpDisplay = document.getElementById('theoretical-rtp');

        // Reels
        this.reels = [
            document.getElementById('reel1'),
            document.getElementById('reel2'),
            document.getElementById('reel3')
        ];

        // Event listeners
        this.spinBtn.addEventListener('click', () => this.spin());
        this.newSessionBtn.addEventListener('click', () => this.newSession());
        this.simulateBtn?.addEventListener('click', () => this.runSimulation());

        console.log('Игровые автоматы инициализированы');
    }

    async createSession() {
        try {
            const response = await fetch('/api/v1/session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                const data = await response.json();
                this.sessionId = data.session_id;
                console.log('Создана новая сессия:', this.sessionId);
            } else {
                // Fallback to local session
                this.sessionId = 'local_' + Date.now();
                console.log('Используется локальная сессия');
            }
        } catch (error) {
            console.log('Ошибка создания сессии, используется локальный режим:', error);
            this.sessionId = 'local_' + Date.now();
        }
    }

    async loadProbabilityData() {
        try {
            const response = await fetch('/api/v1/probability');
            if (response.ok) {
                const data = await response.json();
                this.displayProbabilityInfo(data);
                this.displayPayoutTable();
            }
        } catch (error) {
            console.log('Загружаются локальные данные вероятности');
            this.displayLocalProbabilityInfo();
            this.displayPayoutTable();
        }
    }

    displayProbabilityInfo(data) {
        const symbolProbsContainer = document.getElementById('symbol-probs');
        if (symbolProbsContainer && data.symbol_probabilities) {
            symbolProbsContainer.innerHTML = '';
            Object.entries(data.symbol_probabilities).forEach(([symbol, prob]) => {
                const probItem = document.createElement('div');
                probItem.className = 'prob-item';
                probItem.innerHTML = `
                    <span>${symbol}</span>
                    <span>${(prob * 100).toFixed(1)}%</span>
                `;
                symbolProbsContainer.appendChild(probItem);
            });
        }

        if (this.theoreticalRtpDisplay && data.theoretical_rtp) {
            this.theoreticalRtpDisplay.textContent = `${data.theoretical_rtp.toFixed(2)}%`;
        }
    }

    displayLocalProbabilityInfo() {
        const totalWeight = this.symbolWeights.reduce((a, b) => a + b, 0);
        const probabilities = {};

        this.symbols.forEach((symbol, index) => {
            probabilities[symbol] = this.symbolWeights[index] / totalWeight;
        });

        this.displayProbabilityInfo({
            symbol_probabilities: probabilities,
            theoretical_rtp: this.calculateTheoreticalRTP()
        });
    }

    calculateTheoreticalRTP() {
        // Simplified RTP calculation
        const totalWeight = this.symbolWeights.reduce((a, b) => a + b, 0);
        let expectedPayout = 0;

        this.symbols.forEach((symbol, index) => {
            const probability = this.symbolWeights[index] / totalWeight;
            const multiplier = this.payoutMultipliers[symbol];
            expectedPayout += probability * probability * probability * multiplier * 2; // Three of a kind
            expectedPayout += probability * probability * (1 - probability) * 3 * multiplier; // Two of a kind
        });

        return (expectedPayout / 10) * 100; // Assuming bet of 10
    }

    displayPayoutTable() {
        const payoutGrid = document.getElementById('payout-grid');
        if (payoutGrid) {
            payoutGrid.innerHTML = '';
            Object.entries(this.payoutMultipliers).forEach(([symbol, multiplier]) => {
                const payoutItem = document.createElement('div');
                payoutItem.className = 'payout-item';
                payoutItem.innerHTML = `
                    <span>${symbol} x2</span>
                    <span>${multiplier}x ставка</span>
                `;
                payoutGrid.appendChild(payoutItem);

                const payoutItem3 = document.createElement('div');
                payoutItem3.className = 'payout-item';
                payoutItem3.innerHTML = `
                    <span>${symbol} x3</span>
                    <span>${multiplier * 2}x ставка</span>
                `;
                payoutGrid.appendChild(payoutItem3);
            });
        }
    }

    async spin() {
        if (this.isSpinning) return;

        const betAmount = parseInt(this.betAmountInput.value) || 10;

        if (this.credits < betAmount) {
            this.showMessage('Недостаточно кредитов!', 'error');
            return;
        }

        this.isSpinning = true;
        this.spinBtn.disabled = true;
        this.spinBtn.textContent = 'КРУТИТСЯ...';

        // Deduct bet
        this.credits -= betAmount;
        this.updateDisplay();

        // Start spinning animation
        this.startSpinAnimation();

        try {
            // Try to use API
            const response = await fetch(`/api/v1/spin/${this.sessionId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ bet_amount: betAmount })
            });

            let result;
            if (response.ok) {
                result = await response.json();
            } else {
                // Fallback to local spin
                result = this.localSpin(betAmount);
            }

            // Stop reels with result
            await this.stopReelsWithResult(result.symbols);

            // Handle payout
            this.credits = result.credits_remaining || (this.credits + result.payout);

            if (result.payout > 0) {
                await this.showWinAnimation(result.payout);
            }

            this.lastWinDisplay.textContent = result.payout;
            this.updateDisplay();

        } catch (error) {
            console.log('Ошибка API, используется локальная логика:', error);
            const result = this.localSpin(betAmount);
            await this.stopReelsWithResult(result.symbols);

            this.credits += result.payout;
            if (result.payout > 0) {
                await this.showWinAnimation(result.payout);
            }

            this.lastWinDisplay.textContent = result.payout;
            this.updateDisplay();
        }

        this.isSpinning = false;
        this.spinBtn.disabled = false;
        this.spinBtn.textContent = 'КРУТИТЬ!';
    }

    localSpin(betAmount) {
        const symbols = this.spinReels();
        const payout = this.calculatePayout(symbols, betAmount);

        return {
            symbols: symbols,
            payout: payout,
            is_winner: payout > 0
        };
    }

    spinReels() {
        const result = [];
        for (let i = 0; i < 3; i++) {
            const totalWeight = this.symbolWeights.reduce((a, b) => a + b, 0);
            let random = Math.random() * totalWeight;

            for (let j = 0; j < this.symbols.length; j++) {
                random -= this.symbolWeights[j];
                if (random <= 0) {
                    result.push(this.symbols[j]);
                    break;
                }
            }
        }
        return result;
    }

    calculatePayout(spinResult, betAmount) {
        const symbolCounts = {};
        spinResult.forEach(symbol => {
            symbolCounts[symbol] = (symbolCounts[symbol] || 0) + 1;
        });

        const maxCount = Math.max(...Object.values(symbolCounts));

        if (maxCount < 2) return 0;

        const matchingSymbols = Object.keys(symbolCounts).filter(symbol =>
            symbolCounts[symbol] === maxCount
        );

        const bestSymbol = matchingSymbols.reduce((best, current) =>
            this.payoutMultipliers[current] > this.payoutMultipliers[best] ? current : best
        );

        let multiplier = this.payoutMultipliers[bestSymbol];
        if (maxCount === 3) {
            multiplier *= 2; // Bonus for three of a kind
        }

        return betAmount * multiplier;
    }

    startSpinAnimation() {
        this.reels.forEach(reel => {
            reel.classList.add('spinning');
            this.animateReel(reel);
        });
    }

    animateReel(reel) {
        let counter = 0;
        const interval = setInterval(() => {
            const randomSymbol = this.symbols[Math.floor(Math.random() * this.symbols.length)];
            reel.textContent = randomSymbol;
            counter++;

            if (counter > 20) { // Stop after enough spins
                clearInterval(interval);
            }
        }, 100);
    }

    async stopReelsWithResult(resultSymbols) {
        for (let i = 0; i < this.reels.length; i++) {
            await this.delay(this.reelDelays[i]);
            this.reels[i].textContent = resultSymbols[i];
            this.reels[i].classList.remove('spinning');
            this.reels[i].classList.add('stopped');

            // Add bounce effect
            setTimeout(() => {
                this.reels[i].classList.remove('stopped');
            }, 300);
        }
    }

    async showWinAnimation(payout) {
        // Create win message
        const winMessage = document.createElement('div');
        winMessage.className = 'win-message';
        winMessage.innerHTML = `
            <div class="win-amount">ВЫИГРЫШ!</div>
            <div class="win-payout">+${payout}</div>
        `;

        document.body.appendChild(winMessage);

        // Add celebration effects
        this.createConfetti();

        // Flash reels
        this.reels.forEach(reel => {
            reel.classList.add('winning');
        });

        // Play win sound (if available)
        this.playWinSound();

        // Remove effects after animation
        setTimeout(() => {
            winMessage.remove();
            this.reels.forEach(reel => {
                reel.classList.remove('winning');
            });
        }, 3000);
    }

    createConfetti() {
        for (let i = 0; i < 50; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = Math.random() * 100 + '%';
            confetti.style.backgroundColor = this.getRandomColor();
            confetti.style.animationDelay = Math.random() * 2 + 's';

            document.body.appendChild(confetti);

            setTimeout(() => {
                confetti.remove();
            }, 4000);
        }
    }

    getRandomColor() {
        const colors = ['#FFD700', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'];
        return colors[Math.floor(Math.random() * colors.length)];
    }

    playWinSound() {
        // Create audio context for win sound
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            oscillator.frequency.setValueAtTime(523.25, audioContext.currentTime); // C5
            oscillator.frequency.setValueAtTime(659.25, audioContext.currentTime + 0.1); // E5
            oscillator.frequency.setValueAtTime(783.99, audioContext.currentTime + 0.2); // G5

            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
        } catch (error) {
            console.log('Звук недоступен:', error);
        }
    }

    showMessage(message, type = 'info') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = message;

        document.body.appendChild(messageDiv);

        setTimeout(() => {
            messageDiv.remove();
        }, 3000);
    }

    async newSession() {
        this.credits = 100;
        this.lastWinDisplay.textContent = '0';
        await this.createSession();
        this.updateDisplay();
        this.showMessage('Новая игровая сессия началась!', 'success');
    }

    async runSimulation() {
        const simSpins = parseInt(document.getElementById('sim-spins')?.value) || 1000;
        const simulationResults = document.getElementById('simulation-results');

        if (!simulationResults) return;

        simulationResults.style.display = 'block';
        simulationResults.innerHTML = '<div class="loading">Выполняется симуляция...</div>';

        try {
            const response = await fetch('/api/v1/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    num_simulations: simSpins,
                    bet_amount: 10
                })
            });

            if (response.ok) {
                const result = await response.json();
                this.displaySimulationResults(result);
            } else {
                throw new Error('Ошибка API');
            }
        } catch (error) {
            console.log('Запуск локальной симуляции:', error);
            const result = this.runLocalSimulation(simSpins);
            this.displaySimulationResults(result);
        }
    }

    runLocalSimulation(numSpins) {
        let totalBet = numSpins * 10;
        let totalPayout = 0;
        let wins = 0;
        let biggestWin = 0;

        for (let i = 0; i < numSpins; i++) {
            const symbols = this.spinReels();
            const payout = this.calculatePayout(symbols, 10);
            totalPayout += payout;

            if (payout > 0) {
                wins++;
                if (payout > biggestWin) {
                    biggestWin = payout;
                }
            }
        }

        return {
            simulation_stats: {
                total_spins: numSpins,
                total_bet: totalBet,
                total_payout: totalPayout,
                win_rate: (wins / numSpins) * 100,
                actual_rtp: (totalPayout / totalBet) * 100,
                biggest_win: biggestWin
            },
            comparison_data: {
                theoretical_rtp: this.calculateTheoreticalRTP(),
                actual_rtp: (totalPayout / totalBet) * 100
            }
        };
    }

    displaySimulationResults(result) {
        const simulationResults = document.getElementById('simulation-results');
        const stats = result.simulation_stats;
        const comparison = result.comparison_data;

        simulationResults.innerHTML = `
            <h4>Результаты симуляции</h4>
            <div class="sim-stat">Общее количество вращений: ${stats.total_spins}</div>
            <div class="sim-stat">Общая ставка: ${stats.total_bet}</div>
            <div class="sim-stat">Общий выигрыш: ${stats.total_payout}</div>
            <div class="sim-stat">Процент выигрышей: ${stats.win_rate.toFixed(2)}%</div>
            <div class="sim-stat">Фактический RTP: ${stats.actual_rtp.toFixed(2)}%</div>
            <div class="sim-stat">Наибольший выигрыш: ${stats.biggest_win}</div>
            <div class="sim-stat">Теоретический RTP: ${comparison.theoretical_rtp.toFixed(2)}%</div>
            <div class="sim-stat">Разница RTP: ${Math.abs(comparison.theoretical_rtp - comparison.actual_rtp).toFixed(2)}%</div>
        `;
    }

    updateDisplay() {
        if (this.creditsDisplay) {
            this.creditsDisplay.textContent = this.credits;
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialize the game when page loads
document.addEventListener('DOMContentLoaded', () => {
    new SlotMachine();
});

// CSS animations and styles for the new effects
const additionalStyles = `
    .reel.spinning {
        animation: spin 0.1s infinite;
        border-color: #ff6b6b;
    }
    
    .reel.stopped {
        animation: bounce 0.3s ease;
        border-color: #2ecc71;
    }
    
    .reel.winning {
        animation: flash 0.5s infinite alternate;
        border-color: #ffd700;
        box-shadow: 0 0 20px #ffd700;
    }
    
    @keyframes spin {
        0% { transform: rotateY(0deg); }
        100% { transform: rotateY(360deg); }
    }
    
    @keyframes bounce {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }
    
    @keyframes flash {
        0% { background: white; }
        100% { background: #ffd700; }
    }
    
    .win-message {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: linear-gradient(45deg, #ffd700, #ffed4e);
        color: #333;
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        font-size: 2em;
        font-weight: bold;
        z-index: 1000;
        animation: winPulse 2s infinite;
        box-shadow: 0 10px 30px rgba(255, 215, 0, 0.5);
    }
    
    @keyframes winPulse {
        0%, 100% { transform: translate(-50%, -50%) scale(1); }
        50% { transform: translate(-50%, -50%) scale(1.05); }
    }
    
    .confetti {
        position: fixed;
        width: 10px;
        height: 10px;
        background: #ffd700;
        animation: confettiFall 3s linear infinite;
        z-index: 999;
    }
    
    @keyframes confettiFall {
        0% {
            top: -10px;
            transform: rotate(0deg);
            opacity: 1;
        }
        100% {
            top: 100vh;
            transform: rotate(360deg);
            opacity: 0;
        }
    }
    
    .message {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        border-radius: 10px;
        color: white;
        font-weight: bold;
        z-index: 1000;
        animation: slideIn 0.5s ease;
    }
    
    .message.success { background: #2ecc71; }
    .message.error { background: #e74c3c; }
    .message.info { background: #3498db; }
    
    @keyframes slideIn {
        from { transform: translateX(100%); }
        to { transform: translateX(0); }
    }
    
    .loading {
        text-align: center;
        font-style: italic;
        opacity: 0.7;
    }
    
    .sim-stat {
        padding: 5px 0;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
`;

// Add the additional styles to the page
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);