import { state } from '../state.js';
import { GatewayAPI } from '../api.js';
import { Toast } from './toast.js';

export function renderRoutingTab() {
    const routing = state.config?.routing || { mode: 'smart', sandbox: false };
    const providers = (state.config?.providers || []).filter(p => p.enabled);
    
    return `
        <div class="space-y-6">
            <!-- Mode Selection -->
            <div>
                <h3 class="text-xl font-semibold mb-4">Routing Mode</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <button onclick="setRoutingMode('manual')" 
                            class="p-6 rounded-lg border-2 transition-all ${routing.mode === 'manual' ? 'bg-indigo-600/20 border-indigo-500' : 'bg-slate-800 border-slate-700 hover:border-slate-600'}">
                        <h4 class="text-lg font-semibold mb-2">Manual Load Balancing</h4>
                        <p class="text-sm text-slate-400">You control the traffic split with weighted distribution</p>
                    </button>
                    <button onclick="setRoutingMode('smart')" 
                            class="p-6 rounded-lg border-2 transition-all ${routing.mode === 'smart' ? 'bg-indigo-600/20 border-indigo-500' : 'bg-slate-800 border-slate-700 hover:border-slate-600'}">
                        <h4 class="text-lg font-semibold mb-2">Smart Failover</h4>
                        <p class="text-sm text-slate-400">Automatic failover to next available provider</p>
                    </button>
                </div>
            </div>
            
            <!-- Provider Order/Weights -->
            ${routing.mode === 'smart' ? renderSmartModeConfig(providers) : renderManualModeConfig(providers)}
        </div>
    `;
}

export function renderSmartModeConfig(providers) {
    if (providers.length === 0) {
        return `
            <div class="bg-slate-800 border border-slate-700 rounded-lg p-6">
                <p class="text-slate-400">No active providers. Enable at least one provider to configure routing.</p>
            </div>
        `;
    }
    
    const sorted = [...providers].sort((a, b) => b.weight - a.weight);
    
    return `
        <div class="bg-slate-800 border border-slate-700 rounded-lg p-6">
            <h4 class="text-lg font-semibold mb-4">Failover Order (by weight)</h4>
            <p class="text-sm text-slate-400 mb-4">Providers are tried in order of weight (highest first)</p>
            <div class="space-y-2">
                ${sorted.map((p, i) => `
                    <div class="flex items-center gap-3 p-3 bg-slate-700 rounded">
                        <span class="text-lg font-bold text-indigo-400">${i + 1}</span>
                        <span class="flex-1">${p.name}</span>
                        <span class="text-sm text-slate-400">Weight: ${p.weight}%</span>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

export function renderManualModeConfig(providers) {
    if (providers.length === 0) {
        return `
            <div class="bg-slate-800 border border-slate-700 rounded-lg p-6">
                <p class="text-slate-400">No active providers. Enable at least one provider to configure routing.</p>
            </div>
        `;
    }
    
    const totalWeight = providers.reduce((sum, p) => sum + p.weight, 0);
    
    return `
        <div class="bg-slate-800 border border-slate-700 rounded-lg p-6">
            <h4 class="text-lg font-semibold mb-4">Weight Distribution</h4>
            ${totalWeight !== 100 ? `
                <div class="bg-amber-500/20 border border-amber-500/50 rounded-lg p-3 mb-4">
                    <span class="text-amber-400 text-sm">⚠ Weights sum to ${totalWeight}% (will be normalized automatically)</span>
                </div>
            ` : ''}
            
            <!-- Weight Visualizer -->
            <div class="mb-6">
                <div class="flex h-8 rounded-lg overflow-hidden">
                    ${providers.map(p => `
                        <div style="width: ${(p.weight / totalWeight) * 100}%" 
                             class="bg-indigo-500 hover:bg-indigo-400 transition-colors flex items-center justify-center text-xs font-semibold"
                             title="${p.name}: ${p.weight}%">
                            ${p.weight > 10 ? p.name : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <p class="text-sm text-slate-400 mb-4">Traffic is split randomly based on provider weights. A provider with weight 75 gets ~75% of emails.</p>
        </div>
    `;
}

export async function setRoutingMode(mode) {
    try {
        await GatewayAPI.post('/api/config/routing', {
            mode: mode,
            sandbox: state.config.routing.sandbox
        });
        
        await window.loadConfig();
        Toast.success(`Routing mode set to ${mode}`);
        window.renderTabContent('routing');
    } catch (error) {
        Toast.error('Failed to update routing mode');
    }
}
