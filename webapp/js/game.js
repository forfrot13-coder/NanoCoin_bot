// Game logic and UI management

class GameManager {
    constructor() {
        this.userData = null;
        this.clickThrottle = throttle(this.handleClick.bind(this), 100);
        this.isLoading = false;
    }

    // Initialize game
    async init() {
        try {
            // Load user profile
            this.userData = await api.getUserProfile();
            this.updateUI();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Start auto-sync
            this.startAutoSync();
            
        } catch (error) {
            console.error('Failed to initialize game:', error);
            showToast('خطا در بارگذاری اطلاعات', 'error');
        }
    }

    // Update UI with user data
    updateUI() {
        if (!this.userData) return;

        // Header
        document.getElementById('user-name').textContent = this.userData.first_name || 'بازیکن';
        document.getElementById('user-level').textContent = `سطح ${this.userData.click_level}`;
        document.getElementById('coins').textContent = formatNumber(this.userData.coins);
        document.getElementById('diamonds').textContent = formatNumber(this.userData.diamonds);

        // Energy bar
        const energyPercent = (this.userData.energy / this.userData.max_energy) * 100;
        document.getElementById('energy-bar').style.width = `${energyPercent}%`;
        document.getElementById('energy-text').textContent = 
            `${this.userData.energy}/${this.userData.max_energy}`;

        // XP bar
        const xpNeeded = calculateXPForLevel(this.userData.click_level);
        const xpPercent = (this.userData.click_xp / xpNeeded) * 100;
        document.getElementById('xp-bar').style.width = `${xpPercent}%`;
        document.getElementById('xp-text').textContent = 
            `${this.userData.click_xp}/${xpNeeded}`;

        // Electricity
        document.getElementById('electricity-text').textContent = 
            `${this.userData.electricity}/${this.userData.max_electricity}`;

        // Disable click button if no energy
        const clickBtn = document.getElementById('click-btn');
        clickBtn.disabled = this.userData.energy <= 0;
    }

    // Setup event listeners
    setupEventListeners() {
        // Click button
        document.getElementById('click-btn').addEventListener('click', () => {
            this.clickThrottle();
        });

        // Mining claim
        document.getElementById('claim-mining-btn').addEventListener('click', () => {
            this.handleMining();
        });

        // Daily reward
        document.getElementById('daily-reward-btn').addEventListener('click', () => {
            this.handleDailyReward();
        });

        // Refill energy
        document.getElementById('refill-energy-btn').addEventListener('click', () => {
            this.handleRefillEnergy();
        });

        // Activate boost
        document.getElementById('activate-boost-btn').addEventListener('click', () => {
            this.handleActivateBoost();
        });
    }

    // Handle click action
    async handleClick() {
        if (this.isLoading) return;
        if (this.userData.energy <= 0) {
            showToast('انرژی شما تمام شده است!', 'warning');
            return;
        }

        try {
            hapticFeedback('light');
            
            const result = await api.click();
            
            // Update local data
            this.userData.coins = result.new_coins;
            this.userData.diamonds = result.new_diamonds;
            this.userData.energy = result.new_energy;
            
            if (result.new_level) {
                this.userData.click_level = result.new_level;
            }

            // Show feedback
            const clickBtn = document.getElementById('click-btn');
            showCoinPopup(clickBtn, result.coins_earned);

            if (result.leveled_up) {
                hapticFeedback('heavy');
                showToast(`🎉 تبریک! شما به سطح ${result.new_level} رسیدید!`, 'success');
            }

            if (result.diamond_found) {
                hapticFeedback('medium');
                showToast('💎 شما یک الماس پیدا کردید!', 'success');
            }

            this.updateUI();

        } catch (error) {
            console.error('Click error:', error);
            showToast(error.message || 'خطا در کلیک', 'error');
        }
    }

    // Handle mining claim
    async handleMining() {
        if (this.isLoading) return;
        this.isLoading = true;

        try {
            const result = await api.claimMining();

            // Update local data
            this.userData.coins = result.new_coins;
            this.userData.diamonds = result.new_diamonds;
            this.userData.electricity = result.new_electricity;

            hapticFeedback('medium');
            showToast(
                `⛏ استخراج موفق!\n💰 ${formatNumber(result.coins_earned)} سکه\n💎 ${result.diamonds_earned} الماس`,
                'success'
            );

            this.updateUI();

        } catch (error) {
            console.error('Mining error:', error);
            showToast(error.message || 'خطا در استخراج', 'error');
        } finally {
            this.isLoading = false;
        }
    }

    // Handle daily reward
    async handleDailyReward() {
        if (this.isLoading) return;
        this.isLoading = true;

        try {
            const result = await api.claimDailyReward();

            hapticFeedback('heavy');
            showToast(
                `🎁 جایزه روزانه!\n💰 ${formatNumber(result.coins)} سکه\n💎 ${result.diamonds} الماس\n🔥 روز ${result.streak}`,
                'success'
            );

            // Refresh profile
            this.userData = await api.getUserProfile();
            this.updateUI();

        } catch (error) {
            console.error('Daily reward error:', error);
            showToast(error.message || 'خطا در دریافت جایزه', 'error');
        } finally {
            this.isLoading = false;
        }
    }

    // Handle refill energy
    async handleRefillEnergy() {
        if (this.isLoading) return;
        this.isLoading = true;

        try {
            const result = await api.refillEnergy();

            this.userData.energy = result.new_energy;
            this.userData.diamonds = result.new_diamonds;

            hapticFeedback('medium');
            showToast('⚡️ انرژی شارژ شد!', 'success');

            this.updateUI();

        } catch (error) {
            console.error('Refill energy error:', error);
            showToast(error.message || 'خطا در شارژ انرژی', 'error');
        } finally {
            this.isLoading = false;
        }
    }

    // Handle activate boost
    async handleActivateBoost() {
        if (this.isLoading) return;
        this.isLoading = true;

        try {
            const result = await api.activateBoost();

            this.userData.diamonds = result.new_diamonds;

            hapticFeedback('heavy');
            showToast('🚀 بوست ۲x فعال شد!', 'success');

            this.updateUI();

        } catch (error) {
            console.error('Activate boost error:', error);
            showToast(error.message || 'خطا در فعال‌سازی بوست', 'error');
        } finally {
            this.isLoading = false;
        }
    }

    // Auto-sync user data periodically
    startAutoSync() {
        setInterval(async () => {
            try {
                const syncData = await api.syncUser();
                
                // Update local data
                if (syncData.energy !== undefined) {
                    this.userData.energy = syncData.energy;
                    this.userData.electricity = syncData.electricity;
                    this.updateUI();
                }
            } catch (error) {
                console.error('Auto-sync error:', error);
            }
        }, 30000); // Every 30 seconds
    }
}

// Create global game manager instance
const gameManager = new GameManager();
