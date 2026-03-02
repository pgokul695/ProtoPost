import { state } from '../state.js';
import { GatewayAPI } from '../api.js';
import { Toast } from './toast.js';

export function showWalkthroughLauncher(providerType) {
    const container = document.getElementById('providerCredentials');
    state.wizard.provider = providerType;
    state.wizard.totalSteps = providerType === 'gmail' ? 5 : 4; // resend=4, mailtrap=4
    
    container.innerHTML = `
        <div class="bg-indigo-900/30 border-2 border-indigo-500/50 rounded-lg p-6">
            <div class="flex items-start gap-4">
                <div class="text-3xl">🧭</div>
                <div class="flex-1">
                    <h4 class="text-lg font-semibold text-white mb-2">Not sure where to find your credentials?</h4>
                    <p class="text-sm text-slate-300 mb-4">We'll walk you through the entire setup process step-by-step.</p>
                    <div class="flex gap-3">
                        <button type="button" onclick="startWalkthrough()" 
                                class="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium transition-colors">
                            Start Setup Guide
                        </button>
                        <button type="button" onclick="skipWalkthrough()" 
                                class="px-6 py-2.5 bg-slate-700 hover:bg-slate-600 rounded-lg font-medium transition-colors">
                            Skip — I have my key
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

export function hideWalkthroughLauncher() {
    state.wizard.active = false;
    state.wizard.currentStep = 1;
    state.wizard.collectedData = {};
}

export function startWalkthrough() {
    state.wizard.active = true;
    state.wizard.currentStep = 1;
    state.wizard.collectedData = {};
    renderWizardContent();
}

export function skipWalkthrough() {
    hideWalkthroughLauncher();
    window.updateProviderFormFields(state.wizard.provider);
}

export function renderWizardContent() {
    const container = document.getElementById('providerCredentials');
    const { provider, currentStep, totalSteps } = state.wizard;
    const stepContent = getWizardStepContent(provider, currentStep);
    
    container.innerHTML = `
        <div class="wizard-step space-y-6">
            <!-- Step Indicator -->
            ${renderStepDots(currentStep, totalSteps)}
            
            <!-- Step Content -->
            <div class="space-y-4">
                <div class="flex items-start gap-3">
                    <div class="text-3xl">${stepContent.icon}</div>
                    <div class="flex-1">
                        <h3 class="text-xl font-bold text-white mb-2">${stepContent.title}</h3>
                        <div class="text-slate-300 space-y-3">
                            ${stepContent.body}
                        </div>
                    </div>
                </div>
                
                ${stepContent.callout ? renderCallout(stepContent.callout.type, stepContent.callout.content) : ''}
                
                ${stepContent.actionButton ? `
                    <a href="${stepContent.actionButton.href}" target="_blank" rel="noopener noreferrer" 
                       class="inline-flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium transition-colors arrow-nudge">
                        ${stepContent.actionButton.label}
                        <span class="arrow-icon">→</span>
                    </a>
                ` : ''}
                
                ${stepContent.subNote ? `
                    <p class="text-sm text-slate-400 italic">${stepContent.subNote}</p>
                ` : ''}
                
                ${stepContent.inlineInputs ? stepContent.inlineInputs : ''}
            </div>
            
            <!-- Navigation -->
            <div class="flex items-center justify-between pt-6 border-t border-slate-700">
                <div>
                    ${currentStep > 1 ? `
                        <button type="button" onclick="navigateWizard(-1)" 
                                class="px-6 py-2.5 bg-slate-700 hover:bg-slate-600 rounded-lg font-medium transition-colors">
                            ← Back
                        </button>
                    ` : ''}
                </div>
                
                <div class="flex items-center gap-3">
                    <button type="button" onclick="skipWalkthrough()" 
                            class="text-sm text-slate-400 hover:text-slate-300 transition-colors">
                        Skip walkthrough
                    </button>
                    
                    ${currentStep < totalSteps ? `
                        <button type="button" onclick="navigateWizard(1)" 
                                class="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium transition-colors">
                            Next Step →
                        </button>
                    ` : `
                        <button type="button" onclick="saveWizardProvider(event)" 
                                class="px-8 py-2.5 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium transition-colors btn-save-final">
                            Save Provider →
                        </button>
                    `}
                </div>
            </div>
        </div>
    `;
}

export function renderStepDots(currentStep, totalSteps) {
    let dots = '';
    for (let i = 1; i <= totalSteps; i++) {
        if (i < currentStep) {
            dots += '<div class="w-3 h-3 rounded-full bg-indigo-500"></div>';
        } else if (i === currentStep) {
            dots += '<div class="w-3 h-3 rounded-full bg-white"></div>';
        } else {
            dots += '<div class="w-3 h-3 rounded-full bg-slate-600"></div>';
        }
    }
    
    return `
        <div class="flex items-center gap-2">
            ${dots}
            <span class="ml-3 text-sm text-slate-400">Step ${currentStep} of ${totalSteps}</span>
        </div>
    `;
}

export function renderCallout(type, content) {
    const styles = {
        info: 'border-indigo-500 bg-indigo-950/50 text-indigo-300',
        warning: 'border-amber-500 bg-amber-950/50 text-amber-300',
        success: 'border-green-500 bg-green-950/50 text-green-300'
    };
    
    return `
        <div class="border-l-4 ${styles[type]} rounded-r-lg p-4 font-mono text-sm whitespace-pre-line">
${content}</div>
    `;
}

export function getWizardStepContent(provider, step) {
    if (provider === 'gmail') {
        return getGmailWizardStep(step);
    } else if (provider === 'resend') {
        return getResendWizardStep(step);
    } else if (provider === 'mailtrap') {
        return getMailtrapWizardStep(step);
    }
}

export function getGmailWizardStep(step) {
    const steps = {
        1: {
            icon: '📋',
            title: 'Before you begin',
            body: `
                <p>Gmail App Passwords require <strong>2-Step Verification</strong> to be active on your Google Account. This takes about 2 minutes if you haven't done it yet.</p>
                <p>You'll need access to your Google Account settings. Keep this panel open — you'll come back here to paste your App Password.</p>
            `,
            callout: {
                type: 'info',
                content: `✓  You have a Google Account (personal or Workspace)\n✓  You can receive a verification SMS or use an authenticator app`
            },
            actionButton: {
                label: 'Open Google Account',
                href: 'https://myaccount.google.com'
            }
        },
        2: {
            icon: '🔐',
            title: 'Enable 2-Step Verification',
            body: `
                <p>In your Google Account, go to <strong>Security</strong> in the left sidebar. Scroll to "How you sign in to Google" and click <strong>2-Step Verification</strong>.</p>
            `,
            callout: {
                type: 'info',
                content: `Click:  Security  →  2-Step Verification  →  Get Started`
            },
            actionButton: {
                label: 'Open Security Settings',
                href: 'https://myaccount.google.com/security'
            },
            subNote: 'Already have 2-Step Verification enabled? Skip to the next step.'
        },
        3: {
            icon: '🗝️',
            title: 'Open App Passwords',
            body: `
                <p>Once 2-Step Verification is on, search for <strong>"App Passwords"</strong> in the search bar at the top of your Google Account page, or navigate directly using the button below.</p>
            `,
            callout: {
                type: 'info',
                content: `Search bar → type: "App Passwords" → click the result`
            },
            actionButton: {
                label: 'Open App Passwords',
                href: 'https://myaccount.google.com/apppasswords'
            },
            subNote: 'If you see "App Passwords" is missing, it means 2-Step Verification isn\'t active yet. Go back to Step 2.'
        },
        4: {
            icon: '⚙️',
            title: 'Create a new App Password',
            body: `
                <p>In the App Passwords page, type a name for this password — use something like <strong>Email Gateway</strong> so you remember what it's for. Then click <strong>Create</strong>.</p>
            `,
            callout: {
                type: 'info',
                content: `App name:  Email Gateway\n           ↓\n           Click  [Create]`
            },
            subNote: 'Google will show you a 16-character password. You only see this <strong>once</strong> — copy it immediately.'
        },
        5: {
            icon: '✅',
            title: 'Copy your App Password',
            body: `
                <p>Google shows a 16-character password in a yellow box. Copy it now.</p>
            `,
            callout: {
                type: 'success',
                content: `It looks like this:   xxxx xxxx xxxx xxxx\n                      (spaces are included — paste as-is)`
            },
            inlineInputs: `
                <div class="space-y-4 mt-4">
                    <div>
                        <label class="block text-sm font-medium mb-2 text-white">Gmail Address</label>
                        <input type="email" id="wizardGmailAddress" required 
                               class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:border-indigo-500 text-white"
                               placeholder="your.email@gmail.com">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-2 text-white">App Password</label>
                        <div class="relative">
                            <input type="password" id="wizardGmailAppPassword" required 
                                   class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:border-indigo-500 pr-10 text-white"
                                   placeholder="xxxx xxxx xxxx xxxx">
                            <button type="button" onclick="togglePasswordVisibility('wizardGmailAppPassword')" 
                                    class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white">
                                👁
                            </button>
                        </div>
                    </div>
                </div>
            `
        }
    };
    return steps[step];
}

export function getResendWizardStep(step) {
    const steps = {
        1: {
            icon: '📋',
            title: 'Create your Resend account',
            body: `
                <p>Resend is a developer email API. If you don't have an account yet, sign up for free — no credit card required. The free tier supports up to <strong>3,000 emails/month</strong>.</p>
            `,
            callout: {
                type: 'info',
                content: `Free tier:   3,000 emails / month\n             100 emails / day\n             1 custom domain`
            },
            actionButton: {
                label: 'Sign up for free',
                href: 'https://resend.com/signup'
            },
            subNote: 'Already have an account? Skip to the next step.'
        },
        2: {
            icon: '🌐',
            title: 'Set up a sending domain',
            body: `
                <p>Resend requires a verified domain to send emails. Go to <strong>Domains</strong> in your Resend dashboard and add your domain. Follow the DNS instructions to verify it.</p>
            `,
            callout: {
                type: 'warning',
                content: `⚠  No domain yet?\n   Use  onboarding@resend.dev  as your "From" address to test\n   without a custom domain. Works immediately, no DNS needed.`
            },
            actionButton: {
                label: 'Open Resend Domains',
                href: 'https://resend.com/domains'
            }
        },
        3: {
            icon: '🗝️',
            title: 'Create an API Key',
            body: `
                <p>In your Resend dashboard, go to <strong>API Keys</strong> and click <strong>Create API Key</strong>. Give it a name like <strong>Email Gateway</strong> and set permission to <strong>Full Access</strong> (or Sending Access only, if you prefer).</p>
            `,
            callout: {
                type: 'info',
                content: `Dashboard → API Keys → Create API Key\nName:        Email Gateway\nPermission:  Full Access`
            },
            actionButton: {
                label: 'Open API Keys',
                href: 'https://resend.com/api-keys'
            },
            subNote: 'Your key starts with <code>re_</code>. Copy it — it\'s only shown once.'
        },
        4: {
            icon: '✅',
            title: 'Paste your API Key',
            body: `
                <p>Paste the API key you just copied below. It starts with <code>re_</code>.</p>
            `,
            callout: {
                type: 'success',
                content: `Looks like:   re_xxxxxxxxxxxxxxxxxxxxxxxxxxxx`
            },
            inlineInputs: `
                <div class="mt-4">
                    <label class="block text-sm font-medium mb-2 text-white">API Key</label>
                    <div class="relative">
                        <input type="password" id="wizardApiKey" required 
                               class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:border-indigo-500 pr-10 text-white"
                               placeholder="re_...">
                        <button type="button" onclick="togglePasswordVisibility('wizardApiKey')" 
                                class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white">
                            👁
                        </button>
                    </div>
                </div>
            `
        }
    };
    return steps[step];
}

export function getMailtrapWizardStep(step) {
    const steps = {
        1: {
            icon: '📋',
            title: 'Create your Mailtrap account',
            body: `
                <p>Mailtrap Email Sending is a transactional email API — not to be confused with their Email Testing inbox. Sign up for free; <strong>1,000 emails/month included</strong> with no credit card required.</p>
            `,
            callout: {
                type: 'info',
                content: `Free tier:   1,000 emails / month\n             Transactional + bulk sending\n             Free DKIM / SPF hosting`
            },
            actionButton: {
                label: 'Sign up for free',
                href: 'https://mailtrap.io/register/signup'
            },
            subNote: 'Already have an account? Skip to the next step.'
        },
        2: {
            icon: '🌐',
            title: 'Add a verified sending domain',
            body: `
                <p>In the Mailtrap dashboard, open <strong>Email Sending → Sending Domains</strong> and add your domain. Mailtrap gives you the DNS records to add (DKIM + SPF) — usually live within a few minutes.</p>
            `,
            callout: {
                type: 'warning',
                content: `⚠  No domain yet?\n   Use the sandbox address Mailtrap provides during onboarding.\n   Go to:  Sending Domains → click  "Add Domain"  to start.`
            },
            actionButton: {
                label: 'Open Sending Domains',
                href: 'https://mailtrap.io/sending/domains'
            }
        },
        3: {
            icon: '🗝️',
            title: 'Get your API Token',
            body: `
                <p>In the Mailtrap dashboard, go to <strong>Email Sending → API Tokens</strong> (or via <strong>Settings</strong>) and click <strong>Add Token</strong>. Give it a name like <strong>Email Gateway</strong>.</p>
            `,
            callout: {
                type: 'info',
                content: `Dashboard → Email Sending → API Tokens\n           → Add Token\nName:        Email Gateway`
            },
            actionButton: {
                label: 'Open API Tokens',
                href: 'https://mailtrap.io/sending/api-tokens'
            },
            subNote: 'Your token is shown once — copy it immediately after clicking Create.'
        },
        4: {
            icon: '✅',
            title: 'Paste your API Token',
            body: `
                <p>Paste the token you just copied below.</p>
            `,
            callout: {
                type: 'success',
                content: `Looks like:   a1b2c3d4e5f6... (long hex string)`
            },
            inlineInputs: `
                <div class="mt-4">
                    <label class="block text-sm font-medium mb-2 text-white">API Token</label>
                    <div class="relative">
                        <input type="password" id="wizardMailtrapApiKey" required 
                               class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:border-indigo-500 pr-10 text-white"
                               placeholder="Paste your Mailtrap API token...">
                        <button type="button" onclick="togglePasswordVisibility('wizardMailtrapApiKey')" 
                                class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white">
                            👁
                        </button>
                    </div>
                </div>
            `
        }
    };
    return steps[step];
}

export function navigateWizard(direction) {
    const newStep = state.wizard.currentStep + direction;
    if (newStep >= 1 && newStep <= state.wizard.totalSteps) {
        state.wizard.currentStep = newStep;
        renderWizardContent();
    }
}

export async function saveWizardProvider(event) {
    event?.preventDefault();
    
    const { provider } = state.wizard;
    const providerData = {
        name: document.getElementById('providerName').value,
        type: provider,
        weight: parseInt(document.getElementById('providerWeight').value),
        enabled: document.getElementById('providerEnabled').checked
    };
    
    // Collect credentials from wizard inline inputs
    if (provider === 'gmail') {
        const gmailAddress = document.getElementById('wizardGmailAddress')?.value;
        const gmailAppPassword = document.getElementById('wizardGmailAppPassword')?.value;
        
        if (!gmailAddress || !gmailAppPassword) {
            // Validation failed - highlight fields and shake
            const addrInput = document.getElementById('wizardGmailAddress');
            const passInput = document.getElementById('wizardGmailAppPassword');
            
            if (!gmailAddress && addrInput) {
                addrInput.classList.add('border-red-500', 'shake');
                setTimeout(() => addrInput.classList.remove('shake'), 300);
            }
            if (!gmailAppPassword && passInput) {
                passInput.classList.add('border-red-500', 'shake');
                setTimeout(() => passInput.classList.remove('shake'), 300);
            }
            
            Toast.error('Please fill in all required fields');
            return;
        }
        
        providerData.gmail_address = gmailAddress;
        providerData.gmail_app_password = gmailAppPassword;
    } else if (provider === 'resend') {
        const apiKey = document.getElementById('wizardApiKey')?.value;
        
        if (!apiKey) {
            const keyInput = document.getElementById('wizardApiKey');
            if (keyInput) {
                keyInput.classList.add('border-red-500', 'shake');
                setTimeout(() => keyInput.classList.remove('shake'), 300);
            }
            Toast.error('Please enter your API key');
            return;
        }
        
        providerData.api_key = apiKey;
    } else if (provider === 'mailtrap') {
        const apiKey = document.getElementById('wizardMailtrapApiKey')?.value;

        if (!apiKey) {
            const keyInput = document.getElementById('wizardMailtrapApiKey');
            if (keyInput) {
                keyInput.classList.add('border-red-500', 'shake');
                setTimeout(() => keyInput.classList.remove('shake'), 300);
            }
            Toast.error('Please enter your API token');
            return;
        }

        providerData.api_key = apiKey;
    }
    
    try {
        await GatewayAPI.post('/api/config/providers', providerData);
        
        const successMessages = {
            gmail: '✓ Gmail provider added successfully',
            resend: '✓ Resend provider added successfully',
            mailtrap: '✓ Mailtrap provider added successfully'
        };
        
        Toast.success(successMessages[provider]);
        
        await window.loadConfig();
        window.closeSidePanel();
        window.renderTabContent('providers');
    } catch (error) {
        Toast.error(`Failed to save provider: ${error.message}`);
    }
}
