import { state } from '../state.js';
import { GatewayAPI } from '../api.js';
import { Toast } from './toast.js';

export function renderTestTab() {
    return `
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Form -->
            <div class="bg-slate-800 border border-slate-700 rounded-lg p-6">
                <h3 class="text-xl font-semibold mb-4">Send Test Email</h3>
                
                <form onsubmit="sendTestEmail(event)" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium mb-2">From</label>
                        <input type="email" id="testFrom" required 
                               placeholder="sender@example.com"
                               class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:border-indigo-500">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium mb-2">To</label>
                        <input type="email" id="testTo" required 
                               placeholder="recipient@example.com"
                               class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:border-indigo-500">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium mb-2">Subject</label>
                        <input type="text" id="testSubject" required 
                               placeholder="Test email from gateway"
                               class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:border-indigo-500">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium mb-2">Body (Plain Text)</label>
                        <textarea id="testBodyText" rows="4" 
                                  placeholder="Plain text email body..."
                                  class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:border-indigo-500"></textarea>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium mb-2">Body (HTML)</label>
                        <textarea id="testBodyHtml" rows="4" 
                                  placeholder="<h1>HTML email body</h1>..."
                                  class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:border-indigo-500"></textarea>
                    </div>
                    
                    <button type="submit" class="w-full px-6 py-3 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium transition-colors">
                        Send via Gateway
                    </button>
                </form>
            </div>
            
            <!-- Response Panel -->
            <div class="bg-slate-800 border border-slate-700 rounded-lg p-6">
                <h3 class="text-xl font-semibold mb-4">Response</h3>
                <div id="testResponse" class="text-sm text-slate-400">
                    <p>Response will appear here after sending...</p>
                </div>
            </div>
        </div>
    `;
}

export async function sendTestEmail(event) {
    event.preventDefault();
    
    const from = document.getElementById('testFrom').value;
    const to = document.getElementById('testTo').value;
    const subject = document.getElementById('testSubject').value;
    const bodyText = document.getElementById('testBodyText').value;
    const bodyHtml = document.getElementById('testBodyHtml').value;
    
    if (!bodyText && !bodyHtml) {
        Toast.error('Please provide at least one body type (text or HTML)');
        return;
    }
    
    const payload = {
        from: from,
        to: [to],
        subject: subject
    };
    
    if (bodyText) payload.body_text = bodyText;
    if (bodyHtml) payload.body_html = bodyHtml;
    
    document.getElementById('testResponse').innerHTML = `
        <div class="flex items-center gap-2 text-indigo-400">
            <div class="animate-spin">⟳</div>
            <span>Sending email...</span>
        </div>
    `;
    
    try {
        const result = await GatewayAPI.post('/api/send', payload);
        
        document.getElementById('testResponse').innerHTML = `
            <div class="space-y-3">
                <div class="flex items-center gap-2 text-green-400 text-lg font-semibold">
                    <span>✓</span>
                    <span>Email sent successfully!</span>
                </div>
                
                ${result.provider ? `
                    <div class="p-3 bg-slate-700 rounded">
                        <div class="text-xs text-slate-400 mb-1">Provider Used</div>
                        <div class="font-semibold">${result.provider.name} (${result.provider.type})</div>
                    </div>
                ` : ''}
                
                <div class="p-3 bg-slate-700 rounded">
                    <div class="text-xs text-slate-400 mb-1">Processing Time</div>
                    <div class="font-semibold">${result.processing_time_ms?.toFixed(2)} ms</div>
                </div>
                
                <div class="p-3 bg-slate-700 rounded">
                    <div class="text-xs text-slate-400 mb-1">Status</div>
                    <div class="font-semibold">${result.status.toUpperCase()}</div>
                </div>
                
                <pre class="p-3 bg-slate-900 rounded overflow-x-auto text-xs">${JSON.stringify(result, null, 2)}</pre>
            </div>
        `;
        
        Toast.success(`Email sent via ${result.provider?.name || 'gateway'}`);
        
        // Refresh logs
        await window.refreshLogs();
    } catch (error) {
        let errorMsg = error.message;
        try {
            const errorObj = JSON.parse(error.message);
            errorMsg = JSON.stringify(errorObj, null, 2);
        } catch (e) {}
        
        document.getElementById('testResponse').innerHTML = `
            <div class="space-y-3">
                <div class="flex items-center gap-2 text-red-400 text-lg font-semibold">
                    <span>✕</span>
                    <span>Send failed</span>
                </div>
                <pre class="p-3 bg-red-900/20 border border-red-500/50 rounded overflow-x-auto text-xs text-red-400">${errorMsg}</pre>
            </div>
        `;
        
        Toast.error('Failed to send email');
    }
}
