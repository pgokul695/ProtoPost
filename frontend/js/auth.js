export const AuthToken = {
    _key: 'protopost_auth_token',

    get() {
        return localStorage.getItem(this._key) || '';
    },

    set(token) {
        if (token) {
            localStorage.setItem(this._key, token);
        } else {
            localStorage.removeItem(this._key);
        }
        this.updateUI();
    },

    updateUI() {
        const token = this.get();
        const btn = document.getElementById('authBtn');
        const icon = document.getElementById('authIcon');
        const label = document.getElementById('authLabel');
        if (!btn) return;
        if (token) {
            icon.textContent = '🔒';
            label.textContent = 'Token set';
            label.className = 'text-green-400';
            btn.className = btn.className.replace('border-slate-600', 'border-green-600');
            btn.classList.add('border-green-600');
            btn.classList.remove('border-slate-600');
        } else {
            icon.textContent = '🔓';
            label.textContent = 'No auth';
            label.className = 'text-slate-400';
            btn.classList.add('border-slate-600');
            btn.classList.remove('border-green-600');
        }
    },

    _resolve: null,

    prompt({ is401 = false } = {}) {
        return new Promise((resolve) => {
            this._resolve = resolve;
            const modal   = document.getElementById('authModal');
            const banner  = document.getElementById('authModal401Banner');
            const title   = document.getElementById('authModalTitle');
            const input   = document.getElementById('authModalInput');
            banner.classList.toggle('hidden', !is401);
            title.textContent = is401 ? 'Authentication Required' : 'Auth Token';
            input.value = this.get();
            modal.classList.remove('hidden');
            // focus after transition
            setTimeout(() => input.focus(), 50);
            // allow Enter to save
            input.onkeydown = (e) => { if (e.key === 'Enter') this.saveModal(); };
        });
    },

    saveModal() {
        const input = document.getElementById('authModalInput');
        const token = (input.value || '').trim();
        this.set(token);
        this.closeModal();
        if (this._resolve) { this._resolve(token); this._resolve = null; }
    },

    closeModal() {
        document.getElementById('authModal').classList.add('hidden');
        if (this._resolve) { this._resolve(null); this._resolve = null; }
    },

    init() {
        this.updateUI();
    }
};
