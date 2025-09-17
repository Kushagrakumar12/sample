import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import { toast } from 'react-toastify';

const WebSocketContext = createContext();

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

export const WebSocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [connectionAttempts, setConnectionAttempts] = useState(0);
  const reconnectTimeout = useRef(null);
  const maxReconnectAttempts = 5;

  const connect = () => {
    try {
      const wsUrl = getWebSocketUrl();
      const clientId = `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const ws = new WebSocket(`${wsUrl}/${clientId}`);

      ws.onopen = () => {
        console.log('🔗 WebSocket connected');
        setIsConnected(true);
        setConnectionAttempts(0);
        setSocket(ws);
        
        // Show connection success toast
        toast.success('Connected to real-time updates', {
          position: 'bottom-right',
          autoClose: 3000,
        });
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
          handleMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('❌ WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        setSocket(null);

        // Show disconnection toast
        toast.warning('Real-time connection lost', {
          position: 'bottom-right',
          autoClose: 5000,
        });

        // Attempt to reconnect
        if (connectionAttempts < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, connectionAttempts), 30000);
          console.log(`Attempting to reconnect in ${delay}ms...`);
          
          reconnectTimeout.current = setTimeout(() => {
            setConnectionAttempts(prev => prev + 1);
            connect();
          }, delay);
        } else {
          toast.error('Failed to maintain real-time connection', {
            position: 'bottom-right',
            autoClose: 0, // Don't auto-close
          });
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        
        toast.error('Real-time connection error', {
          position: 'bottom-right',
          autoClose: 5000,
        });
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  };

  const disconnect = () => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }

    if (socket) {
      socket.close();
    }

    setSocket(null);
    setIsConnected(false);
    setConnectionAttempts(0);
  };

  const sendMessage = (message) => {
    if (socket && isConnected) {
      socket.send(JSON.stringify(message));
    } else {
      console.warn('Cannot send message: WebSocket not connected');
    }
  };

  const handleMessage = (data) => {
    switch (data.type) {
      case 'connection':
        console.log('Connection confirmed:', data.message);
        break;

      case 'train_update':
        console.log('Train update received:', data.data);
        // Could dispatch to a global state or trigger specific handlers
        break;

      case 'schedule_update':
        console.log('Schedule update received:', data.data);
        toast.info(`Schedule updated for train ${data.data.train_id}`, {
          position: 'top-right',
          autoClose: 4000,
        });
        break;

      case 'conflict_alert':
        console.log('Conflict alert received:', data.data);
        const severity = data.data.severity || 'medium';
        const toastType = severity === 'critical' ? 'error' : 
                         severity === 'high' ? 'warning' : 'info';
        
        toast[toastType](`Conflict Alert: ${data.data.message || 'Train conflict detected'}`, {
          position: 'top-center',
          autoClose: severity === 'critical' ? 0 : 8000,
        });
        break;

      case 'optimization_result':
        console.log('Optimization result received:', data.data);
        toast.success('Schedule optimization completed', {
          position: 'top-right',
          autoClose: 5000,
        });
        break;

      case 'system_status':
        console.log('System status update:', data.data);
        // Could update global system health state
        break;

      case 'ping':
        // Respond to ping with pong
        sendMessage({ type: 'pong', timestamp: new Date().toISOString() });
        break;

      default:
        console.log('Unknown message type:', data.type, data);
    }
  };

  const getWebSocketUrl = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = process.env.REACT_APP_WS_HOST || window.location.host.replace('3000', '8000');
    return `${protocol}//${host}/ws`;
  };

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
    };
  }, []);

  const value = {
    socket,
    isConnected,
    lastMessage,
    connectionAttempts,
    maxReconnectAttempts,
    connect,
    disconnect,
    sendMessage,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

export default WebSocketProvider;