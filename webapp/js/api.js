// API Client for NanoCoin Backend

class APIClient {
    constructor() {
        // Get base URL from current location or default to localhost
        this.baseURL = window.location.origin;
        this.initData = null;
    }

    // Initialize with Telegram WebApp data
    init() {
        if (window.Telegram?.WebApp) {
            this.initData = window.Telegram.WebApp.initData;
            
            // Set theme
            document.body.style.backgroundColor = window.Telegram.WebApp.backgroundColor || '#1a1a2e';
            
            // Expand to full height
            window.Telegram.WebApp.expand();
            
            // Enable closing confirmation
            window.Telegram.WebApp.enableClosingConfirmation();
        }
    }

    // Get auth headers
    getHeaders() {
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.initData}`
        };
    }

    // Generic API call
    async call(endpoint, method = 'GET', data = null) {
        const options = {
            method,
            headers: this.getHeaders()
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, options);
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'خطای سرور');
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // User APIs
    async getUserProfile() {
        return this.call('/api/user/profile');
    }

    async getLeaderboard(limit = 100) {
        return this.call(`/api/user/leaderboard?limit=${limit}`);
    }

    async syncUser() {
        return this.call('/api/user/sync', 'POST');
    }

    // Game APIs
    async click() {
        return this.call('/api/game/click', 'POST');
    }

    async claimMining() {
        return this.call('/api/game/mine', 'POST');
    }

    async refillEnergy(amount = 50) {
        return this.call('/api/game/refill-energy', 'POST', { amount });
    }

    async activateBoost(duration_minutes = 15) {
        return this.call('/api/game/activate-boost', 'POST', { duration_minutes });
    }

    async claimDailyReward() {
        return this.call('/api/game/daily-reward', 'POST');
    }

    // Shop APIs
    async getShopItems() {
        return this.call('/api/shop/items');
    }

    async buyItem(item_id, quantity = 1) {
        return this.call('/api/shop/buy', 'POST', { item_id, quantity });
    }

    async getInventory() {
        return this.call('/api/shop/inventory');
    }

    async toggleItem(inventory_id, active) {
        return this.call('/api/shop/toggle-item', 'POST', { inventory_id, active });
    }

    async sellItem(inventory_id, quantity = 1) {
        return this.call(`/api/shop/sell/${inventory_id}?quantity=${quantity}`, 'POST');
    }
}

// Create global API instance
const api = new APIClient();
