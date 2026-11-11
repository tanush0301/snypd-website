# Builds cookies.html, privacy.html and terms.html for the SNYPD site from one
# shared layout (homepage v5 look), so the three pages cannot drift apart.
#   python gen_legal.py <repo> live    -> Privacy/Terms linked everywhere
#   python gen_legal.py <repo> held    -> only the cookie page is linked
import sys, os

REPO, MODE = sys.argv[1], sys.argv[2]
LIVE = MODE == 'live'
UPDATED = '9 October 2026'
# A page whose text changed later carries its own date (privacy: hunter statistics, 7 Nov 2026).
UPDATED_BY_SLUG = {'privacy': '10 November 2026', 'terms': '7 November 2026'}  # terms: check speed wording (60 s median)
EMAIL = 'help@snypd.store'   # = the live pages since 1 Nov 2026 (c537565 edited the HTML by hand)
DISCORD = 'https://discord.gg/gjKD4auXhK'

CSS = r"""
@font-face { font-family: 'Cabinet Grotesk'; src: url('/assets/home/CabinetGrotesk-Black.woff2') format('woff2'); font-weight: 900; font-style: normal; font-display: swap; }
html, body { margin: 0; background: #0A0A0B; }
body { font-family: 'DM Mono', ui-monospace, monospace; color: #E8EAEB; -webkit-font-smoothing: antialiased; }
a { color: #00E5A0; text-decoration: none; }
a:hover { color: #57FFC8; }
a:focus-visible, button:focus-visible { outline: 2px solid #00E5A0; outline-offset: 2px; }
::selection { background: #A200FF; color: #FFFFFF; }
@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }
@media (prefers-reduced-motion: reduce) { .lg-cursor { animation: none !important; } }
.lg-wrap { max-width: 1320px; margin: 0 auto; padding-left: 20px; padding-right: 20px; box-sizing: border-box; }
/* nav: same bar as the homepage */
.lg-nav { position: sticky; top: 0; z-index: 30; background: rgba(10,10,11,.92); border-bottom: 1px solid #1D1D20; }
.lg-nav-in { display: flex; align-items: center; gap: 10px 18px; padding-top: 8px; padding-bottom: 8px; }
.lg-brand { display: flex; align-items: center; gap: 9px; color: #FFFFFF; min-height: 44px; }
.lg-brand:hover { color: #FFFFFF; }
.lg-brand img { width: 22px; height: 22px; object-fit: contain; display: block; }
.lg-brand span { font-size: 15.5px; font-weight: 700; letter-spacing: .02em; }
.lg-cursor { animation: blink 1.2s step-end infinite; }
.lg-links { display: flex; gap: 4px; flex: 1; }
.lg-navlink { font-size: 12px; letter-spacing: .1em; color: #8B9094; padding: 14px 10px; }
.lg-navlink:hover { color: #FFFFFF; }
.lg-cta { font-size: 12px; letter-spacing: .1em; color: #FFFFFF; background: #A200FF; padding: 14px 16px; }
.lg-cta:hover { color: #FFFFFF; filter: brightness(1.18); }
@media (max-width: 699.98px) { .lg-links { display: none; } .lg-nav-in { justify-content: space-between; } .lg-login { margin-left: auto; } }
/* header */
.lg-head { border-bottom: 1px solid #1D1D20; }
.lg-head-in { padding-top: 56px; padding-bottom: 40px; display: flex; flex-direction: column; gap: 14px; }
.lg-eyebrow { font-size: 11px; letter-spacing: .16em; color: #8B9094; }
.lg-h1 { margin: 0; font-family: 'Cabinet Grotesk', 'DM Mono', sans-serif; font-weight: 900; font-size: clamp(38px, 6.4vw, 64px); line-height: .95; letter-spacing: -.045em; color: #FFFFFF; }
.lg-meta { font-size: 12px; color: #8B9094; }
.lg-lead { margin: 6px 0 0; max-width: 68ch; font-size: 14px; line-height: 1.7; color: #B8BCBF; }
/* body */
.lg-grid { display: grid; grid-template-columns: 240px minmax(0, 1fr); gap: 48px; padding-top: 40px; padding-bottom: 72px; align-items: start; }
@media (max-width: 899.98px) { .lg-grid { grid-template-columns: minmax(0, 1fr); gap: 28px; padding-top: 28px; } }
.lg-toc { position: sticky; top: 84px; border: 1px solid #1D1D20; background: #0C0C0D; padding: 16px 18px; display: flex; flex-direction: column; gap: 2px; }
@media (max-width: 899.98px) { .lg-toc { position: static; } }
.lg-toc span { font-size: 11px; letter-spacing: .14em; color: #8B9094; margin-bottom: 8px; }
.lg-toc a { font-size: 12px; line-height: 1.5; color: #B8BCBF; padding: 5px 0; }
.lg-toc a:hover { color: #00E5A0; }
.lg-doc { max-width: 760px; min-width: 0; }
.lg-doc section { border-top: 1px solid #1D1D20; padding: 30px 0 6px; scroll-margin-top: 80px; }
.lg-doc section:first-child { border-top: 0; padding-top: 0; }
.lg-doc h2 { margin: 0 0 14px; font-family: 'Cabinet Grotesk', 'DM Mono', sans-serif; font-weight: 900; font-size: clamp(24px, 3.2vw, 30px); line-height: 1.05; letter-spacing: -.03em; color: #FFFFFF; }
.lg-doc h3 { margin: 22px 0 8px; font-size: 12.5px; font-weight: 400; letter-spacing: .1em; color: #FFFFFF; }
.lg-doc p, .lg-doc li { font-size: 13px; line-height: 1.75; color: #B8BCBF; }
.lg-doc p { margin: 0 0 14px; }
.lg-doc ul { margin: 0 0 14px; padding-left: 18px; }
.lg-doc li { margin: 0 0 6px; }
.lg-doc strong { font-weight: 400; color: #FFFFFF; }
.lg-doc code { font-family: inherit; font-size: 12px; color: #FFFFFF; background: #141416; border: 1px solid #26262A; padding: 1px 5px; overflow-wrap: anywhere; }
/* cookie / data rows */
.lg-rows { border: 1px solid #1D1D20; margin: 0 0 18px; }
.lg-row { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(0, 2fr) minmax(0, .9fr); gap: 6px 18px; padding: 14px 16px; border-top: 1px solid #1D1D20; background: #0C0C0D; }
.lg-row:first-child { border-top: 0; }
.lg-row.lg-rh { background: #121214; }
.lg-row.lg-rh span { font-size: 11px; letter-spacing: .12em; color: #8B9094; }
.lg-row span { font-size: 12px; line-height: 1.6; color: #B8BCBF; min-width: 0; }
.lg-row span:first-child { color: #FFFFFF; }
@media (max-width: 699.98px) { .lg-row { grid-template-columns: minmax(0, 1fr); } .lg-row.lg-rh { display: none; } .lg-row span[data-l]:before { content: attr(data-l) ' '; color: #8B9094; font-size: 11px; letter-spacing: .1em; } }
/* boxes and buttons */
.lg-box { border: 1px solid #1D1D20; background: #0C0C0D; padding: 18px; margin: 0 0 18px; display: flex; flex-direction: column; gap: 12px; }
.lg-box.lg-mint { border-color: rgba(0,229,160,.38); background: rgba(0,229,160,.06); }
.lg-box.lg-amber { border-color: rgba(255,176,32,.45); background: rgba(255,176,32,.06); }
.lg-box p { margin: 0; }
.lg-btn { align-self: flex-start; font-family: inherit; font-size: 12px; letter-spacing: .09em; color: #FFFFFF; background: #141416; border: 1px solid #3A3A40; padding: 13px 18px; min-height: 46px; cursor: pointer; border-radius: 0; }
.lg-btn:hover { background: #1C1C1F; border-color: #55555C; }
.lg-state { font-size: 12px; color: #8B9094; }
.lg-state b { font-weight: 400; color: #FFFFFF; }
.lg-form { white-space: pre-wrap; font-size: 12px; line-height: 1.7; color: #E8EAEB; background: #121214; border: 1px solid #26262A; padding: 16px; margin: 0 0 18px; }
/* footer: same as the homepage */
.lg-foot { border-top: 1px solid #1D1D20; }
.lg-foot-in { padding-top: 24px; padding-bottom: 24px; display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.lg-foot-a { display: flex; flex-direction: column; gap: 6px; }
.lg-foot small { font-size: 11px; letter-spacing: .1em; color: #8B9094; }
.lg-foot-t { font-size: 12px; color: #8B9094; }
.lg-foot-l { display: flex; gap: 16px; flex-wrap: wrap; margin-top: 4px; }
.lg-foot-l a, .lg-foot-l button { font-size: 12px; }
.lg-foot-l button { font-family: inherit; color: #00E5A0; background: none; border: 0; padding: 0; cursor: pointer; }
.lg-foot-l button:hover { color: #57FFC8; }
"""


def legal_links():
    parts = []
    if LIVE:
        parts += ['<a href="/privacy">Privacy</a>', '<a href="/terms">Terms</a>', '<a href="mailto:%s">Contact</a>' % EMAIL]
    parts += ['<a href="/cookies">Cookies</a>', '<a href="/cookies" data-cookie-settings>Cookie settings</a>']
    if not LIVE:
        parts += ['<span class="lg-foot-t">Privacy and Terms pages coming soon.</span>']
    return ''.join(parts)


def page(slug, title, desc, h1, lead, toc, body):
    toc_html = ''.join('<a href="#%s">%s</a>' % (a, t) for a, t in toc)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://www.snypd.store/{slug}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="https://www.snypd.store/{slug}">
<meta property="og:site_name" content="SNYPD">
<meta property="og:locale" content="en_GB">
<meta property="og:image" content="https://www.snypd.store/assets/og/og-v5.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="SNYPD - Vinted monitor and new listing alerts for resellers">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0A0A0B">
<link rel="icon" type="image/png" sizes="192x192" href="/assets/icons/icon-192.png">
<link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/dm-mono-400-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts/dm-mono.css">
<link rel="preload" href="/assets/home/CabinetGrotesk-Black.woff2" as="font" type="font/woff2" crossorigin="anonymous">
<style>{CSS}</style>
<!-- Cookie consent: Google Analytics, the Whop pixel and the Meta Pixel load only after the visitor agrees -->
<script src="/assets/consent.js" data-ga="G-VBC0SXPR6F" data-whop="biz_FO7MS9yTf8rm6n"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-VBC0SXPR6F');
</script>
</head>
<body>
<header class="lg-nav">
  <div class="lg-wrap lg-nav-in">
    <a class="lg-brand" href="/"><img src="/assets/home/logo.png" alt="SNYPD"><span>SNYPD<span class="lg-cursor">_</span></span></a>
    <nav class="lg-links" aria-label="Main">
      <a class="lg-navlink" href="/#how">HOW IT WORKS</a>
      <a class="lg-navlink" href="{DISCORD}">DISCORD</a>
      <a class="lg-navlink" href="/#pricing">PRICING</a>
    </nav>
    <a class="lg-navlink lg-login" href="/login">LOG IN</a>
    <a class="lg-cta" href="/signup">START FREE</a>
  </div>
</header>
<main>
  <div class="lg-head">
    <div class="lg-wrap lg-head-in">
      <span class="lg-eyebrow">LEGAL</span>
      <h1 class="lg-h1">{h1}</h1>
      <span class="lg-meta">Last updated {UPDATED_BY_SLUG.get(slug, UPDATED)}</span>
      <p class="lg-lead">{lead}</p>
    </div>
  </div>
  <div class="lg-wrap lg-grid">
    <nav class="lg-toc" aria-label="On this page"><span>ON THIS PAGE</span>{toc_html}</nav>
    <article class="lg-doc">
{body}
    </article>
  </div>
</main>
<footer class="lg-foot">
  <div class="lg-wrap lg-foot-in">
    <div class="lg-foot-a">
      <small>SNYPD &middot; NOT AFFILIATED WITH VINTED</small>
      <span class="lg-foot-t">Reads public listings only.</span>
      <span class="lg-foot-l"><a href="/faq">FAQ</a><a href="/support">Support</a><a href="{DISCORD}">Discord</a></span>
    </div>
    <nav class="lg-foot-l" aria-label="Legal" style="align-items:flex-start;">{legal_links()}</nav>
  </div>
</footer>
</body>
</html>
"""


def rows(head, items):
    h = '<div class="lg-row lg-rh">' + ''.join('<span>%s</span>' % x for x in head) + '</div>'
    r = ''.join('<div class="lg-row">' + ''.join(
        '<span%s>%s</span>' % ('' if i == 0 else ' data-l="%s:"' % head[i].upper(), c) for i, c in enumerate(it)) + '</div>'
        for it in items)
    return '<div class="lg-rows">' + h + r + '</div>'


# ------------------------------------------------------------------ cookies
COOKIE_HEAD = ['Name', 'What it does', 'How long']
necessary = [
    ('<code>sb-igbuqanjocfmahlzzupc-auth-token</code><br>local storage, Supabase', 'Keeps you signed in to your SNYPD account.', 'Until you sign out'),
    ('<code>snypd_consent</code><br>local storage, SNYPD', 'Remembers the cookie choice you made on this page or in the banner.', 'Until you change it or clear your browser'),
    ('<code>snypd_ui_lang</code><br>local storage, SNYPD; <code>snypd-prefs</code> cache storage, SNYPD', 'The language you chose for the sign-up pages and dashboard (English or French), or French when you came from a French page. The same choice is saved on your account, and a copy lets alert notifications use that language.', 'Until you clear your browser'),
    ('<code>snypd_last_email</code><br>local storage, SNYPD', 'The email you last signed in with on this device, so a timed-out session can take you back to a log-in screen with it filled in.', 'Until you sign out'),
    ('<code>snypd_plan_intent</code>, <code>snypd_plan_intent_done</code><br>local storage, SNYPD', 'Remembers which paid plan you picked before signing up, so its checkout opens once your account exists.', 'Removed once checkout opens; the "done" marker stays until you clear your browser'),
    ('<code>snypd_refer</code><br>local storage, SNYPD', 'Only if you arrived through a friend\'s SNYPD invite link: the invite code, so the bonus days you were offered are added when you sign up. Not used for ads or tracking.', 'Read for 60 days; stays until you clear your browser'),
    ('<code>snypd_manual_paused</code>, <code>snypd_sidebar_focus</code>, <code>snypd_claim_hint_dismissed</code>, <code>snypd_reconcile_snooze_until</code>, <code>snypd_last_tier_seen</code>, <code>snypd_mr_recent</code><br>local storage, SNYPD', 'Dashboard settings you chose: whether monitoring is paused, tips you dismissed, a snoozed reminder, the last rank you saw and your recent Market Report searches.', 'Until you clear your browser'),
    ('Service worker and push subscription<br>your browser', 'Only if you turn on alerts: lets your browser receive SNYPD notifications through its own push service.', 'Until you turn alerts off'),
    ('Whop checkout<br>cookies inside Whop\'s checkout frame', 'Loads only when you open a checkout on the plans page. Set by Whop, our payment provider, to process the payment and prevent fraud. Whop\'s checkout also runs Whop\'s own measurement script, and inside its frame Whop loads Google Ads, HubSpot and Snapchat tags.','Set by Whop, see <a href="https://whop.com/privacy/">Whop\'s privacy policy</a>'),
]
analytics = [
    ('<code>_ga</code>, <code>_ga_VBC0SXPR6F</code><br>cookie, Google', 'Google Analytics 4: tells visits and visitors apart so we can see which pages are used and how people find SNYPD. On some pages it is loaded through Google Tag Manager, which runs nothing except this same Analytics property.', 'Up to 2 years (most browsers cap this at 400 days)'),
]
marketing = [
    ('<code>_wuid</code>, <code>_wuid_link</code><br>cookie, Whop', 'Whop pixel: connects a sign-up or purchase to the ad or partner link that led to it.', 'Up to 400 days'),
    ('<code>_wuid</code>, <code>_wuid_link_domain</code>, <code>_wsc</code>, <code>_wsc_probed_at</code>, <code>_wfp</code>, <code>_wsc_probed</code><br>local and session storage, Whop', 'Used by the same Whop pixel for the same purpose.', 'Until you clear your browser (<code>_wsc_probed</code>: until you close the tab)'),
    ('<code>_fbp</code><br>cookie, Meta', 'Meta Pixel: tells visits apart so Meta can connect a SNYPD sign-up to the Facebook or Instagram ad that led to it.', '90 days'),
    ('<code>_fbc</code><br>cookie, Meta', 'Meta Pixel: only set when you arrive by clicking a Facebook or Instagram ad; stores that click so the sign-up can be credited to the ad.', '90 days'),
    ('<code>snypd_ref</code><br>local storage, SNYPD', 'The partner code from a partner link you arrived through, so the partner is credited if you sign up.', 'Until you clear your browser'),
    ('<code>snypd_aff</code><br>local storage, SNYPD', 'The Whop username of the partner whose link you arrived through, so Whop credits that partner if you subscribe.', 'Read for 30 days; stays until you clear your browser'),
]

cookies_body = f"""
<section id="choice">
  <h2>Your choice</h2>
  <div class="lg-box lg-mint">
    <p class="lg-state" id="lg-state">Checking your current choice...</p>
    <button type="button" class="lg-btn" data-cookie-settings>OPEN COOKIE SETTINGS</button>
  </div>
  <p>Nothing in the analytics or marketing lists below runs until you say yes. You can change your mind at any time with the button above or the <strong>Cookie settings</strong> link in the homepage footer. Saying no later deletes the analytics and marketing cookies SNYPD can reach and reloads the page, so the scripts stop.</p>
</section>
<section id="what">
  <h2>What this covers</h2>
  <p>"Cookies" here means cookies and anything similar that a website stores on your device: local storage, session storage and service workers. SNYPD itself sets no cookies at all. Everything it stores is in your browser's local storage, and only the items listed below.</p>
</section>
<section id="necessary">
  <h2>Necessary</h2>
  <p>Always on. SNYPD cannot sign you in, open your checkout or keep your dashboard settings without these. The law allows them without consent because they are needed for the service you asked for.</p>
  {rows(COOKIE_HEAD, necessary)}
</section>
<section id="analytics">
  <h2>Analytics</h2>
  <p>Only with your consent. Google receives your IP address and browser details when these load.</p>
  {rows(COOKIE_HEAD, analytics)}
</section>
<section id="marketing">
  <h2>Marketing</h2>
  <p>Only with your consent. Whop and Meta receive your IP address and browser details when their pixels load; Meta also receives which SNYPD pages you visit and, if you sign up, that a sign-up happened.</p>
  {rows(COOKIE_HEAD, marketing)}
</section>
<section id="other">
  <h2>Other services your browser contacts</h2>
  <p>It stores nothing on your device, but your browser fetches a file from it, so it sees your IP address: <strong>jsDelivr</strong> (the library that handles sign-in). SNYPD's fonts are served from snypd.store itself. <strong>Vercel Web Analytics</strong>, which hosts the site, counts page views without cookies or anything stored on your device, so it runs without asking. On pages where you are signed in, your browser also talks to <strong>Supabase</strong>, which runs SNYPD's database.</p>
</section>
<section id="contact">
  <h2>Questions</h2>
  <p>Email <a href="mailto:{EMAIL}">{EMAIL}</a>.{' More about how SNYPD handles personal data is in the <a href="/privacy">privacy policy</a>.' if LIVE else ''}</p>
</section>
<script>
(function () {{
  var MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  var el = document.getElementById('lg-state');
  function render() {{
    var c = window.SNYPDConsent && window.SNYPDConsent.get();
    if (!window.SNYPDConsent) {{ el.textContent = 'Cookie settings could not load. Try reloading the page.'; return; }}
    if (!c) {{ el.innerHTML = 'You have not made a choice yet, so <b>analytics and marketing are off</b>.'; return; }}
    var d = new Date(c.at), when = isNaN(d.getTime()) ? '' : ' (saved ' + d.getDate() + ' ' + MONTHS[d.getMonth()] + ' ' + d.getFullYear() + ')';
    el.innerHTML = 'Your current choice: <b>analytics ' + (c.analytics ? 'on' : 'off') + '</b> &middot; <b>marketing ' + (c.marketing ? 'on' : 'off') + '</b>' + when + '.';
  }}
  render();
  document.addEventListener('snypd:consent', render);
}})();
</script>"""

files = {
    'cookies.html': page('cookies', 'Cookie Policy | SNYPD',
        'Which cookies and similar storage SNYPD uses, why, and how to change your choice. Analytics and marketing only run with your consent.',
        'Cookie policy', 'What SNYPD stores on your device, why, and how to change your mind.',
        [('choice', 'Your choice'), ('what', 'What this covers'), ('necessary', 'Necessary'), ('analytics', 'Analytics'), ('marketing', 'Marketing'), ('other', 'Other services'), ('contact', 'Questions')],
        cookies_body),
}

if LIVE:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from legal_texts import privacy_body, terms_body, PRIVACY_TOC, TERMS_TOC
    files['privacy.html'] = page('privacy', 'Privacy Policy | SNYPD',
        'How SNYPD collects, uses and protects personal data, which services it relies on, how long data is kept and how to use your GDPR rights.',
        'Privacy policy', 'What personal data SNYPD collects, why, who helps process it, how long it is kept and what you can ask for.',
        PRIVACY_TOC, privacy_body(EMAIL, DISCORD))
    files['terms.html'] = page('terms', 'Terms of Service | SNYPD',
        'The terms for using SNYPD: plans and billing, the 14-day refund, what the service does and does not do, and your rights as a consumer.',
        'Terms of service', 'The agreement between you and SNYPD when you create an account or buy a plan.',
        TERMS_TOC, terms_body(EMAIL, DISCORD))

sys.path.insert(0, os.path.join(REPO, 'ops', 'seo'))
import plans  # noqa: E402  (fills the @@trial_days@@-style tokens in the terms from ops/seo/data/plans.json)

for name, html in files.items():
    assert '{' not in html.split('<style>')[0], name
    html = plans.fill(html, 'en')
    with open(os.path.join(REPO, name), 'w', encoding='utf-8', newline='\n') as f:
        f.write(html)
    print('wrote', name, len(html.encode('utf-8')), 'bytes')
