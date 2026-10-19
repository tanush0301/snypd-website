"""Generate /login, /signup and /reset-password from one template.

The three pages are one design ("SNYPDAuthScreen", Claude Design project
a9271573-..., boards in "SNYPD Auth 1a States.dc.html"); only the <head>
metadata and the starting view differ. All behaviour lives in
/assets/auth.js. Edit this file, then run from the repo root:

    python ops/auth/gen_auth_pages.py

ops/ is in .vercelignore, so this script never deploys.
"""
import os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'ops', 'seo'))
import plans  # noqa: E402  (trial length from ops/seo/data/plans.json)

SUPABASE_URL = 'https://igbuqanjocfmahlzzupc.supabase.co'
SUPABASE_ANON = ('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlnYnVxYW5qb2Nm'
                 'bWFobHp6dXBjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYzMTY4OTgsImV4cCI6MjA3MTg5Mjg5OH0.'
                 'iAF7dzPqrfbd3YZmnhKOTnMcNVslR5AMo8cBxxwpaJQ')

PAGES = {
    'login': dict(file='login.html', title='Log in to SNYPD',
                  desc='Log in to your SNYPD dashboard to see new Vinted listings that match your saved searches.',
                  # noindex since 9 Oct 2026: 33 Google impressions in 28 days, 0 clicks (GSC), taking brand
                  # queries that the homepage answers better. Not in the sitemap.
                  index=False),
    'signup': dict(file='signup.html', title='Sign up free - SNYPD Vinted Monitor',
                   desc='Create a free SNYPD account: one Vinted search free with no time limit, 24/7 for the first '
                        '%d days. Get a push alert when a new Vinted listing matches your filters.' % plans.TRIAL_DAYS,
                   index=True),
    'reset': dict(file='reset-password.html', title='Set a new password - SNYPD',
                  desc='Set a new password for your SNYPD account.', index=False),
}

PLAN_INTENT = """<script>
  /* Homepage START SOLO / KICKSTART / PRO / ELITE link here as /signup?plan=<plan>.
     Remember the choice so the dashboard can send the buyer to that checkout
     once they are signed in (see the plan-intent hook in dashboard.html). */
  (function () {
    try {
      var plan = (new URLSearchParams(location.search).get('plan') || '').toLowerCase();
      if (plan === 'solo' || plan === 'kickstart' || plan === 'pro' || plan === 'elite') {
        localStorage.setItem('snypd_plan_intent', JSON.stringify({ plan: plan, ts: Date.now() }));
      }
    } catch (e) {}
  })();
</script>
"""

HEAD = """<!DOCTYPE html>
<html lang="en" data-i18n-app>
<head>
<meta charset="utf-8">
<script src="/assets/i18n.js"></script>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
{seo}<link rel="icon" type="image/png" sizes="192x192" href="/assets/icons/icon-192.png">
<link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/dm-mono-400-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts/dm-mono.css">
<link rel="preload" href="/assets/home/CabinetGrotesk-Black.woff2" as="font" type="font/woff2" crossorigin="anonymous">
<style>
  @font-face {{ font-family: 'Cabinet Grotesk'; src: url('/assets/home/CabinetGrotesk-Black.woff2') format('woff2'); font-weight: 900; font-style: normal; font-display: swap; }}
  html, body {{ margin: 0; background: #0B0C0D; font-family: 'DM Mono', ui-monospace, monospace; }}
  a {{ color: #00E5A0; text-decoration: none; }}
  a:hover {{ color: #57FFC8; text-decoration: underline; }}
  button, input {{ font-family: inherit; }}
  a:focus-visible, button:focus-visible, input:focus-visible {{ outline: 2px solid #00E5A0; outline-offset: 2px; }}
  ::selection {{ background: #A200FF; color: #FFFFFF; }}
  @keyframes pulseDot {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: .2; }} }}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
  /* The design's style-hover / style-focus attributes. They sit on top of
     inline styles, so they need !important to win, as in the design. */
  .h-brand:hover {{ background: var(--brand-hover) !important; }}
  .h-brandlink:hover {{ background: var(--brand-hover) !important; color: var(--brand-fg) !important; text-decoration: none !important; }}
  .h-ghost:hover {{ border-color: var(--border3) !important; }}
  .h-toggle:hover {{ color: var(--text-primary) !important; }}
  .f-in:focus {{ border-color: var(--success) !important; }}
</style>
<script>
  /* Capture the URL before the Supabase client reads (and clears) it, so an
     error sent back by Google or an email link can be shown. */
  window.SNYPD_AUTH_URL = {{ hash: location.hash, search: location.search }};
</script>
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.js"></script>
<script>
  window.SNYPD = window.SNYPD || {{}};
  if (!SNYPD.supabase && window.supabase) {{
    SNYPD.supabase = supabase.createClient(
      '{sb_url}',
      '{sb_anon}'
    );
  }}
</script>
<!-- Cookie consent: Google Analytics and the Whop pixel load only after the visitor agrees -->
<script src="/assets/consent.js" data-ga="G-VBC0SXPR6F" data-whop="biz_FO7MS9yTf8rm6n"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-VBC0SXPR6F');
</script>
{extra}</head>
"""

SEO = """<link rel="canonical" href="https://www.snypd.store/{path}">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="https://www.snypd.store/{path}">
<meta property="og:site_name" content="SNYPD">
<meta property="og:locale" content="en_GB">
<meta property="og:image" content="https://www.snypd.store/assets/og/og-v5.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="SNYPD - Vinted monitor and new listing alerts for resellers">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="https://www.snypd.store/assets/og/og-v5.png">
"""

EXAMPLES = [
    ('Jordan 1 Travis Scott Velvet Brown', '/assets/home/catch-jordan1-travis-velvet.jpg', '€225', 'Jordan • 42,5 • vinted.be'),
    ('Jordan 4 Bred OG', '/assets/home/catch-jordan4-bred.jpeg', '€140', 'Jordan • 42 • vinted.be'),
    ('Supreme 99 Football Top', '/assets/home/catch-supreme-99.webp', '€120', 'Supreme • L • vinted.be'),
]

CARD = """          <div style="background:var(--bg);display:flex;flex-direction:column;">
            <span style="position:relative;display:block;">
              <img src="{img}" alt="{title}" loading="lazy" style="width:100%;aspect-ratio:1/1;object-fit:cover;display:block;">
              <span style="position:absolute;top:8px;left:8px;font-size:11px;letter-spacing:.1em;color:var(--text-primary);background:var(--bg);border:1px solid var(--border3);padding:3px 7px;">EXAMPLE MATCH</span>
            </span>
            <div style="padding:12px;display:flex;flex-direction:column;gap:6px;">
              <span style="font-size:13px;line-height:1.35;color:var(--text-primary);">{title}</span>
              <span style="font-size:18px;color:var(--text-primary);">{price}</span>
              <span style="font-size:12px;line-height:1.5;color:var(--text-muted);">{meta}</span>
            </div>
          </div>
"""

BODY = """<body>
<div style="--bg:#0B0C0D;--panel:#0F1113;--panel-header:#101214;--border:#1E2225;--border-hover:#262B2F;--border3:#3A4147;--text-primary:#EDEFF0;--text-secondary:#A6ADB1;--text-muted:#7C8489;--text-caption:#5C6469;--brand:#A200FF;--brand-hover:#C54BFF;--brand-fg:#FFFFFF;--success:#00E5A0;--warning:#FFB020;--danger:#FF5C5C;--font:'DM Mono',ui-monospace,monospace;background:var(--bg);font-family:var(--font);color:var(--text-primary);min-height:100vh;min-height:100dvh;display:flex;flex-direction:column;">

  <div style="height:64px;padding:0 clamp(16px,3vw,28px);border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;gap:12px;">
    <a href="/" style="display:flex;align-items:center;gap:9px;color:var(--text-primary);min-height:44px;text-decoration:none;"><img src="/assets/home/logo.png" alt="" style="width:22px;height:22px;object-fit:contain;"><span style="font-size:15px;letter-spacing:.02em;">SNYPD<span style="color:var(--success);">_</span></span></a>
    <div style="display:flex;align-items:center;gap:16px;"><span data-i18n-switch></span><a href="/" style="font-size:12px;letter-spacing:.1em;color:var(--text-secondary);min-height:44px;display:flex;align-items:center;">← BACK TO SITE</a></div>
  </div>

  <div style="flex:1;display:grid;grid-template-columns:repeat(auto-fit,minmax(min(460px,100%),1fr));">

    <div style="display:flex;justify-content:center;align-items:center;padding:clamp(28px,5vw,56px) clamp(20px,4vw,40px);">
      <form id="au-form" novalidate aria-busy="false" style="width:100%;max-width:400px;display:flex;flex-direction:column;gap:20px;"></form>
      <noscript><p style="max-width:400px;font-size:13px;line-height:1.6;color:#A6ADB1;">Logging in to SNYPD needs JavaScript. Turn it on for this site and reload the page.</p></noscript>
    </div>

    <div style="background:var(--panel);border-left:1px solid var(--border);padding:clamp(28px,4vw,48px) clamp(20px,4vw,40px);display:flex;flex-direction:column;gap:24px;justify-content:center;">
      <div style="display:flex;flex-direction:column;gap:10px;">
        <div style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;"><span style="font-size:12px;letter-spacing:.14em;color:var(--text-muted);">EXAMPLE MATCHES</span><span style="font-size:12px;letter-spacing:.1em;color:var(--text-muted);">DASHBOARD LAYOUT · SAMPLE LISTINGS</span></div>
        <span style="font-family:'Cabinet Grotesk',var(--font);font-weight:900;font-size:clamp(30px,3.4vw,40px);line-height:1;letter-spacing:-.04em;">What a match looks like.</span>
      </div>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:1px;background:var(--border);border:1px solid var(--border);">
{cards}      </div>
      <div style="border:1px solid var(--border);background:var(--bg);padding:18px;display:flex;flex-direction:column;gap:6px;">
        <span id="au-listings" style="font-family:'Cabinet Grotesk',var(--font);font-weight:900;font-size:32px;line-height:1;letter-spacing:-.03em;">{listings}</span>
        <span style="font-size:13px;line-height:1.5;color:var(--text-primary);">Vinted listings matched to users' searches since 17 Sept 2026</span>
        <span id="au-asof" style="font-size:12px;color:var(--text-muted);">{asof}</span>
      </div>
    </div>

  </div>
</div>
<script src="/assets/auth.js" data-page="{page}"></script>
</body>
</html>
"""


# The listings figure is written by ops/seo/prepublish.py (COUNTER_PAGES) from public_stats,
# like the homepage's. Regenerating keeps the figure already in the file, so it can never fall
# back to an old hard-coded number; a brand-new file gets a dash until prepublish fills it.
COUNTER_RE = re.compile(r'id="au-listings"[^>]*>([^<]*)<.*?id="au-asof"[^>]*>([^<]*)<', re.S)


def current_counter(path):
    try:
        m = COUNTER_RE.search(open(path, encoding='utf-8').read())
    except FileNotFoundError:
        m = None
    return (m.group(1), m.group(2)) if m else ('&mdash;', 'As of &mdash;')


def build(page, cfg):
    path = {'login': 'login', 'signup': 'signup', 'reset': 'reset-password'}[page]
    if cfg['index']:
        seo = SEO.format(path=path, title=cfg['title'], desc=cfg['desc'])
    else:
        seo = '<meta name="robots" content="noindex, nofollow">\n'
    extra = PLAN_INTENT if page == 'signup' else ''
    head = HEAD.format(title=cfg['title'], desc=cfg['desc'], seo=seo, sb_url=SUPABASE_URL,
                       sb_anon=SUPABASE_ANON, extra=extra)
    cards = ''.join(CARD.format(title=t, img=i, price=p, meta=m) for t, i, p, m in EXAMPLES)
    listings, asof = current_counter(os.path.join(ROOT, cfg['file']))
    return head + BODY.format(cards=cards, page=page, listings=listings, asof=asof)


if __name__ == '__main__':
    only = sys.argv[1:]  # e.g. "signup" to rebuild one page
    for page, cfg in PAGES.items():
        if only and page not in only:
            continue
        out = os.path.join(ROOT, cfg['file'])
        data = build(page, cfg)  # before opening: build() reads the current counter from this file
        with open(out, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(data)
        print('wrote', cfg['file'])
