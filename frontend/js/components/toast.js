export const Toast = {
    container: null,
    
    init() {
        this.container = document.getElementById('toastContainer');
    },
    
    show(message, type = 'info', duration = 4000) {
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };
        
        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-amber-500',
            info: 'bg-indigo-500'
        };
        
        const toast = document.createElement('div');
        toast.className = `toast-enter ${colors[type]} text-white px-6 py-4 rounded-lg shadow-lg flex items-start gap-3 min-w-[300px]`;
        
        toast.innerHTML = `
            <div class="text-2xl font-bold">${icons[type]}</div>
            <div class="flex-1">
                <div class="text-sm font-medium">${message}</div>
                <div class="h-1 bg-white bg-opacity-30 rounded-full mt-2 overflow-hidden">
                    <div class="h-full bg-white toast-progress" style="animation-duration: ${duration}ms"></div>
                </div>
            </div>
            <button onclick="this.parentElement.remove()" class="text-white hover:text-gray-200 text-xl font-bold">×</button>
        `;
        
        this.container.appendChild(toast);
        
        if (duration > 0) {
            setTimeout(() => {
                toast.classList.add('toast-exit');
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }
    },
    
    success(msg) { this.show(msg, 'success'); },
    error(msg, duration = 8000) { this.show(msg, 'error', duration); },
    warning(msg) { this.show(msg, 'warning'); },
    info(msg) { this.show(msg, 'info'); }
};
