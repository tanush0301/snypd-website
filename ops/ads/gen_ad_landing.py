#!/usr/bin/env python3
# Builds the landing pages for paid ads, separate from the SEO pages:
#   start.html     -> /start     (English)
#   fr/start.html  -> /fr/start  (French, added 7 Oct 2026 for French search ads)
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
# Google and Reddit ads use it too (outreach/11-ad-channels.md).
#
# RULES: every sentence must be on outreach/00-fact-sheet.md. Never: instant, real-time,
# fastest, a catch-time figure, safe, allowed by Vinted, savings or price claims.
# French: "tu", typographic apostrophe, no-break space ( ) before : ; ? ! and before EUR.
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'ops', 'seo'))
from gen_content import CSS, COMPARE_CSS, PLANS_HEAD, PLANS_ROWS, SITE, EMAIL, esc, figure, table  # noqa: E402

NB = ' '

T = {
    'en': dict(
        path='/start', out='start.html',
        title='SNYPD - Push alerts for new Vinted listings',
        desc=('Paste a Vinted search link with your filters. SNYPD checks it about every 30 seconds '
              'and sends a push notification when a new listing matches. Free plan: 1 search, no card, 24/7 for the first 7 days.'),
        steps=[
            ('Copy your search', 'On Vinted, set your filters (brand, size, price, condition) and copy the link from the address bar.'),
            ('Paste it into SNYPD', 'Every filter in the link is kept. A link SNYPD cannot read in full is refused, not trimmed.'),
            ('Get a push', 'SNYPD checks the search about every 30 seconds and sends a push notification when a new '
                           'listing matches. You open it on Vinted and decide.'),
        ],
        never=[
            'Never asks for your Vinted password and never signs in to your Vinted account.',
            'Never buys, makes offers or messages sellers. Every purchase is yours to make on Vinted.',
            'No Telegram, Discord or email alerts: push notifications and the dashboard only.',
        ],
        h_how='How it works', h_never='What SNYPD never does', h_where='Where it works', h_plans='Plans', h_who='Who runs SNYPD',
        where='Every Vinted site in Europe and the US: 26 sites. Alerts arrive on your phone or computer. On iPhone they work after you add SNYPD to your Home Screen, because Apple only allows web push there.',
        plans_note='Prices include VAT. The free plan needs no card and has no time limit or cap on notifications; it watches your search 24/7 for the first 7 days, then while your dashboard is open. Paid plans keep watching with the dashboard closed. 14-day refund on the first payment of a plan.',
        box='<strong>Start with one search, free.</strong> No card. The first 7 days run 24/7 with alerts.',
        start='START FREE', nav_cta='START FREE', see_plans='SEE PLANS', how_btn='HOW IT WORKS', login='LOG IN',
        who1='Built by a Belgian sneaker reseller. Operator: Tanush Khandelwal, Belgium. Contact: ',
        who2='SNYPD is independent and not affiliated with or endorsed by Vinted.',
        eyebrow='FOR VINTED BUYERS AND RESELLERS',
        h1='A push alert when a new listing matches your Vinted search',
        lead='Paste a Vinted search link with your filters. SNYPD checks it about every 30 seconds and sends a push notification to your phone or computer when a new listing matches. Free plan: 1 search, no card, 24/7 for the first 7 days.',
        foot='SNYPD &middot; NOT AFFILIATED WITH VINTED',
        legal=('Privacy', 'Terms', 'Contact', 'Cookies', 'Cookie settings'),
    ),
    'fr': dict(
        path='/fr/start', out=os.path.join('fr', 'start.html'),
        title='SNYPD - Alertes push pour les nouvelles annonces Vinted',
        desc=('Colle le lien d’une recherche Vinted avec tes filtres. SNYPD la vérifie environ toutes les 30 secondes '
              'et envoie une notification push quand une nouvelle annonce correspond. Plan gratuit' + NB + ': 1 recherche, sans carte, 24h/24 les 7 premiers jours.'),
        steps=[
            ('Copie ta recherche', 'Sur Vinted, règle tes filtres (marque, taille, prix, état) et copie le lien dans la barre d’adresse.'),
            ('Colle-la dans SNYPD', 'Tous les filtres du lien sont conservés. Un lien que SNYPD ne peut pas lire en entier est refusé, pas tronqué.'),
            ('Reçois une notification push', 'SNYPD vérifie la recherche environ toutes les 30 secondes et envoie une notification push '
                                             'quand une nouvelle annonce correspond. Tu l’ouvres sur Vinted et tu décides.'),
        ],
        never=[
            'Ne demande jamais ton mot de passe Vinted et ne se connecte jamais à ton compte Vinted.',
            'N’achète rien, ne fait pas d’offre et n’envoie aucun message aux vendeurs. Chaque achat, c’est toi qui le fais sur Vinted.',
            'Pas d’alertes Telegram, Discord ou e-mail' + NB + ': notifications push et tableau de bord uniquement.',
        ],
        h_how='Comment ça marche', h_never='Ce que SNYPD ne fait jamais', h_where='Où ça marche', h_plans='Plans', h_who='Qui gère SNYPD',
        where=('Tous les sites Vinted d’Europe et des États-Unis' + NB + ': 26 sites. Les alertes arrivent sur ton téléphone ou ton ordinateur. '
               'Sur iPhone, elles fonctionnent une fois SNYPD ajouté à ton écran d’accueil, car Apple n’autorise les notifications web push que là.'),
        plans_note=('Prix TVA incluse. Le plan gratuit ne demande pas de carte et n’a ni limite de durée ni plafond de notifications' + NB + '; '
                    'il surveille ta recherche 24h/24 pendant les 7 premiers jours, puis tant que ton tableau de bord est ouvert. Les plans payants continuent de surveiller tableau de bord fermé. '
                    'Remboursement sous 14 jours sur le premier paiement d’un plan.'),
        box='<strong>Commence avec une recherche, gratuitement.</strong> Sans carte. Les 7 premiers jours tournent 24h/24 avec les alertes.',
        start='COMMENCER GRATUITEMENT', nav_cta='COMMENCER', see_plans='VOIR LES PLANS', how_btn='COMMENT ÇA MARCHE', login='CONNEXION',
        who1='Créé par un revendeur de sneakers belge. Exploitant' + NB + ': Tanush Khandelwal, Belgique. Contact' + NB + ': ',
        who2='SNYPD est indépendant, sans lien avec Vinted et non approuvé par Vinted.',
        eyebrow='POUR LES ACHETEURS ET REVENDEURS VINTED',
        h1='Une notification push quand une nouvelle annonce correspond à ta recherche Vinted',
        lead=('Colle le lien d’une recherche Vinted avec tes filtres. SNYPD la vérifie environ toutes les 30 secondes et envoie une '
              'notification push sur ton téléphone ou ton ordinateur quand une nouvelle annonce correspond. Plan gratuit' + NB + ': 1 recherche, sans carte, 24h/24 les 7 premiers jours.'),
        foot='SNYPD &middot; NON AFFILIÉ À VINTED',
        legal=('Confidentialité', 'Conditions', 'Contact', 'Cookies', 'Paramètres des cookies'),
    ),
}


def build(lang):
    t = T[lang]
    body = f"""
<section id="how">
  <h2>{esc(t['h_how'])}</h2>
  <ol>{''.join('<li><strong>%s.</strong> %s</li>' % (esc(a), esc(d)) for a, d in t['steps'])}</ol>
  {figure('feed', lang)}
</section>
<section id="never">
  <h2>{esc(t['h_never'])}</h2>
  <ul>{''.join('<li>%s</li>' % esc(x) for x in t['never'])}</ul>
</section>
<section id="where">
  <h2>{esc(t['h_where'])}</h2>
  <p>{esc(t['where'])}</p>
</section>
<section id="plans">
  <h2>{esc(t['h_plans'])}</h2>
  {table(PLANS_HEAD[lang], PLANS_ROWS[lang], us_row=0)}
  <p>{esc(t['plans_note'])}</p>
  <div class="lg-box lg-mint"><p>{t['box']}</p>
    <div class="ct-actions"><a class="ct-btn" href="/signup">{t['start']}</a><a class="ct-btn ct-ghost" href="/plans">{t['see_plans']}</a></div></div>
</section>
<section id="who">
  <h2>{esc(t['h_who'])}</h2>
  <p>{esc(t['who1'])}<a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
  <p>{esc(t['who2'])}</p>
</section>"""
    p, l = t['path'], t['legal']
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(t['title'])}</title>
<meta name="description" content="{esc(t['desc'])}">
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="{SITE}{p}">
<meta property="og:title" content="{esc(t['title'])}">
<meta property="og:description" content="{esc(t['desc'])}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE}{p}">
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
    <a class="lg-navlink lg-login" href="/login">{t['login']}</a>
    <a class="lg-cta" href="/signup">{t['nav_cta']}</a>
  </div>
</header>
<main>
  <div class="lg-head">
    <div class="lg-wrap lg-head-in">
      <span class="lg-eyebrow">{esc(t['eyebrow'])}</span>
      <h1 class="lg-h1">{esc(t['h1'])}</h1>
      <p class="lg-lead">{esc(t['lead'])}</p>
      <div class="ct-actions"><a class="ct-btn" href="/signup">{t['start']}</a><a class="ct-btn ct-ghost" href="#how">{t['how_btn']}</a></div>
    </div>
  </div>
  <div class="lg-wrap lg-grid lg-wide">
    <article class="lg-doc">
{body}
    </article>
  </div>
</main>
<footer class="lg-foot">
  <div class="lg-wrap lg-foot-in">
    <div class="lg-foot-a">
      <small>{t['foot']}</small>
      <span class="lg-foot-l"><a href="/plans">Plans</a><a href="/faq">FAQ</a><a href="/support">Support</a></span>
    </div>
    <nav class="lg-foot-l" aria-label="Legal" style="align-items:flex-start;"><a href="/privacy">{l[0]}</a><a href="/terms">{l[1]}</a><a href="mailto:{EMAIL}">{l[2]}</a><a href="/cookies">{l[3]}</a><a href="/cookies" data-cookie-settings>{l[4]}</a></nav>
  </div>
</footer>
</body>
</html>
"""


for lang in ('en', 'fr'):
    html_out = build(lang)
    path = os.path.join(ROOT, T[lang]['out'])
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(html_out)
    print('wrote', T[lang]['out'], len(html_out.encode('utf-8')), 'bytes')
