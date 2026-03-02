import { GatewayAPI } from './api.js';
import { AuthToken } from './auth.js';
import { Toast } from './components/toast.js';
import { state } from './state.js';
import { renderLogsTab, refreshLogs, toggleAutoRefresh, viewLogDetail, closeModal } from './components/logs.js';
import { renderProvidersTab, renderProviderCard, toggleProvider, deleteProvider, openProviderForm, closeSidePanel, saveProvider, updateProviderFormFields, togglePasswordVisibility } from './components/providers.js';
import { renderRoutingTab, setRoutingMode } from './components/routing.js';
import { renderTestTab, sendTestEmail } from './components/test-send.js';
import { showWalkthroughLauncher, hideWalkthroughLauncher, startWalkthrough, skipWalkthrough, navigateWizard, saveWizardProvider } from './components/wizard.js';

// ============================================
// INITIALIZATION
// ============================================

async function init() {
    Toast.init();
    AuthToken.init();
    
    // Check server connectivity
    await checkServerHealth();
    
    // Load initial data
    await loadConfig();
    await loadLogs();
    await loadStats();
    
    // Setup sandbox toggle
    setupSandboxToggle();
    
    // Render initial tab
    switchTab('logs');
}

async function checkServerHealth() {
    try {
        const health = await GatewayAPI.get('/api/health');
        document.getElementById('connectionDot').className = 'w-3 h-3 rounded-full bg-green-500';
        document.getElementById('serverStatus').textContent = window.location.host;
    } catch (error) {
        document.getElementById('connectionDot').className = 'w-3 h-3 rounded-full bg-red-500';
        document.getElementById('serverStatus').textContent = 'offline';
        Toast.error('Cannot connect to gateway server', 0);
    }
}

async function loadConfig() {
    try {
        state.config = await GatewayAPI.get('/api/config');
        
        // Update sandbox toggle
        document.getElementById('sandboxToggle').checked = state.config.routing.sandbox;
    } catch (error) {
        console.error('Failed to load config:', error);
    }
}

async function loadLogs() {
    try {
        const response = await GatewayAPI.get('/api/logs?limit=100');
        state.logs = response.logs;
    } catch (error) {
        console.error('Failed to load logs:', error);
    }
}

async function loadStats() {
    try {
        state.stats = await GatewayAPI.get('/api/stats');
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

function setupSandboxToggle() {
    document.getElementById('sandboxToggle').addEventListener('change', async (e) => {
        const enabled = e.target.checked;
        
        try {
            await GatewayAPI.post('/api/config/routing', {
                mode: state.config.routing.mode,
                sandbox: enabled
            });
            
            state.config.routing.sandbox = enabled;
            
            if (enabled) {
                Toast.info('Sandbox Mode enabled - All emails will be intercepted locally');
            } else {
                Toast.info('Sandbox Mode disabled - Live routing resumed');
            }
        } catch (error) {
            Toast.error('Failed to toggle sandbox mode');
            e.target.checked = !enabled; // Revert
        }
    });
}

// ============================================
// TAB MANAGEMENT
// ============================================

function switchTab(tabName) {
    state.activeTab = tabName;
    
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('text-indigo-400', 'border-indigo-500');
        btn.classList.add('text-slate-400');
    });
    
    const activeBtn = document.getElementById(`tab-${tabName}`);
    activeBtn.classList.remove('text-slate-400');
    activeBtn.classList.add('text-indigo-400', 'border-indigo-500');
    
    // Render tab content
    renderTabContent(tabName);
}

function renderTabContent(tabName) {
    const content = document.getElementById('tabContent');
    
    if (tabName === 'logs') {
        content.innerHTML = renderLogsTab();
    } else if (tabName === 'providers') {
        content.innerHTML = renderProvidersTab();
    } else if (tabName === 'routing') {
        content.innerHTML = renderRoutingTab();
    } else if (tabName === 'test') {
        content.innerHTML = renderTestTab();
    }
}

// ============================================
// EXPOSE GLOBALS (for onclick handlers in HTML and dynamically rendered markup)
// ============================================

window.AuthToken = AuthToken;
window.switchTab = switchTab;
window.renderTabContent = renderTabContent;
window.loadConfig = loadConfig;

// Internal helpers needed by component modules
window._loadLogs = loadLogs;
window._loadStats = loadStats;

// Logs
window.refreshLogs = refreshLogs;
window.toggleAutoRefresh = toggleAutoRefresh;
window.viewLogDetail = viewLogDetail;
window.closeModal = closeModal;

// Providers
window.openProviderForm = openProviderForm;
window.closeSidePanel = closeSidePanel;
window.toggleProvider = toggleProvider;
window.deleteProvider = deleteProvider;
window.saveProvider = saveProvider;
window.updateProviderFormFields = updateProviderFormFields;
window.togglePasswordVisibility = togglePasswordVisibility;

// Wizard
window.showWalkthroughLauncher = showWalkthroughLauncher;
window.hideWalkthroughLauncher = hideWalkthroughLauncher;
window.startWalkthrough = startWalkthrough;
window.skipWalkthrough = skipWalkthrough;
window.navigateWizard = navigateWizard;
window.saveWizardProvider = saveWizardProvider;

// Routing
window.setRoutingMode = setRoutingMode;

// Test Send
window.sendTestEmail = sendTestEmail;

// ============================================
// ENTRY POINT
// ============================================

document.addEventListener('DOMContentLoaded', init);
