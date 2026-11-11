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
    .replace(/^1 new match overnight$/, '1 nouvelle annonce cette nuit')
    .replace(/^(\d+) new matches overnight$/, '$1 nouvelles annonces cette nuit')
    .replace(/^1 new match - /, '1 nouvelle annonce - ')
    .replace(/^(\d+) new matches - /, '$1 nouvelles annonces - ')
    .replace(/^From (.+)\. Tap to see them\.$/, 'D\u00e8s $1. Touche pour les voir.')
    .replace(/^Tap to see them\.$/, 'Touche pour les voir.');
}

async function show(data) {
  let title = data.title || 'SNYPD';
  let body = data.body || 'A new listing matched your search.';
  let fr = false;
  try {
    fr = (await uiLang()) === 'fr';
    if (fr) { title = toFrench(title); body = toFrench(body); }
  } catch (e) {}
  // Price check (Session 66): push.py sends "rank" (50-100) only for paid plans and running trials, as a number,
  // so the sentence follows the user's language here. Payloads without it are shown exactly as before.
  if (Number.isInteger(data.rank) && data.rank >= 50 && data.rank <= 100) {
    body = (fr ? 'Moins cher que ' + data.rank + '\u00a0% des trouvailles de la semaine \u00b7 '
               : 'Cheaper than ' + data.rank + '% of this week\'s finds \u00b7 ') + body;
  }
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
    data: { url: data.url || DEFAULT_URL, lang: fr ? 'fr' : 'en' },
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

/* Notification tap (11 Nov 2026, website outreach/47; replaces the unfinished codex/iphone-notification-handoff).
 * Two bugs before: (1) with a SNYPD tab open, the tap only focused that tab and never opened the listing;
 * (2) on iPhone, a link opened BY CODE from a Home Screen app goes to Safari (logged out), never to the Vinted
 * app: iOS hands a universal link to the app only on a real user tap. So on iPhone/iPad the tap opens our own
 * /open-vinted page, whose big button is that real tap. Only https www.vinted.<tld>/items/<id> links are allowed;
 * keep VINTED_RE in step with open-vinted.html. */
const VINTED_RE = /^(www\.)?vinted\.(be|fr|nl|de|it|es|pt|at|lu|ie|co\.uk|com|pl|cz|sk|lt|lv|ee|fi|se|dk|hu|ro|hr|si|gr)$/;

function isVintedListing(u) {
  return u.protocol === 'https:' && !u.username && !u.password && !u.port &&
    VINTED_RE.test(u.hostname) && /^\/items\/[0-9]+(?:-[^/]*)?\/?$/.test(u.pathname);
}

function tapTarget(raw) {
  try {
    if (typeof raw === 'string' && raw.trim()) {
      const u = new URL(raw, self.location.origin);
      if (u.origin === self.location.origin || isVintedListing(u)) return u;
    }
  } catch (e) {}
  return new URL(DEFAULT_URL, self.location.origin);
}

function isAppleMobile() {
  const ua = String((self.navigator && self.navigator.userAgent) || '');
  // iPadOS reports a Mac user agent; the service worker has no touch info, so "Mobile/" in it is the tell.
  return /iPhone|iPad|iPod/.test(ua) || /Macintosh.*Mobile\//.test(ua);
}

async function openOwnPage(target) {
  let list = [];
  try { list = await self.clients.matchAll({ type: 'window', includeUncontrolled: true }); } catch (e) {}
  for (const client of list) {
    try {
      if (new URL(client.url).origin !== self.location.origin || !client.navigate) continue;
      const nav = await client.navigate(target.href);
      if (nav) return nav.focus ? nav.focus() : nav;
    } catch (e) { /* stale client: fall through to a new window */ }
  }
  if (self.clients.openWindow) return self.clients.openWindow(target.href);
}

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const data = event.notification.data || {};
  const target = tapTarget(data.url);
  if (!isVintedListing(target)) {
    event.waitUntil(openOwnPage(target));
    return;
  }
  if (isAppleMobile()) {
    const page = new URL('/open-vinted', self.location.origin);
    page.hash = new URLSearchParams({ url: target.href, lang: data.lang === 'fr' ? 'fr' : 'en' }).toString();
    event.waitUntil(openOwnPage(page));
    return;
  }
  // Android/desktop: open the listing itself during the tap (Android hands vinted.* links to the app when it is
  // installed); never stop at focusing a SNYPD tab. If that fails, the handoff page still offers the link.
  event.waitUntil((async () => {
    try { if (self.clients.openWindow && await self.clients.openWindow(target.href)) return; } catch (e) {}
    const page = new URL('/open-vinted', self.location.origin);
    page.hash = new URLSearchParams({ url: target.href, lang: data.lang === 'fr' ? 'fr' : 'en' }).toString();
    return openOwnPage(page);
  })());
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
