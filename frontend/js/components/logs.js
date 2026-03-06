import { state } from '../state.js';
import { GatewayAPI } from '../api.js';
import { Toast } from './toast.js';
import { escapeHtml } from '../utils.js';

export function renderLogsTab() {
    const stats = state.stats;
    
    return `
        <!-- Stats Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div class="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <div class="text-sm text-slate-400">Total Sent</div>
                <div class="text-3xl font-bold text-green-400">${stats.total_sent || 0}</div>
            </div>
            <div class="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <div class="text-sm text-slate-400">Failed</div>
                <div class="text-3xl font-bold text-red-400">${stats.total_failed || 0}</div>
            </div>
            <div class="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <div class="text-sm text-slate-400">Sandbox</div>
                <div class="text-3xl font-bold text-amber-400">${stats.total_sandbox || 0}</div>
            </div>
            <div class="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <div class="text-sm text-slate-400">Avg Response</div>
                <div class="text-3xl font-bold text-indigo-400">${stats.avg_processing_time || 0}<span class="text-sm">ms</span></div>
            </div>
        </div>
        
        <!-- Controls -->
        <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
                <label class="flex items-center gap-2 text-sm">
                    <input type="checkbox" id="autoRefreshToggle" onchange="toggleAutoRefresh()" class="rounded accent-indigo-500">
                    <span>Auto-refresh (5s)</span>
                </label>
                <button onclick="refreshLogs()" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-sm font-medium transition-colors">
                    Refresh Now
                </button>
            </div>
        </div>
        
        <!-- Logs Table -->
        ${state.logs.length === 0 ? renderEmptyLogs() : renderLogsTable()}
    `;
}

export function renderEmptyLogs() {
    return `
        <div class="bg-slate-800 border border-slate-700 rounded-lg p-12 text-center">
            <div class="text-6xl mb-4">📭</div>
            <h3 class="text-xl font-semibold mb-2">No emails sent yet</h3>
            <p class="text-slate-400">Send a test email from the "Test Send" tab to get started</p>
        </div>
    `;
}

export function renderLogsTable() {
    return `
        <div class="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
            <table class="w-full">
                <thead class="bg-slate-700">
                    <tr>
                        <th class="px-4 py-3 text-left text-xs font-medium text-slate-300 uppercase">Timestamp</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-slate-300 uppercase">To</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-slate-300 uppercase">Subject</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-slate-300 uppercase">Provider</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-slate-300 uppercase">Status</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-slate-300 uppercase">Time (ms)</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-slate-300 uppercase">Actions</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-700">
                    ${state.logs.map(log => renderLogRow(log)).join('')}
                </tbody>
            </table>
        </div>
    `;
}

export function renderLogRow(log) {
    const statusColors = {
        success: 'bg-green-500/20 text-green-400 border-green-500/50',
        failed: 'bg-red-500/20 text-red-400 border-red-500/50',
        sandbox: 'bg-amber-500/20 text-amber-400 border-amber-500/50'
    };
    
    const toAddresses = JSON.parse(log.to_addresses);
    const timestamp = new Date(log.timestamp).toLocaleString();
    
    return `
        <tr class="hover:bg-slate-750">
            <td class="px-4 py-3 text-sm text-slate-300">${timestamp}</td>
            <td class="px-4 py-3 text-sm text-slate-300">${escapeHtml(toAddresses[0])}</td>
            <td class="px-4 py-3 text-sm text-slate-300">${escapeHtml(log.subject)}</td>
            <td class="px-4 py-3 text-sm text-slate-300">${escapeHtml(log.provider_name || 'N/A')}</td>
            <td class="px-4 py-3">
                <span class="px-2 py-1 text-xs font-medium rounded border ${statusColors[log.status]}">
                    ${escapeHtml(log.status.toUpperCase())}
                </span>
            </td>
            <td class="px-4 py-3 text-sm text-slate-300">${log.processing_time_ms.toFixed(2)}</td>
            <td class="px-4 py-3">
                <button onclick="viewLogDetail('${escapeHtml(log.id)}')" class="text-indigo-400 hover:text-indigo-300 text-sm font-medium">
                    View Details
                </button>
            </td>
        </tr>
    `;
}

export async function refreshLogs() {
    await window._loadLogs();
    await window._loadStats();
    if (state.activeTab === 'logs') {
        window.renderTabContent('logs');
    }
}

export function toggleAutoRefresh() {
    state.autoRefresh = document.getElementById('autoRefreshToggle').checked;
    
    if (state.autoRefresh) {
        state.autoRefreshInterval = setInterval(refreshLogs, 5000);
    } else {
        if (state.autoRefreshInterval) {
            clearInterval(state.autoRefreshInterval);
        }
    }
}

export async function viewLogDetail(logId) {
    try {
        const log = await GatewayAPI.get(`/api/logs/${logId}`);
        
        const toAddresses = JSON.parse(log.to_addresses);
        const requestPayload = JSON.parse(log.request_payload);
        const responsePayload = JSON.parse(log.response_payload);
        
        document.getElementById('modalContent').innerHTML = `
            <div class="p-6">
                <div class="flex items-center justify-between mb-6">
                    <h2 class="text-2xl font-bold">Email Log Details</h2>
                    <button onclick="closeModal()" class="text-slate-400 hover:text-white text-2xl">×</button>
                </div>
                
                <div class="space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <div class="text-xs text-slate-400 mb-1">Log ID</div>
                            <div class="text-sm font-mono">${escapeHtml(log.id)}</div>
                        </div>
                        <div>
                            <div class="text-xs text-slate-400 mb-1">Timestamp</div>
                            <div class="text-sm">${new Date(log.timestamp).toLocaleString()}</div>
                        </div>
                        <div>
                            <div class="text-xs text-slate-400 mb-1">Status</div>
                            <div class="text-sm font-semibold">${escapeHtml(log.status.toUpperCase())}</div>
                        </div>
                        <div>
                            <div class="text-xs text-slate-400 mb-1">Processing Time</div>
                            <div class="text-sm">${log.processing_time_ms.toFixed(2)} ms</div>
                        </div>
                    </div>
                    
                    <div>
                        <div class="text-xs text-slate-400 mb-1">To</div>
                        <div class="text-sm">${escapeHtml(toAddresses.join(', '))}</div>
                    </div>
                    
                    <div>
                        <div class="text-xs text-slate-400 mb-1">From</div>
                        <div class="text-sm">${escapeHtml(log.from_address)}</div>
                    </div>
                    
                    <div>
                        <div class="text-xs text-slate-400 mb-1">Subject</div>
                        <div class="text-sm">${escapeHtml(log.subject)}</div>
                    </div>
                    
                    <div>
                        <div class="text-xs text-slate-400 mb-1">Provider</div>
                        <div class="text-sm">${escapeHtml(log.provider_name || 'N/A')}</div>
                    </div>
                    
                    ${log.error_trace ? `
                        <div>
                            <div class="text-xs text-slate-400 mb-1">Error Trace</div>
                            <pre class="text-xs bg-slate-900 p-3 rounded overflow-x-auto">${escapeHtml(log.error_trace || '')}</pre>
                        </div>
                    ` : ''}
                    
                    <div>
                        <div class="text-xs text-slate-400 mb-1">Request Payload</div>
                        <pre class="text-xs bg-slate-900 p-3 rounded overflow-x-auto">${escapeHtml(JSON.stringify(requestPayload, null, 2))}</pre>
                    </div>
                    
                    <div>
                        <div class="text-xs text-slate-400 mb-1">Response Payload</div>
                        <pre class="text-xs bg-slate-900 p-3 rounded overflow-x-auto">${escapeHtml(JSON.stringify(responsePayload, null, 2))}
                    </div>
                </div>
            </div>
        `;
        
        document.getElementById('modalOverlay').classList.remove('hidden');
    } catch (error) {
        Toast.error('Failed to load log details');
    }
}

export function closeModal() {
    document.getElementById('modalOverlay').classList.add('hidden');
}
