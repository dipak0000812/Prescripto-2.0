import { getVapidPublicKeyApi, subscribeWebPushApi } from '../api/reminders';
import { urlBase64ToUint8Array } from './base64Utils';

export { urlBase64ToUint8Array };

export function isPushSupported(): boolean {
  return (
    typeof window !== 'undefined' &&
    'serviceWorker' in navigator &&
    'PushManager' in window &&
    'Notification' in window
  );
}

export async function registerServiceWorkerAndSubscribe(): Promise<{
  success: boolean;
  reason?: 'unsupported' | 'denied' | 'error';
  errorMessage?: string;
}> {
  if (!isPushSupported()) {
    return { success: false, reason: 'unsupported' };
  }

  try {
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') {
      return { success: false, reason: 'denied' };
    }

    const registration = await navigator.serviceWorker.register('/sw.js');
    await navigator.serviceWorker.ready;

    const vapidKey = await getVapidPublicKeyApi();
    const convertedKey = urlBase64ToUint8Array(vapidKey);

    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: convertedKey as unknown as BufferSource,
    });

    const subJson = subscription.toJSON();
    if (!subJson.endpoint || !subJson.keys?.p256dh || !subJson.keys?.auth) {
      return {
        success: false,
        reason: 'error',
        errorMessage: 'Subscription keys missing from browser PushManager response',
      };
    }

    await subscribeWebPushApi({
      endpoint: subJson.endpoint,
      keys_p256dh: subJson.keys.p256dh,
      keys_auth: subJson.keys.auth,
      user_agent: navigator.userAgent,
    });

    return { success: true };
  } catch (err: any) {
    return {
      success: false,
      reason: 'error',
      errorMessage: err?.message || 'Failed to register push subscription',
    };
  }
}
