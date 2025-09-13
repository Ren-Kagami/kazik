// Admin Panel JavaScript
class AdminPanel {
    constructor() {
        this.authToken = localStorage.getItem('admin_token');
        this.currentSection = 'overview';
        this.refreshInterval = null;
        this.init();
    }

    async init() {
        // Hide loading screen after a short delay
        setTimeout(() => {
            document.getElementById('loading-screen').style.display = 'none';
            this.checkAuthentication();
        }, 1000);

        this.setupEventListeners();
    }

    checkAuthentication() {
        if (this.authToken) {
            this.showDashboard();
            this.loadDashboardData();
        } else {
            this.showLogin();
        }
    }

    showLogin() {
        document.getElementById('login-section').style.display = 'flex';
        document.getElementById('dashboard').style.display = 'none';
    }

    showDashboard() {
        document.getElementById('login-section').style.display = 'none';
        document.getElementById('dashboard').style.display = 'grid';
        this.startAutoRefresh();
    }

    setupEventListeners() {
        // Login form
        document.getElementById('login-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        // Logout
        document.getElementById('logout-btn').addEventListener('click', () => {
            this.handleLogout();
        });

        // Navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchSection(e.target.dataset.section);
            });
        });

        // Probability form
        document.getElementById('probability-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleProbabilityUpdate();
        });

        // Preview changes
        document.getElementById('preview-changes-btn').addEventListener('click', () => {
            this.previewProbabilityChanges();
        });

        // Reset probability
        document.getElementById('reset-probability-btn').addEventListener('click', () => {
            this.resetProbabilitySettings();
        });

        // Testing
        document.getElementById('run-test-btn').addEventListener('click', () => {
            this.runProbabilityTest();
        });

        // Sessions management
        document.getElementById('refresh-sessions-btn').addEventListener('click', () => {
            this.loadSessionsData();
        });

        document.getElementById('session-filter').addEventListener('change', () => {
            this.loadSessionsData();
        });

        // Analytics
        document.getElementById('analytics-period').addEventListener('change', () => {
            this.loadAnalyticsData();
        });

        // Export
        document.getElementById('export-analytics-btn').addEventListener('click', () => {
            this.exportAnalytics();
        });

        // Modal
        document.querySelector('.modal-close').addEventListener('click', () => {
            this.hideModal();
        });

        document.getElementById('modal-cancel').addEventListener('click', () => {
            this.hideModal();
        });

        // Report buttons
        document.querySelectorAll('.report-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.generateReport(e.target.dataset.report);
            });
        });
    }

    async handleLogin() {
        const loginBtn = document.getElementById('login-btn');
        const errorDiv = document.getElementById('login-error');
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        // Show loading state
        loginBtn.querySelector('.button-text').style.display = 'none';
        loginBtn.querySelector('.button-spinner').style.display = 'inline';
        loginBtn.disabled = true;
        errorDiv.style.display = 'none';

        try {
            const response = await fetch('/api/v1/admin/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            if (response.ok) {
                const data = await response.json();
                this.authToken = data.access_token;
                localStorage.setItem('admin_token', this.authToken);

                this.showNotification('Успешный вход в систему', 'success');
                this.showDashboard();
                this.loadDashboardData();
            } else {
                const error = await response.json();
                errorDiv.textContent = error.message || 'Неверные учетные данные';
                errorDiv.style.display = 'block';
            }
        } catch (error) {
            console.error('Login error:', error);
            errorDiv.textContent = 'Ошибка подключения к серверу';
            errorDiv.style.display = 'block';
        } finally {
            // Reset button state
            loginBtn.querySelector('.button-text').style.display = 'inline';
            loginBtn.querySelector('.button-spinner').style.display = 'none';
            loginBtn.disabled = false;
        }
    }

    handleLogout() {
        localStorage.removeItem('admin_token');
        this.authToken = null;
        this.stopAutoRefresh();
        this.showLogin();
        this.showNotification('Выход из системы выполнен', 'info');

        // Reset form
        document.getElementById('login-form').reset();
        document.getElementById('login-error').style.display = 'none';
    }

    switchSection(section) {
        // Update navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.section === section);
        });

        // Update content
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(`${section}-section`).classList.add('active');

        this.currentSection = section;

        // Load section-specific data
        switch (section) {
            case 'overview':
                this.loadOverviewData();
                break;
            case 'probability':
                this.loadProbabilityData();
                break;
            case 'sessions':
                this.loadSessionsData();
                break;
            case 'analytics':
                this.loadAnalyticsData();
                break;
        }
    }

    async loadDashboardData() {
        try {
            await Promise.all([
                this.loadOverviewData(),
                this.loadProbabilityData()
            ]);
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showNotification('Ошибка загрузки данных панели', 'error');
        }
    }

    async loadOverviewData() {
        try {
            const response = await this.apiCall('/api/v1/admin/sessions/analytics');
            const data = await response.json();

            // Update stats cards
            document.getElementById('active-sessions').textContent = data.active_sessions || '-';
            document.getElementById('total-spins').textContent = data.total_spins || '-';
            document.getElementById('total-winnings').textContent = data.total_winnings || '-';
            document.getElementById('house-edge').textContent =
                data.house_edge_percent ? `${data.house_edge_percent.toFixed(2)}%` : '-';

            this.createSessionChart(data);
            this.createWinningsChart(data);
        } catch (error) {
            console.error('Error loading overview data:', error);
            this.showNotification('Ошибка загрузки обзорных данных', 'error');
        }
    }

    async loadProbabilityData() {
        try {
            const response = await this.apiCall('/api/v1/probability');
            const data = await response.json();

            // Display current settings
            this.displayCurrentProbabilitySettings(data);

            // Setup probability editor
            this.setupProbabilityEditor(data);

            document.getElementById('current-rtp').textContent =
                `${data.theoretical_rtp.toFixed(2)}%`;
        } catch (error) {
            console.error('Error loading probability data:', error);
            this.showNotification('Ошибка загрузки данных вероятностей', 'error');
        }
    }

    displayCurrentProbabilitySettings(data) {
        const container = document.getElementById('current-probability-display');
        container.innerHTML = '';

        Object.entries(data.symbol_probabilities).forEach(([symbol, prob]) => {
            const item = document.createElement('div');
            item.className = 'prob-display-item';
            item.innerHTML = `
                <span class="symbol">${symbol}</span>
                <span class="probability">${(prob * 100).toFixed(1)}%</span>
                <span class="payout">${data.payout_multipliers[symbol]}x</span>
            `;
            container.appendChild(item);
        });
    }

    setupProbabilityEditor(data) {
        const container = document.getElementById('symbols-grid');
        container.innerHTML = '';

        Object.keys(data.symbol_probabilities).forEach(symbol => {
            const weight = data.weights[symbol];
            const payout = data.payout_multipliers[symbol];

            const controlDiv = document.createElement('div');
            controlDiv.className = 'symbol-control';
            controlDiv.innerHTML = `
                <div class="symbol">${symbol}</div>
                <label>Вес:</label>
                <input type="number" name="weight_${symbol}" value="${weight}" min="1" max="100">
                <label>Множитель:</label>
                <input type="number" name="payout_${symbol}" value="${payout}" min="1" max="100">
            `;
            container.appendChild(controlDiv);
        });
    }

    async previewProbabilityChanges() {
        const formData = new FormData(document.getElementById('probability-form'));
        const changes = this.extractProbabilityChanges(formData);

        // Calculate new RTP
        const newRTP = this.calculateRTP(changes.weights, changes.payouts);
        const currentRTP = parseFloat(document.getElementById('current-rtp').textContent);
        const diff = newRTP - currentRTP;

        // Show preview
        const previewSection = document.getElementById('probability-preview');
        document.getElementById('preview-rtp').textContent = `${newRTP.toFixed(2)}%`;

        const diffSpan = document.getElementById('rtp-difference');
        diffSpan.textContent = `(${diff > 0 ? '+' : ''}${diff.toFixed(2)}%)`;
        diffSpan.className = `rtp-diff ${diff > 0 ? 'positive' : 'negative'}`;

        // Show probability preview
        const probsContainer = document.getElementById('preview-probabilities');
        probsContainer.innerHTML = '';

        const totalWeight = Object.values(changes.weights).reduce((a, b) => a + b, 0);
        Object.entries(changes.weights).forEach(([symbol, weight]) => {
            const prob = (weight / totalWeight) * 100;
            const item = document.createElement('div');
            item.innerHTML = `${symbol}: ${prob.toFixed(1)}%`;
            probsContainer.appendChild(item);
        });

        previewSection.style.display = 'block';
    }

    extractProbabilityChanges(formData) {
        const weights = {};
        const payouts = {};

        for (const [key, value] of formData.entries()) {
            if (key.startsWith('weight_')) {
                const symbol = key.replace('weight_', '');
                weights[symbol] = parseInt(value);
            } else if (key.startsWith('payout_')) {
                const symbol = key.replace('payout_', '');
                payouts[symbol] = parseInt(value);
            }
        }

        return { weights, payouts };
    }

    calculateRTP(weights, payouts) {
        const totalWeight = Object.values(weights).reduce((a, b) => a + b, 0);
        let expectedPayout = 0;

        Object.entries(weights).forEach(([symbol, weight]) => {
            const prob = weight / totalWeight;
            const multiplier = payouts[symbol];

            // Two of a kind
            const probTwo = prob * prob * (1 - prob) * 3;
            expectedPayout += probTwo * multiplier;

            // Three of a kind (double payout)
            const probThree = prob * prob * prob;
            expectedPayout += probThree * multiplier * 2;
        });

        return expectedPayout * 100;
    }

    async handleProbabilityUpdate() {
        const formData = new FormData(document.getElementById('probability-form'));
        const changes = this.extractProbabilityChanges(formData);

        try {
            const response = await this.apiCall('/api/v1/admin/probability/update', {
                method: 'POST',
                body: JSON.stringify({
                    symbol_weights: changes.weights,
                    payout_multipliers: changes.payouts
                })
            });

            if (response.ok) {
                this.showNotification('Настройки вероятностей обновлены', 'success');
                await this.loadProbabilityData();
                document.getElementById('probability-preview').style.display = 'none';
            } else {
                const error = await response.json();
                this.showNotification(`Ошибка: ${error.message}`, 'error');
            }
        } catch (error) {
            console.error('Error updating probability:', error);
            this.showNotification('Ошибка обновления настроек', 'error');
        }
    }

    async resetProbabilitySettings() {
        const confirmed = await this.showModal(
            'Сброс настроек',
            'Вы уверены, что хотите сбросить настройки вероятностей к значениям по умолчанию?'
        );

        if (confirmed) {
            // Reset to default values (would call API endpoint)
            this.showNotification('Настройки сброшены к умолчаниям', 'info');
            await this.loadProbabilityData();
        }
    }

    async runProbabilityTest() {
        const simulations = parseInt(document.getElementById('test-simulations').value);
        const resultsContainer = document.getElementById('test-results');

        resultsContainer.innerHTML = '<div class="loading">Выполняется тестирование...</div>';
        resultsContainer.style.display = 'block';

        try {
            const response = await this.apiCall('/api/v1/simulate', {
                method: 'POST',
                body: JSON.stringify({
                    num_simulations: simulations,
                    bet_amount: 10
                })
            });

            const data = await response.json();
            this.displayTestResults(data);
        } catch (error) {
            console.error('Error running test:', error);
            resultsContainer.innerHTML = '<div class="error">Ошибка выполнения теста</div>';
        }
    }

    displayTestResults(data) {
        const container = document.getElementById('test-results');
        const stats = data.simulation_stats;
        const comparison = data.comparison_data;

        container.innerHTML = `
            <h4>Результаты тестирования</h4>
            <div class="test-stat">Симуляций: ${stats.total_spins}</div>
            <div class="test-stat">Фактический RTP: ${stats.actual_rtp.toFixed(2)}%</div>
            <div class="test-stat">Теоретический RTP: ${comparison.theoretical_rtp.toFixed(2)}%</div>
            <div class="test-stat">Разность: ${Math.abs(comparison.rtp_difference).toFixed(2)}%</div>
            <div class="test-stat">Процент выигрышей: ${stats.win_rate.toFixed(2)}%</div>
            <div class="test-stat">Наибольший выигрыш: ${stats.biggest_win}</div>
        `;
    }

    async loadSessionsData() {
        try {
            const filter = document.getElementById('session-filter').value;
            const response = await this.apiCall('/api/v1/sessions/stats?limit=100');
            const sessions = await response.json();

            this.displaySessionsTable(sessions);
        } catch (error) {
            console.error('Error loading sessions:', error);
            this.showNotification('Ошибка загрузки данных сессий', 'error');
        }
    }

    displaySessionsTable(sessions) {
        const tbody = document.getElementById('sessions-table-body');
        tbody.innerHTML = '';

        sessions.forEach(session => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${session.session_id.substring(0, 8)}...</td>
                <td>${new Date(session.created_at).toLocaleString('ru')}</td>
                <td>${new Date(session.created_at).toLocaleString('ru')}</td>
                <td>${session.final_credits}</td>
                <td>${session.total_spins}</td>
                <td>${session.total_winnings}</td>
                <td>${session.estimated_rtp.toFixed(2)}%</td>
                <td><span class="status-badge ${session.final_credits > 0 ? 'status-active' : 'status-inactive'}">
                    ${session.final_credits > 0 ? 'Активна' : 'Неактивна'}
                </span></td>
                <td>
                    <button class="action-btn delete" onclick="adminPanel.deleteSession('${session.session_id}')">
                        Удалить
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    async deleteSession(sessionId) {
        const confirmed = await this.showModal(
            'Удаление сессии',
            `Вы уверены, что хотите удалить сессию ${sessionId.substring(0, 8)}?`
        );

        if (confirmed) {
            try {
                const response = await this.apiCall(`/api/v1/admin/sessions/${sessionId}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    this.showNotification('Сессия удалена', 'success');
                    this.loadSessionsData();
                } else {
                    throw new Error('Failed to delete session');
                }
            } catch (error) {
                console.error('Error deleting session:', error);
                this.showNotification('Ошибка удаления сессии', 'error');
            }
        }
    }

    async loadAnalyticsData() {
        // Implementation for detailed analytics
        this.showNotification('Аналитические данные загружаются...', 'info');
    }

    async exportAnalytics() {
        try {
            const response = await this.apiCall('/api/v1/admin/sessions/analytics');
            const data = await response.json();

            // Convert to CSV
            const csv = this.convertToCSV(data);
            this.downloadCSV(csv, `analytics_${new Date().toISOString().split('T')[0]}.csv`);

            this.showNotification('Данные экспортированы', 'success');
        } catch (error) {
            console.error('Error exporting analytics:', error);
            this.showNotification('Ошибка экспорта данных', 'error');
        }
    }

    convertToCSV(data) {
        const headers = Object.keys(data).join(',');
        const values = Object.values(data).join(',');
        return `${headers}\n${values}`;
    }

    downloadCSV(csvContent, fileName) {
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        a.click();
        window.URL.revokeObjectURL(url);
    }

    async generateReport(reportType) {
        this.showNotification(`Генерация отчета "${reportType}"...`, 'info');
        // Implementation for report generation
    }

    createSessionChart(data) {
        // Simple chart implementation (would use Chart.js in production)
        const canvas = document.getElementById('sessions-chart');
        const ctx = canvas.getContext('2d');

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw simple bar chart
        ctx.fillStyle = '#3498db';
        ctx.fillRect(50, 50, 100, data.active_sessions * 2);
        ctx.fillText('Active Sessions', 50, 170);
    }

    createWinningsChart(data) {
        // Simple chart implementation
        const canvas = document.getElementById('winnings-chart');
        const ctx = canvas.getContext('2d');

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw pie chart segment
        ctx.beginPath();
        ctx.arc(200, 100, 80, 0, Math.PI);
        ctx.fillStyle = '#2ecc71';
        ctx.fill();

        ctx.fillText('Winnings Distribution', 120, 190);
    }

    async apiCall(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.authToken}`
            }
        };

        const response = await fetch(url, { ...defaultOptions, ...options });

        if (response.status === 401) {
            this.handleLogout();
            throw new Error('Unauthorized');
        }

        return response;
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notification-container');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        container.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);

        // Remove on click
        notification.addEventListener('click', () => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        });
    }

    showModal(title, message) {
        return new Promise((resolve) => {
            const modal = document.getElementById('modal');
            document.getElementById('modal-title').textContent = title;
            document.getElementById('modal-message').textContent = message;

            modal.style.display = 'flex';

            const confirmBtn = document.getElementById('modal-confirm');
            const cancelBtn = document.getElementById('modal-cancel');

            const cleanup = () => {
                modal.style.display = 'none';
                confirmBtn.replaceWith(confirmBtn.cloneNode(true));
                cancelBtn.replaceWith(cancelBtn.cloneNode(true));
                document.getElementById('modal-confirm').addEventListener('click', () => {
                    cleanup();
                    resolve(true);
                });
                document.getElementById('modal-cancel').addEventListener('click', () => {
                    cleanup();
                    resolve(false);
                });
            };

            document.getElementById('modal-confirm').addEventListener('click', () => {
                cleanup();
                resolve(true);
            });

            document.getElementById('modal-cancel').addEventListener('click', () => {
                cleanup();
                resolve(false);
            });
        });
    }

    hideModal() {
        document.getElementById('modal').style.display = 'none';
    }

    startAutoRefresh() {
        // Refresh overview data every 30 seconds
        this.refreshInterval = setInterval(() => {
            if (this.currentSection === 'overview') {
                this.loadOverviewData();
            }
        }, 30000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
}

// Initialize admin panel when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.adminPanel = new AdminPanel();
});

// Handle browser back/forward
window.addEventListener('popstate', (event) => {
    if (window.adminPanel) {
        window.adminPanel.checkAuthentication();
    }
});