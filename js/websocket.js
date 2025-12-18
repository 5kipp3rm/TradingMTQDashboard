/**
 * WebSocket Client for Real-time Updates
 */

class WebSocketClient {
    constructor(url = 'ws://localhost:8000/api/ws') {
        this.url = url;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000; // Start with 1 second
        this.maxReconnectDelay = 30000; // Max 30 seconds
        this.isIntentionalClose = false;
        this.messageHandlers = new Map();
        this.connectionListeners = [];
        this.clientId = `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Connect to WebSocket server
     */
    connect() {
        if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
            console.log('[WS] Already connected or connecting');
            return;
        }

        try {
            console.log(`[WS] Connecting to ${this.url}...`);
            this.ws = new WebSocket(`${this.url}?client_id=${this.clientId}`);

            this.ws.onopen = (event) => {
                console.log('[WS] Connected successfully');
                this.reconnectAttempts = 0;
                this.reconnectDelay = 1000;
                this.notifyConnectionListeners('connected');
            };

            this.ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);
                } catch (error) {
                    console.error('[WS] Error parsing message:', error);
                }
            };

            this.ws.onerror = (error) => {
                console.error('[WS] Error:', error);
                this.notifyConnectionListeners('error', error);
            };

            this.ws.onclose = (event) => {
                console.log(`[WS] Disconnected (code: ${event.code}, reason: ${event.reason})`);
                this.notifyConnectionListeners('disconnected', event);

                // Attempt reconnection if not intentional
                if (!this.isIntentionalClose) {
                    this.attemptReconnect();
                }
            };

        } catch (error) {
            console.error('[WS] Connection error:', error);
            this.attemptReconnect();
        }
    }

    /**
     * Disconnect from WebSocket server
     */
    disconnect() {
        this.isIntentionalClose = true;
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    /**
     * Attempt to reconnect with exponential backoff
     */
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('[WS] Max reconnection attempts reached');
            this.notifyConnectionListeners('max_reconnect_attempts');
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1), this.maxReconnectDelay);

        console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.notifyConnectionListeners('reconnecting', { attempt: this.reconnectAttempts, delay });

        setTimeout(() => {
            if (!this.isIntentionalClose) {
                this.connect();
            }
        }, delay);
    }

    /**
     * Handle incoming message
     */
    handleMessage(message) {
        const messageType = message.type;

        // Call registered handlers for this message type
        if (this.messageHandlers.has(messageType)) {
            const handlers = this.messageHandlers.get(messageType);
            handlers.forEach(handler => {
                try {
                    handler(message);
                } catch (error) {
                    console.error(`[WS] Error in message handler for type '${messageType}':`, error);
                }
            });
        }

        // Call 'all' handlers
        if (this.messageHandlers.has('*')) {
            const handlers = this.messageHandlers.get('*');
            handlers.forEach(handler => {
                try {
                    handler(message);
                } catch (error) {
                    console.error('[WS] Error in wildcard message handler:', error);
                }
            });
        }
    }

    /**
     * Register a message handler for specific message type
     */
    on(messageType, handler) {
        if (!this.messageHandlers.has(messageType)) {
            this.messageHandlers.set(messageType, []);
        }
        this.messageHandlers.get(messageType).push(handler);
    }

    /**
     * Remove a message handler
     */
    off(messageType, handler) {
        if (this.messageHandlers.has(messageType)) {
            const handlers = this.messageHandlers.get(messageType);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    /**
     * Register a connection state listener
     */
    onConnection(listener) {
        this.connectionListeners.push(listener);
    }

    /**
     * Notify connection listeners
     */
    notifyConnectionListeners(state, data = null) {
        this.connectionListeners.forEach(listener => {
            try {
                listener(state, data);
            } catch (error) {
                console.error('[WS] Error in connection listener:', error);
            }
        });
    }

    /**
     * Send a message to the server
     */
    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                this.ws.send(JSON.stringify(message));
                return true;
            } catch (error) {
                console.error('[WS] Error sending message:', error);
                return false;
            }
        } else {
            console.warn('[WS] Cannot send message, not connected');
            return false;
        }
    }

    /**
     * Send a ping to check connection
     */
    ping() {
        return this.send({
            type: 'ping',
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Subscribe to specific channels
     */
    subscribe(channels) {
        return this.send({
            type: 'subscribe',
            channels: Array.isArray(channels) ? channels : [channels]
        });
    }

    /**
     * Unsubscribe from channels
     */
    unsubscribe(channels) {
        return this.send({
            type: 'unsubscribe',
            channels: Array.isArray(channels) ? channels : [channels]
        });
    }

    /**
     * Request connection statistics
     */
    getStats() {
        return this.send({
            type: 'get_stats'
        });
    }

    /**
     * Get connection state
     */
    getState() {
        if (!this.ws) return 'disconnected';

        switch (this.ws.readyState) {
            case WebSocket.CONNECTING:
                return 'connecting';
            case WebSocket.OPEN:
                return 'connected';
            case WebSocket.CLOSING:
                return 'closing';
            case WebSocket.CLOSED:
                return 'disconnected';
            default:
                return 'unknown';
        }
    }

    /**
     * Check if connected
     */
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

// Export singleton instance
const wsClient = new WebSocketClient();
