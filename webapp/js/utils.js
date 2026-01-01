// Utility functions

// Show toast notification
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Format number with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Show coin popup animation
function showCoinPopup(element, amount) {
    const popup = document.createElement('div');
    popup.className = 'coin-popup';
    popup.textContent = `+${amount}`;
    
    const rect = element.getBoundingClientRect();
    popup.style.left = `${rect.left + rect.width / 2}px`;
    popup.style.top = `${rect.top}px`;
    
    document.body.appendChild(popup);
    
    setTimeout(() => popup.remove(), 1000);
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle function for click limiting
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Haptic feedback using Telegram WebApp API
function hapticFeedback(type = 'light') {
    if (window.Telegram?.WebApp?.HapticFeedback) {
        if (type === 'light') {
            window.Telegram.WebApp.HapticFeedback.impactOccurred('light');
        } else if (type === 'medium') {
            window.Telegram.WebApp.HapticFeedback.impactOccurred('medium');
        } else if (type === 'heavy') {
            window.Telegram.WebApp.HapticFeedback.impactOccurred('heavy');
        }
    }
}

// Calculate XP needed for level
function calculateXPForLevel(level) {
    const base = 100;
    const multiplier = 1.2;
    return Math.floor(base * Math.pow(level, multiplier));
}
