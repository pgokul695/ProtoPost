import { AuthToken } from './auth.js';

export const GatewayAPI = {
    base: window.location.origin,  // Dynamically use current origin
    
    async request(method, path, body = null) {
        try {
            const options = {
                method,
                headers: {
                    'Content-Type': 'application/json'
                }
            };

            // Attach bearer token if one is stored
            const token = AuthToken.get();
            if (token) {
                options.headers['Authorization'] = `Bearer ${token}`;
            }
            
            if (body) {
                options.body = JSON.stringify(body);
            }
            
            const response = await fetch(`${this.base}${path}`, options);
            
            if (response.status === 401) {
                await AuthToken.prompt({ is401: true });
                throw new Error('Unauthorized — enter your AUTH_TOKEN and retry.');
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(JSON.stringify(errorData.detail || errorData));
            }
            
            return await response.json();
        } catch (error) {
            if (error.message.includes('Failed to fetch')) {
                throw new Error('Cannot connect to gateway server. Is it running?');
            }
            throw error;
        }
    },
    
    async get(path) { return this.request('GET', path); },
    async post(path, body) { return this.request('POST', path, body); },
    async put(path, body) { return this.request('PUT', path, body); },
    async delete(path) { return this.request('DELETE', path); }
};
