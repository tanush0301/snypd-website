/* SNYPD service worker.
 *
 * Exists for one reason: to receive a push message and draw a notification when
 * the site is not open. Registered from /dashboard but served from the root so
 * its scope covers the whole site.
 *
 * DELIBERATELY NOT AN OFFLINE CACHE. A service worker is usually introduced to
 * cache pages, and doing that here would be actively harmful: the dashboard's
 * entire value is that it shows what is on Vinted right now, and a cached copy
 * of a listing that has already sold is worse than no page at all. Nothing here
 * intercepts fetch.
 */

const DEFAULT_URL = '/dashboard';

// Take over immediately rather than waiting for every tab to close. A stale
// worker that cannot parse the current payload shape would silently drop
// notifications, and the user would have no way to know.
self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('push', (event) => {
  // Always show something. On Chrome and Firefox a push that resolves without
  // displaying a notification counts as a violation, and repeated violations
  // get the site's push permission revoked. A generic notification is a far
  // better outcome than losing the channel.
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    try {
      data = { body: event.data ? event.data.text() : '' };
    } catch (e2) {
      data = {};
    }
  }

  const title = data.title || 'SNYPD';
  const options = {
    body: data.body || 'A new listing matched your search.',
    icon: '/assets/icons/icon-192.png',
    badge: '/assets/icons/icon-192.png',
    // A stable tag means a second alert replaces the first instead of stacking
    // five of them on the lock screen. renotify still buzzes.
    tag: 'snypd-find',
    renotify: true,
    requireInteraction: false,
    timestamp: data.ts ? data.ts * 1000 : Date.now(),
    data: { url: data.url || DEFAULT_URL },
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const target = (event.notification.data && event.notification.data.url) || DEFAULT_URL;

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
      // Prefer focusing a tab that is already open over opening a second one.
      for (const client of list) {
        if ('focus' in client) {
          try {
            if (client.url && new URL(client.url).origin === self.location.origin) {
              client.focus();
              if ('navigate' in client && target.startsWith('/')) {
                return client.navigate(target);
              }
              return;
            }
          } catch (e) {
            /* a client with an unparseable URL is not worth failing over */
          }
        }
      }
      if (self.clients.openWindow) {
        return self.clients.openWindow(target);
      }
    })
  );
});

// Push services rotate subscriptions without warning. When that happens the
// browser fires this event and the old endpoint stops working, so the page has
// to re-register. The worker cannot do it alone -- it has no auth token -- so it
// tells any open tab to redo the subscription.
self.addEventListener('pushsubscriptionchange', (event) => {
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
      for (const client of list) {
        client.postMessage({ type: 'snypd-resubscribe' });
      }
    })
  );
});
