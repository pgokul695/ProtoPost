export const state = {
    config: null,
    logs: [],
    stats: {},
    activeTab: 'logs',
    autoRefresh: false,
    autoRefreshInterval: null,
    editingProvider: null,
    wizard: {
        active: false,
        provider: null,
        currentStep: 1,
        totalSteps: 0,
        collectedData: {}
    }
};
