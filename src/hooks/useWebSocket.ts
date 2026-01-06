import { useEffect, useRef, useCallback } from 'react';

interface WebSocketMessage {
  type: 'position_event' | 'trade_event' | 'connection' | 'pong';
  event?: string;
  data?: any;
  status?: string;
}

interface UseWebSocketOptions {
  enabled?: boolean;
  onPositionUpdate?: (position: any) => void;
  onPositionClosed?: (position: any) => void;
  onTradeExecuted?: (trade: any) => void;
  onConnectionChange?: (status: 'connected' | 'disconnected' | 'connecting') => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
}

export function useWebSocket(url: string, options: UseWebSocketOptions = {}) {
  const {
    onPositionUpdate,
    onPositionClosed,
    onTradeExecuted,
    onConnectionChange,
    autoReconnect = true,
    reconnectInterval = 5000,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const isConnectingRef = useRef(false);

  const connect = useCallback(() => {
    if (isConnectingRef.current || (wsRef.current?.readyState === WebSocket.OPEN)) {
      return;
    }

    isConnectingRef.current = true;
    onConnectionChange?.('connecting');

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        isConnectingRef.current = false;
        onConnectionChange?.('connected');
        
        // Clear any reconnection attempts
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = undefined;
        }
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          
          // Handle position events (backend format)
          if (message.type === 'position_event' && message.event && message.data) {
            switch (message.event) {
              case 'position_opened':
              case 'position_modified':
                onPositionUpdate?.(message.data);
                break;
              case 'position_closed':
                onPositionClosed?.(message.data);
                break;
            }
          }
          
          // Handle trade events
          if (message.type === 'trade_event' && message.event && message.data) {
            if (message.event === 'trade_executed') {
              onTradeExecuted?.(message.data);
            }
          }
          
          // Handle connection confirmation
          if (message.type === 'connection' && message.status === 'connected') {
            console.log('WebSocket connection confirmed by server');
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        isConnectingRef.current = false;
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        isConnectingRef.current = false;
        wsRef.current = null;
        onConnectionChange?.('disconnected');

        // Auto-reconnect
        if (autoReconnect) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connect();
          }, reconnectInterval);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      isConnectingRef.current = false;
      onConnectionChange?.('disconnected');
    }
  }, [url, onPositionUpdate, onPositionClosed, onTradeExecuted, onConnectionChange, autoReconnect, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = undefined;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const send = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    send,
    disconnect,
    reconnect: connect,
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
  };
}
