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
  let lang = 'en';
  try {
    lang = await uiLang();
    if (lang === 'fr') { title = toFrench(title); body = toFrench(body); }
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
    data: { url: data.url || DEFAULT_URL, lang: lang },
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

// Keep this allowlist aligned with open-vinted.html and the dashboard.
function isVintedListing(url) {
  return url.protocol === 'https:' && !url.username && !url.password && !url.port &&
    /^(www\.)?vinted\.(be|fr|nl|de|it|es|pt|at|lu|ie|co\.uk|com|pl|cz|sk|lt|lv|ee|fi|se|dk|hu|ro|hr|si|gr)$/.test(url.hostname) &&
    /^\/items\/[0-9]+(?:-[^/]+)?\/?$/.test(url.pathname);
}

function notificationTarget(raw) {
  try {
    if (typeof raw !== 'string' || !raw.trim()) throw new Error('Missing URL');
    const url = new URL(raw, self.location.origin);
    if (url.protocol === 'https:' && !url.username && !url.password &&
        (url.origin === self.location.origin || isVintedListing(url))) return url;
  } catch (_) {}
  return new URL(DEFAULT_URL, self.location.origin);
}

function listingHandoff(target, lang) {
  const url = new URL('/open-vinted.html', self.location.origin);
  url.hash = new URLSearchParams({ url: target.href, lang: lang === 'fr' ? 'fr' : 'en' }).toString();
  return url;
}

async function openInternalTarget(target) {
  let list = [];
  try { list = await self.clients.matchAll({ type: 'window', includeUncontrolled: true }); }
  catch (_) { /* A failed lookup must not swallow the notification destination. */ }
  for (const client of list) {
    try {
      if (new URL(client.url).origin !== self.location.origin || !client.navigate || !client.focus) continue;
      const navigated = await client.navigate(target.href);
      if (!navigated) continue;
      return await navigated.focus();
    } catch (_) { /* Closed/stale clients are retried in a fresh window below. */ }
  }
  if (self.clients.openWindow) return self.clients.openWindow(target.href);
}

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const data = event.notification.data || {};
  const target = notificationTarget(data.url);
  if (isVintedListing(target)) {
    // A direct, user-tapped link works from the iPhone dashboard. A service
    // worker opening a URL is a different path and can land in the browser.
    // Use one explicit link tap on iOS; never simulate a click or guess a scheme.
    const nav = self.navigator || {};
    const lang = data.lang || String(nav.language || 'en').slice(0, 2).toLowerCase();
    const handoff = listingHandoff(target, lang);
    if (/iPad|iPhone|iPod|Macintosh.*Mobile\//i.test(nav.userAgent || '')) {
      event.waitUntil(openInternalTarget(handoff));
    } else {
      // Do not focus a SNYPD tab and return: that discarded external URLs.
      // Start the external open during the click, before any client lookup.
      event.waitUntil((async () => {
        try {
          if (self.clients.openWindow) return await self.clients.openWindow(target.href);
        } catch (_) { /* Keep the actual listing available if navigation fails. */ }
        return openInternalTarget(handoff);
      })());
    }
    return;
  }
  event.waitUntil(openInternalTarget(target));
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
