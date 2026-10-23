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

  event.waitUntil(show(data));
});

/* UI language for the few fixed words the backend puts in a push (backend
 * push.py: "New find", "N new finds", "& N more", "New listing", and the calm
 * summary "N new matches - <hunt>" / "From <price>. Tap to see them."). A service
 * worker cannot read localStorage, so /assets/i18n.js stores the language the
 * visitor uses in cache storage ('snypd-prefs', '/__ui_lang'); without it the
 * browser language decides. Any failure here falls back to English text: the
 * notification itself must always be shown. */
async function uiLang() {
  try {
    const c = await caches.open('snypd-prefs');
    const r = await c.match('/__ui_lang');
    if (r) return (await r.text()).slice(0, 2);
  } catch (e) {}
  try { return String(self.navigator.language || 'en').slice(0, 2).toLowerCase(); } catch (e) { return 'en'; }
}

function toFrench(s) {
  return String(s)
    .replace(/^New find$/, 'Nouvelle trouvaille')
    .replace(/^(\d+) new finds$/, '$1 nouvelles trouvailles')
    .replace(/ & (\d+) more$/, ' et $1 de plus')
    .replace(/(^|\u2014 )New listing\b/, '$1Nouvelle annonce')
    .replace(/^A new listing matched your search\.$/, 'Une nouvelle annonce correspond \u00e0 ta recherche.')
    .replace(/^1 new match - /, '1 nouvelle annonce - ')
    .replace(/^(\d+) new matches - /, '$1 nouvelles annonces - ')
    .replace(/^From (.+)\. Tap to see them\.$/, 'D\u00e8s $1. Touche pour les voir.')
    .replace(/^Tap to see them\.$/, 'Touche pour les voir.');
}

async function show(data) {
  let title = data.title || 'SNYPD';
  let body = data.body || 'A new listing matched your search.';
  try {
    if ((await uiLang()) === 'fr') { title = toFrench(title); body = toFrench(body); }
  } catch (e) {}
  const options = {
    body: body,
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
  // Android Chrome and Windows Chrome/Edge render this as the big preview
  // photo. iOS Safari and any macOS browser (via the OS's own Notification
  // Center) silently ignore it and always show the app icon instead -- a
  // platform limit, not a bug, so the price/condition text in `body` above is
  // what actually has to carry that information everywhere.
  if (data.image) {
    options.image = data.image;
  }

  return self.registration.showNotification(title, options);
}

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
