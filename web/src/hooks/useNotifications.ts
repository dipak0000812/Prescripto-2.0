import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/ui/Toast';

export type NotificationType =
  | 'connected'
  | 'review_queue_update'
  | 'safety_alert'
  | 'new_message'
  | 'system_announcement'
  | 'error';

export interface Notification {
  type: NotificationType;
  timestamp: string;
  [key: string]: any;
}

interface UseNotificationsOptions {
  onReviewQueueUpdate?: (data: any) => void;
  onSafetyAlert?: (data: any) => void;
  onNewMessage?: (data: any) => void;
  onSystemAnnouncement?: (data: any) => void;
  onError?: (data: any) => void;
  enabled?: boolean;
}

export function useNotifications(options: UseNotificationsOptions = {}) {
  const { session, isAuthenticated } = useAuth();
  const { showToast } = useToast();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastNotification, setLastNotification] = useState<Notification | null>(null);

  const {
    onReviewQueueUpdate,
    onSafetyAlert,
    onNewMessage,
    onSystemAnnouncement,
    onError,
    enabled = true,
  } = options;

  const connect = useCallback(() => {
    if (!isAuthenticated || !session?.access_token) return;

    // Determine WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = import.meta.env.VITE_API_BASE_URL
      ? import.meta.env.VITE_API_BASE_URL.replace(/^https?:/, '').replace(/\/api\/v1$/, '')
      : window.location.host;
    const wsUrl = `${protocol}//${host}/api/v1/notifications/ws?token=${session.access_token}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        console.log('[Notifications] WebSocket connected');
      };

      ws.onmessage = (event) => {
        try {
          const notification = JSON.parse(event.data) as Notification;
          setLastNotification(notification);

          // Handle different notification types
          switch (notification.type) {
            case 'connected':
              console.log('[Notifications] Server confirmed connection');
              break;

            case 'review_queue_update':
              if (onReviewQueueUpdate) {
                onReviewQueueUpdate(notification);
              }
              showToast({
                type: 'info',
                title: 'Review Queue Updated',
                message: `Analysis ${notification.analysis_id?.slice(0, 8)} status: ${notification.status}`,
              });
              break;

            case 'safety_alert':
              if (onSafetyAlert) {
                onSafetyAlert(notification);
              }
              showToast({
                type: 'warning',
                title: 'Safety Alert',
                message: `New ${notification.finding_type} for patient ${notification.patient_id?.slice(0, 8)} (${notification.severity})`,
              });
              break;

            case 'new_message':
              if (onNewMessage) {
                onNewMessage(notification);
              }
              showToast({
                type: 'info',
                title: 'New Message',
                message: notification.preview || 'You have a new message from your doctor',
              });
              break;

            case 'system_announcement':
              if (onSystemAnnouncement) {
                onSystemAnnouncement(notification);
              }
              showToast({
                type: 'info',
                title: notification.title || 'System Announcement',
                message: notification.message,
              });
              break;

            case 'error':
              if (onError) {
                onError(notification);
              }
              showToast({
                type: 'error',
                title: 'Notification Error',
                message: notification.message,
              });
              break;

            default:
              console.log('[Notifications] Unknown type:', notification.type);
          }
        } catch (err) {
          console.error('[Notifications] Failed to parse message:', err);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        console.log('[Notifications] WebSocket disconnected');

        // Attempt reconnect after 5 seconds
        if (enabled && isAuthenticated) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, 5000);
        }
      };

      ws.onerror = (error) => {
        console.error('[Notifications] WebSocket error:', error);
      };
    } catch (err) {
      console.error('[Notifications] Failed to create WebSocket:', err);
    }
  }, [isAuthenticated, session?.access_token, enabled, onReviewQueueUpdate, onSafetyAlert, onNewMessage, onSystemAnnouncement, onError, showToast]);

  useEffect(() => {
    if (enabled && isAuthenticated) {
      connect();
    } else if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
      setIsConnected(false);
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [enabled, isAuthenticated, connect]);

  const sendMessage = useCallback((message: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const subscribe = useCallback((channels: string[]) => {
    sendMessage({ type: 'subscribe', channels });
  }, [sendMessage]);

  const markRead = useCallback((notificationId: string) => {
    sendMessage({ type: 'mark_read', notification_id: notificationId });
  }, [sendMessage]);

  return {
    isConnected,
    lastNotification,
    sendMessage,
    subscribe,
    markRead,
  };
}