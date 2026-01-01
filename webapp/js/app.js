// Main app initialization and navigation

class App {
    constructor() {
        this.currentScreen = 'main-screen';
    }

    // Initialize app
    async init() {
        // Initialize Telegram WebApp API
        api.init();

        // Show loading screen
        this.showLoading();

        try {
            // Initialize game
            await gameManager.init();

            // Setup navigation
            this.setupNavigation();

            // Hide loading, show app
            this.hideLoading();

        } catch (error) {
            console.error('App initialization error:', error);
            this.showError('خطا در بارگذاری بازی. لطفاً دوباره تلاش کنید.');
        }
    }

    // Show loading screen
    showLoading() {
        document.getElementById('loading-screen').style.display = 'flex';
        document.getElementById('app').style.display = 'none';
    }

    // Hide loading screen
    hideLoading() {
        document.getElementById('loading-screen').style.display = 'none';
        document.getElementById('app').style.display = 'flex';
    }

    // Show error
    showError(message) {
        const loadingScreen = document.getElementById('loading-screen');
        loadingScreen.innerHTML = `
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 48px; margin-bottom: 20px;">❌</div>
                <p style="color: var(--text-color);">${message}</p>
                <button class="btn btn-primary" onclick="location.reload()" 
                    style="margin-top: 20px; max-width: 200px;">
                    تلاش مجدد
                </button>
            </div>
        `;
    }

    // Setup navigation
    setupNavigation() {
        const navButtons = document.querySelectorAll('.nav-btn');
        
        navButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const screenId = btn.getAttribute('data-screen');
                this.navigateTo(screenId);
            });
        });
    }

    // Navigate to screen
    navigateTo(screenId) {
        // Hide all screens
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });

        // Remove active from all nav buttons
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Show target screen
        const targetScreen = document.getElementById(screenId);
        if (targetScreen) {
            targetScreen.classList.add('active');
            this.currentScreen = screenId;

            // Update active nav button
            const activeBtn = document.querySelector(`[data-screen="${screenId}"]`);
            if (activeBtn) {
                activeBtn.classList.add('active');
            }

            // Load screen data
            this.loadScreenData(screenId);

            // Haptic feedback
            hapticFeedback('light');
        }
    }

    // Load data for specific screen
    async loadScreenData(screenId) {
        switch(screenId) {
            case 'shop-screen':
                await shopManager.loadShop();
                break;
            case 'inventory-screen':
                await shopManager.loadInventory();
                break;
            case 'leaderboard-screen':
                await leaderboardManager.loadLeaderboard();
                break;
            default:
                // Main screen - already loaded
                break;
        }
    }
}

// Create and initialize app
const app = new App();

// Start app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        app.init();
    });
} else {
    app.init();
}

// Handle visibility change (when user returns to app)
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && gameManager.userData) {
        // Refresh data when user returns
        gameManager.userData = api.getUserProfile().then(data => {
            gameManager.userData = data;
            gameManager.updateUI();
        }).catch(console.error);
    }
});
