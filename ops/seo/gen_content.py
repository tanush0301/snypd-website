#!/usr/bin/env python3
# Builds the SEO content pages (English + French) from one layout, so the
# language versions and pages cannot drift apart. Homepage v5 look, same shell
# as ops/legal/gen_legal.py.
#
#   python ops/seo/gen_content.py
#
# Writes: vinted-bot.html, vinted-saved-search-alerts.html, vinted-bot-comparison.html,
#         vinted-prices.html, vinted-prices-2026-09.csv and fr/*.html
#
# RULES FOR EDITING THE COPY
# - Every product fact must match what SNYPD really does (CLAUDE.md, plans.html's
#   audit comment). Never: sub-second speed, "instant", email/Telegram/Discord
#   alerts, re-list filtering, per-plan speed differences, "allowed by Vinted".
# - Competitor facts come from each vendor's own website and carry the date they
#   were checked (CHECKED). Re-check them before changing that date.
# - Prices on vinted-prices come ONLY from ops/seo/data/price-report-*.json, which
#   is the real Market Report output (ops/seo/price_report_batch.py, run inside
#   the backend container). Never type a price by hand.
import csv, datetime, html, io, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = 'https://www.snypd.store'
DISCORD = 'https://discord.gg/gjKD4auXhK'
EMAIL = 'snypd@gmail.com'
PUBLISHED = '2026-09-28'
MODIFIED = '2026-10-01'
CHECKED = {'en': '28 September 2026', 'fr': '28 septembre 2026'}
# French pages stay unpublished until SNYPD really polls vinted.fr (decided 2026-10-01).
# While False: no French files are written, English pages carry no hreflang or
# language switch, and prepublish.py leaves French URLs out of the sitemap.
FR_LIVE = True
# The Vinted sites the scraper accepts (scraper-worker/src/catalogue_contract.py
# MARKETS, verified live 2026-10-01). Update together with that list.
MARKETS_TEXT = {'en': 'every Vinted site in Europe and the US', 'fr': 'tous les sites Vinted d’Europe et des États-Unis'}
REPORT = os.path.join(ROOT, 'ops', 'seo', 'data', 'price-report-2026-09.json')
REPORT_CSV = 'vinted-prices-2026-09.csv'

# slug per language; the key is the page id
SLUGS = {
    'bot':     {'en': '/vinted-bot',                 'fr': '/fr/bot-vinted'},
    'notify':  {'en': '/vinted-saved-search-alerts', 'fr': '/fr/alertes-recherche-vinted'},
    'compare': {'en': '/vinted-bot-comparison',      'fr': '/fr/comparatif-bot-vinted'},
    'prices':  {'en': '/vinted-prices',              'fr': '/fr/prix-vinted'},
}

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
.lg-navlink[aria-current="page"] { color: #FFFFFF; }
.lg-cta { font-size: 12px; letter-spacing: .1em; color: #FFFFFF; background: #A200FF; padding: 14px 16px; }
.lg-cta:hover { color: #FFFFFF; filter: brightness(1.18); }
@media (max-width: 699.98px) { .lg-links { display: none; } .lg-nav-in { justify-content: space-between; } .lg-login { margin-left: auto; } }
@media (max-width: 459.98px) { .lg-nav-in { gap: 4px; } .lg-navlink { padding: 14px 6px; letter-spacing: .05em; } .lg-cta { padding: 14px 10px; letter-spacing: .05em; } .lg-brand span { font-size: 14px; } }
.lg-head { border-bottom: 1px solid #1D1D20; }
.lg-head-in { padding-top: 56px; padding-bottom: 40px; display: flex; flex-direction: column; gap: 14px; }
.lg-eyebrow { font-size: 11px; letter-spacing: .16em; color: #8B9094; }
.lg-h1 { margin: 0; max-width: 20ch; font-family: 'Cabinet Grotesk', 'DM Mono', sans-serif; font-weight: 900; font-size: clamp(36px, 6vw, 60px); line-height: .98; letter-spacing: -.04em; color: #FFFFFF; }
.lg-meta { font-size: 12px; color: #8B9094; }
.lg-lead { margin: 6px 0 0; max-width: 68ch; font-size: 14px; line-height: 1.7; color: #B8BCBF; }
.lg-grid { display: grid; grid-template-columns: 240px minmax(0, 1fr); gap: 48px; padding-top: 40px; padding-bottom: 72px; align-items: start; }
@media (max-width: 899.98px) { .lg-grid { grid-template-columns: minmax(0, 1fr); gap: 28px; padding-top: 28px; } }
.lg-toc { position: sticky; top: 84px; border: 1px solid #1D1D20; background: #0C0C0D; padding: 16px 18px; display: flex; flex-direction: column; gap: 2px; }
@media (max-width: 899.98px) { .lg-toc { position: static; } }
.lg-toc span { font-size: 11px; letter-spacing: .14em; color: #8B9094; margin-bottom: 8px; }
.lg-toc a { font-size: 12px; line-height: 1.5; color: #B8BCBF; padding: 5px 0; }
.lg-toc a:hover { color: #00E5A0; }
.lg-doc { max-width: 820px; min-width: 0; }
.lg-wide { grid-template-columns: minmax(0, 1fr); }
.lg-wide .lg-doc { max-width: 1120px; }
.lg-doc section { border-top: 1px solid #1D1D20; padding: 30px 0 6px; scroll-margin-top: 80px; }
.lg-doc section:first-child { border-top: 0; padding-top: 0; }
.lg-doc h2 { margin: 0 0 14px; font-family: 'Cabinet Grotesk', 'DM Mono', sans-serif; font-weight: 900; font-size: clamp(24px, 3.2vw, 30px); line-height: 1.05; letter-spacing: -.03em; color: #FFFFFF; }
.lg-doc h3 { margin: 22px 0 8px; font-size: 12.5px; font-weight: 400; letter-spacing: .1em; color: #FFFFFF; }
.lg-doc p, .lg-doc li { font-size: 13px; line-height: 1.75; color: #B8BCBF; }
.lg-doc p { margin: 0 0 14px; }
.lg-doc ul, .lg-doc ol { margin: 0 0 14px; padding-left: 20px; }
.lg-doc li { margin: 0 0 6px; }
.lg-doc strong { font-weight: 400; color: #FFFFFF; }
.lg-doc code { font-family: inherit; font-size: 12px; color: #FFFFFF; background: #141416; border: 1px solid #26262A; padding: 1px 5px; overflow-wrap: anywhere; }
.lg-doc blockquote { margin: 0 0 14px; padding: 12px 16px; border-left: 2px solid #00E5A0; background: #0C0C0D; font-size: 13px; line-height: 1.7; color: #E8EAEB; }
.lg-doc blockquote cite { display: block; margin-top: 6px; font-style: normal; font-size: 11.5px; color: #8B9094; }
.lg-box { border: 1px solid #1D1D20; background: #0C0C0D; padding: 18px; margin: 0 0 18px; display: flex; flex-direction: column; gap: 12px; }
.lg-box.lg-mint { border-color: rgba(0,229,160,.38); background: rgba(0,229,160,.06); }
.lg-box p { margin: 0; }
.ct-scroll { overflow-x: auto; margin: 0 0 18px; border: 1px solid #1D1D20; -webkit-overflow-scrolling: touch; }
.ct-table { width: 100%; border-collapse: collapse; min-width: 640px; }
.ct-table th, .ct-table td { text-align: left; vertical-align: top; padding: 12px 14px; border-top: 1px solid #1D1D20; font-size: 12px; line-height: 1.55; color: #B8BCBF; }
.ct-table thead th { border-top: 0; background: #121214; font-size: 11px; font-weight: 400; letter-spacing: .1em; color: #8B9094; }
.ct-table tbody th { font-weight: 400; color: #FFFFFF; min-width: 150px; }
.ct-table tbody tr { background: #0C0C0D; }
.ct-table tbody tr.ct-us { background: rgba(162,0,255,.07); }
.ct-table .ct-num { white-space: nowrap; color: #FFFFFF; }
.ct-table small { display: block; color: #8B9094; font-size: 11px; }
.ct-note { font-size: 11.5px !important; color: #8B9094 !important; }
.ct-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.ct-btn { display: inline-flex; align-items: center; min-height: 46px; padding: 0 18px; font-size: 12px; letter-spacing: .09em; color: #FFFFFF; background: #A200FF; }
.ct-btn:hover { color: #FFFFFF; filter: brightness(1.18); }
.ct-btn.ct-ghost { background: #141416; border: 1px solid #3A3A40; }
.ct-btn.ct-ghost:hover { filter: none; background: #1C1C1F; border-color: #55555C; }
.lg-foot { border-top: 1px solid #1D1D20; }
.lg-foot-in { padding-top: 24px; padding-bottom: 24px; display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.lg-foot-a { display: flex; flex-direction: column; gap: 6px; }
.lg-foot small { font-size: 11px; letter-spacing: .1em; color: #8B9094; }
.lg-foot-t { font-size: 12px; color: #8B9094; }
.lg-foot-l { display: flex; gap: 8px 16px; flex-wrap: wrap; margin-top: 4px; }
.lg-foot-l a, .lg-foot-l button { font-size: 12px; }
.lg-foot-l button { font-family: inherit; color: #00E5A0; background: none; border: 0; padding: 0; cursor: pointer; }
.lg-foot-l button:hover { color: #57FFC8; }
"""

UI = {
    'en': dict(locale='en_GB', toc='ON THIS PAGE', updated='Updated', by='By SNYPD, built by a Belgian sneaker reseller',
               nav=[('bot', 'VINTED BOT'), ('prices', 'VINTED PRICES'), ('/plans', 'PRICING'), (DISCORD, 'DISCORD')],
               login='LOG IN', start='START FREE', switch=('FR', 'fr', 'Version française'),
               foot_tag='SNYPD &middot; NOT AFFILIATED WITH VINTED', foot_t='Reads public listings only.',
               foot=[('bot', 'Vinted bot'), ('notify', 'Vinted notifications'), ('compare', 'Vinted bots compared'), ('prices', 'Vinted prices'),
                     ('/faq', 'FAQ'), ('/support', 'Support'), (DISCORD, 'Discord')],
               legal='<a href="/cookies">Cookies</a><a href="/cookies" data-cookie-settings>Cookie settings</a>',
               home='Home'),
    'fr': dict(locale='fr_FR', toc='SUR CETTE PAGE', updated='Mis à jour le', by='Par SNYPD, créé par un revendeur de sneakers belge',
               nav=[('bot', 'BOT VINTED'), ('prices', 'PRIX VINTED'), ('/plans', 'TARIFS'), (DISCORD, 'DISCORD')],
               login='CONNEXION', start='COMMENCER', switch=('EN', 'en', 'English version'),
               foot_tag='SNYPD &middot; NON AFFILIÉ À VINTED', foot_t='Lit uniquement les annonces publiques.',
               foot=[('bot', 'Bot Vinted'), ('notify', 'Alertes Vinted'), ('compare', 'Comparatif des bots Vinted'), ('prices', 'Prix Vinted'),
                     ('/faq', 'FAQ (anglais)'), ('/support', 'Support (anglais)'), (DISCORD, 'Discord')],
               legal='<a href="/cookies">Cookies</a><a href="/cookies" data-cookie-settings>Paramètres des cookies</a>',
               home='Accueil'),
}
# Last real content change per page (shown as 'Updated' and used as dateModified).
PAGE_MODIFIED = {'bot': '2026-10-02', 'notify': '2026-10-02', 'compare': '2026-10-02', 'prices': '2026-10-02'}
MONTHS_TXT = {'en': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
              'fr': ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']}


def date_txt(iso, lang):
    y, m, d = (int(x) for x in iso.split('-'))
    day = ('1er' if d == 1 else str(d)) if lang == 'fr' else str(d)
    return '%s %s %d' % (day, MONTHS_TXT[lang][m - 1], y)


def esc(s):
    return html.escape(s, quote=True)


def href(key, lang):
    return SLUGS[key][lang] if key in SLUGS else key


def jsonld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(',', ':')) + '</script>'


def page(key, lang, title, desc, eyebrow, h1, lead, toc, body, extra_ld=(), head_extra=''):
    u = UI[lang]
    path = SLUGS[key][lang]
    url = SITE + path
    other = u['switch'][1]
    alts = ''
    if FR_LIVE:
        alts = ''.join('<link rel="alternate" hreflang="%s" href="%s%s">\n' % (l, SITE, SLUGS[key][l]) for l in ('en', 'fr'))
        alts += '<link rel="alternate" hreflang="x-default" href="%s%s">\n' % (SITE, SLUGS[key]['en'])
    switch = ('<a class="lg-navlink" href="%s" hreflang="%s" lang="%s" title="%s">%s</a>'
              % (SLUGS[key][other], other, other, u['switch'][2], u['switch'][0])) if FR_LIVE else ''
    nav = ''.join('<a class="lg-navlink" href="%s"%s>%s</a>' % (href(k, lang), ' aria-current="page"' if k == key else '', t) for k, t in u['nav'])
    foot = ''.join('<a href="%s">%s</a>' % (href(k, lang), t) for k, t in u['foot'])
    toc_html = ''.join('<a href="#%s">%s</a>' % (a, t) for a, t in (toc or []))
    toc_block = ('<nav class="lg-toc" aria-label="%s"><span>%s</span>%s</nav>' % (u['toc'].title(), u['toc'], toc_html)) if toc else ''
    grid_cls = 'lg-grid' if toc else 'lg-grid lg-wide'
    ld = [
        {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': u['home'], 'item': SITE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': h1_plain(h1), 'item': url}]},
        {'@context': 'https://schema.org', '@type': 'WebPage', '@id': url + '#page', 'url': url, 'name': title,
         'description': desc, 'inLanguage': lang, 'datePublished': PUBLISHED, 'dateModified': PAGE_MODIFIED[key],
         'isPartOf': {'@id': SITE + '/#website'}, 'publisher': {'@id': SITE + '/#org'}, 'about': {'@id': SITE + '/#app'}},
    ] + list(extra_ld)
    ld_html = '\n'.join(jsonld(o) for o in ld)
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
{alts}<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="SNYPD">
<meta property="og:locale" content="{u['locale']}">
<meta property="og:image" content="{SITE}/assets/og/og-v5.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="SNYPD - Vinted bot and monitor for new listing alerts">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0A0A0B">
<link rel="icon" type="image/png" sizes="192x192" href="/assets/icons/icon-192.png">
<link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/dm-mono-400-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts/dm-mono.css">
<link rel="preload" href="/assets/home/CabinetGrotesk-Black.woff2" as="font" type="font/woff2" crossorigin="anonymous">
<style>{CSS}{COMPARE_CSS}</style>
{ld_html}
<!-- Cookie consent: Google Analytics and the Whop pixel load only after the visitor agrees -->
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
    <nav class="lg-links" aria-label="Main">{nav}</nav>
    {switch}
    <a class="lg-navlink lg-login" href="/login">{u['login']}</a>
    <a class="lg-cta" href="/signup">{u['start']}</a>
  </div>
</header>
<main>
  <div class="lg-head">
    <div class="lg-wrap lg-head-in">
      <span class="lg-eyebrow">{eyebrow}</span>
      <h1 class="lg-h1">{h1}</h1>
      <span class="lg-meta">{u['updated']} <time datetime="{PAGE_MODIFIED[key]}">{date_txt(PAGE_MODIFIED[key], lang)}</time> &middot; {u['by']}</span>
      <p class="lg-lead">{lead}</p>
      {head_extra}
    </div>
  </div>
  <div class="lg-wrap {grid_cls}">
    {toc_block}
    <article class="lg-doc">
{body}
    </article>
  </div>
</main>
<footer class="lg-foot">
  <div class="lg-wrap lg-foot-in">
    <div class="lg-foot-a">
      <small>{u['foot_tag']}</small>
      <span class="lg-foot-t">{u['foot_t']}</span>
      <span class="lg-foot-l">{foot}</span>
    </div>
    <nav class="lg-foot-l" aria-label="Legal" style="align-items:flex-start;">{u['legal']}</nav>
  </div>
</footer>
</body>
</html>
"""


def h1_plain(h):
    return html.unescape(h.replace('<br>', ' '))


def table(head, rows, us_row=None):
    th = ''.join('<th scope="col">%s</th>' % h for h in head)
    tr = []
    for i, r in enumerate(rows):
        cls = ' class="ct-us"' if us_row is not None and i == us_row else ''
        cells = '<th scope="row">%s</th>' % r[0] + ''.join('<td>%s</td>' % c for c in r[1:])
        tr.append('<tr%s>%s</tr>' % (cls, cells))
    return '<div class="ct-scroll"><table class="ct-table"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (th, ''.join(tr))


def faq_ld(pairs):
    return {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': html.unescape(a)}} for q, a in pairs]}


def faq_html(pairs):
    return ''.join('<h3>%s</h3><p>%s</p>' % (esc(q), a) for q, a in pairs)


def cta(lang):
    if lang == 'en':
        return ('<div class="lg-box lg-mint"><p><strong>Start with one search, free.</strong> No card, no time limit, no cap on notifications. '
                'Upgrade when you want it to keep watching with your dashboard closed.</p>'
                '<div class="ct-actions"><a class="ct-btn" href="/signup">START FREE</a>'
                '<a class="ct-btn ct-ghost" href="/plans">SEE PLANS</a></div></div>')
    return ('<div class="lg-box lg-mint"><p><strong>Commence avec une recherche, gratuitement.</strong> Sans carte, sans limite de durée ni de notifications. '
            'Passe à un plan payant quand tu veux que la surveillance continue tableau de bord fermé.</p>'
            '<p class="ct-note">L’inscription et le paiement sont pour l’instant en anglais.</p>'
            '<div class="ct-actions"><a class="ct-btn" href="/signup">COMMENCER GRATUITEMENT</a>'
            '<a class="ct-btn ct-ghost" href="/plans">VOIR LES TARIFS</a></div></div>')


# ------------------------------------------------------------------ shared facts
PLANS_ROWS = {
    'en': [['Free', '<span class="ct-num">&euro;0</span>', '1', 'No, only while your dashboard is open', 'No'],
           ['Kickstart', '<span class="ct-num">&euro;14.99</span>', '2', 'Yes, 24/7', 'No'],
           ['Pro', '<span class="ct-num">&euro;24.99</span>', '5', 'Yes, 24/7', 'Yes'],
           ['Elite', '<span class="ct-num">&euro;34.99</span>', '10', 'Yes, 24/7', 'Yes']],
    'fr': [['Free', '<span class="ct-num">0&nbsp;&euro;</span>', '1', 'Non, seulement tableau de bord ouvert', 'Non'],
           ['Kickstart', '<span class="ct-num">14,99&nbsp;&euro;</span>', '2', 'Oui, 24h/24', 'Non'],
           ['Pro', '<span class="ct-num">24,99&nbsp;&euro;</span>', '5', 'Oui, 24h/24', 'Oui'],
           ['Elite', '<span class="ct-num">34,99&nbsp;&euro;</span>', '10', 'Oui, 24h/24', 'Oui']],
}
PLANS_HEAD = {'en': ['PLAN', 'PER MONTH, VAT INCL.', 'ACTIVE SEARCHES', 'WATCHES WITH DASHBOARD CLOSED', 'MARKET REPORT'],
              'fr': ['PLAN', 'PAR MOIS, TVA INCLUSE', 'RECHERCHES ACTIVES', 'SURVEILLE TABLEAU DE BORD FERMÉ', 'MARKET REPORT']}

HELP435 = {'en': 'https://www.vinted.co.uk/help/435-save-your-searches', 'fr': 'https://www.vinted.fr/help/435'}
HELP433 = {'en': 'https://www.vinted.co.uk/help/433', 'fr': 'https://www.vinted.fr/help/433'}


# ------------------------------------------------------------------ page: vinted bot
def page_bot(lang):
    if lang == 'en':
        faq = [
            ('Does SNYPD buy items for me?', 'No. SNYPD finds new listings and alerts you. You open the listing on Vinted and buy or make an offer yourself, through Vinted’s normal checkout.'),
            ('Do I need to give SNYPD my Vinted password?', 'No. SNYPD never asks for your Vinted login and never signs in to your account. You only need an email address for your SNYPD account.'),
            ('How often does SNYPD check my search?', 'Every 30 seconds to 5 minutes. Searches that keep finding new items are checked more often, quiet ones less often. Speed is the same on every plan.'),
            ('Does it work on iPhone?', 'Yes, once SNYPD is added to your Home Screen: open snypd.store in Safari, tap Share, then Add to Home Screen, and turn on alerts in the installed app. Apple only allows web push for Home Screen apps. On Android, Windows and Mac, alerts work straight from the browser.'),
            ('Is there a free plan?', 'Yes. Free includes one search with no time limit and no card. It checks while your SNYPD dashboard is open; paid plans from &euro;14.99 a month keep checking 24/7 with it closed.'),
            ('Which Vinted countries does it work with?', 'Every Vinted site in Europe and the US, 26 in all: vinted.fr, vinted.be, vinted.de, vinted.nl, vinted.it, vinted.es, vinted.pl, vinted.co.uk, vinted.com and the rest. Paste a search link from the site you shop on; prices show in that site’s currency.'),
        ]
        body = f"""
<section id="answer">
  <h2>SNYPD in one paragraph</h2>
  <div class="lg-box lg-mint"><p>SNYPD is a Vinted alert bot for resellers. You paste a Vinted search link with your filters (brand, size, price, condition) and SNYPD checks that search every 30 seconds to 5 minutes. When a new listing matches, it appears in your dashboard and you get a push notification on your phone or computer. SNYPD never asks for your Vinted password, never signs in to your account, never buys and never messages sellers. The free plan runs one search while your dashboard is open; paid plans from &euro;14.99 a month keep watching 24/7.</p></div>
</section>
<section id="kinds">
  <h2>The three kinds of Vinted bot</h2>
  <p>&ldquo;Vinted bot&rdquo; covers tools that do very different things. What separates them is whether they act on your Vinted account.</p>
  <h3>ALERT BOTS</h3>
  <p>They watch your searches and tell you when something new matches. You buy yourself, so they have no reason to act on your Vinted account. SNYPD, Telvin Bot and Crazed are alert tools.</p>
  <h3>AUTOBUY AND AUTOCOP BOTS</h3>
  <p>They buy or check out for you. Buying on Vinted needs a logged-in account, so these tools act through yours; V-Tools, for example, states that you connect your own Vinted accounts. Souk, V-Tools and Resell Reserve sell autobuy features.</p>
  <h3>DO-IT-YOURSELF SCRIPTS</h3>
  <p>Open-source projects on GitHub that you host yourself, usually posting to Discord or Telegram. Free, but you run the server and fix it when Vinted changes something.</p>
  <p>Prices, channels and free plans of each tool are side by side in <a href="{SLUGS['compare']['en']}">Vinted bots compared</a>.</p>
</section>
<section id="how">
  <h2>How SNYPD works</h2>
  <ol>
    <li>In a browser, search on your Vinted site and set your filters: brand, size, price, condition.</li>
    <li>Copy the address from the browser bar. A search address contains <code>/catalog?</code>.</li>
    <li>Paste it into SNYPD, give it a short name and switch it on.</li>
    <li>SNYPD checks it every 30 seconds to 5 minutes. New matches go to your dashboard and, if you turned alerts on, to your phone or computer. Several finds close together arrive as one notification.</li>
    <li>Tap the alert. It opens the listing on Vinted, where you buy or make an offer.</li>
  </ol>
  {figure('feed', 'en')}
</section>
<section id="speed">
  <h2>How fast is it?</h2>
  <p>SNYPD checks each active search as often as every 30 seconds. Searches that keep producing new items stay at that pace; searches that go quiet slow down, up to about 5 minutes between checks, and speed back up as soon as they find something. The speed is the same on every plan: paying buys more searches and 24/7 watching, not faster checks.</p>
  <p>Some tools advertise alerts in milliseconds. SNYPD does not make that claim. What it does promise is that a paid search keeps running when your laptop is closed and your phone is in your pocket, which is when most finds are missed.</p>
</section>
<section id="pricing">
  <h2>What it costs</h2>
  {table(PLANS_HEAD['en'], PLANS_ROWS['en'])}
  <p>Billed monthly, cancel any time. The Market Report shows the typical Vinted asking price of an item by condition; see a sample in <a href="{SLUGS['prices']['en']}">Vinted prices</a>. Full details on <a href="/plans">the plans page</a>.</p>
</section>
<section id="account">
  <h2>What SNYPD needs from you</h2>
  <p>An email address for your SNYPD account. No Vinted password, no Vinted login and no browser extension. SNYPD reads public listings with its own systems: the same search results anyone can open on Vinted without an account.</p>
  <p>Because SNYPD never signs in as you, nothing it does happens on your Vinted account. When you buy, you buy through Vinted like any other buyer.</p>
</section>
<section id="faq">
  <h2>Questions</h2>
  {faq_html(faq)}
</section>
<section id="start">
  <h2>Try it on one search</h2>
  {cta('en')}
</section>"""
        return page('bot', 'en', 'Vinted Bot for New Listing Alerts, No Autobuy | SNYPD',
                    'SNYPD is a Vinted bot that watches your searches and sends a push alert when a matching listing appears. It never logs in, buys or messages for you.',
                    'VINTED BOT', 'A Vinted bot that alerts you and never touches your account.',
                    'Most Vinted bots are sold on buying for you, which means acting as you. SNYPD does the other part of the job: it keeps watching your Vinted searches and tells you when something new matches, so you decide and buy on Vinted yourself.',
                    [('answer', 'In one paragraph'), ('kinds', 'Three kinds of bot'), ('how', 'How it works'), ('speed', 'How fast'), ('pricing', 'What it costs'), ('account', 'Your Vinted account'), ('faq', 'Questions')],
                    body, [faq_ld(faq)])
    faq = [
        ('Est-ce que SNYPD achète à ma place ?', 'Non. SNYPD trouve les nouvelles annonces et t’alerte. Tu ouvres l’annonce sur Vinted et tu achètes ou fais une offre toi-même, avec le paiement normal de Vinted.'),
        ('Dois-je donner mon mot de passe Vinted ?', 'Non. SNYPD ne demande jamais tes identifiants Vinted et ne se connecte jamais à ton compte. Il te faut seulement une adresse e-mail pour ton compte SNYPD.'),
        ('À quelle fréquence SNYPD vérifie ma recherche ?', 'Toutes les 30 secondes à 5 minutes. Les recherches qui trouvent souvent de nouveaux articles sont vérifiées plus souvent, les recherches calmes moins souvent. La vitesse est la même pour tous les plans.'),
        ('Est-ce que ça marche sur iPhone ?', 'Oui, une fois SNYPD ajouté à l’écran d’accueil : ouvre snypd.store dans Safari, appuie sur Partager puis Sur l’écran d’accueil, et active les alertes dans l’app installée. Apple n’autorise les notifications web que pour les apps de l’écran d’accueil. Sur Android, Windows et Mac, les alertes marchent directement depuis le navigateur.'),
        ('Y a-t-il un plan gratuit ?', 'Oui. Le plan Free comprend une recherche, sans limite de durée et sans carte. Il vérifie tant que ton tableau de bord SNYPD est ouvert ; les plans payants, à partir de 14,99&nbsp;&euro; par mois, vérifient 24h/24 même fermé.'),
        ('Avec quels pays Vinted ça fonctionne ?', 'Tous les sites Vinted d’Europe et des États-Unis, 26 au total : vinted.fr, vinted.be, vinted.de, vinted.nl, vinted.it, vinted.es, vinted.pl, vinted.co.uk et vinted.com, entre autres. Colle un lien de recherche du site où tu achètes ; les prix s’affichent dans la devise de ce site.'),
    ]
    body = f"""
<section id="resume">
  <h2>SNYPD en un paragraphe</h2>
  <div class="lg-box lg-mint"><p>SNYPD est un bot d’alertes Vinted pour les revendeurs. Tu colles le lien d’une recherche Vinted avec tes filtres (marque, taille, prix, état) et SNYPD vérifie cette recherche toutes les 30 secondes à 5 minutes. Quand une nouvelle annonce correspond, elle apparaît dans ton tableau de bord et tu reçois une notification push sur ton téléphone ou ton ordinateur. SNYPD ne demande jamais ton mot de passe Vinted, ne se connecte jamais à ton compte, n’achète rien et n’envoie aucun message aux vendeurs. Le plan gratuit fait tourner une recherche tant que ton tableau de bord est ouvert ; les plans payants, à partir de 14,99&nbsp;&euro; par mois, surveillent 24h/24.</p></div>
</section>
<section id="types">
  <h2>Les trois types de bot Vinted</h2>
  <p>« Bot Vinted » désigne des outils qui font des choses très différentes. Ce qui les distingue : est-ce qu’ils agissent sur ton compte Vinted ?</p>
  <h3>BOTS D’ALERTES</h3>
  <p>Ils surveillent tes recherches et te préviennent quand un nouvel article correspond. Tu achètes toi-même, donc ils n’ont aucune raison d’agir sur ton compte Vinted. SNYPD, Telvin Bot et Crazed sont des outils d’alertes.</p>
  <h3>BOTS D’ACHAT AUTOMATIQUE (AUTOBUY, AUTOCOP)</h3>
  <p>Ils achètent ou passent commande à ta place. Acheter sur Vinted demande un compte connecté, donc ces outils agissent via le tien ; V-Tools, par exemple, indique que tu connectes tes propres comptes Vinted. Souk, V-Tools et Resell Reserve vendent de l’achat automatique.</p>
  <h3>SCRIPTS À HÉBERGER SOI-MÊME</h3>
  <p>Des projets open source sur GitHub que tu héberges toi-même, qui postent en général sur Discord ou Telegram. Gratuits, mais c’est toi qui gères le serveur et qui répares quand Vinted change quelque chose.</p>
  <p>Les prix, canaux d’alerte et plans gratuits de chaque outil sont côte à côte dans le <a href="{SLUGS['compare']['fr']}">comparatif des bots Vinted</a>.</p>
</section>
<section id="fonctionnement">
  <h2>Comment marche SNYPD</h2>
  <ol>
    <li>Dans un navigateur, fais ta recherche sur ton site Vinted et règle tes filtres : marque, taille, prix, état.</li>
    <li>Copie l’adresse dans la barre du navigateur. Une adresse de recherche contient <code>/catalog?</code>.</li>
    <li>Colle-la dans SNYPD, donne-lui un nom court et active-la.</li>
    <li>SNYPD la vérifie toutes les 30 secondes à 5 minutes. Les nouvelles annonces arrivent dans ton tableau de bord et, si tu as activé les alertes, sur ton téléphone ou ton ordinateur. Plusieurs trouvailles rapprochées arrivent en une seule notification.</li>
    <li>Appuie sur l’alerte. Elle ouvre l’annonce sur Vinted, où tu achètes ou fais une offre.</li>
  </ol>
  {figure('feed', 'fr')}
</section>
<section id="vitesse">
  <h2>C’est rapide ?</h2>
  <p>SNYPD vérifie chaque recherche active jusqu’à toutes les 30 secondes. Les recherches qui trouvent souvent de nouveaux articles gardent ce rythme ; celles qui deviennent calmes ralentissent, jusqu’à environ 5 minutes entre deux vérifications, et réaccélèrent dès qu’elles trouvent quelque chose. La vitesse est la même pour tous les plans : payer donne plus de recherches et une surveillance 24h/24, pas des vérifications plus rapides.</p>
  <p>Certains outils annoncent des alertes en millisecondes. SNYPD ne fait pas cette promesse. Ce qu’il promet, c’est qu’une recherche payante continue de tourner quand ton ordinateur est fermé et ton téléphone dans ta poche, c’est-à-dire au moment où l’on rate le plus d’affaires.</p>
</section>
<section id="prix">
  <h2>Combien ça coûte</h2>
  {table(PLANS_HEAD['fr'], PLANS_ROWS['fr'])}
  <p>Facturé chaque mois, résiliable à tout moment. Le Market Report montre le prix demandé typique d’un article sur Vinted selon son état ; un exemple dans <a href="{SLUGS['prices']['fr']}">Prix Vinted</a>. Tous les détails sur <a href="/plans">la page des tarifs</a> (en anglais).</p>
</section>
<section id="compte">
  <h2>Ce dont SNYPD a besoin</h2>
  <p>Une adresse e-mail pour ton compte SNYPD. Pas de mot de passe Vinted, pas de connexion Vinted, pas d’extension de navigateur. SNYPD lit les annonces publiques avec ses propres systèmes : les mêmes résultats de recherche que n’importe qui peut ouvrir sur Vinted sans compte.</p>
  <p>Comme SNYPD ne se connecte jamais à ta place, rien de ce qu’il fait ne se passe sur ton compte Vinted. Quand tu achètes, tu achètes sur Vinted comme n’importe quel acheteur.</p>
</section>
<section id="questions">
  <h2>Questions</h2>
  {faq_html(faq)}
</section>
<section id="essayer">
  <h2>Essaie sur une recherche</h2>
  {cta('fr')}
</section>"""
    return page('bot', 'fr', 'Bot Vinted d’alertes, sans achat automatique | SNYPD',
                'SNYPD est un bot Vinted qui surveille tes recherches et t’envoie une alerte push quand une annonce correspond. Sans accès à ton compte, sans achat auto.',
                'BOT VINTED', 'Un bot Vinted qui t’alerte, sans jamais toucher à ton compte.',
                'La plupart des bots Vinted se vendent sur l’achat automatique, donc sur le fait d’agir à ta place. SNYPD fait l’autre partie du travail : il surveille tes recherches Vinted et te prévient quand un nouvel article correspond. Tu décides et tu achètes toi-même sur Vinted.',
                [('resume', 'En un paragraphe'), ('types', 'Trois types de bot'), ('fonctionnement', 'Fonctionnement'), ('vitesse', 'Vitesse'), ('prix', 'Prix'), ('compte', 'Ton compte Vinted'), ('questions', 'Questions')],
                body, [faq_ld(faq)])


# ------------------------------------------------------------------ page: notifications
def page_notify(lang):
    if lang == 'en':
        body = f"""
<section id="answer">
  <h2>Short answer</h2>
  <div class="lg-box lg-mint"><p>Vinted&rsquo;s saved searches show a counter, not an alert. According to Vinted&rsquo;s help centre, a saved search shows a number with a plus sign (&ldquo;+N&rdquo;) for new items the next time you open the search bar, and the count resets when you look. Vinted&rsquo;s list of what triggers a notification does not include new matches for a saved search. To get a push notification for each new match, you need a tool that watches the search for you.</p></div>
</section>
<section id="vinted">
  <h2>What Vinted&rsquo;s saved searches do</h2>
  <p>Vinted&rsquo;s own help page says that, the next time you open the search bar, a saved search shows</p>
  <blockquote>&ldquo;a number with a plus indicating how many new items were listed&rdquo;<cite>Vinted Help Centre, <a href="{HELP435['en']}" rel="nofollow noopener">Save your searches</a></cite></blockquote>
  <ul>
    <li>You can save an unlimited number of searches.</li>
    <li>The counter resets each time you view the search.</li>
    <li>Saved searches you never open are removed after 6 months.</li>
  </ul>
  <p>Vinted&rsquo;s notifications page lists what does trigger a notification: members you follow listing new items, price drops and sales on items you favourited, favourites on your own items, new followers, feedback, messages and news from Vinted (<a href="{HELP433['en']}" rel="nofollow noopener">Managing your notifications</a>). New matches for a saved search are not on that list.</p>
  <p>Some third-party sites say Vinted sends occasional notifications for saved searches. Vinted does not document one, so this page does not assume one.</p>
</section>
<section id="enough">
  <h2>When Vinted&rsquo;s own tools are enough</h2>
  <ul>
    <li>You browse Vinted several times a day anyway: the counter tells you where to look.</li>
    <li>You want new items from one particular seller: follow them, and Vinted notifies you when they list.</li>
    <li>You are waiting for a price drop on one item: favourite it, and Vinted notifies you when the price is reduced.</li>
  </ul>
</section>
<section id="alerts">
  <h2>When you need real alerts</h2>
  <p>If you resell, the listings worth having can be gone before your next look at the counter. An alert tool checks the search for you and notifies you when something new matches, so you see it while it is still for sale.</p>
  <p>With SNYPD, that search is the same one you saved on Vinted:</p>
  <ol>
    <li>Open the search on Vinted in a browser, with your filters (brand, size, price, condition).</li>
    <li>Copy the address from the browser bar. It contains <code>/catalog?</code>.</li>
    <li>Paste it into SNYPD and switch it on.</li>
    <li>SNYPD checks it every 30 seconds to 5 minutes and sends a push notification to your phone or computer when a new listing matches. The alert opens the listing on Vinted.</li>
  </ol>
  <p>SNYPD never asks for your Vinted login. The free plan runs one search while your dashboard is open; paid plans from &euro;14.99 a month keep checking 24/7. More on how it works: <a href="{SLUGS['bot']['en']}">SNYPD, the Vinted alert bot</a>.</p>
  {figure('feed', 'en')}
</section>
<section id="iphone">
  <h2>Alerts on iPhone</h2>
  <p>Apple only allows web push notifications for web apps added to the Home Screen. Open snypd.store in Safari, tap Share, then Add to Home Screen, and turn on alerts from the installed app. On Android, Windows and Mac, alerts work straight from the browser.</p>
</section>
<section id="start">
  <h2>Try it on one search</h2>
  {cta('en')}
</section>"""
        return page('notify', 'en', 'How to Get Notified of New Vinted Listings | SNYPD',
                    'Vinted’s saved searches show a +N counter, not a push alert. What Vinted’s own help centre says, and how to get a notification for each new match.',
                    'VINTED NOTIFICATIONS', 'How to get notified when something new is listed on Vinted',
                    'Vinted lets you save searches, but it does not document a notification for new matches. Here is exactly what Vinted&rsquo;s help centre says, and how to get an alert on your phone for every new listing that matches.',
                    [('answer', 'Short answer'), ('vinted', 'What Vinted does'), ('enough', 'When that is enough'), ('alerts', 'Real alerts'), ('iphone', 'iPhone')],
                    body)
    body = f"""
<section id="reponse">
  <h2>Réponse courte</h2>
  <div class="lg-box lg-mint"><p>Les recherches sauvegardées de Vinted affichent un compteur, pas une alerte. Selon le centre d’aide de Vinted, une recherche sauvegardée affiche un nombre suivi d’un signe plus (« +N ») pour les nouveaux articles la prochaine fois que tu ouvres la barre de recherche, et le compteur revient à zéro quand tu consultes la recherche. La liste de Vinted de ce qui déclenche une notification ne contient pas les nouvelles annonces d’une recherche sauvegardée. Pour recevoir une notification push à chaque nouvelle annonce, il faut un outil qui surveille la recherche pour toi.</p></div>
</section>
<section id="vinted">
  <h2>Ce que font les recherches sauvegardées de Vinted</h2>
  <p>D’après la page d’aide de Vinted, la prochaine fois que tu ouvres la barre de recherche, une recherche sauvegardée affiche</p>
  <blockquote>« un nombre suivi d’un signe plus indiquant le nombre de nouveaux articles »<cite>Centre d’aide Vinted, <a href="{HELP435['fr']}" rel="nofollow noopener">Comment sauvegarder une recherche ?</a></cite></blockquote>
  <ul>
    <li>Tu peux sauvegarder un nombre illimité de recherches.</li>
    <li>Le compteur est remis à zéro à chaque fois que tu consultes la recherche.</li>
    <li>Les recherches sauvegardées que tu n’ouvres jamais sont retirées au bout de 6 mois.</li>
  </ul>
  <p>La page de Vinted sur les notifications liste ce qui en déclenche une : les membres que tu suis qui publient de nouveaux articles, les baisses de prix et les ventes des articles en favoris, les favoris sur tes articles, les nouveaux abonnés, les évaluations, les messages et les actualités de Vinted (<a href="{HELP433['fr']}" rel="nofollow noopener">Comment gérer tes notifications ?</a>). Les nouvelles annonces d’une recherche sauvegardée n’y figurent pas.</p>
  <p>Certains sites affirment que Vinted envoie parfois des notifications pour les recherches sauvegardées. Vinted n’en documente aucune, donc cette page n’en suppose aucune.</p>
</section>
<section id="suffisant">
  <h2>Quand les outils de Vinted suffisent</h2>
  <ul>
    <li>Tu vas sur Vinted plusieurs fois par jour de toute façon : le compteur te dit où regarder.</li>
    <li>Tu veux les nouveautés d’un vendeur précis : abonne-toi à lui, Vinted te prévient quand il publie.</li>
    <li>Tu attends une baisse de prix sur un article : mets-le en favori, Vinted te prévient quand le prix baisse.</li>
  </ul>
</section>
<section id="alertes">
  <h2>Quand il te faut de vraies alertes</h2>
  <p>Si tu revends, les annonces intéressantes peuvent être parties avant ton prochain coup d’œil au compteur. Un outil d’alertes vérifie la recherche pour toi et te prévient quand un nouvel article correspond, pour que tu le voies tant qu’il est encore en vente.</p>
  <p>Avec SNYPD, c’est la même recherche que celle que tu as sauvegardée sur Vinted :</p>
  <ol>
    <li>Ouvre la recherche sur Vinted dans un navigateur, avec tes filtres (marque, taille, prix, état).</li>
    <li>Copie l’adresse dans la barre du navigateur. Elle contient <code>/catalog?</code>.</li>
    <li>Colle-la dans SNYPD et active-la.</li>
    <li>SNYPD la vérifie toutes les 30 secondes à 5 minutes et envoie une notification push sur ton téléphone ou ton ordinateur quand une nouvelle annonce correspond. L’alerte ouvre l’annonce sur Vinted.</li>
  </ol>
  <p>SNYPD ne demande jamais tes identifiants Vinted. Le plan gratuit fait tourner une recherche tant que ton tableau de bord est ouvert ; les plans payants, à partir de 14,99&nbsp;&euro; par mois, vérifient 24h/24. Plus de détails : <a href="{SLUGS['bot']['fr']}">SNYPD, le bot d’alertes Vinted</a>.</p>
  {figure('feed', 'fr')}
</section>
<section id="iphone">
  <h2>Alertes sur iPhone</h2>
  <p>Apple n’autorise les notifications web que pour les web apps ajoutées à l’écran d’accueil. Ouvre snypd.store dans Safari, appuie sur Partager puis Sur l’écran d’accueil, et active les alertes dans l’app installée. Sur Android, Windows et Mac, les alertes marchent directement depuis le navigateur.</p>
</section>
<section id="essayer">
  <h2>Essaie sur une recherche</h2>
  {cta('fr')}
</section>"""
    return page('notify', 'fr', 'Alerte Vinted : être prévenu des nouvelles annonces | SNYPD',
                'Les recherches sauvegardées Vinted affichent un compteur +N, pas une alerte. Ce que dit Vinted, et comment être notifié de chaque nouvelle annonce.',
                'ALERTES VINTED', 'Être prévenu dès qu’une nouvelle annonce Vinted correspond à ta recherche',
                'Vinted permet de sauvegarder des recherches, mais ne documente aucune notification pour les nouvelles annonces. Voici exactement ce que dit le centre d’aide de Vinted, et comment recevoir une alerte sur ton téléphone pour chaque nouvelle annonce qui correspond.',
                [('reponse', 'Réponse courte'), ('vinted', 'Ce que fait Vinted'), ('suffisant', 'Quand ça suffit'), ('alertes', 'De vraies alertes'), ('iphone', 'iPhone')],
                body)


# ------------------------------------------------------------------ page: comparison
# Why SNYPD, then the side-by-side table. Every competitor fact is from that
# vendor's own homepage on COMPARE_CHECKED and is linked from its row.
# EU comparative-advertising rules (Directive 2006/114/EC; Belgian Code of
# Economic Law VI.17) allow naming competitors only when each comparison is
# objective, verifiable and not misleading: keep every claim checkable, write
# "not stated" (never "no") when a site is silent, and re-check before changing
# the date. Tanush chose the eight reasons on 2026-10-01; none use testimonials
# because none exist yet.
COMPARE_CHECKED = {'en': '1 October 2026', 'fr': '1er octobre 2026'}
COMPARE_CHECKED_SHORT = {'en': '1 OCT 2026', 'fr': '1ER OCT. 2026'}

COMPARE_CSS = r"""
.rs-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin: 0 0 18px; }
@media (max-width: 759.98px) { .rs-grid { grid-template-columns: minmax(0, 1fr); } }
.rs-card { border: 1px solid #1D1D20; background: #0C0C0D; padding: 18px 18px 16px; display: flex; flex-direction: column; gap: 9px; min-width: 0; }
.rs-card:first-child, .rs-card:nth-child(2) { border-color: rgba(0,229,160,.38); background: rgba(0,229,160,.05); }
.rs-num { font-size: 11px; letter-spacing: .14em; color: #00E5A0; }
.lg-doc .rs-title { margin: 0; font-family: 'Cabinet Grotesk', 'DM Mono', sans-serif; font-weight: 900; font-size: 21px; line-height: 1.08; letter-spacing: -.02em; color: #FFFFFF; }
.lg-doc .rs-card p { margin: 0; font-size: 12.5px; line-height: 1.7; }
.lg-doc .rs-card p.rs-proof { padding-top: 9px; border-top: 1px dashed #26262A; font-size: 11.5px; color: #8B9094; }
.rs-proof a { color: #00E5A0; }
.ct-yes { color: #00E5A0; }
.ct-table tbody tr.ct-us th, .ct-table tbody tr.ct-us td { color: #FFFFFF; border-top-color: rgba(0,229,160,.45); }
.ct-table tbody tr.ct-us th { box-shadow: inset 3px 0 0 #00E5A0; }
.ct-badge { display: inline-block; margin-left: 6px; padding: 2px 6px; font-size: 10px; letter-spacing: .1em; color: #0A0A0B; background: #00E5A0; vertical-align: 1px; }
.ct-table tbody th[scope="row"] { position: sticky; left: 0; z-index: 1; background: #0C0C0D; }
.ct-table thead th:first-child { position: sticky; left: 0; z-index: 2; background: #121214; }
.ct-table tbody tr.ct-us th[scope="row"] { background: #160C20; }
@media (max-width: 699.98px) { .ct-table tbody th { min-width: 118px; } }
.glance { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0 0; padding: 0; list-style: none; }
.glance li { font-size: 12px; letter-spacing: .04em; color: #FFFFFF; border: 1px solid rgba(0,229,160,.38); background: rgba(0,229,160,.06); padding: 8px 11px; }
.glance li span { color: #00E5A0; margin-right: 6px; }
.fit-list { list-style: none; padding: 0 !important; margin: 0 0 18px !important; display: flex; flex-direction: column; gap: 10px; }
.fit-list li { margin: 0 !important; padding: 12px 14px; border: 1px solid #1D1D20; background: #0C0C0D; }
.fit-list li strong { display: block; margin-bottom: 3px; }
.fit-list li.fit-yes { border-color: rgba(0,229,160,.38); }
.lg-fig { margin: 4px 0 20px; border: 1px solid #1D1D20; background: #0C0C0D; }
.lg-fig picture { display: block; }
.lg-fig img { display: block; width: 100%; height: auto; }
.lg-fig figcaption { padding: 10px 14px; border-top: 1px solid #1D1D20; font-size: 11.5px; line-height: 1.6; color: #8B9094; }
.lg-fig.fig-narrow { max-width: 520px; }
.fig-row { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; align-items: start; margin: 0 0 18px; }
.fig-row .lg-fig { margin: 0; max-width: none; }
@media (max-width: 759.98px) { .fig-row { grid-template-columns: minmax(0, 1fr); } }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0; }
.ct-duel { margin: 0 0 18px; }
.ct-duel label { display: flex; flex-direction: column; gap: 8px; margin: 0 0 10px; font-size: 11px; letter-spacing: .12em; color: #8B9094; }
.ct-duel select { font-family: inherit; font-size: 14px; color: #FFFFFF; background: #141416; border: 1px solid #3A3A40; border-radius: 0; padding: 0 12px; min-height: 46px; }
.ct-duel table { width: 100%; border-collapse: collapse; table-layout: fixed; border: 1px solid #1D1D20; }
.ct-duel th, .ct-duel td { text-align: left; vertical-align: top; padding: 11px 10px; border-top: 1px solid #1D1D20; font-size: 12px; line-height: 1.5; color: #B8BCBF; overflow-wrap: anywhere; }
.ct-duel thead th { border-top: 0; background: #121214; font-size: 11px; font-weight: 400; letter-spacing: .08em; color: #8B9094; }
.ct-duel thead th.d-us { color: #FFFFFF; }
.ct-duel tbody th { width: 28%; font-weight: 400; font-size: 11px; letter-spacing: .06em; color: #8B9094; }
.ct-duel td.d-us { color: #FFFFFF; background: rgba(162,0,255,.07); }
.ct-duel [data-t] { display: none; }
.ct-duel [data-t].on { display: table-cell; }
@media (min-width: 700px) { .ct-duel { display: none; } }
@media (max-width: 699.98px) { .ct-full { display: none; } }
"""

# Real screenshots of the live SNYPD dashboard, taken 2 October 2026 in a signed-in session.
# Listing photos belong to Vinted sellers and are blurred; nothing else is edited. Files: assets/seo/.
# Phones get their own capture (one card / the panel at phone width), because the desktop
# capture scaled to ~350px makes its text about 7px tall.
SHOTS = {
    'feed':   ('/assets/seo/snypd-feed.webp', 1400, 662, ('/assets/seo/snypd-feed-phone.webp', 396, 650), ''),
    'market': ('/assets/seo/snypd-market-report.webp', 781, 665, ('/assets/seo/snypd-market-report-phone.webp', 358, 653), ' fig-narrow'),
    'hunts':  ('/assets/seo/snypd-hunts.webp', 635, 674, ('/assets/seo/snypd-hunts-phone.webp', 350, 537), ' fig-narrow'),
}
SHOT_TEXT = {
    'en': {
        'feed': ('SNYPD dashboard feed showing new Vinted listings with price, price including Buyer Protection, condition and the time found',
                 'SNYPD&rsquo;s feed during a real session on 2 October 2026: new listings from one search, each with its price, the price including Vinted&rsquo;s Buyer Protection, its condition and when it was found. Photos are blurred because they belong to the sellers.'),
        'market': ('SNYPD Market Report for jordan 1 mid: typical asking price 45 euros from 975 listings, broken down by condition',
                   'A real Market Report for &ldquo;jordan 1 mid&rdquo; on 2 October 2026: a typical asking price of &euro;45 from 975 listings by 880 sellers, then the price for each condition.'),
        'hunts': ('List of SNYPD hunts, each a Vinted search on vinted.be, some live and some paused',
                  'Hunts in SNYPD: each one is a Vinted search link with its own filters, either live or paused. Screenshot from 2 October 2026.'),
    },
    'fr': {
        'feed': ('Flux du tableau de bord SNYPD avec de nouvelles annonces Vinted : prix, prix avec protection acheteurs, état et moment de la détection',
                 'Le flux SNYPD pendant une vraie session, le 2 octobre 2026 : de nouvelles annonces d’une même recherche, avec leur prix, le prix protection acheteurs de Vinted incluse, leur état et le moment où elles ont été trouvées. Photos floutées, car elles appartiennent aux vendeurs. Interface en anglais.'),
        'market': ('Market Report SNYPD pour jordan 1 mid : prix demandé typique de 45 euros sur 975 annonces, détaillé par état',
                   'Un vrai Market Report pour « jordan 1 mid », le 2 octobre 2026 : un prix demandé typique de 45 &euro; sur 975 annonces de 880 vendeurs, puis le prix pour chaque état. Interface en anglais.'),
        'hunts': ('Liste des recherches SNYPD, chacune une recherche Vinted sur vinted.be, certaines actives et d’autres en pause',
                  'Les recherches dans SNYPD : chacune est un lien de recherche Vinted avec ses propres filtres, active ou en pause. Capture du 2 octobre 2026, interface en anglais.'),
    },
}


def figure(key, lang):
    src, w, h, (psrc, pw, ph), extra = SHOTS[key]
    alt, cap = SHOT_TEXT[lang][key]
    return ('<figure class="lg-fig%s"><picture><source media="(max-width: 699.98px)" srcset="%s" width="%d" height="%d">'
            '<img src="%s" alt="%s" width="%d" height="%d" loading="lazy" decoding="async"></picture><figcaption>%s</figcaption></figure>'
            % (extra, psrc, pw, ph, src, esc(alt), w, h, cap))


# One row per tool, cells per language: (en, fr). Order: tool, type, price data,
# account, alerts arrive, refund, per month, free option.
def _c(en, fr=None):
    return (en, fr if fr is not None else en)

YES = '<span class="ct-yes">&#10003;</span> '
COMPETITORS = [
    {'name': ('SNYPD', 'SNYPD'), 'url': SITE + '/plans', 'us': True, 'cells': [
        _c('Alerts + price data', 'Alertes + données de prix'),
        _c(YES + 'Market Report on Pro and Elite', YES + 'Market Report sur Pro et Elite'),
        _c(YES + 'Never: email only', YES + 'Jamais : e-mail seulement'),
        _c(YES + 'Push to phone and computer', YES + 'Push sur téléphone et ordinateur'),
        _c(YES + '14 days, full, after use', YES + '14 jours, intégral, même après usage'),
        _c('&euro;14.99&ndash;&euro;34.99 <small>VAT incl.</small>', '14,99&ndash;34,99&nbsp;&euro; <small>TVA incluse</small>'),
        _c(YES + '1 search, no time limit, no notification cap', YES + '1 recherche, sans limite de durée ni de notifications')]},
    # souk.to/en + souk.to/en/docs/pro-autobuy-billing ("after you link your Vinted account")
    {'name': ('Souk', 'Souk'), 'url': 'https://souk.to/en', 'cells': [
        _c('Alerts + autobuy', 'Alertes + achat automatique'),
        _c('Not on its site', 'Absent de son site'),
        _c('Yes, to autobuy: you link your Vinted account', 'Oui, pour l’achat auto : tu lies ton compte Vinted'),
        _c('Push', 'Push'),
        _c('One week', 'Une semaine'),
        _c('&euro;29&ndash;&euro;99', '29&ndash;99&nbsp;&euro;'),
        _c('&ldquo;Start for free&rdquo;, no details', '« Start for free », sans détail')]},
    # telvin-bot.com/en/ and /en/vinted-alerts/: free = 1 keyword alert, 100 notifications; notification only
    {'name': ('Telvin Bot', 'Telvin Bot'), 'url': 'https://www.telvin-bot.com/en/', 'cells': [
        _c('Alerts', 'Alertes'),
        _c('Not on its site', 'Absent de son site'),
        _c('Not stated', 'Non précisé'),
        _c('Telegram only', 'Telegram uniquement'),
        _c('Not on its homepage', 'Absent de sa page d’accueil'),
        _c('&euro;4.90&ndash;&euro;14.90', '4,90&ndash;14,90&nbsp;&euro;'),
        _c('1 keyword alert, 100 notifications', '1 alerte mot-clé, 100 notifications')]},
    # v-tools.com is the vendor; v-tools.eu is an affiliate site ("V-tools Affiliation"), never cite it
    {'name': ('V-Tools', 'V-Tools'), 'url': 'https://www.v-tools.com/', 'cells': [
        _c('Autobuy, multi-account', 'Achat automatique, multi-comptes'),
        _c('Own sales CRM, no market prices listed', 'CRM de ses ventes, pas de prix du marché indiqués'),
        _c('Yes: you connect your Vinted accounts', 'Oui : tu connectes tes comptes Vinted'),
        _c('Its own app feed', 'Le flux de son app'),
        _c('Not on its homepage', 'Absent de sa page d’accueil'),
        _c('&euro;29.99&ndash;&euro;79.99', '29,99&ndash;79,99&nbsp;&euro;'),
        _c('None stated', 'Aucune indiquée')]},
    # crazed.fr: Premium 4,99 and Crazy 9,99 both marked "Bientôt disponible" on 1 Oct 2026
    {'name': ('Crazed', 'Crazed'), 'url': 'https://crazed.fr/', 'cells': [
        _c('Alerts', 'Alertes'),
        _c('Not on its site', 'Absent de son site'),
        _c('Not stated', 'Non précisé'),
        _c('In its platform; push only on a plan marked &ldquo;coming soon&rdquo;', 'Dans sa plateforme ; push seulement sur un plan « bientôt disponible »'),
        _c('Not on its homepage', 'Absent de sa page d’accueil'),
        _c('Free only; paid plans &ldquo;coming soon&rdquo;', 'Gratuit seulement ; plans payants « bientôt disponibles »'),
        _c('3 alerts, 30 items a day', '3 alertes, 30 articles par jour')]},
    # resellreserve.co.uk (serves legacy.resellreserve.co.uk) + /refund-policy (updated 27 Sept 2026)
    {'name': ('Resell Reserve', 'Resell Reserve'), 'url': 'https://resellreserve.co.uk/', 'cells': [
        _c('Alerts + autobuy', 'Alertes + achat automatique'),
        _c('AI estimates, &pound;44.99 plan only', 'Estimations IA, plan à 44,99&nbsp;&pound; seulement'),
        _c('To buy, yes*', 'Pour acheter, oui*'),
        _c('Discord', 'Discord'),
        _c('Change of mind: only before you start using it', 'Changement d’avis : seulement avant de commencer à l’utiliser'),
        _c('&pound;19.99&ndash;&pound;44.99', '19,99&ndash;44,99&nbsp;&pound;'),
        _c('Free preview channels', 'Salons d’aperçu gratuits')]},
    # marktalert.nl/pricing: its own pages disagree on free alert count/validity, so only the check interval is used
    {'name': ('MarktAlert', 'MarktAlert'), 'url': 'https://marktalert.nl/pricing', 'cells': [
        _c('Alerts (also Marktplaats, 2dehands)', 'Alertes (aussi Marktplaats, 2dehands)'),
        _c('Price-drop alerts only', 'Alertes de baisse de prix seulement'),
        _c('Not stated', 'Non précisé'),
        _c('Telegram, app push, email, webhooks', 'Telegram, push dans l’app, e-mail, webhooks'),
        _c('Not on its site', 'Absent de son site'),
        _c('&euro;6.95&ndash;&euro;10.95', '6,95&ndash;10,95&nbsp;&euro;'),
        _c('Free plan, checks every 15 min', 'Plan gratuit, vérification toutes les 15 min')]},
    {'name': ('Vinted saved searches', 'Recherches sauvegardées Vinted'), 'url': None, 'cells': [
        _c('Built into Vinted', 'Intégré à Vinted'),
        _c('No', 'Non'),
        _c('Your own account', 'Ton propre compte'),
        _c('&ldquo;+N&rdquo; counter, no alert', 'Compteur « +N », pas d’alerte'),
        _c('&mdash;', '&mdash;'),
        _c('Free', 'Gratuit'),
        _c('Yes', 'Oui')]},
]


def compare_table(lang):
    L = 0 if lang == 'en' else 1
    head = {'en': ['TOOL', 'WHAT IT DOES', 'PRICE DATA', 'NEEDS YOUR VINTED ACCOUNT', 'ALERTS ARRIVE', 'REFUND', 'PER MONTH', 'FREE OPTION'],
            'fr': ['OUTIL', 'CE QU’IL FAIT', 'DONNÉES DE PRIX', 'BESOIN DE TON COMPTE VINTED', 'ALERTES VIA', 'REMBOURSEMENT', 'PAR MOIS', 'OPTION GRATUITE']}[lang]
    rows, us = [], None
    for i, c in enumerate(COMPETITORS):
        name = c['name'][L]
        url = c['url'] or HELP435[lang]
        label = '<a href="%s"%s>%s</a>' % (url, '' if c.get('us') else ' rel="nofollow noopener"', name)
        if c.get('us'):
            label += '<span class="ct-badge">%s</span>' % ('US' if lang == 'en' else 'NOUS')
            us = i
        rows.append([label] + [cell[L] for cell in c['cells']])
    return '<div class="ct-full">%s</div>' % table(head, rows, us_row=us)


DUEL_HEAD = {'en': ['WHAT IT DOES', 'PRICE DATA', 'NEEDS YOUR VINTED ACCOUNT', 'ALERTS ARRIVE', 'REFUND', 'PER MONTH', 'FREE OPTION'],
             'fr': ['CE QU’IL FAIT', 'DONNÉES DE PRIX', 'BESOIN DE TON COMPTE VINTED', 'ALERTES VIA', 'REMBOURSEMENT', 'PAR MOIS', 'OPTION GRATUITE']}


def compare_duel(lang):
    # Phones get SNYPD next to ONE other tool at a time (NN/g: at most 2 options side by side
    # on small screens). Same cells as the full table; the full table is hidden below 700px.
    L = 0 if lang == 'en' else 1
    us, others = COMPETITORS[0], COMPETITORS[1:]
    label = {'en': 'COMPARE SNYPD WITH', 'fr': 'COMPARER SNYPD AVEC'}[lang]
    cap = {'en': 'SNYPD compared with the tool you pick', 'fr': 'SNYPD comparé à l’outil choisi'}[lang]
    point = {'en': 'Point', 'fr': 'Critère'}[lang]
    opts = ''.join('<option value="%d"%s>%s</option>' % (i, ' selected' if i == 0 else '', c['name'][L]) for i, c in enumerate(others))
    heads = ''.join('<th scope="col" data-t="%d"%s><a href="%s" rel="nofollow noopener">%s</a></th>'
                    % (i, ' class="on"' if i == 0 else '', c['url'] or HELP435[lang], c['name'][L]) for i, c in enumerate(others))
    body = ''
    for j, h in enumerate(DUEL_HEAD[lang]):
        cells = ''.join('<td data-t="%d"%s>%s</td>' % (i, ' class="on"' if i == 0 else '', c['cells'][j][L]) for i, c in enumerate(others))
        body += '<tr><th scope="row">%s</th><td class="d-us">%s</td>%s</tr>' % (h, us['cells'][j][L], cells)
    js = ("<script>(function(){var s=document.getElementById('duel-pick');if(!s)return;"
          "function on(){var v=s.value;var c=document.querySelectorAll('.ct-duel [data-t]');"
          "for(var i=0;i<c.length;i++){c[i].className=c[i].getAttribute('data-t')===v?'on':'';}}"
          "s.addEventListener('change',on);on();})();</script>")
    return ('<div class="ct-duel"><label for="duel-pick">%s<select id="duel-pick">%s</select></label>'
            '<table><caption class="sr-only">%s</caption><thead><tr><th scope="col"><span class="sr-only">%s</span></th>'
            '<th scope="col" class="d-us">SNYPD</th>%s</tr></thead><tbody>%s</tbody></table></div>%s'
            % (label, opts, cap, point, heads, body, js))


def reasons(lang):
    if lang == 'en':
        R = [
            ('Price data is built in',
             'Pro (&euro;24.99 a month) includes the Market Report: type an item and see its typical Vinted asking price, split by condition. It shows no price at all when the data is too thin or too mixed to trust.',
             'Of the six other tools here, only Resell Reserve offers price estimates, and only on its &pound;44.99 Ultimate plan. See a sample: <a href="%s">Vinted prices, September 2026</a>.' % SLUGS['prices']['en']),
            ('Your Vinted account stays yours',
             'SNYPD needs an email address and nothing else: no Vinted password, no login, no browser extension. It never buys and never messages sellers. You buy through Vinted&rsquo;s normal checkout.',
             'Autobuy needs your account: Souk&rsquo;s docs say it works &ldquo;after you link your Vinted account&rdquo;, and V-Tools&rsquo; plans come with connected Vinted accounts. V-Tools&rsquo; own FAQ on bans: &ldquo;No tool can guarantee zero risk.&rdquo;'),
            ('Alerts land on your phone',
             'Push notifications go straight to your phone or computer. No Telegram, no Discord server, no extra account. Several finds close together arrive as one notification, not a buzz each.',
             'Telvin alerts only inside Telegram; Resell Reserve alerts in Discord. On iPhone, add SNYPD to your Home Screen once: Apple only allows web push for Home Screen apps.'),
            ('Every Vinted filter you set',
             'Paste a Vinted search link and SNYPD keeps every filter in it: brand, size, price, condition, colour, material, category. If you can filter it on Vinted, SNYPD keeps that filter.',
             'Souk builds alerts from its own form (brand, category, size, keywords, price). SNYPD works on %s: 26 sites, each in its own currency.' % MARKETS_TEXT['en']),
            ('14 days to change your mind',
             'Not happy with a paid plan? Email within 14 days of your first payment and you get it back in full. Prices include VAT, plans run month to month, cancel any time.',
             'Souk&rsquo;s site states one week. Resell Reserve&rsquo;s refund policy covers a change of mind only before you start using the service.'),
            ('Your finds, tracked to the profit',
             'Claim an item you bought and SNYPD keeps it in History: Holding, then Sold, with your realised profit added up for you. No spreadsheet next to your bot.',
             'Part of the SNYPD dashboard. Matches also carry a NEW badge, a DROP badge when the price fell since SNYPD first saw it, and Vinted&rsquo;s own suspicious-photo warning.'),
            ('Made by a reseller',
             'SNYPD is built by a Belgian sneaker reseller with 150+ sales and 4.5k followers, and run in the open with resellers in its Discord.',
             'Questions go to a person: <a href="mailto:%s">%s</a> or the <a href="%s">Discord</a>.' % (EMAIL, EMAIL, DISCORD)),
            ('A founding price, for life',
             'The first 100 accounts, free accounts included, keep Pro at &euro;24.99 a month for life.',
             'The number of places left is counted live on the <a href="/">homepage</a>.'),
        ]
    else:
        R = [
            ('Les données de prix sont incluses',
             'Pro (24,99&nbsp;&euro; par mois) inclut le Market Report : tape un article et vois son prix demandé typique sur Vinted, détaillé par état. Il n’affiche aucun prix quand les données sont trop maigres ou trop mélangées pour être fiables.',
             'Des six autres outils ici, seul Resell Reserve propose des estimations de prix, et seulement sur son plan Ultimate à 44,99&nbsp;&pound;. Un exemple : <a href="%s">Prix Vinted, septembre 2026</a>.' % SLUGS['prices']['fr']),
            ('Ton compte Vinted reste à toi',
             'SNYPD a besoin d’une adresse e-mail, rien d’autre : pas de mot de passe Vinted, pas de connexion, pas d’extension. Il n’achète jamais et n’écrit jamais aux vendeurs. Tu achètes avec le paiement normal de Vinted.',
             'L’achat automatique passe par ton compte : la doc de Souk dit qu’il fonctionne « after you link your Vinted account », et les plans de V-Tools incluent des comptes Vinted connectés. La FAQ de V-Tools sur les bannissements : « No tool can guarantee zero risk ».'),
            ('Les alertes arrivent sur ton téléphone',
             'Les notifications push arrivent directement sur ton téléphone ou ton ordinateur. Pas de Telegram, pas de serveur Discord, pas de compte en plus. Plusieurs trouvailles rapprochées arrivent en une seule notification.',
             'Telvin alerte uniquement dans Telegram ; Resell Reserve dans Discord. Sur iPhone, ajoute SNYPD à ton écran d’accueil une fois : Apple n’autorise les notifications web que pour les apps de l’écran d’accueil.'),
            ('Chaque filtre Vinted que tu règles',
             'Colle un lien de recherche Vinted et SNYPD garde tous ses filtres : marque, taille, prix, état, couleur, matière, catégorie. Si tu peux le filtrer sur Vinted, SNYPD garde ce filtre.',
             'Souk crée les alertes depuis son propre formulaire (marque, catégorie, taille, mots-clés, prix). SNYPD fonctionne sur %s : 26 sites, chacun dans sa devise.' % MARKETS_TEXT['fr']),
            ('14 jours pour changer d’avis',
             'Pas convaincu par un plan payant ? Écris dans les 14 jours suivant ton premier paiement et tu es remboursé en totalité. Prix TVA incluse, plans au mois, résiliables à tout moment.',
             'Le site de Souk indique une semaine. La politique de Resell Reserve ne rembourse un changement d’avis qu’avant de commencer à utiliser le service.'),
            ('Tes trouvailles, suivies jusqu’au bénéfice',
             'Marque un article acheté et SNYPD le garde dans History : Holding, puis Sold, avec ton bénéfice réalisé calculé pour toi. Plus besoin d’un tableur à côté de ton bot.',
             'Inclus dans le tableau de bord SNYPD. Les annonces portent aussi un badge NEW, un badge DROP quand le prix a baissé depuis que SNYPD l’a vue, et l’avertissement de Vinted sur les photos suspectes.'),
            ('Créé par un revendeur',
             'SNYPD est créé par un revendeur de sneakers belge, avec plus de 150 ventes et 4,5k abonnés, et développé au grand jour avec des revendeurs sur son Discord.',
             'Tes questions arrivent à une vraie personne : <a href="mailto:%s">%s</a> ou le <a href="%s">Discord</a>.' % (EMAIL, EMAIL, DISCORD)),
            ('Un prix fondateur, à vie',
             'Les 100 premiers comptes, gratuits compris, gardent Pro à 24,99&nbsp;&euro; par mois à vie.',
             'Le nombre de places restantes est affiché en direct sur la <a href="/">page d’accueil</a>.'),
        ]
    cards = ''.join('<div class="rs-card"><span class="rs-num">%02d</span><h3 class="rs-title">%s</h3><p>%s</p><p class="rs-proof">%s</p></div>' % (i + 1, t, b, p)
                    for i, (t, b, p) in enumerate(R))
    return '<div class="rs-grid">%s</div>' % cards


def page_compare(lang):
    tbl = compare_table(lang)
    if lang == 'en':
        body = f"""
<section id="disclosure">
  <div class="lg-box lg-mint"><p><strong>We make SNYPD, so we&rsquo;re not neutral.</strong> Every fact about another tool on this page comes from that tool&rsquo;s own website, checked on {COMPARE_CHECKED['en']}, and is linked in the table. Prices change: check before you pay. Spotted something out of date? Email <a href="mailto:{EMAIL}">{EMAIL}</a> and it gets fixed.</p></div>
</section>
<section id="reasons">
  <h2>8 reasons resellers choose SNYPD</h2>
  {reasons('en')}
  <div class="fig-row">{figure('market', 'en')}{figure('hunts', 'en')}</div>
</section>
<section id="table">
  <h2>SNYPD and six other Vinted bots, side by side</h2>
  {tbl}
  {compare_duel('en')}
  <p class="ct-note">* Buying on Vinted needs a logged-in account, so any autobuy feature acts through yours; Resell Reserve&rsquo;s homepage doesn&rsquo;t say how it connects to it. &ldquo;Not stated&rdquo;, &ldquo;not on its site&rdquo; and &ldquo;not on its homepage&rdquo; mean we couldn&rsquo;t find it on that tool&rsquo;s public pages, not proof it doesn&rsquo;t exist.</p>
</section>
<section id="others">
  <h2>What other tools do better</h2>
  <p>No tool is best at everything. Three things other Vinted bots offer that SNYPD does not, from each tool&rsquo;s own site:</p>
  <ul class="fit-list">
    <li><strong>They can buy for you.</strong>Souk, V-Tools and Resell Reserve sell autobuy. Buying on Vinted needs a logged-in account, so those features act through yours. SNYPD never signs in as you, so every purchase stays your decision, made on Vinted.</li>
    <li><strong>They post alerts in Telegram or Discord.</strong>Telvin sends alerts in Telegram, Resell Reserve in Discord, MarktAlert by Telegram, email or webhooks. SNYPD sends push notifications to your phone or computer only: no extra app or server to join, but no Telegram or Discord option.</li>
    <li><strong>Their first paid plan costs less.</strong>Telvin starts at &euro;4.90 a month and MarktAlert at &euro;6.95. SNYPD&rsquo;s first paid plan, Kickstart, is &euro;14.99 and watches 2 searches 24/7; the Market Report starts with Pro at &euro;24.99.</li>
  </ul>
</section>
<section id="speed">
  <h2>What about speed?</h2>
  <p>Telvin advertises alerts in 750 ms, Resell Reserve detection in under 0.15 s, V-Tools detection &ldquo;in a few milliseconds&rdquo;, and Crazed &ldquo;real time&rdquo; on a plan it lists as coming soon. Those are each vendor&rsquo;s own figures, measured in their own way, so they can&rsquo;t be compared with each other, or with SNYPD.</p>
  <p>SNYPD checks each search every 30 seconds to 5 minutes, faster on searches that keep finding things, and the same on every plan. What it adds is reach: paid searches keep running 24/7 with your laptop closed, and the alert finds you on your phone wherever you are.</p>
</section>
<section id="fit">
  <h2>Is SNYPD right for you?</h2>
  <ul class="fit-list">
    <li class="fit-yes"><strong>Yes, if you want to judge every deal yourself.</strong>You see the listing first, check it against real Vinted price data, and buy it on Vinted without handing over your account.</li>
    <li><strong>Not if you want a bot to buy for you.</strong>Automatic buying needs a tool that operates your Vinted account, such as Souk, V-Tools or Resell Reserve.</li>
    <li><strong>Also buying on Marktplaats or 2dehands?</strong>MarktAlert covers those. SNYPD is Vinted only.</li>
  </ul>
</section>
<section id="start">
  <h2>Try it on one search</h2>
  {cta('en')}
</section>"""
        return page('compare', 'en', 'Best Vinted Bot in 2026? 7 Bots Compared | SNYPD',
                    'SNYPD vs Souk, Telvin, V-Tools, Crazed, Resell Reserve and MarktAlert: price data, account safety, phone alerts and refunds, each fact from the tool’s own site.',
                    'VINTED BOTS COMPARED &middot; CHECKED ' + COMPARE_CHECKED_SHORT['en'], 'Why resellers pick SNYPD over other Vinted bots',
                    'SNYPD alerts you to new Vinted listings, shows the typical Vinted asking price of what you&rsquo;re looking at, and never touches your Vinted account. Here is how that compares with six other Vinted bots, point by point, with the source for every fact.',
                    None, body, head_extra='<ul class="glance" aria-label="SNYPD at a glance"><li><span>&#10003;</span>Price data included</li><li><span>&#10003;</span>No Vinted login, ever</li><li><span>&#10003;</span>Alerts on your phone</li><li><span>&#10003;</span>14-day refund</li></ul>')
    body = f"""
<section id="transparence">
  <div class="lg-box lg-mint"><p><strong>SNYPD est notre outil, donc cette page n’est pas neutre.</strong> Chaque information sur un autre outil vient du site de cet outil, vérifié le {COMPARE_CHECKED['fr']}, avec un lien dans le tableau. Les prix changent : vérifie avant de payer. Une info n’est plus à jour ? Écris à <a href="mailto:{EMAIL}">{EMAIL}</a> et elle sera corrigée.</p></div>
</section>
<section id="raisons">
  <h2>8 raisons de choisir SNYPD</h2>
  {reasons('fr')}
  <div class="fig-row">{figure('market', 'fr')}{figure('hunts', 'fr')}</div>
</section>
<section id="tableau">
  <h2>SNYPD et six autres bots Vinted, côte à côte</h2>
  {tbl}
  {compare_duel('fr')}
  <p class="ct-note">* Acheter sur Vinted demande un compte connecté, donc toute fonction d’achat automatique passe par le tien ; la page d’accueil de Resell Reserve ne dit pas comment elle s’y connecte. « Non précisé », « absent de son site » et « absent de sa page d’accueil » veulent dire que nous ne l’avons pas trouvé sur les pages publiques de l’outil, pas que cela n’existe pas.</p>
</section>
<section id="autres">
  <h2>Ce que d’autres outils font mieux</h2>
  <p>Aucun outil n’est le meilleur en tout. Trois choses que d’autres bots Vinted proposent et pas SNYPD, d’après le site de chaque outil :</p>
  <ul class="fit-list">
    <li><strong>Ils peuvent acheter à ta place.</strong>Souk, V-Tools et Resell Reserve vendent de l’achat automatique. Acheter sur Vinted demande un compte connecté, donc ces fonctions passent par le tien. SNYPD ne se connecte jamais à ta place : chaque achat reste ta décision, sur Vinted.</li>
    <li><strong>Ils envoient les alertes dans Telegram ou Discord.</strong>Telvin alerte dans Telegram, Resell Reserve dans Discord, MarktAlert par Telegram, e-mail ou webhooks. SNYPD envoie uniquement des notifications push sur ton téléphone ou ton ordinateur : pas d’app ni de serveur en plus à rejoindre, mais pas d’option Telegram ou Discord.</li>
    <li><strong>Leur premier plan payant coûte moins cher.</strong>Telvin commence à 4,90 &euro; par mois et MarktAlert à 6,95 &euro;. Le premier plan payant de SNYPD, Kickstart, coûte 14,99 &euro; et surveille 2 recherches 24h/24 ; le Market Report commence avec Pro à 24,99 &euro;.</li>
  </ul>
</section>
<section id="vitesse">
  <h2>Et la vitesse ?</h2>
  <p>Telvin annonce des alertes en 750 ms, Resell Reserve une détection en moins de 0,15 s, V-Tools une détection « in a few milliseconds », et Crazed du « temps réel » sur un plan annoncé comme bientôt disponible. Ce sont les chiffres de chaque éditeur, mesurés à sa façon, donc impossibles à comparer entre eux ou avec SNYPD.</p>
  <p>SNYPD vérifie chaque recherche toutes les 30 secondes à 5 minutes, plus souvent sur les recherches qui trouvent beaucoup, et pareil pour tous les plans. Ce qu’il apporte, c’est la portée : les recherches payantes tournent 24h/24 ordinateur fermé, et l’alerte te trouve sur ton téléphone où que tu sois.</p>
</section>
<section id="pour-qui">
  <h2>SNYPD est-il fait pour toi ?</h2>
  <ul class="fit-list">
    <li class="fit-yes"><strong>Oui, si tu veux juger chaque affaire toi-même.</strong>Tu vois l’annonce en premier, tu la compares aux vrais prix Vinted, et tu achètes sur Vinted sans confier ton compte.</li>
    <li><strong>Non, si tu veux qu’un bot achète à ta place.</strong>L’achat automatique demande un outil qui utilise ton compte Vinted, comme Souk, V-Tools ou Resell Reserve.</li>
    <li><strong>Tu achètes aussi sur Marktplaats ou 2dehands ?</strong>MarktAlert couvre ces sites. SNYPD ne couvre que Vinted.</li>
  </ul>
</section>
<section id="essayer">
  <h2>Essaie sur une recherche</h2>
  {cta('fr')}
</section>"""
    return page('compare', 'fr', 'Meilleur bot Vinted 2026 ? 7 bots comparés | SNYPD',
                'SNYPD face à Souk, Telvin, V-Tools, Crazed, Resell Reserve et MarktAlert : prix, compte, alertes, remboursement, d’après le site de chaque outil.',
                'COMPARATIF DES BOTS VINTED &middot; VÉRIFIÉ LE ' + COMPARE_CHECKED_SHORT['fr'], 'Pourquoi les revendeurs choisissent SNYPD plutôt qu’un autre bot Vinted',
                'SNYPD t’alerte des nouvelles annonces Vinted, te montre le prix demandé typique d’un article sur Vinted, et ne touche jamais à ton compte Vinted. Voici la comparaison avec six autres bots Vinted, point par point, avec la source de chaque information.',
                None, body, head_extra='<ul class="glance" aria-label="SNYPD en bref"><li><span>&#10003;</span>Données de prix incluses</li><li><span>&#10003;</span>Jamais de connexion Vinted</li><li><span>&#10003;</span>Alertes sur ton téléphone</li><li><span>&#10003;</span>Remboursement sous 14 jours</li></ul>')


# ------------------------------------------------------------------ page: prices
ITEMS = [  # query as run in the Market Report, display name, group
    ('jordan 1 mid', 'Air Jordan 1 Mid', 'sneakers'), ('nike dunk low', 'Nike Dunk Low', 'sneakers'),
    ('nike air force 1', 'Nike Air Force 1', 'sneakers'), ('air max 90', 'Nike Air Max 90', 'sneakers'),
    ('air max 95', 'Nike Air Max 95', 'sneakers'), ('adidas samba', 'adidas Samba', 'sneakers'),
    ('adidas gazelle', 'adidas Gazelle', 'sneakers'), ('adidas campus', 'adidas Campus', 'sneakers'),
    ('new balance 550', 'New Balance 550', 'sneakers'), ('new balance 9060', 'New Balance 9060', 'sneakers'),
    ('new balance 2002r', 'New Balance 2002R', 'sneakers'), ('salomon xt-6', 'Salomon XT-6', 'sneakers'),
    ('asics gel kayano', 'ASICS Gel-Kayano', 'sneakers'),
    ('stone island jumper', 'Stone Island jumper', 'clothing'), ('carhartt detroit jacket', 'Carhartt Detroit jacket', 'clothing'),
    ('arcteryx beta', 'Arc’teryx Beta', 'clothing'), ('patagonia fleece', 'Patagonia fleece', 'clothing'),
    ('the north face nuptse', 'The North Face Nuptse', 'clothing'), ('ralph lauren quarter zip', 'Ralph Lauren quarter zip', 'clothing'),
]
REFUSED = [('jordan 1 low', 'Air Jordan 1 Low'), ('jordan 4', 'Air Jordan 4'), ('yeezy 350', 'Yeezy 350')]


def money(cents, lang):
    whole = cents % 100 == 0
    if lang == 'en':
        s = '{:,}'.format(cents // 100) if whole else '{:,.2f}'.format(cents / 100)
        return '&euro;' + s
    s = '{:,}'.format(cents // 100) if whole else '{:,.2f}'.format(cents / 100)
    s = s.replace(',', ' ').replace('.', ',')
    return s + '&nbsp;&euro;'


def num(n, lang):
    return '{:,}'.format(n) if lang == 'en' else '{:,}'.format(n).replace(',', ' ')


def load_report():
    d = json.load(open(REPORT, encoding='utf-8'))
    by_q = {r['q']: r for r in d['results']}
    gen = datetime.datetime.fromisoformat(d['generated_at'].replace('Z', '+00:00'))
    return by_q, gen


def price_rows(lang):
    by_q, gen = load_report()
    rows, csv_rows = [], []
    for q, name, group in ITEMS:
        r = by_q[q]
        v = r['view']
        if not r['ok'] or v.get('display_verdict') != 'ok' or not v.get('show_headline'):
            sys.exit(f'{q}: not a trustworthy price in the report ({v.get("display_verdict")}); move it to REFUSED')
        typ, lo, hi = v['typical_cents'], v['range_cents']['low'], v['range_cents']['high']
        codes = {f['code'] for f in v.get('flags', [])}
        pct = v.get('outlier_pct')
        notes = []
        if 'outliers_high' in codes and pct is not None:
            notes.append(f'{pct:g}% of listings priced far above the rest (possible fakes or other models).' if lang == 'en' else
                         f'{str(pct).replace(".", ",")} % des annonces nettement plus chères que les autres (contrefaçons ou autres modèles possibles).')
        if 'price_skew_high' in codes:
            notes.append('Prices skew high.' if lang == 'en' else 'Prix tirés vers le haut.')
        if v['sample_size'] < 100:
            notes.append('Smaller sample: a rough guide.' if lang == 'en' else 'Échantillon plus petit : ordre de grandeur.')
        if not notes:
            notes.append('Consistent prices.' if lang == 'en' else 'Prix homogènes.')
        note = ' '.join(notes)
        rows.append([f'{name}<small>{"search" if lang == "en" else "recherche"}: {esc(q)}</small>',
                     f'<span class="ct-num">{money(typ, lang)}</span>',
                     f'<span class="ct-num">{money(lo, lang)}&ndash;{money(hi, lang)}</span>',
                     f'<span class="ct-num">{num(v["sample_size"], lang)}</span><small>{num(v["distinct_sellers"], lang)} {"sellers" if lang == "en" else "vendeurs"}</small>',
                     note])
        csv_rows.append([name, q, group, f'{typ/100:.2f}', f'{lo/100:.2f}', f'{hi/100:.2f}', v['sample_size'], v['distinct_sellers'], v.get('confidence'), pct if pct is not None else ''])
    refused = []
    for q, name in REFUSED:
        v = by_q[q]['view']
        if v.get('show_headline'):
            sys.exit(f'{q}: now has a price; move it to ITEMS')
        o = v.get('observed_cents') or {}
        refused.append((name, q, v['sample_size'], o.get('low'), o.get('high'), v.get('display_verdict')))
    first = by_q[ITEMS[0][0]]['view']
    return rows, csv_rows, refused, gen, first


def page_prices(lang):
    rows, csv_rows, refused, gen, first = price_rows(lang)
    f_typ, f_lo, f_hi = first['typical_cents'], first['range_cents']['low'], first['range_cents']['high']
    end = gen.date()
    start = end - datetime.timedelta(days=14)
    if lang == 'en':
        head = ['ITEM', 'TYPICAL ASKING PRICE', 'MIDDLE HALF OF PRICES', 'LISTINGS', 'NOTE']
        ref = ''.join(f'<li><strong>{n}</strong> ({num(c, "en")} listings, {money(lo, "en")} to {money(hi, "en")}): too spread out for one honest price.</li>' for n, q, c, lo, hi, vd in refused)
        dataset = {'@context': 'https://schema.org', '@type': 'Dataset', 'name': 'Typical Vinted asking prices for resale items, September 2026',
                   'description': 'Median asking price and interquartile range for 19 sneaker and streetwear searches, from listings SNYPD saw on vinted.be in the 14 days to 28 September 2026. Asking prices, not sold prices.',
                   'url': SITE + SLUGS['prices']['en'], 'temporalCoverage': f'{start.isoformat()}/{end.isoformat()}', 'isAccessibleForFree': True,
                   'creator': {'@id': SITE + '/#org'}, 'inLanguage': 'en', 'variableMeasured': ['median asking price (EUR)', '25th percentile (EUR)', '75th percentile (EUR)', 'number of listings', 'number of sellers'],
                   'distribution': [{'@type': 'DataDownload', 'encodingFormat': 'text/csv', 'contentUrl': SITE + '/' + REPORT_CSV}]}
        body = f"""
<section id="answer">
  <h2>Short answer</h2>
  <div class="lg-box lg-mint"><p>These are typical <strong>asking</strong> prices on Vinted, not sold prices: the median price of every listing SNYPD saw on vinted.be for each search in the 14 days to {end.day} September {end.year}, all sizes and conditions together. For example, an Air Jordan 1 Mid was typically listed at {money(f_typ, 'en')}, with the middle half of listings between {money(f_lo, 'en')} and {money(f_hi, 'en')}.</p></div>
</section>
<section id="table">
  <h2>September 2026 prices</h2>
  <h3>SNEAKERS</h3>
  {table(head, [r for r, (q, n, g) in zip(rows, ITEMS) if g == 'sneakers'])}
  <h3>CLOTHING</h3>
  {table(head, [r for r, (q, n, g) in zip(rows, ITEMS) if g == 'clothing'])}
  <p class="ct-note">Download the numbers: <a href="/{REPORT_CSV}">{REPORT_CSV}</a>. Figures come straight from SNYPD&rsquo;s Market Report, run on {end.day} September {end.year}.</p>
</section>
<section id="refused">
  <h2>Searches with no price</h2>
  <p>The Market Report refuses to give a single price when listings are too spread out: when the 75th-percentile price is more than three times the 25th-percentile price. That usually means one search is catching many different colourways, kids&rsquo; and adult sizes, or fakes. These three got no price this month:</p>
  <ul>{ref}</ul>
  <p>A narrower search, such as a specific colourway, usually gets a usable price.</p>
</section>
<section id="method">
  <h2>How these numbers are made</h2>
  <ul>
    <li><strong>Source.</strong> Listings SNYPD&rsquo;s systems saw on vinted.be while watching searches, in euros.</li>
    <li><strong>Window.</strong> Listings seen at least once between {start.day} and {end.day} September {end.year}. SNYPD keeps listing data for 14 days after it last sees a listing.</li>
    <li><strong>Matching.</strong> A listing counts when its title contains every word of the search. Garment words also match their usual synonyms (jumper, sweater, pull, trui), so a search is not split by language.</li>
    <li><strong>Typical price</strong> is the median. <strong>Middle half</strong> is the 25th to 75th percentile, so a quarter of listings are cheaper and a quarter dearer.</li>
    <li><strong>Refusals.</strong> On this page, no price is shown when there are fewer than 8 listings, when prices are too spread out, or when one seller has more than 40% of the listings.</li>
  </ul>
  <h3>LIMITS</h3>
  <ul>
    <li>Asking prices are what sellers want, not what buyers paid.</li>
    <li>All conditions and sizes are mixed. The Market Report in Pro and Elite breaks prices down by condition.</li>
    <li>Fakes are not removed. The notes column flags searches where many listings sit far above the rest.</li>
  </ul>
</section>
<section id="report">
  <h2>Price any item yourself</h2>
  <p>The Market Report in SNYPD Pro and Elite does this for any search you type, broken down by condition, and refuses to show a number when the data is too thin or too mixed. Pro is &euro;24.99 a month and also watches 5 Vinted searches 24/7. <a href="/plans">See plans</a>.</p>
  {figure('market', 'en')}
  {cta('en')}
</section>"""
        out = page('prices', 'en', 'Vinted Prices, Sept 2026: Typical Asking Prices | SNYPD',
                   'Typical Vinted asking prices for 19 sneakers and streetwear items in September 2026: median, middle half and number of listings, from real vinted.be listings.',
                   'VINTED PRICES &middot; SEPTEMBER 2026', 'What sneakers and streetwear are listed for on Vinted',
                   f'Median asking prices for 19 resale items, from listings SNYPD saw on vinted.be in the 14 days to {end.day} September {end.year}. The number of listings behind each price is in the table. This is the September 2026 edition. Asking prices, not sold prices.',
                   [('answer', 'Short answer'), ('table', 'September prices'), ('refused', 'No price'), ('method', 'Method and limits'), ('report', 'Price any item')],
                   body, [dataset])
        return out, csv_rows
    head = ['ARTICLE', 'PRIX DEMANDÉ TYPIQUE', 'MOITIÉ CENTRALE DES PRIX', 'ANNONCES', 'REMARQUE']
    ref = ''.join(f'<li><strong>{n}</strong> ({num(c, "fr")} annonces, de {money(lo, "fr")} à {money(hi, "fr")}) : trop dispersé pour un prix honnête.</li>' for n, q, c, lo, hi, vd in refused)
    dataset = {'@context': 'https://schema.org', '@type': 'Dataset', 'name': 'Prix demandés typiques sur Vinted pour des articles de revente, septembre 2026',
               'description': 'Prix demandé médian et écart interquartile pour 19 recherches de sneakers et streetwear, d’après les annonces vues par SNYPD sur vinted.be sur les 14 jours au 28 septembre 2026. Prix demandés, pas prix de vente.',
               'url': SITE + SLUGS['prices']['fr'], 'temporalCoverage': f'{start.isoformat()}/{end.isoformat()}', 'isAccessibleForFree': True,
               'creator': {'@id': SITE + '/#org'}, 'inLanguage': 'fr',
               'distribution': [{'@type': 'DataDownload', 'encodingFormat': 'text/csv', 'contentUrl': SITE + '/' + REPORT_CSV}]}
    body = f"""
<section id="reponse">
  <h2>Réponse courte</h2>
  <div class="lg-box lg-mint"><p>Ce sont des prix <strong>demandés</strong> typiques sur Vinted, pas des prix de vente : le prix médian de toutes les annonces vues par SNYPD sur vinted.be pour chaque recherche, sur les 14 jours au {end.day} septembre {end.year}, toutes tailles et tous états confondus. Par exemple, une Air Jordan 1 Mid était typiquement mise en vente à {money(f_typ, 'fr')}, la moitié centrale des annonces se situant entre {money(f_lo, 'fr')} et {money(f_hi, 'fr')}.</p></div>
</section>
<section id="tableau">
  <h2>Les prix de septembre 2026</h2>
  <h3>SNEAKERS</h3>
  {table(head, [r for r, (q, n, g) in zip(rows, ITEMS) if g == 'sneakers'])}
  <h3>VÊTEMENTS</h3>
  {table(head, [r for r, (q, n, g) in zip(rows, ITEMS) if g == 'clothing'])}
  <p class="ct-note">Télécharger les chiffres : <a href="/{REPORT_CSV}">{REPORT_CSV}</a> (en anglais). Les chiffres viennent directement du Market Report de SNYPD, calculé le {end.day} septembre {end.year}.</p>
</section>
<section id="sans-prix">
  <h2>Recherches sans prix</h2>
  <p>Le Market Report refuse de donner un prix unique quand les annonces sont trop dispersées : quand le prix du 75e centile dépasse trois fois celui du 25e centile. En général, la recherche attrape alors plein de coloris différents, des tailles enfant et adulte, ou des contrefaçons. Ces trois recherches n’ont pas eu de prix ce mois-ci :</p>
  <ul>{ref}</ul>
  <p>Une recherche plus précise, par exemple un coloris précis, obtient en général un prix utilisable.</p>
</section>
<section id="methode">
  <h2>Comment ces chiffres sont calculés</h2>
  <ul>
    <li><strong>Source.</strong> Les annonces vues par les systèmes de SNYPD sur vinted.be en surveillant des recherches, en euros.</li>
    <li><strong>Période.</strong> Annonces vues au moins une fois entre le {start.day} et le {end.day} septembre {end.year}. SNYPD garde les données d’une annonce 14 jours après l’avoir vue pour la dernière fois.</li>
    <li><strong>Correspondance.</strong> Une annonce compte quand son titre contient tous les mots de la recherche. Les mots de vêtements correspondent aussi à leurs synonymes courants (jumper, sweater, pull, trui), pour que la langue ne coupe pas une recherche en deux.</li>
    <li><strong>Prix typique</strong> : la médiane. <strong>Moitié centrale</strong> : du 25e au 75e centile, donc un quart des annonces est moins cher et un quart plus cher.</li>
    <li><strong>Refus.</strong> Sur cette page, aucun prix quand il y a moins de 8 annonces, quand les prix sont trop dispersés, ou quand un seul vendeur a plus de 40 % des annonces.</li>
  </ul>
  <h3>LIMITES</h3>
  <ul>
    <li>Un prix demandé est ce que le vendeur veut, pas ce que l’acheteur a payé.</li>
    <li>Tous les états et toutes les tailles sont mélangés. Le Market Report de Pro et Elite détaille les prix par état.</li>
    <li>Les contrefaçons ne sont pas retirées. La colonne Remarque signale les recherches où beaucoup d’annonces sont bien plus chères que les autres.</li>
  </ul>
</section>
<section id="market-report">
  <h2>Estime le prix de n’importe quel article</h2>
  <p>Le Market Report de SNYPD Pro et Elite fait ce calcul pour n’importe quelle recherche, détaillé par état, et refuse d’afficher un chiffre quand les données sont trop maigres ou trop mélangées. Pro coûte 24,99&nbsp;&euro; par mois et surveille aussi 5 recherches Vinted 24h/24. <a href="/plans">Voir les tarifs</a>.</p>
  {figure('market', 'fr')}
  {cta('fr')}
</section>"""
    out = page('prices', 'fr', 'Prix Vinted septembre 2026 : prix demandés typiques | SNYPD',
               'Prix demandés typiques sur Vinted pour 19 sneakers et vêtements streetwear, septembre 2026 : médiane, moitié centrale et nombre d’annonces vinted.be.',
               'PRIX VINTED &middot; SEPTEMBRE 2026', 'À quel prix les sneakers et le streetwear sont mis en vente sur Vinted',
               f'Prix demandés médians pour 19 articles de revente, d’après les annonces vues par SNYPD sur vinted.be sur les 14 jours au {end.day} septembre {end.year}. Le nombre d’annonces derrière chaque prix est dans le tableau. Édition de septembre 2026. Prix demandés, pas prix de vente.',
               [('reponse', 'Réponse courte'), ('tableau', 'Prix de septembre'), ('sans-prix', 'Sans prix'), ('methode', 'Méthode et limites'), ('market-report', 'Estimer un article')],
               body, [dataset])
    return out, csv_rows


def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = text.encode('utf-8')
    if not os.path.isfile(path) or open(path, 'rb').read() != data:
        open(path, 'wb').write(data)
    print('wrote', rel, len(data), 'bytes')


if __name__ == '__main__':
    for lang in (('en', 'fr') if FR_LIVE else ('en',)):
        prefix = '' if lang == 'en' else 'fr/'
        write(prefix + SLUGS['bot'][lang].rsplit('/', 1)[1] + '.html', page_bot(lang))
        write(prefix + SLUGS['notify'][lang].rsplit('/', 1)[1] + '.html', page_notify(lang))
        write(prefix + SLUGS['compare'][lang].rsplit('/', 1)[1] + '.html', page_compare(lang))
        html_out, csv_rows = page_prices(lang)
        write(prefix + SLUGS['prices'][lang].rsplit('/', 1)[1] + '.html', html_out)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator='\n')
    w.writerow(['item', 'search', 'group', 'typical_asking_eur', 'p25_eur', 'p75_eur', 'listings', 'sellers', 'confidence', 'outlier_high_pct'])
    w.writerows(csv_rows)
    buf.write('# Source: SNYPD Market Report (median asking price, not sold price), listings seen on vinted.be in the 14 days to 2026-09-28. https://www.snypd.store/vinted-prices\n')
    write(REPORT_CSV, buf.getvalue())
