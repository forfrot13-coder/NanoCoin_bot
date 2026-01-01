// Shop and Inventory management

class ShopManager {
    constructor() {
        this.shopItems = [];
        this.inventoryItems = [];
    }

    // Load shop items
    async loadShop() {
        try {
            this.shopItems = await api.getShopItems();
            this.renderShop();
        } catch (error) {
            console.error('Failed to load shop:', error);
            showToast('خطا در بارگذاری فروشگاه', 'error');
        }
    }

    // Render shop items
    renderShop() {
        const container = document.getElementById('shop-items');
        container.innerHTML = '';

        if (this.shopItems.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">فروشگاه خالی است</p>';
            return;
        }

        this.shopItems.forEach(item => {
            const card = document.createElement('div');
            card.className = 'item-card';
            
            const stockText = item.stock === -1 ? 'نامحدود' : `موجودی: ${item.stock}`;
            const canBuy = item.stock === -1 || item.stock > 0;
            
            card.innerHTML = `
                <div class="item-icon">${item.emoji}</div>
                <div class="item-name">${item.name}</div>
                <div class="item-price">💎 ${item.price_diamonds}</div>
                <div style="font-size: 12px; color: var(--text-secondary);">${stockText}</div>
                ${item.mining_rate > 0 ? `<div style="font-size: 12px;">⛏ ${item.mining_rate}/ساعت</div>` : ''}
                <button class="btn btn-primary btn-small" ${!canBuy ? 'disabled' : ''} 
                    onclick="shopManager.buyItem(${item.id})">
                    خرید
                </button>
            `;
            
            container.appendChild(card);
        });
    }

    // Buy item
    async buyItem(itemId) {
        try {
            hapticFeedback('medium');
            await api.buyItem(itemId, 1);
            
            showToast('✅ آیتم خریداری شد!', 'success');
            
            // Refresh shop and user data
            await this.loadShop();
            gameManager.userData = await api.getUserProfile();
            gameManager.updateUI();
            
        } catch (error) {
            console.error('Buy item error:', error);
            showToast(error.message || 'خطا در خرید آیتم', 'error');
        }
    }

    // Load inventory
    async loadInventory() {
        try {
            this.inventoryItems = await api.getInventory();
            this.renderInventory();
        } catch (error) {
            console.error('Failed to load inventory:', error);
            showToast('خطا در بارگذاری کیف', 'error');
        }
    }

    // Render inventory
    renderInventory() {
        const container = document.getElementById('inventory-items');
        container.innerHTML = '';

        if (this.inventoryItems.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">کیف شما خالی است</p>';
            return;
        }

        this.inventoryItems.forEach(invItem => {
            const item = invItem.item;
            const card = document.createElement('div');
            card.className = 'item-card';
            
            card.innerHTML = `
                <div class="item-icon">${item.emoji}</div>
                <div class="item-name">${item.name}</div>
                <div style="font-size: 14px;">تعداد: ${invItem.quantity}</div>
                ${invItem.is_active ? '<div style="color: var(--success-color);">✅ فعال</div>' : ''}
                <div class="item-actions">
                    <button class="btn btn-small ${invItem.is_active ? 'btn-secondary' : 'btn-success'}" 
                        onclick="shopManager.toggleItem(${invItem.id}, ${!invItem.is_active})">
                        ${invItem.is_active ? 'غیرفعال' : 'فعال'}
                    </button>
                </div>
            `;
            
            container.appendChild(card);
        });
    }

    // Toggle item active status
    async toggleItem(inventoryId, active) {
        try {
            hapticFeedback('light');
            await api.toggleItem(inventoryId, active);
            
            showToast(active ? '✅ آیتم فعال شد' : '⏸ آیتم غیرفعال شد', 'success');
            
            // Refresh inventory
            await this.loadInventory();
            
        } catch (error) {
            console.error('Toggle item error:', error);
            showToast(error.message || 'خطا در تغییر وضعیت آیتم', 'error');
        }
    }
}

// Leaderboard manager
class LeaderboardManager {
    async loadLeaderboard() {
        try {
            const leaderboard = await api.getLeaderboard(100);
            this.renderLeaderboard(leaderboard);
        } catch (error) {
            console.error('Failed to load leaderboard:', error);
            showToast('خطا در بارگذاری جدول امتیازات', 'error');
        }
    }

    renderLeaderboard(leaderboard) {
        const container = document.getElementById('leaderboard-list');
        container.innerHTML = '';

        if (leaderboard.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">جدول امتیازات خالی است</p>';
            return;
        }

        leaderboard.forEach(entry => {
            const item = document.createElement('div');
            item.className = 'leaderboard-item';
            
            let rankEmoji = '🥇';
            if (entry.rank === 2) rankEmoji = '🥈';
            else if (entry.rank === 3) rankEmoji = '🥉';
            else if (entry.rank > 3) rankEmoji = `${entry.rank}.`;
            
            item.innerHTML = `
                <div class="leaderboard-rank">${rankEmoji}</div>
                <div class="leaderboard-user">
                    <div style="font-weight: bold;">${entry.first_name || 'بازیکن'}</div>
                    <div style="font-size: 12px; color: var(--text-secondary);">سطح ${entry.click_level}</div>
                </div>
                <div class="leaderboard-coins">💰 ${formatNumber(entry.coins)}</div>
            `;
            
            container.appendChild(item);
        });
    }
}

// Create global manager instances
const shopManager = new ShopManager();
const leaderboardManager = new LeaderboardManager();
