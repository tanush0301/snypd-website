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
    'deals':   {'en': '/vinted-deals'},  # English only for now (decided 2026-10-02)
    'fees':    {'en': '/vinted-fees',                'fr': '/fr/frais-vinted'},
    'monitor': {'en': '/vinted-monitor',             'fr': '/fr/monitor-vinted'},
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
               foot=[('bot', 'Vinted bot'), ('monitor', 'Vinted monitor'), ('notify', 'Vinted notifications'), ('compare', 'Vinted bots compared'), ('prices', 'Vinted prices'),
                     ('deals', 'Vinted deals'), ('fees', 'Vinted fees'), ('/faq', 'FAQ'), ('/support', 'Support'), (DISCORD, 'Discord')],
               legal='<a href="/cookies">Cookies</a><a href="/cookies" data-cookie-settings>Cookie settings</a>',
               home='Home'),
    'fr': dict(locale='fr_FR', toc='SUR CETTE PAGE', updated='Mis à jour le', by='Par SNYPD, créé par un revendeur de sneakers belge',
               nav=[('bot', 'BOT VINTED'), ('prices', 'PRIX VINTED'), ('/plans', 'TARIFS'), (DISCORD, 'DISCORD')],
               login='CONNEXION', start='COMMENCER', switch=('EN', 'en', 'English version'),
               foot_tag='SNYPD &middot; NON AFFILIÉ À VINTED', foot_t='Lit uniquement les annonces publiques.',
               foot=[('bot', 'Bot Vinted'), ('monitor', 'Monitor Vinted'), ('notify', 'Alertes Vinted'), ('compare', 'Comparatif des bots Vinted'), ('prices', 'Prix Vinted'), ('fees', 'Frais Vinted'),
                     ('/faq', 'FAQ (anglais)'), ('/support', 'Support (anglais)'), (DISCORD, 'Discord')],
               legal='<a href="/cookies">Cookies</a><a href="/cookies" data-cookie-settings>Paramètres des cookies</a>',
               home='Accueil'),
}
# Last real content change per page (shown as 'Updated' and used as dateModified).
PAGE_MODIFIED = {'bot': '2026-10-03', 'notify': '2026-10-02', 'compare': '2026-10-03', 'prices': '2026-10-02', 'deals': '2026-10-02', 'fees': '2026-10-02',
                 'monitor': '2026-10-03'}
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
    has_fr = FR_LIVE and 'fr' in SLUGS[key]
    if has_fr:
        alts = ''.join('<link rel="alternate" hreflang="%s" href="%s%s">\n' % (l, SITE, SLUGS[key][l]) for l in ('en', 'fr'))
        alts += '<link rel="alternate" hreflang="x-default" href="%s%s">\n' % (SITE, SLUGS[key]['en'])
    switch = ('<a class="lg-navlink" href="%s" hreflang="%s" lang="%s" title="%s">%s</a>'
              % (SLUGS[key][other], other, other, u['switch'][2], u['switch'][0])) if has_fr else ''
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
  <div class="lg-box lg-mint"><p>SNYPD is a Vinted alert bot, also called a Vinted monitor, for resellers. You paste a Vinted search link with your filters (brand, size, price, condition) and SNYPD checks that search every 30 seconds to 5 minutes. When a new listing matches, it appears in your dashboard and you get a push notification on your phone or computer. SNYPD never asks for your Vinted password, never signs in to your account, never buys and never messages sellers. The free plan runs one search while your dashboard is open; paid plans from &euro;14.99 a month keep watching 24/7.</p></div>
</section>
<section id="kinds">
  <h2>The three kinds of Vinted bot</h2>
  <p>&ldquo;Vinted bot&rdquo; covers tools that do very different things. What separates them is whether they act on your Vinted account.</p>
  <h3>ALERT BOTS, OR VINTED MONITORS</h3>
  <p>They watch your searches and tell you when something new matches; resellers also call them monitors. You buy yourself, so they have no reason to act on your Vinted account. SNYPD, Telvin Bot and Crazed are alert tools.</p>
  <h3>AUTOBUY AND AUTOCOP BOTS</h3>
  <p>They buy or check out for you. Buying on Vinted needs a logged-in account, so these tools act through yours; V-Tools, for example, states that you connect your own Vinted accounts. Souk, V-Tools and Resell Reserve sell autobuy features.</p>
  <h3>DO-IT-YOURSELF SCRIPTS</h3>
  <p>Open-source projects on GitHub that you host yourself, usually posting to Discord or Telegram. Free, but you run the server and fix it when Vinted changes something.</p>
  <p>Prices, channels and free plans of each tool are side by side in <a href="{SLUGS['compare']['en']}">Vinted bots compared</a>. How a monitor works, step by step: <a href="{SLUGS['monitor']['en']}">what is a Vinted monitor?</a></p>
</section>
<section id="automation">
  <h2>Vinted automation: the buyer side, not the seller side</h2>
  <p>&ldquo;Vinted automation&rdquo; usually means seller tools: they relist or bump your items, send offers to people who favourited them, or write your descriptions. They work on your own shop, so they act on your Vinted account.</p>
  <p>SNYPD automates the buyer side only: it watches searches and tells you what is new. It does not touch your shop, your listings or your messages, and it never signs in. If you want your own listings bumped or relisted, SNYPD is not that tool.</p>
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
        return page('bot', 'en', 'Vinted Bot & Monitor: New Listing Alerts, No Autobuy | SNYPD',
                    'SNYPD is a Vinted bot and monitor that watches your searches and sends a push alert when a matching listing appears. It never logs in, buys or messages for you.',
                    'VINTED BOT &amp; MONITOR', 'A Vinted bot and monitor that alerts you and never touches your account.',
                    'Most Vinted bots are sold on buying for you, which means acting as you. SNYPD does the other part of the job: it keeps watching your Vinted searches and tells you when something new matches, so you decide and buy on Vinted yourself.',
                    [('answer', 'In one paragraph'), ('kinds', 'Three kinds of bot'), ('automation', 'Automation'), ('how', 'How it works'), ('speed', 'How fast'), ('pricing', 'What it costs'), ('account', 'Your Vinted account'), ('faq', 'Questions')],
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
  <h3>BOTS D’ALERTES, OU MONITORS VINTED</h3>
  <p>Ils surveillent tes recherches et te préviennent quand un nouvel article correspond ; on parle aussi de « monitor Vinted ». Tu achètes toi-même, donc ils n’ont aucune raison d’agir sur ton compte Vinted. SNYPD, Telvin Bot et Crazed sont des outils d’alertes.</p>
  <h3>BOTS D’ACHAT AUTOMATIQUE (AUTOBUY, AUTOCOP)</h3>
  <p>Ils achètent ou passent commande à ta place. Acheter sur Vinted demande un compte connecté, donc ces outils agissent via le tien ; V-Tools, par exemple, indique que tu connectes tes propres comptes Vinted. Souk, V-Tools et Resell Reserve vendent de l’achat automatique.</p>
  <h3>SCRIPTS À HÉBERGER SOI-MÊME</h3>
  <p>Des projets open source sur GitHub que tu héberges toi-même, qui postent en général sur Discord ou Telegram. Gratuits, mais c’est toi qui gères le serveur et qui répares quand Vinted change quelque chose.</p>
  <p>Les prix, canaux d’alerte et plans gratuits de chaque outil sont côte à côte dans le <a href="{SLUGS['compare']['fr']}">comparatif des bots Vinted</a>. Le fonctionnement d’un monitor, étape par étape : <a href="{SLUGS['monitor']['fr']}">qu’est-ce qu’un monitor Vinted ?</a></p>
</section>
<section id="automatisation">
  <h2>Automatisation Vinted : côté acheteur, pas côté vendeur</h2>
  <p>« Automatisation Vinted » désigne le plus souvent des outils pour vendeurs : ils republient ou remontent tes articles, envoient des offres aux personnes qui les ont mis en favoris, ou rédigent tes descriptions. Ils travaillent sur ta propre boutique, donc ils agissent sur ton compte Vinted.</p>
  <p>SNYPD automatise uniquement le côté acheteur : il surveille des recherches et te dit ce qui est nouveau. Il ne touche ni à ta boutique, ni à tes annonces, ni à tes messages, et ne se connecte jamais. Si tu veux remonter ou republier tes propres annonces, SNYPD n’est pas cet outil.</p>
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
                [('resume', 'En un paragraphe'), ('types', 'Trois types de bot'), ('automatisation', 'Automatisation'), ('fonctionnement', 'Fonctionnement'), ('vitesse', 'Vitesse'), ('prix', 'Prix'), ('compte', 'Ton compte Vinted'), ('questions', 'Questions')],
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
        return page('notify', 'en', 'Vinted Alerts & Notifications for New Listings (2026) | SNYPD',
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
COMPARE_CHECKED = {'en': '3 October 2026', 'fr': '3 octobre 2026'}
COMPARE_CHECKED_SHORT = {'en': '3 OCT 2026', 'fr': '3 OCT. 2026'}

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
.fc { border: 1px solid rgba(0,229,160,.38); background: rgba(0,229,160,.05); padding: 18px; margin: 0 0 18px; display: flex; flex-direction: column; gap: 14px; }
.fc-in { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 12px; }
@media (max-width: 559.98px) { .fc-in { grid-template-columns: minmax(0, 1fr); } }
.fc label { display: flex; flex-direction: column; gap: 8px; font-size: 11px; letter-spacing: .12em; color: #8B9094; }
.fc input, .fc select { font-family: inherit; font-size: 16px; color: #FFFFFF; background: #141416; border: 1px solid #3A3A40; border-radius: 0; padding: 0 12px; min-height: 48px; width: 100%; box-sizing: border-box; }
.fc input:focus-visible, .fc select:focus-visible { outline: 2px solid #00E5A0; outline-offset: 1px; }
.fc-out { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1px; background: #1D1D20; border: 1px solid #1D1D20; margin: 0; }
.fc-out div { background: #0C0C0D; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px; }
.fc-out dt { font-size: 11px; letter-spacing: .1em; color: #8B9094; }
.fc-out dd { margin: 0; font-size: 18px; color: #FFFFFF; }
.fc-out div.fc-total dd { color: #00E5A0; }
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
    # souk.to/en + souk.to/en/docs/autobuy ("To use Autobuy, first link your Vinted account from the Souk settings.", re-read 3 Oct 2026)
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
    # resellreserve.co.uk + /refund-policy (updated 27 Sept 2026: "generally non-refundable", plus a Core break-even guarantee)
    {'name': ('Resell Reserve', 'Resell Reserve'), 'url': 'https://resellreserve.co.uk/', 'cells': [
        _c('Alerts + autobuy', 'Alertes + achat automatique'),
        _c('AI estimates, &pound;44.99 plan only', 'Estimations IA, plan à 44,99&nbsp;&pound; seulement'),
        _c('To buy, yes*', 'Pour acheter, oui*'),
        _c('Discord', 'Discord'),
        _c('Generally non-refundable; Core: conditional first-month guarantee', 'En général non remboursable ; Core : garantie conditionnelle le premier mois'),
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
             'Autobuy needs your account: Souk&rsquo;s docs say &ldquo;To use Autobuy, first link your Vinted account&rdquo;, and V-Tools&rsquo; plans come with connected Vinted accounts. V-Tools&rsquo; own FAQ on bans: &ldquo;No tool can guarantee zero risk.&rdquo;'),
            ('Alerts land on your phone',
             'Push notifications go straight to your phone or computer. No Telegram, no Discord server, no extra account. Several finds close together arrive as one notification, not a buzz each.',
             'Telvin alerts only inside Telegram; Resell Reserve alerts in Discord. On iPhone, add SNYPD to your Home Screen once: Apple only allows web push for Home Screen apps.'),
            ('Every Vinted filter you set',
             'Paste a Vinted search link and SNYPD keeps every filter in it: brand, size, price, condition, colour, material, category. If you can filter it on Vinted, SNYPD keeps that filter.',
             'Souk builds alerts from its own form (brand, category, size, keywords, price). SNYPD works on %s: 26 sites, each in its own currency.' % MARKETS_TEXT['en']),
            ('14 days to change your mind',
             'Not happy with a paid plan? Email within 14 days of your first payment and you get it back in full. Prices include VAT, plans run month to month, cancel any time.',
             'Souk&rsquo;s site states one week. Resell Reserve&rsquo;s refund policy says payments are &ldquo;generally non-refundable&rdquo;, with a conditional first-month guarantee on its Core plan.'),
            ('Your finds, tracked to the profit',
             'Claim an item you bought and SNYPD keeps it in History: Holding, then Sold, with your realised profit added up for you. No spreadsheet next to your bot.',
             'Part of the SNYPD dashboard. Matches also carry a NEW badge and a DROP badge when the price fell since SNYPD first saw it.'),
            ('Made by a reseller',
             'SNYPD is built by a Belgian sneaker reseller with 150+ sales and 3.8k Instagram followers, and run in the open with resellers in its Discord.',
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
             'L’achat automatique passe par ton compte : la doc de Souk dit « To use Autobuy, first link your Vinted account », et les plans de V-Tools incluent des comptes Vinted connectés. La FAQ de V-Tools sur les bannissements : « No tool can guarantee zero risk ».'),
            ('Les alertes arrivent sur ton téléphone',
             'Les notifications push arrivent directement sur ton téléphone ou ton ordinateur. Pas de Telegram, pas de serveur Discord, pas de compte en plus. Plusieurs trouvailles rapprochées arrivent en une seule notification.',
             'Telvin alerte uniquement dans Telegram ; Resell Reserve dans Discord. Sur iPhone, ajoute SNYPD à ton écran d’accueil une fois : Apple n’autorise les notifications web que pour les apps de l’écran d’accueil.'),
            ('Chaque filtre Vinted que tu règles',
             'Colle un lien de recherche Vinted et SNYPD garde tous ses filtres : marque, taille, prix, état, couleur, matière, catégorie. Si tu peux le filtrer sur Vinted, SNYPD garde ce filtre.',
             'Souk crée les alertes depuis son propre formulaire (marque, catégorie, taille, mots-clés, prix). SNYPD fonctionne sur %s : 26 sites, chacun dans sa devise.' % MARKETS_TEXT['fr']),
            ('14 jours pour changer d’avis',
             'Pas convaincu par un plan payant ? Écris dans les 14 jours suivant ton premier paiement et tu es remboursé en totalité. Prix TVA incluse, plans au mois, résiliables à tout moment.',
             'Le site de Souk indique une semaine. La politique de Resell Reserve indique que les paiements sont « generally non-refundable », avec une garantie conditionnelle le premier mois sur son plan Core.'),
            ('Tes trouvailles, suivies jusqu’au bénéfice',
             'Marque un article acheté et SNYPD le garde dans History : Holding, puis Sold, avec ton bénéfice réalisé calculé pour toi. Plus besoin d’un tableur à côté de ton bot.',
             'Inclus dans le tableau de bord SNYPD. Les annonces portent aussi un badge NEW et un badge DROP quand le prix a baissé depuis que SNYPD l’a vue.'),
            ('Créé par un revendeur',
             'SNYPD est créé par un revendeur de sneakers belge, avec plus de 150 ventes et 3,8k abonnés Instagram, et développé au grand jour avec des revendeurs sur son Discord.',
             'Tes questions arrivent à une vraie personne : <a href="mailto:%s">%s</a> ou le <a href="%s">Discord</a>.' % (EMAIL, EMAIL, DISCORD)),
            ('Un prix fondateur, à vie',
             'Les 100 premiers comptes, gratuits compris, gardent Pro à 24,99&nbsp;&euro; par mois à vie.',
             'Le nombre de places restantes est affiché en direct sur la <a href="/">page d’accueil</a>.'),
        ]
    cards = ''.join('<div class="rs-card"><span class="rs-num">%02d</span><h3 class="rs-title">%s</h3><p>%s</p><p class="rs-proof">%s</p></div>' % (i + 1, t, b, p)
                    for i, (t, b, p) in enumerate(R))
    return '<div class="rs-grid">%s</div>' % cards


COMPARE_FAQ = {
    'en': [
        ('What is a Vinted monitor?',
         'A tool that keeps checking a Vinted search for you and alerts you when a new listing matches it. A monitor does not buy: you open the listing and decide. All the tools on this page monitor searches; Souk, V-Tools and Resell Reserve also sell autobuy. More in <a href="%s">what is a Vinted monitor?</a>' % SLUGS['monitor']['en']),
        ('Are Vinted bots worth it?',
         'For resellers who buy in a narrow niche, often. Vinted&rsquo;s own saved searches show a &ldquo;+N&rdquo; counter the next time you open the app, but they do not notify you about each new match, so a well-priced listing can be gone before you look. If you only buy now and then for yourself, saved searches may be enough. Try a free plan before paying: SNYPD, Telvin, Crazed and MarktAlert all list one.'),
        ('Can a Vinted bot get my account banned?',
         'Vinted&rsquo;s terms prohibit bots and scraping programs, so no tool can promise there is no risk. V-Tools&rsquo; own FAQ says: &ldquo;No tool can guarantee zero risk.&rdquo; What differs is what happens on your account: autobuy tools act through your logged-in Vinted account, while SNYPD never signs in as you, so nothing it does happens on your account.'),
        ('Is there a free Vinted bot?',
         'Yes, with limits. According to each tool&rsquo;s own site, checked on %s: SNYPD Free runs 1 search with no time limit while your dashboard is open; Telvin&rsquo;s free plan covers 1 keyword alert and 100 notifications; Crazed is free with 3 alerts and 30 items a day; MarktAlert has a free plan that checks every 15 minutes. Open-source scripts on GitHub are free if you host them yourself.' % COMPARE_CHECKED['en']),
        ('Which Vinted bot is the fastest?',
         'There is no fair way to say. Each vendor measures its own speed in its own way (see <a href="#speed">what about speed?</a>). SNYPD checks each search every 30 seconds to 5 minutes on every plan, and keeps paid searches running 24/7.'),
    ],
    'fr': [
        ('Qu’est-ce qu’un monitor Vinted\xa0?',
         'Un outil qui vérifie une recherche Vinted à ta place et t’alerte quand une nouvelle annonce correspond. Un monitor n’achète pas\xa0: tu ouvres l’annonce et tu décides. Tous les outils de cette page surveillent des recherches\xa0; Souk, V-Tools et Resell Reserve vendent aussi de l’achat automatique. Plus de détails\xa0: <a href="%s">qu’est-ce qu’un monitor Vinted\xa0?</a>' % SLUGS['monitor']['fr']),
        ('Un bot Vinted, ça vaut le coup\xa0?',
         'Pour un revendeur qui achète dans une niche précise, souvent oui. Les recherches sauvegardées de Vinted affichent un compteur «\xa0+N\xa0» à ta prochaine visite dans l’app, mais ne te notifient pas pour chaque nouvelle annonce\xa0: une annonce bien placée peut partir avant que tu regardes. Si tu achètes de temps en temps pour toi, les recherches sauvegardées peuvent suffire. Essaie un plan gratuit avant de payer\xa0: SNYPD, Telvin, Crazed et MarktAlert en proposent un.'),
        ('Un bot Vinted peut-il faire bannir mon compte\xa0?',
         'Les conditions de Vinted interdisent les bots et les programmes de scraping, donc aucun outil ne peut promettre zéro risque. La FAQ de V-Tools le dit elle-même\xa0: «\xa0No tool can guarantee zero risk\xa0». Ce qui change, c’est ce qui se passe sur ton compte\xa0: les outils d’achat automatique agissent via ton compte Vinted connecté, alors que SNYPD ne se connecte jamais à ta place, donc rien de ce qu’il fait ne se passe sur ton compte.'),
        ('Existe-t-il un bot Vinted gratuit\xa0?',
         'Oui, avec des limites. D’après le site de chaque outil, vérifié le %s\xa0: SNYPD Free fait tourner 1 recherche sans limite de durée tant que ton tableau de bord est ouvert\xa0; le plan gratuit de Telvin couvre 1 alerte mot-clé et 100 notifications\xa0; Crazed est gratuit avec 3 alertes et 30 articles par jour\xa0; MarktAlert a un plan gratuit qui vérifie toutes les 15 minutes. Les scripts open source sur GitHub sont gratuits si tu les héberges toi-même.' % COMPARE_CHECKED['fr']),
        ('Quel est le bot Vinted le plus rapide\xa0?',
         'Impossible de le dire honnêtement. Chaque éditeur mesure sa vitesse à sa façon (voir <a href="#vitesse">et la vitesse\xa0?</a>). SNYPD vérifie chaque recherche toutes les 30 secondes à 5 minutes sur tous les plans, et les recherches payantes tournent 24h/24.'),
    ],
}


def page_compare(lang):
    tbl = compare_table(lang)
    faq = COMPARE_FAQ[lang]
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
  <p>Telvin advertises alerts in 750 ms on its paid plans, Resell Reserve detection in under 0.15 s, V-Tools detection &ldquo;in a few milliseconds&rdquo;, and Crazed &ldquo;temps r&eacute;el&rdquo; (real time). Those are each vendor&rsquo;s own figures, measured in their own way, so they can&rsquo;t be compared with each other, or with SNYPD.</p>
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
<section id="faq">
  <h2>Questions about Vinted bots</h2>
  {faq_html(faq)}
</section>
<section id="start">
  <h2>Try it on one search</h2>
  {cta('en')}
</section>"""
        return page('compare', 'en', 'Best Vinted Bot & Monitor 2026: 7 Tools Compared | SNYPD',
                    'SNYPD vs Souk, Telvin, V-Tools, Crazed, Resell Reserve and MarktAlert: price data, account safety, phone alerts and refunds, each fact from the tool’s own site.',
                    'VINTED BOTS &amp; MONITORS COMPARED &middot; CHECKED ' + COMPARE_CHECKED_SHORT['en'], 'Best Vinted bots and monitors in 2026: SNYPD and six others compared',
                    'SNYPD alerts you to new Vinted listings, shows the typical Vinted asking price of what you&rsquo;re looking at, and never touches your Vinted account. Here is how that compares with six other Vinted bots, point by point, with the source for every fact.',
                    None, body, [faq_ld(faq)], head_extra='<ul class="glance" aria-label="SNYPD at a glance"><li><span>&#10003;</span>Price data included</li><li><span>&#10003;</span>No Vinted login, ever</li><li><span>&#10003;</span>Alerts on your phone</li><li><span>&#10003;</span>14-day refund</li></ul>')
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
  <p>Telvin annonce des alertes en 750 ms sur ses plans payants, Resell Reserve une détection en moins de 0,15 s, V-Tools une détection « in a few milliseconds », et Crazed du « temps réel ». Ce sont les chiffres de chaque éditeur, mesurés à sa façon, donc impossibles à comparer entre eux ou avec SNYPD.</p>
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
<section id="questions">
  <h2>Questions sur les bots Vinted</h2>
  {faq_html(faq)}
</section>
<section id="essayer">
  <h2>Essaie sur une recherche</h2>
  {cta('fr')}
</section>"""
    return page('compare', 'fr', 'Meilleur bot Vinted 2026 ? 7 bots comparés | SNYPD',
                'SNYPD face à Souk, Telvin, V-Tools, Crazed, Resell Reserve et MarktAlert : prix, compte, alertes, remboursement, d’après le site de chaque outil.',
                'COMPARATIF DES BOTS VINTED &middot; VÉRIFIÉ LE ' + COMPARE_CHECKED_SHORT['fr'], 'Meilleur bot Vinted en 2026 : SNYPD et six autres bots comparés',
                'SNYPD t’alerte des nouvelles annonces Vinted, te montre le prix demandé typique d’un article sur Vinted, et ne touche jamais à ton compte Vinted. Voici la comparaison avec six autres bots Vinted, point par point, avec la source de chaque information.',
                None, body, [faq_ld(faq)], head_extra='<ul class="glance" aria-label="SNYPD en bref"><li><span>&#10003;</span>Données de prix incluses</li><li><span>&#10003;</span>Jamais de connexion Vinted</li><li><span>&#10003;</span>Alertes sur ton téléphone</li><li><span>&#10003;</span>Remboursement sous 14 jours</li></ul>')


# ------------------------------------------------------------------ page: what is a vinted monitor
# Added 2026-10-03: "vinted monitor" ranks the same sites as "vinted bot" on Google UK, and
# Google's People-also-ask shows "What is a Vinted monitor?" and "Are Vinted bots worth it?".
# Competitor facts below come from COMPETITORS (each vendor's own site, COMPARE_CHECKED).
MONITOR_TYPES_HEAD = {'en': ['TYPE', 'WHAT IT DOES', 'ACTS ON YOUR VINTED ACCOUNT', 'WHO DECIDES EACH PURCHASE'],
                      'fr': ['TYPE', 'CE QU’IL FAIT', 'AGIT SUR TON COMPTE VINTED', 'QUI DÉCIDE DE CHAQUE ACHAT']}
MONITOR_TYPES = {
    'en': [['Monitor (alert bot)', 'Finds new listings in your searches and alerts you', 'No need to: it only reads search results', 'You'],
           ['Autobuy or autocop bot', 'Buys or checks out for you', 'Yes: buying needs a logged-in account', 'The bot, following your rules'],
           ['Seller automation', 'Relists, bumps or sends offers from your shop', 'Yes: it works on your own shop', 'Not a buying tool'],
           ['Script you host (GitHub)', 'A monitor you run on your own server', 'Depends on the script', 'You']],
    'fr': [['Monitor (bot d’alertes)', 'Trouve les nouvelles annonces de tes recherches et t’alerte', 'Pas besoin : il lit seulement les résultats de recherche', 'Toi'],
           ['Bot d’achat automatique (autobuy)', 'Achète ou passe commande à ta place', 'Oui : acheter demande un compte connecté', 'Le bot, selon tes règles'],
           ['Automatisation vendeur', 'Republie, remonte ou envoie des offres depuis ta boutique', 'Oui : il travaille sur ta propre boutique', 'Pas un outil d’achat'],
           ['Script à héberger (GitHub)', 'Un monitor que tu fais tourner sur ton propre serveur', 'Dépend du script', 'Toi']],
}


def page_monitor(lang):
    if lang == 'en':
        faq = [
            ('What is the difference between a Vinted monitor and a Vinted bot?',
             '&ldquo;Vinted bot&rdquo; is the wider word: it covers monitors, autobuy bots and seller tools. A monitor is the kind that only watches searches and alerts you. Resellers often use the two words for the same thing, which is why most monitors also call themselves bots.'),
            ('Is there a free Vinted monitor?',
             'Yes, with limits. SNYPD Free runs one search with no time limit while your dashboard is open. Other tools list free plans too; their limits are side by side in <a href="%s">Vinted bots compared</a>.' % SLUGS['compare']['en']),
            ('How fast is a Vinted monitor?',
             'It depends on how often the tool checks. SNYPD checks each search every 30 seconds to 5 minutes, faster on searches that keep finding new items, on every plan. Some vendors advertise milliseconds; those are their own figures, measured their own way.'),
            ('Do I need Discord or Telegram?',
             'Only if the monitor you pick sends alerts there. SNYPD sends push notifications to your phone or computer, so there is nothing else to install. On iPhone, add SNYPD to your Home Screen first: Apple only allows web push for Home Screen apps.'),
            ('Which Vinted countries can a monitor watch?',
             'That depends on the tool. SNYPD works on %s, 26 sites in all, each in its own currency: paste a search link from the site you shop on.' % MARKETS_TEXT['en']),
        ]
        body = f"""
<section id="answer">
  <h2>The short answer</h2>
  <div class="lg-box lg-mint"><p>A Vinted monitor is a tool that checks your Vinted searches over and over and alerts you when a listing appears that was not there before. Resellers also call it a Vinted alert bot. A monitor only finds and tells: you open the listing on Vinted and decide whether to buy. Tools that also buy for you are autobuy bots, and they need your logged-in Vinted account.</p></div>
</section>
<section id="why">
  <h2>Why resellers use one</h2>
  <p>Vinted&rsquo;s own saved searches show a &ldquo;+N&rdquo; counter the next time you open the app (<a href="{HELP435['en']}" rel="nofollow noopener">Vinted help</a>). They do not send a notification for each new match, so you only find out when you look.</p>
  <p>Everyone watching the same search can see a new listing the moment it appears, and the first person to notice it gets the first chance to buy. Well-priced listings are exactly the ones that go first. How often listings come up well under the typical price is measured in <a href="{SLUGS['deals']['en']}">Vinted deals</a>.</p>
</section>
<section id="how">
  <h2>How a Vinted monitor works</h2>
  <ol>
    <li>You give it a search: usually a Vinted search link with your filters, or keywords in the tool&rsquo;s own form.</li>
    <li>It loads the newest results of that search: the same public results anyone can open on Vinted.</li>
    <li>It compares them with what it saw last time. A listing it has not seen before is new.</li>
    <li>It sends you the new listing: a push notification, a Telegram or Discord message, or a line in an app, depending on the tool.</li>
    <li>It repeats. How often depends on the tool; SNYPD checks every 30 seconds to 5 minutes, faster on searches that keep finding things.</li>
  </ol>
  {figure('feed', 'en')}
</section>
<section id="types">
  <h2>Monitor, autobuy bot or seller automation?</h2>
  <p>All three get called &ldquo;Vinted bots&rdquo;. What separates them is what they do with your Vinted account.</p>
  {table(MONITOR_TYPES_HEAD['en'], MONITOR_TYPES['en'])}
  <p>Searches for &ldquo;Vinted automation&rdquo; mostly lead to seller tools. A monitor automates the buyer side only. More on the differences in <a href="{SLUGS['bot']['en']}">Vinted bot</a>.</p>
</section>
<section id="alerts">
  <h2>Where the alerts arrive</h2>
  <p>Monitors differ most in how they reach you. From each tool&rsquo;s own site, checked on {COMPARE_CHECKED['en']}:</p>
  <ul>
    <li><strong>Push notifications</strong> to your phone or computer: SNYPD. Nothing else to install.</li>
    <li><strong>Telegram</strong>: Telvin Bot sends alerts only there; MarktAlert offers Telegram among other channels.</li>
    <li><strong>Discord</strong>: Resell Reserve posts alerts in Discord channels.</li>
    <li><strong>An app feed</strong>: V-Tools shows finds in its own app.</li>
  </ul>
  <p>Whichever you pick, check that the alert reaches you with your laptop closed. A monitor that only runs while a browser tab is open misses most of the night.</p>
</section>
<section id="checklist">
  <h2>What to check before you pick one</h2>
  <ul class="fit-list">
    <li><strong>Does it ask for your Vinted login?</strong>A monitor only reads search results, so it has no reason to. Tools that buy for you do need it.</li>
    <li><strong>Does it keep every filter?</strong>Pasting a Vinted search link keeps all of them: brand, size, price, condition, colour, material. A tool&rsquo;s own form may offer fewer.</li>
    <li><strong>Does it keep watching when you are not there?</strong>On SNYPD&rsquo;s free plan, a search runs while your dashboard is open; paid plans keep it running 24/7.</li>
    <li><strong>Does it cover your Vinted country?</strong>Each Vinted site has its own listings and currency.</li>
    <li><strong>Can you test it before paying?</strong>Look for a free plan or a refund you can actually use after trying it.</li>
  </ul>
  <p>How seven tools answer these questions: <a href="{SLUGS['compare']['en']}">Vinted bots and monitors compared</a>.</p>
</section>
<section id="rules">
  <h2>Is a Vinted monitor allowed?</h2>
  <p>Vinted&rsquo;s terms prohibit bots and scraping programs, and no monitor can promise how Vinted applies them. What you can control is what happens on your own account. A monitor that never signs in, like SNYPD, does nothing on your Vinted account: you find the listing through the alert and buy it through Vinted&rsquo;s normal checkout. Tools that buy for you act through your logged-in account.</p>
</section>
<section id="snypd">
  <h2>SNYPD as a Vinted monitor</h2>
  <p>Paste a Vinted search link, switch it on, and SNYPD checks it every 30 seconds to 5 minutes. New matches land in your dashboard with their price, the price including Buyer Protection and their condition, and as a push notification on your phone. It never asks for your Vinted password, never buys and never messages sellers. Pro and Elite add the Market Report: the typical Vinted asking price of an item by condition.</p>
  {table(PLANS_HEAD['en'], PLANS_ROWS['en'])}
</section>
<section id="faq">
  <h2>Questions</h2>
  {faq_html(faq)}
</section>
<section id="start">
  <h2>Try a monitor on one search</h2>
  {cta('en')}
</section>"""
        return page('monitor', 'en', 'What Is a Vinted Monitor? How It Works (2026 Guide) | SNYPD',
                    'A Vinted monitor checks your Vinted searches and alerts you when a new listing matches. How monitors work, how they differ from autobuy bots, and what to check.',
                    'VINTED MONITOR &middot; GUIDE', 'What is a Vinted monitor?',
                    'A Vinted monitor watches your Vinted searches and tells you when something new matches. Here is how monitors work, how they differ from autobuy bots and seller tools, what to check before you pick one, and where SNYPD fits.',
                    [('answer', 'Short answer'), ('why', 'Why use one'), ('how', 'How it works'), ('types', 'Monitor or autobuy'), ('alerts', 'Where alerts arrive'),
                     ('checklist', 'What to check'), ('rules', 'Is it allowed?'), ('snypd', 'SNYPD'), ('faq', 'Questions')],
                    body, [faq_ld(faq)])
    faq = [
        ('Quelle différence entre un monitor Vinted et un bot Vinted ?',
         '« Bot Vinted » est le mot le plus large : il couvre les monitors, les bots d’achat automatique et les outils pour vendeurs. Un monitor est le type qui surveille seulement des recherches et t’alerte. Les revendeurs emploient souvent les deux mots pour la même chose, c’est pourquoi la plupart des monitors se présentent aussi comme des bots.'),
        ('Existe-t-il un monitor Vinted gratuit ?',
         'Oui, avec des limites. SNYPD Free fait tourner une recherche sans limite de durée tant que ton tableau de bord est ouvert. D’autres outils proposent aussi un plan gratuit ; leurs limites sont côte à côte dans le <a href="%s">comparatif des bots Vinted</a>.' % SLUGS['compare']['fr']),
        ('Un monitor Vinted, c’est rapide ?',
         'Ça dépend de la fréquence de vérification de l’outil. SNYPD vérifie chaque recherche toutes les 30 secondes à 5 minutes, plus souvent sur les recherches qui trouvent beaucoup, sur tous les plans. Certains éditeurs annoncent des millisecondes ; ce sont leurs propres chiffres, mesurés à leur façon.'),
        ('Faut-il Discord ou Telegram ?',
         'Seulement si le monitor choisi envoie ses alertes là-bas. SNYPD envoie des notifications push sur ton téléphone ou ton ordinateur, sans rien d’autre à installer. Sur iPhone, ajoute d’abord SNYPD à ton écran d’accueil : Apple n’autorise les notifications web que pour les apps de l’écran d’accueil.'),
        ('Quels pays Vinted un monitor peut-il surveiller ?',
         'Ça dépend de l’outil. SNYPD fonctionne sur %s, 26 sites au total, chacun dans sa devise : colle un lien de recherche du site où tu achètes.' % MARKETS_TEXT['fr']),
    ]
    body = f"""
<section id="reponse">
  <h2>La réponse courte</h2>
  <div class="lg-box lg-mint"><p>Un monitor Vinted est un outil qui vérifie tes recherches Vinted encore et encore et t’alerte quand une annonce apparaît qui n’était pas là avant. On parle aussi de bot d’alertes Vinted. Un monitor se contente de trouver et de prévenir : tu ouvres l’annonce sur Vinted et tu décides d’acheter ou non. Les outils qui achètent aussi à ta place sont des bots d’achat automatique, et ils ont besoin de ton compte Vinted connecté.</p></div>
</section>
<section id="pourquoi">
  <h2>Pourquoi les revendeurs en utilisent un</h2>
  <p>Les recherches sauvegardées de Vinted affichent un compteur « +N » à ta prochaine visite dans l’app (<a href="{HELP435['fr']}" rel="nofollow noopener">aide Vinted</a>). Elles n’envoient pas de notification pour chaque nouvelle annonce : tu ne le découvres qu’en allant voir.</p>
  <p>Tous ceux qui surveillent la même recherche voient une nouvelle annonce au même moment, et le premier qui la remarque a la première chance de l’acheter. Les annonces bien placées sont justement celles qui partent en premier.</p>
</section>
<section id="fonctionnement">
  <h2>Comment marche un monitor Vinted</h2>
  <ol>
    <li>Tu lui donnes une recherche : en général un lien de recherche Vinted avec tes filtres, ou des mots-clés dans le formulaire de l’outil.</li>
    <li>Il charge les résultats les plus récents de cette recherche : les mêmes résultats publics que n’importe qui peut ouvrir sur Vinted.</li>
    <li>Il les compare à ce qu’il a vu la dernière fois. Une annonce qu’il n’a jamais vue est nouvelle.</li>
    <li>Il t’envoie la nouvelle annonce : une notification push, un message Telegram ou Discord, ou une ligne dans une app, selon l’outil.</li>
    <li>Il recommence. La fréquence dépend de l’outil ; SNYPD vérifie toutes les 30 secondes à 5 minutes, plus souvent sur les recherches qui trouvent beaucoup.</li>
  </ol>
  {figure('feed', 'fr')}
</section>
<section id="types">
  <h2>Monitor, bot d’achat automatique ou automatisation vendeur ?</h2>
  <p>Les trois sont appelés « bots Vinted ». Ce qui les distingue, c’est ce qu’ils font de ton compte Vinted.</p>
  {table(MONITOR_TYPES_HEAD['fr'], MONITOR_TYPES['fr'])}
  <p>Les recherches « automatisation Vinted » mènent surtout à des outils pour vendeurs. Un monitor automatise uniquement le côté acheteur. Plus de détails sur la page <a href="{SLUGS['bot']['fr']}">bot Vinted</a>.</p>
</section>
<section id="alertes">
  <h2>Où arrivent les alertes</h2>
  <p>Les monitors diffèrent surtout par la façon de te prévenir. D’après le site de chaque outil, vérifié le {COMPARE_CHECKED['fr']} :</p>
  <ul>
    <li><strong>Notifications push</strong> sur ton téléphone ou ton ordinateur : SNYPD. Rien d’autre à installer.</li>
    <li><strong>Telegram</strong> : Telvin Bot alerte uniquement là ; MarktAlert propose Telegram parmi d’autres canaux.</li>
    <li><strong>Discord</strong> : Resell Reserve publie les alertes dans des salons Discord.</li>
    <li><strong>Le flux d’une app</strong> : V-Tools affiche les trouvailles dans sa propre app.</li>
  </ul>
  <p>Quel que soit ton choix, vérifie que l’alerte t’arrive ordinateur fermé. Un monitor qui ne tourne que dans un onglet ouvert rate la plus grande partie de la nuit.</p>
</section>
<section id="verifier">
  <h2>Ce qu’il faut vérifier avant de choisir</h2>
  <ul class="fit-list">
    <li><strong>Il demande tes identifiants Vinted ?</strong>Un monitor lit seulement des résultats de recherche, il n’en a donc pas besoin. Les outils qui achètent à ta place, si.</li>
    <li><strong>Il garde tous tes filtres ?</strong>Coller un lien de recherche Vinted les garde tous : marque, taille, prix, état, couleur, matière. Le formulaire d’un outil peut en proposer moins.</li>
    <li><strong>Il continue quand tu n’es pas là ?</strong>Avec le plan gratuit de SNYPD, une recherche tourne tant que ton tableau de bord est ouvert ; les plans payants la font tourner 24h/24.</li>
    <li><strong>Il couvre ton pays Vinted ?</strong>Chaque site Vinted a ses propres annonces et sa devise.</li>
    <li><strong>Tu peux l’essayer avant de payer ?</strong>Cherche un plan gratuit ou un remboursement utilisable après l’avoir essayé.</li>
  </ul>
  <p>Les réponses de sept outils à ces questions : <a href="{SLUGS['compare']['fr']}">comparatif des bots Vinted</a>.</p>
</section>
<section id="regles">
  <h2>Un monitor Vinted, c’est autorisé ?</h2>
  <p>Les conditions de Vinted interdisent les bots et les programmes de scraping, et aucun monitor ne peut promettre comment Vinted les applique. Ce que tu maîtrises, c’est ce qui se passe sur ton propre compte. Un monitor qui ne se connecte jamais, comme SNYPD, ne fait rien sur ton compte Vinted : tu trouves l’annonce grâce à l’alerte et tu l’achètes avec le paiement normal de Vinted. Les outils qui achètent à ta place agissent via ton compte connecté.</p>
</section>
<section id="snypd">
  <h2>SNYPD, un monitor Vinted</h2>
  <p>Colle un lien de recherche Vinted, active-le, et SNYPD le vérifie toutes les 30 secondes à 5 minutes. Les nouvelles annonces arrivent dans ton tableau de bord avec leur prix, le prix protection acheteurs incluse et leur état, et en notification push sur ton téléphone. Il ne demande jamais ton mot de passe Vinted, n’achète rien et n’écrit jamais aux vendeurs. Pro et Elite ajoutent le Market Report : le prix demandé typique d’un article sur Vinted selon son état.</p>
  {table(PLANS_HEAD['fr'], PLANS_ROWS['fr'])}
</section>
<section id="questions">
  <h2>Questions</h2>
  {faq_html(faq)}
</section>
<section id="essayer">
  <h2>Essaie un monitor sur une recherche</h2>
  {cta('fr')}
</section>"""
    return page('monitor', 'fr', 'Monitor Vinted : c’est quoi et comment ça marche (2026) | SNYPD',
                'Un monitor Vinted surveille tes recherches Vinted et t’alerte quand une nouvelle annonce correspond. Fonctionnement, différences avec l’achat auto, quoi vérifier.',
                'MONITOR VINTED &middot; GUIDE', 'Qu’est-ce qu’un monitor Vinted ?',
                'Un monitor Vinted surveille tes recherches Vinted et te prévient quand un nouvel article correspond. Voici comment marchent les monitors, en quoi ils diffèrent des bots d’achat automatique et des outils pour vendeurs, quoi vérifier avant d’en choisir un, et où se place SNYPD.',
                [('reponse', 'Réponse courte'), ('pourquoi', 'Pourquoi'), ('fonctionnement', 'Fonctionnement'), ('types', 'Monitor ou achat auto'), ('alertes', 'Où arrivent les alertes'),
                 ('verifier', 'Quoi vérifier'), ('regles', 'Autorisé ?'), ('snypd', 'SNYPD'), ('questions', 'Questions')],
                body, [faq_ld(faq)])


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
                   'creator': DATASET_CREATOR, 'license': DATASET_LICENSE, 'inLanguage': 'en', 'variableMeasured': ['median asking price (EUR)', '25th percentile (EUR)', '75th percentile (EUR)', 'number of listings', 'number of sellers'],
                   'distribution': [{'@type': 'DataDownload', 'encodingFormat': 'text/csv', 'contentUrl': SITE + '/' + REPORT_CSV}]}
        body = f"""
<section id="answer">
  <h2>Short answer</h2>
  <div class="lg-box lg-mint"><p>These are typical <strong>asking</strong> prices on Vinted, not sold prices: the median price of every listing SNYPD saw on vinted.be for each search in the 14 days to {end.day} September {end.year}, all sizes and conditions together. For example, an Air Jordan 1 Mid was typically listed at {money(f_typ, 'en')}, with the middle half of listings between {money(f_lo, 'en')} and {money(f_hi, 'en')}.</p></div>
  <p>Looking for what Vinted charges on top of the price? See the <a href="{SLUGS['fees']['en']}">Vinted fee calculator</a>.</p>
</section>
<section id="table">
  <h2>September 2026 prices</h2>
  <h3>SNEAKERS</h3>
  {table(head, [r for r, (q, n, g) in zip(rows, ITEMS) if g == 'sneakers'])}
  <h3>CLOTHING</h3>
  {table(head, [r for r, (q, n, g) in zip(rows, ITEMS) if g == 'clothing'])}
  <p class="ct-note">Download the numbers: <a href="/{REPORT_CSV}">{REPORT_CSV}</a>. Figures come straight from SNYPD&rsquo;s Market Report, run on {end.day} September {end.year}. Free to reuse with credit to SNYPD (<a href="{DATASET_LICENSE}" rel="license noopener">CC BY 4.0</a>).</p>
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
               'creator': DATASET_CREATOR, 'license': DATASET_LICENSE, 'inLanguage': 'fr',
               'distribution': [{'@type': 'DataDownload', 'encodingFormat': 'text/csv', 'contentUrl': SITE + '/' + REPORT_CSV}]}
    body = f"""
<section id="reponse">
  <h2>Réponse courte</h2>
  <div class="lg-box lg-mint"><p>Ce sont des prix <strong>demandés</strong> typiques sur Vinted, pas des prix de vente : le prix médian de toutes les annonces vues par SNYPD sur vinted.be pour chaque recherche, sur les 14 jours au {end.day} septembre {end.year}, toutes tailles et tous états confondus. Par exemple, une Air Jordan 1 Mid était typiquement mise en vente à {money(f_typ, 'fr')}, la moitié centrale des annonces se situant entre {money(f_lo, 'fr')} et {money(f_hi, 'fr')}.</p></div>
  <p>Tu cherches les frais que Vinted ajoute au prix ? Voir le <a href="{SLUGS['fees']['fr']}">calculateur des frais Vinted</a>.</p>
</section>
<section id="tableau">
  <h2>Les prix de septembre 2026</h2>
  <h3>SNEAKERS</h3>
  {table(head, [r for r, (q, n, g) in zip(rows, ITEMS) if g == 'sneakers'])}
  <h3>VÊTEMENTS</h3>
  {table(head, [r for r, (q, n, g) in zip(rows, ITEMS) if g == 'clothing'])}
  <p class="ct-note">Télécharger les chiffres : <a href="/{REPORT_CSV}">{REPORT_CSV}</a> (en anglais). Les chiffres viennent directement du Market Report de SNYPD, calculé le {end.day} septembre {end.year}. Réutilisation libre en citant SNYPD (<a href="{DATASET_LICENSE}" rel="license noopener">CC BY 4.0</a>).</p>
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


# ------------------------------------------------------------------ page: deals guide
# Figures come ONLY from DEALS, the verbatim output of ops/seo/deals_stats.sql (its
# header explains the method and the md5 check). Never type a number into the copy.
DEALS = os.path.join(ROOT, 'ops', 'seo', 'data', 'deals-2026-10.json')
# Vinted's own English names for its condition grades (stored in French on vinted.be).
COND_EN = {'Neuf avec étiquette': 'New with tags', 'Neuf sans étiquette': 'New without tags',
           'Très bon état': 'Very good', 'Bon état': 'Good', 'Satisfaisant': 'Satisfactory'}
BUY_SAFE = 'https://www.vinted.co.uk/help/82'


def pct(a, b):
    return '%d%%' % round(100.0 * a / b)


def page_deals(lang):
    d = json.load(open(DEALS, encoding='utf-8'))
    models = d['models']
    start = datetime.date.fromisoformat(d['window_start'][:10])
    last = datetime.date.fromisoformat(d['window_end'][:10]) - datetime.timedelta(days=1)
    span = f'{start.day} {MONTHS_TXT["en"][start.month - 1]} to {last.day} {MONTHS_TXT["en"][last.month - 1]} {last.year}'
    days = d['days']
    by = {m['name']: m for m in models}
    top = models[0]  # most listings
    rare = min(models, key=lambda m: m['under50'] / m['n'])
    vg = {c['condition']: c['median_cents'] for c in top['ladder']}.get('Très bon état')
    if vg is None:
        sys.exit('deals: the top model has no "Très bon état" median; pick another example')
    cap = int(round(vg * 0.7 / 100.0)) * 100
    lad = {c['condition']: c['median_cents'] for c in top['ladder']}
    good, nwt = lad.get('Bon état'), lad.get('Neuf avec étiquette')
    if not good or not nwt or not (good < cap < vg):
        sys.exit('deals: the condition example no longer holds for ' + top['name'])
    rows = []
    for m in models:
        rows.append([m['name'],
                     f'<span class="ct-num">{num(m["n"], "en")}</span>',
                     f'<span class="ct-num">{num(m["under30"], "en")}</span><small>{pct(m["under30"], m["n"])} &middot; about {num(round(m["under30"] / days), "en")} a day</small>',
                     f'<span class="ct-num">{num(m["under50"], "en")}</span><small>{pct(m["under50"], m["n"])}</small>'])
    ladder_rows = [[COND_EN.get(c['condition'], esc(c['condition'])), f'<span class="ct-num">{money(c["median_cents"], "en")}</span>',
                    f'<span class="ct-num">{num(c["n"], "en")}</span>'] for c in top['ladder']]
    shares = [m['under30'] / m['n'] for m in models]
    lo_pct, hi_pct = '%d%%' % round(100 * min(shares)), '%d%%' % round(100 * max(shares))
    faq = [
        ('What counts as a steal on Vinted?',
         'A listing priced well below what the same item is usually listed for in the same condition, that is still the item it claims to be. A price alone does not make a steal: for the models in this guide, between %s and %s of new listings went up 30%% or more under the typical price for their condition.' % (lo_pct, hi_pct)),
        ('Where can I see the typical Vinted price of an item?',
         f'Vinted does not show one on its listings. SNYPD&rsquo;s free <a href="{SLUGS["prices"]["en"]}">Vinted prices</a> page lists typical asking prices for popular sneakers and streetwear, and the Market Report in Pro and Elite prices any search by condition.'),
        ('Are very cheap Vinted listings fake?',
         'Some are, and a low price is one of the reasons to look closer, but it is not proof. Kids&rsquo; sizes, other colourways, wear the condition label does not show and sellers who want a quick sale also explain low prices. Check the photos, the size and the seller before you buy.'),
        ('Does SNYPD buy deals for me?',
         'No. SNYPD watches your Vinted searches and sends you an alert when a new listing matches. You open it on Vinted and decide yourself. It never signs in to your Vinted account.'),
    ]
    tbl = table(['MODEL', 'NEW LISTINGS', '30% OR MORE UNDER TYPICAL', 'HALF PRICE OR LESS'], rows)
    body = f"""
<section id="answer">
  <h2>Short answer</h2>
  <div class="lg-box lg-mint"><p>A cheap Vinted listing is not rare. From {span}, {num(top['under30'], 'en')} of the {num(top['n'], 'en')} new {top['name']} listings SNYPD saw on vinted.be ({pct(top['under30'], top['n'])}) were posted at 30% or more below the typical asking price for their condition, and {num(top['under50'], 'en')} ({pct(top['under50'], top['n'])}) at half price or less. What is rare is seeing the right one first. Finding Vinted deals comes down to four things: know the typical price for the exact condition, search narrow with a price cap, get alerted to new listings instead of refreshing, and check the listing before you pay.</p></div>
</section>
<section id="data">
  <h2>How often deep discounts appear</h2>
  <p>New listings on vinted.be over {days} days, {span}, compared with the typical asking price for the same model in the same condition:</p>
  {tbl}
  <p>The pattern differs by model. On {top['name']}, half-price listings are common, so a cheap one proves little on its own: check the size, colourway and wear first. On {rare['name']}, only {num(rare['under50'], 'en')} of {num(rare['n'], 'en')} new listings went up at half price or less, so a big discount there is unusual and worth both speed and a closer look.</p>
  <p class="ct-note">How these numbers are made is under <a href="#method">method and limits</a>. Asking prices, not sold prices.</p>
</section>
<section id="price">
  <h2>1. Know the typical price for the exact condition</h2>
  <p>A price only looks low against the right comparison. Condition moves Vinted prices a lot: on {top['name']}, the typical New with tags price is {nwt / good:.1f} times the Good one. Typical asking prices for new {top['name']} listings, {span}:</p>
  {table(['CONDITION', 'TYPICAL ASKING PRICE', 'LISTINGS'], ladder_rows)}
  <p>So the same {money(cap, 'en')} is 30% under the typical price for a Very good pair, but above the typical price for a Good pair ({money(good, 'en')}). For more models, see <a href="{SLUGS['prices']['en']}">Vinted prices</a>. In SNYPD Pro and Elite, the Market Report gives this breakdown for any search you type.</p>
</section>
<section id="search">
  <h2>2. Search narrow, with a price cap</h2>
  <ul>
    <li><strong>Name the exact model</strong> and, for clothing, the garment. &ldquo;Nike&rdquo; alone returns too much to watch.</li>
    <li><strong>Set your size and condition filters</strong>, so every match is one you would actually buy.</li>
    <li><strong>Set the maximum price</strong> around 70% of the typical price for that condition. For a Very good {top['name']}, that is about {money(cap, 'en')}.</li>
    <li><strong>Sort by newest first</strong>, so new listings come to the top. In the search link this shows as <code>order=newest_first</code>.</li>
  </ul>
</section>
<section id="first">
  <h2>3. Be first: get alerted, don&rsquo;t refresh</h2>
  <p>Everyone watching the same search can see a new listing the moment it appears, so the first to notice it gets the first chance. Vinted&rsquo;s saved searches show a &ldquo;+N&rdquo; counter the next time you open the app; they do not send a notification for each new match (<a href="{SLUGS['notify']['en']}">how Vinted notifications work</a>). To hear about a new match while you are doing something else, you need a tool that watches the search for you.</p>
  <p>SNYPD checks each search every 30 seconds to 5 minutes and sends a push notification to your phone or computer when a new listing matches. The free plan runs one search while your dashboard is open; paid plans from &euro;14.99 a month keep watching 24/7.</p>
  {figure('feed', 'en')}
</section>
<section id="check">
  <h2>4. Check before you pay</h2>
  <ul>
    <li><strong>Photos against the label.</strong> Look for wear the condition grade does not mention: soles, creases, stains, missing tags.</li>
    <li><strong>The size.</strong> Kids&rsquo; and adult sizes share model names and differ a lot in price.</li>
    <li><strong>The price against the typical one.</strong> Compare the discount with how often that model gets one: on {rare['name']}, a half-price listing came up {num(rare['under50'], 'en')} times in {days} days.</li>
    <li><strong>The seller.</strong> Reviews and other listings tell you more than one photo.</li>
    <li><strong>Pay with Vinted&rsquo;s Buy now button.</strong> Vinted says that payments made outside its system are not covered by Buyer Protection (<a href="{BUY_SAFE}" rel="noopener">Vinted help: buying safely</a>).</li>
  </ul>
</section>
<section id="method">
  <h2>Method and limits</h2>
  <ul>
    <li><strong>Source.</strong> Listings SNYPD&rsquo;s systems first saw on vinted.be, in euros, from {span}.</li>
    <li><strong>Matching.</strong> A listing counts for a model when its title contains the model&rsquo;s words (for example &ldquo;dunk&rdquo; and &ldquo;low&rdquo;). This is a simpler match than the Market Report&rsquo;s, so counts differ from <a href="{SLUGS['prices']['en']}">Vinted prices</a>.</li>
    <li><strong>Typical price</strong> is the median first asking price for that model in that condition. Conditions with fewer than 30 listings are left out.</li>
    <li><strong>Under</strong> means a first asking price at or below 70% (or 50%) of that median.</li>
  </ul>
  <h3>LIMITS</h3>
  <ul>
    <li>Asking prices, not sold prices. We cannot see which listings sold or for how much.</li>
    <li>Sizes and colourways are mixed, and fakes are not removed, so some low prices are a different item rather than a bargain.</li>
    <li>One site (vinted.be) and one two-week window. Other Vinted sites and months will differ.</li>
  </ul>
</section>
<section id="faq">
  <h2>Questions</h2>
  {faq_html(faq)}
</section>
<section id="start">
  <h2>Watch one search for free</h2>
  {cta('en')}
</section>"""
    return page('deals', 'en', 'Vinted Deals: How to Find Steals Before Anyone Else | SNYPD',
                'How to find Vinted deals and steals: real data on how often listings go up far below the typical price, and four steps to see the right one first.',
                'VINTED DEALS &middot; GUIDE', 'How to find Vinted deals before anyone else',
                f'Low prices on Vinted are common; good deals that are still the item you want, seen before anyone else, are not. This guide uses {num(sum(m["n"] for m in models), "en")} real vinted.be listings from {span} to show how often deep discounts appear, then the four steps that get you to them first.',
                [('answer', 'Short answer'), ('data', 'How often'), ('price', 'Know the price'), ('search', 'Search narrow'), ('first', 'Be first'), ('check', 'Check first'), ('method', 'Method'), ('faq', 'Questions')],
                body, [faq_ld(faq)])


# ------------------------------------------------------------------ page: fees + calculator
# The fee rule is Vinted's own (price lists of vinted.fr/.de/.nl/.it/.es and vinted.com, read
# 2 Oct 2026). FEES_CHECK is the verbatim output of ops/seo/fees_check.sql: the same integer
# formula tested against every real vinted.be listing of a week. If it ever stops matching
# 100%, the build stops instead of publishing a wrong claim.
FEES_CHECK = os.path.join(ROOT, 'ops', 'seo', 'data', 'fees-check-2026-10.json')
FEES_CHECKED = {'en': '2 October 2026', 'fr': '2 octobre 2026'}
FEE_SRC = {
    'fr_list': 'https://www.vinted.fr/pricelist', 'fr_help': 'https://www.vinted.fr/help/1654',
    'us_list': 'https://www.vinted.com/pricelist', 'uk_list': 'https://www.vinted.co.uk/pricelist',
    'free_en': 'https://www.vinted.co.uk/help/373-is-selling-on-vinted-free', 'free_fr': 'https://www.vinted.fr/help/373',
    'ship_en': 'https://www.vinted.co.uk/help/458-who-pays-for-shipping', 'ship_fr': 'https://www.vinted.fr/help/458',
    'safe_en': 'https://www.vinted.co.uk/help/82', 'safe_fr': 'https://www.vinted.fr/help/82',
}
# Dataset rich results (Google): creator must be a typed Organization on the page itself (an @id
# pointing at the homepage's Organization is reported as 'Invalid object type'), and a license
# is expected. CC BY 4.0: anyone may reuse the figures if they credit SNYPD (decided 2026-10-03).
DATASET_CREATOR = {'@type': 'Organization', '@id': SITE + '/#org', 'name': 'SNYPD', 'url': SITE + '/'}
DATASET_LICENSE = 'https://creativecommons.org/licenses/by/4.0/'
FEE_TABLE_CENTS = [500, 1000, 2000, 3000, 5000, 10000, 20000, 50000]

# Plain ASCII on purpose. Whole cents only: fee = 70 + floor((cents * 5 + 50) / 100).
FEE_JS = r"""<script>
(function () {
  var f = document.getElementById('fc'); if (!f) return;
  var inp = document.getElementById('fc-price'), cur = document.getElementById('fc-cur'), L = f.getAttribute('data-lang');
  function fmt(c, k) {
    var s = (c / 100).toFixed(2);
    if (k === 'usd') return L === 'fr' ? s.replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, '\u202f') + '\u00a0$' : '$' + s.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    if (L === 'fr') return s.replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, '\u202f') + '\u00a0\u20ac';
    return '\u20ac' + s.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  }
  function put(id, t) { document.getElementById(id).textContent = t; }
  function run() {
    var r = String(inp.value).replace(/[\s\u00a0\u202f\u20ac$]/g, '');
    r = /,\d{1,2}$/.test(r) ? r.replace(/\./g, '').replace(',', '.') : r.replace(/,/g, '');
    var v = /^\d+(\.\d{0,2})?$/.test(r) ? parseFloat(r) : NaN;
    if (!(v > 0) || v > 1000000) { put('fc-fee', '-'); put('fc-total', '-'); put('fc-pct', '-'); put('fc-seller', '-'); return; }
    var c = Math.round(v * 100), fee = 70 + Math.floor((c * 5 + 50) / 100), k = cur.value;
    put('fc-fee', fmt(fee, k)); put('fc-total', fmt(c + fee, k)); put('fc-seller', fmt(c, k));
    var p = (100 * fee / c).toFixed(1); put('fc-pct', (L === 'fr' ? p.replace('.', ',') + '\u00a0%' : p + '%'));
  }
  inp.addEventListener('input', run); cur.addEventListener('change', run); run();
})();
</script>"""


def fee_cents(c):
    return 70 + (c * 5 + 50) // 100


def m2(c, lang):
    s = '{:,.2f}'.format(c / 100)
    if lang == 'en':
        return '&euro;' + s
    return s.replace(',', '&#8239;').replace('.', ',') + '&nbsp;&euro;'


def pct1(a, b, lang):
    s = '%.1f' % (100.0 * a / b)
    return s + '%' if lang == 'en' else s.replace('.', ',') + '&nbsp;%'


def page_fees(lang):
    chk = json.load(open(FEES_CHECK, encoding='utf-8'))
    if not (chk['listings'] > 0 and chk['fee_matches'] == chk['listings'] == chk['total_matches']):
        sys.exit('fees: the real-listing check no longer matches 100%; do not publish the rule as verified')
    n = num(chk['listings'], lang)
    lo, hi = m2(chk['min_price_cents'], lang), m2(chk['max_price_cents'], lang)
    ws = datetime.date.fromisoformat(chk['window_start'][:10])
    we = datetime.date.fromisoformat(chk['window_end'][:10]) - datetime.timedelta(days=1)
    rows = [[f'<span class="ct-num">{m2(c, lang)}</span>', f'<span class="ct-num">{m2(fee_cents(c), lang)}</span>',
             f'<span class="ct-num">{m2(c + fee_cents(c), lang)}</span>', f'<span class="ct-num">{pct1(fee_cents(c), c, lang)}</span>']
            for c in FEE_TABLE_CENTS]
    ex = 2000
    small, big = FEE_TABLE_CENTS[0], FEE_TABLE_CENTS[-2]
    b1, nb = 1000, 3
    sep, bun = nb * fee_cents(b1), fee_cents(nb * b1)
    ui = {'en': ('ITEM PRICE', 'CURRENCY', 'BUYER PROTECTION FEE', 'BUYER PAYS (BEFORE SHIPPING)', 'FEE AS % OF PRICE', 'SELLER RECEIVES',
                 'Euro sites: vinted.fr, .be, .de, .nl, .it, .es', 'US dollars: vinted.com', '20.00'),
          'fr': ('PRIX DE L’ARTICLE', 'DEVISE', 'FRAIS DE PROTECTION ACHETEURS', 'L’ACHETEUR PAIE (HORS LIVRAISON)', 'FRAIS EN % DU PRIX', 'LE VENDEUR REÇOIT',
                 'Sites en euros : vinted.fr, .be, .de, .nl, .it, .es', 'Dollars US : vinted.com', '20,00')}[lang]
    calc = (f'<div class="fc" id="fc" data-lang="{lang}"><div class="fc-in">'
            f'<label>{ui[0]}<input id="fc-price" type="text" inputmode="decimal" autocomplete="off" value="{ui[8]}"></label>'
            f'<label>{ui[1]}<select id="fc-cur"><option value="eur">{ui[6]}</option><option value="usd">{ui[7]}</option></select></label></div>'
            f'<dl class="fc-out" aria-live="polite"><div><dt>{ui[2]}</dt><dd id="fc-fee">{m2(fee_cents(ex), lang)}</dd></div>'
            f'<div class="fc-total"><dt>{ui[3]}</dt><dd id="fc-total">{m2(ex + fee_cents(ex), lang)}</dd></div>'
            f'<div><dt>{ui[4]}</dt><dd id="fc-pct">{pct1(fee_cents(ex), ex, lang)}</dd></div>'
            f'<div><dt>{ui[5]}</dt><dd id="fc-seller">{m2(ex, lang)}</dd></div></dl></div>' + FEE_JS)
    S = FEE_SRC
    if lang == 'en':
        faq = [
            ('Who pays Vinted fees?', f'The buyer. The Buyer Protection fee is added to the price at checkout, and the buyer also pays shipping. Selling is free: the seller receives the full item price (<a href="{S["free_en"]}" rel="noopener">Vinted help</a>).'),
            ('How much is the Vinted fee on a &euro;20 item?', f'{m2(fee_cents(ex), "en")}: &euro;0.70 plus 5% of &euro;20. The buyer pays {m2(ex + fee_cents(ex), "en")} before shipping.'),
            ('Why is the fee so high on cheap items?', f'Because &euro;0.70 of it is fixed. On a {m2(small, "en")} item the fee is {pct1(fee_cents(small), small, "en")} of the price; on a {m2(big, "en")} item it is {pct1(fee_cents(big), big, "en")}.'),
            ('Is VAT included in the Vinted fee?', f'Yes. Vinted says the total of its fees, VAT included, is added to the final price at checkout (<a href="{S["fr_help"]}" rel="noopener">Vinted help, in French</a>).'),
            ('Can I avoid the Buyer Protection fee?', f'Only by paying outside Vinted, and then you are not covered. Vinted says payments made outside its system are not covered by Buyer Protection (<a href="{S["safe_en"]}" rel="noopener">Vinted help</a>). Buying several items from one seller as a bundle is the legitimate way to pay the &euro;0.70 once.'),
        ]
        body = f"""
<section id="answer">
  <h2>Short answer</h2>
  <div class="lg-box lg-mint"><p>On Vinted&rsquo;s euro sites the buyer pays a <strong>Buyer Protection fee of &euro;0.70 plus 5% of the item price</strong>, VAT included, on top of the price and shipping. Selling is free: the seller gets the full item price. On a &euro;20 item the fee is {m2(fee_cents(ex), 'en')}, so the buyer pays {m2(ex + fee_cents(ex), 'en')} before shipping. We checked the rule against all {n} vinted.be listings SNYPD saw from {ws.day} {MONTHS_TXT['en'][ws.month - 1]} to {we.day} {MONTHS_TXT['en'][we.month - 1]} {we.year}: every fee matched to the cent.</p></div>
</section>
<section id="calculator">
  <h2>Vinted fee calculator</h2>
  <p>Type the item price as shown on the listing.</p>
  {calc}
  <p class="ct-note">Uses the rule in Vinted&rsquo;s price lists: &euro;0.70 (or $0.70 on vinted.com) plus 5% of the item price, rounded to the nearest cent. Shipping is extra and depends on the parcel and carrier. Vinted&rsquo;s checkout always shows the exact total; it describes the rule as what is &ldquo;usually&rdquo; charged.</p>
</section>
<section id="table">
  <h2>The fee at common prices</h2>
  {table(['ITEM PRICE', 'BUYER PROTECTION FEE', 'BUYER PAYS (BEFORE SHIPPING)', 'FEE AS % OF PRICE'], rows)}
  <p>The fixed &euro;0.70 is why the fee weighs most on cheap items: {pct1(fee_cents(small), small, 'en')} of a {m2(small, 'en')} item, but {pct1(fee_cents(big), big, 'en')} of a {m2(big, 'en')} one.</p>
</section>
<section id="bundles">
  <h2>Bundles pay the fixed part once</h2>
  <p>Vinted&rsquo;s price list charges the fee on the price of the item <em>or the bundle</em>. Buy {nb} items of {m2(b1, 'en')} from one seller separately and the fees add up to {m2(sep, 'en')}; buy them as one bundle and the fee is {m2(bun, 'en')}, saving {m2(sep - bun, 'en')}.</p>
</section>
<section id="sites">
  <h2>Fees by Vinted site</h2>
  <ul>
    <li><strong>vinted.fr, vinted.de, vinted.nl, vinted.it, vinted.es:</strong> 5% + &euro;0.70, per each site&rsquo;s price list (<a href="{S['fr_list']}" rel="noopener">vinted.fr</a>). <strong>vinted.be:</strong> the same, checked on {n} real listings.</li>
    <li><strong>vinted.com (US):</strong> $0.70 plus 5% of the agreed item price, not including shipping (<a href="{S['us_list']}" rel="noopener">price list</a>). Not checked against our own data.</li>
    <li><strong>vinted.co.uk:</strong> a range, &ldquo;3% to 8% + &pound;0.3 to &pound;0.8&rdquo;, VAT included, depending on the item, the order value and the order type (<a href="{S['uk_list']}" rel="noopener">price list</a>). No exact calculator is possible; the UK checkout shows the fee.</li>
  </ul>
  <p>Other Vinted sites publish their own price lists; check yours before relying on these numbers.</p>
</section>
<section id="sellers">
  <h2>What sellers pay</h2>
  <p>Nothing to list or sell: Vinted says selling is free and the seller keeps the full item price (<a href="{S['free_en']}" rel="noopener">Vinted help</a>). Sellers only pay if they choose paid visibility, such as bumping an item or a wardrobe showcase; Vinted&rsquo;s price list says those prices depend on duration, item price and reach.</p>
</section>
<section id="shipping">
  <h2>Who pays shipping</h2>
  <p>The buyer, at checkout, when buying with the Buy now button. The price depends on the parcel size and the buyer&rsquo;s and seller&rsquo;s locations. The exception is custom shipping, where the seller pays upfront (<a href="{S['ship_en']}" rel="noopener">Vinted help</a>).</p>
</section>
<section id="resellers">
  <h2>For resellers: count the real buying cost</h2>
  <p>What you pay for stock is the price, plus the Buyer Protection fee, plus shipping. A &ldquo;cheap&rdquo; &euro;5 item really costs {m2(small + fee_cents(small), 'en')} before shipping. SNYPD&rsquo;s dashboard shows each new listing&rsquo;s price including Buyer Protection, and its Market Report shows the typical asking price for an item&rsquo;s condition, so you can see the margin before you buy. See <a href="{SLUGS['deals']['en']}">how to find Vinted deals</a> and <a href="{SLUGS['prices']['en']}">typical Vinted prices</a>.</p>
  {figure('feed', 'en')}
</section>
<section id="method">
  <h2>How we checked</h2>
  <ul>
    <li>SNYPD stores the price, fee and total Vinted reports for every listing it sees. For {n} vinted.be listings seen from {ws.day} {MONTHS_TXT['en'][ws.month - 1]} to {we.day} {MONTHS_TXT['en'][we.month - 1]} {we.year}, priced {lo} to {hi}, the fee always equalled &euro;0.70 plus 5% of the price rounded to the nearest cent, and the total always equalled price plus fee.</li>
    <li>Price lists and help pages were read on {FEES_CHECKED['en']}. Vinted can change its fees; its checkout is the final word.</li>
  </ul>
</section>
<section id="faq">
  <h2>Questions</h2>
  {faq_html(faq)}
</section>
<section id="start">
  <h2>See new listings first</h2>
  {cta('en')}
</section>"""
        return page('fees', 'en', 'Vinted Fees 2026: Buyer Protection Fee Calculator | SNYPD',
                    'Vinted’s Buyer Protection fee is €0.70 + 5% of the price, paid by the buyer; selling is free. Calculator, fee table, and a check on real listings.',
                    'VINTED FEES &middot; CALCULATOR', 'Vinted fees: what buyers pay and sellers keep',
                    f'Buying on Vinted costs more than the price on the listing. Here is the Buyer Protection fee for any price, how it differs by Vinted site, and what it means for your margin, checked against {n} real listings.',
                    [('answer', 'Short answer'), ('calculator', 'Calculator'), ('table', 'Fee table'), ('bundles', 'Bundles'), ('sites', 'By Vinted site'), ('sellers', 'Sellers'), ('shipping', 'Shipping'), ('resellers', 'For resellers'), ('method', 'How we checked'), ('faq', 'Questions')],
                    body, [faq_ld(faq)])
    faq = [
        ('Qui paie les frais Vinted ?', f'L’acheteur. Les frais de protection acheteurs s’ajoutent au prix au paiement, et l’acheteur paie aussi la livraison. Vendre est gratuit : le vendeur reçoit le prix complet de l’article (<a href="{S["free_fr"]}" rel="noopener">aide Vinted</a>).'),
        ('Combien coûtent les frais Vinted sur un article à 20&nbsp;&euro; ?', f'{m2(fee_cents(ex), "fr")} : 0,70&nbsp;&euro; plus 5&nbsp;% de 20&nbsp;&euro;. L’acheteur paie {m2(ex + fee_cents(ex), "fr")} hors livraison.'),
        ('Pourquoi les frais sont-ils si élevés sur les petits prix ?', f'Parce que 0,70&nbsp;&euro; sont fixes. Sur un article à {m2(small, "fr")}, les frais font {pct1(fee_cents(small), small, "fr")} du prix ; sur un article à {m2(big, "fr")}, {pct1(fee_cents(big), big, "fr")}.'),
        ('La TVA est-elle comprise dans les frais Vinted ?', f'Oui. Vinted indique que le total des frais Vinted, TVA incluse, est ajouté au prix final au paiement (<a href="{S["fr_help"]}" rel="noopener">aide Vinted</a>).'),
        ('Peut-on éviter les frais de protection acheteurs ?', f'Seulement en payant hors de Vinted, et tu n’es alors plus protégé : Vinted indique que les paiements effectués en dehors de son système ne sont pas couverts (<a href="{S["safe_fr"]}" rel="noopener">aide Vinted</a>). Acheter plusieurs articles au même vendeur en lot est la façon normale de ne payer les 0,70&nbsp;&euro; qu’une fois.'),
    ]
    body = f"""
<section id="reponse">
  <h2>Réponse courte</h2>
  <div class="lg-box lg-mint"><p>Sur les sites Vinted en euros, l’acheteur paie des <strong>frais de protection acheteurs de 0,70&nbsp;&euro; plus 5&nbsp;% du prix de l’article</strong>, TVA incluse, en plus du prix et de la livraison. Vendre est gratuit : le vendeur reçoit le prix complet. Sur un article à 20&nbsp;&euro;, les frais sont de {m2(fee_cents(ex), 'fr')}, donc l’acheteur paie {m2(ex + fee_cents(ex), 'fr')} hors livraison. Nous avons vérifié la règle sur les {n} annonces vinted.be vues par SNYPD du {date_txt(ws.isoformat(), 'fr')} au {date_txt(we.isoformat(), 'fr')} : tous les frais correspondaient au centime près.</p></div>
</section>
<section id="calculateur">
  <h2>Calculateur des frais Vinted</h2>
  <p>Saisis le prix de l’article tel qu’il apparaît sur l’annonce.</p>
  {calc}
  <p class="ct-note">Applique la règle des grilles tarifaires de Vinted : 0,70&nbsp;&euro; (ou 0,70&nbsp;$ sur vinted.com) plus 5&nbsp;% du prix, arrondi au centime le plus proche. La livraison s’ajoute et dépend du colis et du transporteur. Le paiement Vinted affiche toujours le total exact ; Vinted décrit cette règle comme ce qui est facturé « généralement ».</p>
</section>
<section id="tableau">
  <h2>Les frais aux prix courants</h2>
  {table(['PRIX DE L’ARTICLE', 'FRAIS DE PROTECTION', 'L’ACHETEUR PAIE (HORS LIVRAISON)', 'FRAIS EN % DU PRIX'], rows)}
  <p>Les 0,70&nbsp;&euro; fixes expliquent pourquoi les frais pèsent surtout sur les petits prix : {pct1(fee_cents(small), small, 'fr')} d’un article à {m2(small, 'fr')}, mais {pct1(fee_cents(big), big, 'fr')} d’un article à {m2(big, 'fr')}.</p>
</section>
<section id="lots">
  <h2>En lot, la partie fixe n’est payée qu’une fois</h2>
  <p>La grille tarifaire de Vinted applique les frais au prix de l’article <em>ou du lot</em>. Achète {nb} articles à {m2(b1, 'fr')} chez le même vendeur séparément et les frais font {m2(sep, 'fr')} ; achète-les en un seul lot et les frais sont de {m2(bun, 'fr')}, soit {m2(sep - bun, 'fr')} d’économie.</p>
</section>
<section id="sites">
  <h2>Les frais selon le site Vinted</h2>
  <ul>
    <li><strong>vinted.fr, vinted.de, vinted.nl, vinted.it, vinted.es :</strong> 5&nbsp;% + 0,70&nbsp;&euro;, selon la grille tarifaire de chaque site (<a href="{S['fr_list']}" rel="noopener">vinted.fr</a>). <strong>vinted.be :</strong> pareil, vérifié sur {n} annonces réelles.</li>
    <li><strong>vinted.com (États-Unis) :</strong> 0,70&nbsp;$ plus 5&nbsp;% du prix convenu, hors livraison (<a href="{S['us_list']}" rel="noopener">grille tarifaire</a>). Non vérifié sur nos données.</li>
    <li><strong>vinted.co.uk :</strong> une fourchette, de 3 à 8&nbsp;% + 0,30 à 0,80&nbsp;&pound;, TVA incluse, selon l’article, le montant et le type de commande (<a href="{S['uk_list']}" rel="noopener">grille tarifaire</a>). Pas de calcul exact possible ; le paiement affiche les frais.</li>
  </ul>
  <p>Les autres sites Vinted publient leur propre grille tarifaire ; vérifie la tienne avant de te fier à ces chiffres.</p>
</section>
<section id="vendeurs">
  <h2>Ce que paient les vendeurs</h2>
  <p>Rien pour mettre en ligne ni pour vendre : Vinted indique que vendre est gratuit et que le vendeur garde le prix complet (<a href="{S['free_fr']}" rel="noopener">aide Vinted</a>). Le vendeur ne paie que s’il choisit une option de visibilité, comme le Boost ou la Vitrine ; la grille tarifaire précise que leur prix dépend de la durée, du prix de l’article et de la zone de diffusion.</p>
</section>
<section id="livraison">
  <h2>Qui paie la livraison</h2>
  <p>L’acheteur, au paiement, quand il achète avec le bouton Acheter. Le prix dépend de la taille du colis et de la localisation de l’acheteur et du vendeur. Les frais de port s’affichent au paiement et s’ajoutent au total (<a href="{S['ship_fr']}" rel="noopener">aide Vinted</a>).</p>
</section>
<section id="revendeurs">
  <h2>Pour les revendeurs : compte le vrai prix d’achat</h2>
  <p>Ton stock te coûte le prix, plus les frais de protection acheteurs, plus la livraison. Un article « pas cher » à 5&nbsp;&euro; coûte en réalité {m2(small + fee_cents(small), 'fr')} hors livraison. Le tableau de bord SNYPD affiche le prix de chaque nouvelle annonce protection acheteurs incluse, et son Market Report montre le prix demandé typique selon l’état, pour voir ta marge avant d’acheter. Voir aussi <a href="{SLUGS['prices']['fr']}">les prix Vinted typiques</a>.</p>
  {figure('feed', 'fr')}
</section>
<section id="methode">
  <h2>Comment nous avons vérifié</h2>
  <ul>
    <li>SNYPD enregistre le prix, les frais et le total indiqués par Vinted pour chaque annonce qu’il voit. Sur {n} annonces vinted.be vues du {date_txt(ws.isoformat(), 'fr')} au {date_txt(we.isoformat(), 'fr')}, de {lo} à {hi}, les frais étaient toujours égaux à 0,70&nbsp;&euro; plus 5&nbsp;% du prix arrondi au centime, et le total toujours égal au prix plus les frais.</li>
    <li>Grilles tarifaires et pages d’aide lues le {FEES_CHECKED['fr']}. Vinted peut changer ses frais ; le total affiché au paiement fait foi.</li>
  </ul>
</section>
<section id="questions">
  <h2>Questions</h2>
  {faq_html(faq)}
</section>
<section id="essayer">
  <h2>Vois les nouvelles annonces en premier</h2>
  {cta('fr')}
</section>"""
    return page('fees', 'fr', 'Frais Vinted 2026 : calcul de la protection acheteurs | SNYPD',
                'Les frais Vinted : 0,70 € + 5 % du prix, payés par l’acheteur ; vendre est gratuit. Calculateur, tableau des frais et vérification sur de vraies annonces.',
                'FRAIS VINTED &middot; CALCULATEUR', 'Frais Vinted : ce que paie l’acheteur, ce que garde le vendeur',
                f'Acheter sur Vinted coûte plus que le prix affiché. Voici les frais de protection acheteurs pour n’importe quel prix, les différences entre sites Vinted et ce que ça change pour ta marge, vérifiés sur {n} annonces réelles.',
                [('reponse', 'Réponse courte'), ('calculateur', 'Calculateur'), ('tableau', 'Tableau des frais'), ('lots', 'Lots'), ('sites', 'Par site Vinted'), ('vendeurs', 'Vendeurs'), ('livraison', 'Livraison'), ('revendeurs', 'Revendeurs'), ('methode', 'Vérification'), ('questions', 'Questions')],
                body, [faq_ld(faq)])


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
    write('vinted-deals.html', page_deals('en'))
    for lang in (('en', 'fr') if FR_LIVE else ('en',)):
        write(SLUGS['monitor'][lang].lstrip('/') + '.html', page_monitor(lang))
    for lang in (('en', 'fr') if FR_LIVE else ('en',)):
        write(SLUGS['fees'][lang].lstrip('/') + '.html', page_fees(lang))
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator='\n')
    w.writerow(['item', 'search', 'group', 'typical_asking_eur', 'p25_eur', 'p75_eur', 'listings', 'sellers', 'confidence', 'outlier_high_pct'])
    w.writerows(csv_rows)
    buf.write('# Source: SNYPD Market Report (median asking price, not sold price), listings seen on vinted.be in the 14 days to 2026-09-28. https://www.snypd.store/vinted-prices\n')
    write(REPORT_CSV, buf.getvalue())
