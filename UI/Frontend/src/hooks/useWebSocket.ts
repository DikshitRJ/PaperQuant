import { useEffect, useRef, useCallback, useState } from 'react';
import { apiClient } from '../lib/api-client';
import type { WSEvent, WSEventType } from '../types/api';

type EventHandler = (data: any) => void;

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const handlersRef = useRef<Map<WSEventType, EventHandler[]>>(new Map());
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const connect = useCallback(() => {
    const url = apiClient.getWebSocketUrl();
    const ws = new WebSocket(url);
    
    ws.onopen = () => {
      setIsConnected(true);
      console.log('[WS] Connected');
    };
    
    ws.onmessage = (event) => {
      try {
        const msg: WSEvent = JSON.parse(event.data);
        const handlers = handlersRef.current.get(msg.type);
        if (handlers) {
          handlers.forEach(handler => handler(msg.data));
        }
      } catch (e) {
        console.error('[WS] Parse error:', e);
      }
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      // Reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    };
    
    ws.onerror = () => {
      ws.close();
    };
    
    wsRef.current = ws;
  }, []);

  const on = useCallback((type: WSEventType, handler: EventHandler) => {
    const existing = handlersRef.current.get(type) || [];
    handlersRef.current.set(type, [...existing, handler]);
    
    return () => {
      const current = handlersRef.current.get(type) || [];
      handlersRef.current.set(type, current.filter(h => h !== handler));
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { isConnected, on };
}
