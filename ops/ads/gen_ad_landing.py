#!/usr/bin/env python3
# Builds start.html: the landing page for paid ads (Meta), separate from the SEO pages.
#
#   python ops/ads/gen_ad_landing.py
#
# WHY A SEPARATE PAGE (5 Oct 2026): Meta rejected the first 3 ads under its Prohibited
# Commercial Practices / fraud-scams policy. Meta reviews the ad AND its landing page as one
# unit; the SEO pages are written for search (the words people search for, competitor
# comparisons, a Vinted-terms FAQ) and carry a nav full of "Vinted bot" links. This page
# says only what the ad says, in plain words, with the plans, the limits of the free plan,
# who runs SNYPD and the legal links on the page itself. It is shown to every visitor alike
# (never to reviewers only - that would be cloaking) and is noindex: it is not an SEO page.
#
# RULES: every sentence must be on outreach/00-fact-sheet.md. Never: instant, real-time,
# fastest, a catch-time figure, safe, allowed by Vinted, savings or price claims.
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'ops', 'seo'))
from gen_content import CSS, COMPARE_CSS, PLANS_HEAD, PLANS_ROWS, SITE, EMAIL, esc, figure, table  # noqa: E402

TITLE = 'SNYPD - Push alerts for new Vinted listings'
DESC = ('Paste a Vinted search link with your filters. SNYPD checks it every 30 seconds to 5 minutes '
        'and sends a push notification when a new listing matches. Free plan: 1 search, no card.')

STEPS = [
    ('Copy your search', 'On Vinted, set your filters (brand, size, price, condition) and copy the link from the address bar.'),
    ('Paste it into SNYPD', 'Every filter in the link is kept. A link SNYPD cannot read in full is refused, not trimmed.'),
    ('Get a push', 'SNYPD checks the search every 30 seconds to 5 minutes and sends a push notification when a new '
                   'listing matches. You open it on Vinted and decide.'),
]

NEVER = [
    'Never asks for your Vinted password and never signs in to your Vinted account.',
    'Never buys, makes offers or messages sellers. Every purchase is yours to make on Vinted.',
    'No Telegram, Discord or email alerts: push notifications and the dashboard only.',
]

BODY = f"""
<section id="how">
  <h2>How it works</h2>
  <ol>{''.join('<li><strong>%s.</strong> %s</li>' % (esc(t), esc(d)) for t, d in STEPS)}</ol>
  {figure('feed', 'en')}
</section>
<section id="never">
  <h2>What SNYPD never does</h2>
  <ul>{''.join('<li>%s</li>' % esc(x) for x in NEVER)}</ul>
</section>
<section id="where">
  <h2>Where it works</h2>
  <p>Every Vinted site in Europe and the US: 26 sites. Alerts arrive on your phone or computer. On iPhone they work after you add SNYPD to your Home Screen, because Apple only allows web push there.</p>
</section>
<section id="plans">
  <h2>Plans</h2>
  {table(PLANS_HEAD['en'], PLANS_ROWS['en'], us_row=0)}
  <p>Prices include VAT. The free plan needs no card and has no time limit or cap on notifications; it watches your search while your dashboard is open. Paid plans keep watching with the dashboard closed. 14-day refund on the first payment of a plan.</p>
  <div class="lg-box lg-mint"><p><strong>Start with one search, free.</strong> No card.</p>
    <div class="ct-actions"><a class="ct-btn" href="/signup">START FREE</a><a class="ct-btn ct-ghost" href="/plans">SEE PLANS</a></div></div>
</section>
<section id="who">
  <h2>Who runs SNYPD</h2>
  <p>Built by a Belgian sneaker reseller. Operator: Tanush Khandelwal, Belgium. Contact: <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
  <p>SNYPD is independent and not affiliated with or endorsed by Vinted.</p>
</section>"""

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(TITLE)}</title>
<meta name="description" content="{esc(DESC)}">
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="{SITE}/start">
<meta property="og:title" content="{esc(TITLE)}">
<meta property="og:description" content="{esc(DESC)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE}/start">
<meta property="og:site_name" content="SNYPD">
<meta property="og:image" content="{SITE}/assets/og/og-v5.png">
<meta name="theme-color" content="#0A0A0B">
<link rel="icon" type="image/png" sizes="192x192" href="/assets/icons/icon-192.png">
<link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/dm-mono-400-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts/dm-mono.css">
<link rel="preload" href="/assets/home/CabinetGrotesk-Black.woff2" as="font" type="font/woff2" crossorigin="anonymous">
<style>{CSS}{COMPARE_CSS}</style>
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
    <a class="lg-brand" href="/"><img src="/assets/home/logo.png" alt="SNYPD" width="22" height="22"><span>SNYPD<span class="lg-cursor">_</span></span></a>
    <a class="lg-navlink lg-login" href="/login">LOG IN</a>
    <a class="lg-cta" href="/signup">START FREE</a>
  </div>
</header>
<main>
  <div class="lg-head">
    <div class="lg-wrap lg-head-in">
      <span class="lg-eyebrow">FOR VINTED BUYERS AND RESELLERS</span>
      <h1 class="lg-h1">A push alert when a new listing matches your Vinted search</h1>
      <p class="lg-lead">Paste a Vinted search link with your filters. SNYPD checks it every 30 seconds to 5 minutes and sends a push notification to your phone or computer when a new listing matches. Free plan: 1 search, no card.</p>
      <div class="ct-actions"><a class="ct-btn" href="/signup">START FREE</a><a class="ct-btn ct-ghost" href="#how">HOW IT WORKS</a></div>
    </div>
  </div>
  <div class="lg-wrap lg-grid lg-wide">
    <article class="lg-doc">
{BODY}
    </article>
  </div>
</main>
<footer class="lg-foot">
  <div class="lg-wrap lg-foot-in">
    <div class="lg-foot-a">
      <small>SNYPD &middot; NOT AFFILIATED WITH VINTED</small>
      <span class="lg-foot-l"><a href="/plans">Plans</a><a href="/faq">FAQ</a><a href="/support">Support</a></span>
    </div>
    <nav class="lg-foot-l" aria-label="Legal" style="align-items:flex-start;"><a href="/privacy">Privacy</a><a href="/terms">Terms</a><a href="mailto:{EMAIL}">Contact</a><a href="/cookies">Cookies</a><a href="/cookies" data-cookie-settings>Cookie settings</a></nav>
  </div>
</footer>
</body>
</html>
"""

with open(os.path.join(ROOT, 'start.html'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(HTML)
print('wrote start.html', len(HTML.encode('utf-8')), 'bytes')
