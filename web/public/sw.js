// Prescripto 2.0 — Web Push & Medication Alarm Service Worker

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('push', (event) => {
  let data = {};
  if (event.data) {
    try {
      data = event.data.json();
    } catch {
      data = { title: 'Prescripto Reminder', body: event.data.text() };
    }
  }

  const title = data.title || 'Medicine Reminder';
  const options = {
    body: data.body || 'Time to take your scheduled dose.',
    icon: '/favicon.svg',
    badge: '/favicon.svg',
    tag: data.tag || 'prescripto-dose',
    renotify: true,
    requireInteraction: true,
    data: {
      eventId: data.eventId,
      planId: data.planId,
      medicineName: data.medicineName,
      url: '/today',
    },
    actions: [
      { action: 'taken', title: 'Taken' },
      { action: 'snooze', title: 'Snooze 10m' },
      { action: 'skip', title: 'Skip' },
    ],
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const notificationData = event.notification.data || {};
  const action = event.action;

  if (action && notificationData.eventId) {
    // Forward action to API in background if possible
    const eventId = notificationData.eventId;
    let actType = 'TAKEN';
    if (action === 'snooze') actType = 'SNOOZE';
    if (action === 'skip') actType = 'SKIP';

    event.waitUntil(
      fetch(`/api/v1/reminders/events/${eventId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: actType }),
      }).catch(() => {})
    );
  }

  // Open or focus the app on /today
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if ('focus' in client) {
          if (client.url.includes('/today')) {
            return client.focus();
          }
          client.navigate('/today');
          return client.focus();
        }
      }
      if (self.clients.openWindow) {
        return self.clients.openWindow('/today');
      }
    })
  );
});

