import { state } from '../state.js';
import { GatewayAPI } from '../api.js';
import { Toast } from './toast.js';

export function renderProvidersTab() {
    const providers = state.config?.providers || [];
    
    return `
        <div class="mb-6">
            <button onclick="openProviderForm(null)" class="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium transition-colors">
                + Add Provider
            </button>
        </div>
        
        ${providers.length === 0 ? `
            <div class="bg-slate-800 border border-slate-700 rounded-lg p-12 text-center">
                <div class="text-6xl mb-4">📮</div>
                <h3 class="text-xl font-semibold mb-2">No providers configured</h3>
                <p class="text-slate-400 mb-4">Add your first email provider to get started</p>
                <button onclick="openProviderForm(null)" class="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium transition-colors">
                    Add Provider
                </button>
            </div>
        ` : `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                ${providers.map(provider => renderProviderCard(provider)).join('')}
            </div>
        `}
    `;
}

export function renderProviderCard(provider) {
    const typeLabels = {
        resend: 'Resend API',
        mailtrap: 'Mailtrap API',
        gmail: 'Gmail',
        custom_smtp: 'Custom SMTP'
    };
    
    const typeColors = {
        resend: 'bg-purple-500/20 text-purple-400',
        mailtrap: 'bg-green-500/20 text-green-400',
        gmail: 'bg-red-500/20 text-red-400',
        custom_smtp: 'bg-blue-500/20 text-blue-400'
    };
    
    return `
        <div class="bg-slate-800 border border-slate-700 rounded-lg p-6">
            <div class="flex items-start justify-between mb-4">
                <div class="flex-1">
                    <h3 class="text-lg font-semibold mb-2">${provider.name}</h3>
                    <span class="px-2 py-1 text-xs font-medium rounded ${typeColors[provider.type]}">
                        ${typeLabels[provider.type]}
                    </span>
                </div>
                <label class="flex items-center gap-2">
                    <input type="checkbox" ${provider.enabled ? 'checked' : ''} 
                           onchange="toggleProvider('${provider.id}')"
                           class="w-5 h-5 rounded accent-indigo-500">
                </label>
            </div>
            
            <div class="mb-4">
                <div class="text-xs text-slate-400 mb-1">Weight</div>
                <div class="flex items-center gap-2">
                    <div class="flex-1 bg-slate-700 rounded-full h-2">
                        <div class="bg-indigo-500 h-2 rounded-full" style="width: ${provider.weight}%"></div>
                    </div>
                    <span class="text-sm font-semibold">${provider.weight}%</span>
                </div>
            </div>
            
            <div class="flex gap-2">
                <button onclick="openProviderForm('${provider.id}')" 
                        class="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-sm font-medium transition-colors">
                    Edit
                </button>
                <button onclick="deleteProvider('${provider.id}', '${provider.name}')" 
                        class="px-4 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded text-sm font-medium transition-colors">
                    Delete
                </button>
            </div>
        </div>
    `;
}

export async function toggleProvider(providerId) {
    try {
        const provider = state.config.providers.find(p => p.id === providerId);
        provider.enabled = !provider.enabled;
        
        await GatewayAPI.put(`/api/config/providers/${providerId}`, provider);
        await window.loadConfig();
        
        Toast.success(`Provider ${provider.enabled ? 'enabled' : 'disabled'}`);
        window.renderTabContent('providers');
    } catch (error) {
        Toast.error('Failed to toggle provider');
        await window.loadConfig();
        window.renderTabContent('providers');
    }
}

export async function deleteProvider(providerId, providerName) {
    if (!confirm(`Delete provider "${providerName}"?`)) return;
    
    try {
        await GatewayAPI.delete(`/api/config/providers/${providerId}`);
        await window.loadConfig();
        
        Toast.warning(`Provider "${providerName}" deleted`);
        window.renderTabContent('providers');
    } catch (error) {
        Toast.error('Failed to delete provider');
    }
}

export function openProviderForm(providerId) {
    const provider = providerId ? state.config.providers.find(p => p.id === providerId) : null;
    state.editingProvider = provider;
    
    document.getElementById('sidePanelContent').innerHTML = renderProviderForm(provider);
    document.getElementById('sidePanel').classList.remove('hidden');
    
    // Setup type change listener
    document.getElementById('providerType').addEventListener('change', (e) => {
        const selectedType = e.target.value;
        
        // Show walkthrough launcher for guided providers (only when adding new)
        if (!provider) {
            if (selectedType === 'gmail' || selectedType === 'resend' || selectedType === 'mailtrap') {
                window.showWalkthroughLauncher(selectedType);
            } else {
                window.hideWalkthroughLauncher();
                updateProviderFormFields(selectedType);
            }
        } else {
            // Edit mode - no wizard
            updateProviderFormFields(selectedType);
        }
    });
    
    // Trigger initial field update
    if (provider) {
        // Edit mode - skip wizard entirely
        state.wizard.active = false;
        updateProviderFormFields(provider.type);
    } else {
        // New provider - check if wizard should show
        const initialType = document.getElementById('providerType').value;
        if (initialType === 'gmail' || initialType === 'resend' || initialType === 'mailtrap') {
            window.showWalkthroughLauncher(initialType);
        } else {
            updateProviderFormFields(initialType);
        }
    }
}

export function renderProviderForm(provider) {
    const isEdit = !!provider;
    
    return `
        <div class="p-6">
            <div class="flex items-center justify-between mb-6">
                <h2 class="text-2xl font-bold">${isEdit ? 'Edit' : 'Add'} Provider</h2>
                <button onclick="closeSidePanel()" class="text-slate-400 hover:text-white text-2xl">×</button>
            </div>
            
            <form onsubmit="saveProvider(event)" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium mb-2">Provider Name</label>
                    <input type="text" id="providerName" value="${provider?.name || ''}" 
                           required class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:border-indigo-500">
                </div>
                
                <div>
                    <label class="block text-sm font-medium mb-2">Provider Type</label>
                    <select id="providerType" required 
                            class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:border-indigo-500">
                        <option value="gmail" ${provider?.type === 'gmail' ? 'selected' : ''}>Gmail App Password</option>
                        <option value="resend" ${provider?.type === 'resend' ? 'selected' : ''}>Resend API</option>
                        <option value="mailtrap" ${provider?.type === 'mailtrap' ? 'selected' : ''}>Mailtrap API</option>
                        <option value="custom_smtp" ${provider?.type === 'custom_smtp' ? 'selected' : ''}>Custom SMTP Server</option>
                    </select>
                </div>
                
                <div>
                    <label class="block text-sm font-medium mb-2">Weight (%)</label>
                    <input type="range" id="providerWeight" min="0" max="100" value="${provider?.weight || 100}" 
                           oninput="document.getElementById('weightValue').textContent = this.value"
                           class="w-full accent-indigo-500">
                    <div class="text-right text-sm text-slate-400">
                        <span id="weightValue">${provider?.weight || 100}</span>%
                    </div>
                </div>
                
                <div>
                    <label class="flex items-center gap-2">
                        <input type="checkbox" id="providerEnabled" ${provider?.enabled !== false ? 'checked' : ''} 
                               class="w-5 h-5 rounded accent-indigo-500">
                        <span class="text-sm font-medium">Enabled</span>
                    </label>
                </div>
                
                <div class="border-t border-slate-700 pt-4">
                    <div id="providerCredentials">
                        <!-- Dynamic fields will be inserted here -->
                    </div>
                </div>
                
                <div class="flex gap-3 pt-4">
                    <button type="submit" class="flex-1 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium transition-colors">
                        ${isEdit ? 'Save Changes' : 'Add Provider'}
                    </button>
                    <button type="button" onclick="closeSidePanel()" 
                            class="px-6 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg font-medium transition-colors">
                        Cancel
                    </button>
                </div>
            </form>
        </div>
    `;
}

export function updateProviderFormFields(type) {
    const container = document.getElementById('providerCredentials');
    const provider = state.editingProvider;
    
    if (type === 'resend' || type === 'mailtrap') {
        container.innerHTML = `
            <div>
                <label class="block text-sm font-medium mb-2">API Key</label>
                <div class="relative">
                    <input type="password" id="apiKey" value="${provider?.api_key || ''}" 
                           required class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:border-indigo-500 pr-10">
                    <button type="button" onclick="togglePasswordVisibility('apiKey')" 
                            class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white">
                        👁
                    </button>
                </div>
            </div>
        `;
    } else if (type === 'gmail') {
        container.innerHTML = `
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium mb-2">Gmail Address</label>
                    <input type="email" id="gmailAddress" value="${provider?.gmail_address || ''}" 
                           required class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:border-indigo-500">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">App Password</label>
                    <div class="relative">
                        <input type="password" id="gmailAppPassword" value="${provider?.gmail_app_password || ''}" 
                               required class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:border-indigo-500 pr-10">
                        <button type="button" onclick="togglePasswordVisibility('gmailAppPassword')" 
                                class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white">
                            👁
                        </button>
                    </div>
                </div>
            </div>
        `;
    } else if (type === 'custom_smtp') {
        container.innerHTML = `
            <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium mb-2">SMTP Host</label>
                        <input type="text" id="smtpHost" value="${provider?.smtp_host || ''}" 
                               required class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:border-indigo-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-2">SMTP Port</label>
                        <input type="number" id="smtpPort" value="${provider?.smtp_port || 587}" 
                               required min="1" max="65535" class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:border-indigo-500">
                    </div>
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">Username</label>
                    <input type="text" id="smtpUsername" value="${provider?.smtp_username || ''}" 
                           required class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:border-indigo-500">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">Password</label>
                    <div class="relative">
                        <input type="password" id="smtpPassword" value="${provider?.smtp_password || ''}" 
                               required class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:border-indigo-500 pr-10">
                        <button type="button" onclick="togglePasswordVisibility('smtpPassword')" 
                                class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white">
                            👁
                        </button>
                    </div>
                </div>
                <div class="flex gap-4">
                    <label class="flex items-center gap-2">
                        <input type="checkbox" id="smtpUseTls" ${provider?.smtp_use_tls !== false ? 'checked' : ''} 
                               class="w-5 h-5 rounded accent-indigo-500">
                        <span class="text-sm">Use TLS (STARTTLS)</span>
                    </label>
                    <label class="flex items-center gap-2">
                        <input type="checkbox" id="smtpUseSsl" ${provider?.smtp_use_ssl ? 'checked' : ''} 
                               class="w-5 h-5 rounded accent-indigo-500">
                        <span class="text-sm">Use SSL</span>
                    </label>
                </div>
            </div>
        `;
    }
}

export function togglePasswordVisibility(fieldId) {
    const field = document.getElementById(fieldId);
    field.type = field.type === 'password' ? 'text' : 'password';
}

export async function saveProvider(event) {
    event.preventDefault();
    
    const type = document.getElementById('providerType').value;
    const providerData = {
        name: document.getElementById('providerName').value,
        type: type,
        weight: parseInt(document.getElementById('providerWeight').value),
        enabled: document.getElementById('providerEnabled').checked
    };
    
    // Add type-specific fields
    if (type === 'resend' || type === 'mailtrap') {
        providerData.api_key = document.getElementById('apiKey').value;
    } else if (type === 'gmail') {
        providerData.gmail_address = document.getElementById('gmailAddress').value;
        providerData.gmail_app_password = document.getElementById('gmailAppPassword').value;
    } else if (type === 'custom_smtp') {
        providerData.smtp_host = document.getElementById('smtpHost').value;
        providerData.smtp_port = parseInt(document.getElementById('smtpPort').value);
        providerData.smtp_username = document.getElementById('smtpUsername').value;
        providerData.smtp_password = document.getElementById('smtpPassword').value;
        providerData.smtp_use_tls = document.getElementById('smtpUseTls').checked;
        providerData.smtp_use_ssl = document.getElementById('smtpUseSsl').checked;
    }
    
    try {
        if (state.editingProvider) {
            // Update existing provider
            await GatewayAPI.put(`/api/config/providers/${state.editingProvider.id}`, providerData);
            Toast.success('Provider updated successfully');
        } else {
            // Add new provider
            await GatewayAPI.post('/api/config/providers', providerData);
            Toast.success('Provider added successfully');
        }
        
        await window.loadConfig();
        closeSidePanel();
        window.renderTabContent('providers');
    } catch (error) {
        Toast.error(`Failed to save provider: ${error.message}`);
    }
}

export function closeSidePanel() {
    document.getElementById('sidePanel').classList.add('hidden');
    state.editingProvider = null;
}
