#!/usr/bin/env python3
# Vinted price guide: one page per item (ops/seo/price_items.json) plus a hub, in English and
# French, built only from SNYPD's own Market Report output (ops/seo/data/price-guide.json, made
# by ops/seo/price_guide_batch.py inside the backend container).
#
#   python ops/seo/gen_price_guide.py          (then python ops/seo/prepublish.py)
#
# RULES
# - Asking prices only. Never "sold", "sells for", "worth" as a fact: Vinted publishes no sale
#   prices and SNYPD cannot see them.
# - An item gets a page only when its report is verdict "ok", confidence medium/high and at
#   least MIN_LISTINGS listings: no thin pages. Conditions with fewer than MIN_COND listings, or
#   whose prices are too spread out, say so instead of printing a number.
# - The data is vinted.be listings that matched SNYPD users' searches in the last 14 days.
#   Every page says so. Refresh monthly (see ops/seo/price_guide_batch.py).
import datetime, json, os, sys, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_content as gc  # noqa: E402
from gen_content import SITE, SLUGS, PAGE_MODIFIED, esc, table, faq_ld, faq_html, money, num, fee_cents, FEE_SRC, \
    DATASET_CREATOR, DATASET_LICENSE, write  # noqa: E402

ROOT = gc.ROOT
ITEMS = json.load(open(os.path.join(ROOT, 'ops', 'seo', 'price_items.json'), encoding='utf-8'))['items']
DATA = json.load(open(os.path.join(ROOT, 'ops', 'seo', 'data', 'price-guide.json'), encoding='utf-8'))
MIN_LISTINGS = 100
MIN_COND = 10
LANGS = ('en', 'fr')
HUB = {'en': '/vinted-price-guide', 'fr': '/fr/guide-prix-vinted'}
FEES_CHECKED = gc.FEES_CHECKED

GEN = datetime.datetime.fromisoformat(DATA['generated_at'].replace('Z', '+00:00')).date()
WIN_DAYS = DATA.get('window_days', 14)
WIN_FROM = GEN - datetime.timedelta(days=WIN_DAYS)
MONTHS = gc.MONTHS_TXT
CAT = {'sneakers': {'en': 'Sneakers', 'fr': 'Sneakers'}, 'clothing': {'en': 'Clothing', 'fr': 'Vêtements'},
       'accessories': {'en': 'Bags, watches and jewellery', 'fr': 'Sacs, montres et bijoux'},
       'collectibles': {'en': 'Collectibles', 'fr': 'Objets de collection'}}
COND = {'New, with tag': {'en': 'New with tags', 'fr': 'Neuf avec étiquette'},
        'New, no tag': {'en': 'New without tags', 'fr': 'Neuf sans étiquette'},
        'Very good': {'en': 'Very good', 'fr': 'Très bon état'},
        'Good': {'en': 'Good', 'fr': 'Bon état'},
        'Satisfactory': {'en': 'Satisfactory', 'fr': 'Satisfaisant'}}


def plain_eur(cents, lang):
    """Euro amount for <title>/description (no HTML entities)."""
    return money(cents, lang).replace('&euro;', '€').replace('&nbsp;', ' ')


def window(lang):
    a, b = WIN_FROM, GEN
    m = MONTHS[lang]
    if lang == 'en':
        return ('%d %s to %d %s %d' % (a.day, m[a.month - 1], b.day, m[b.month - 1], b.year)) if a.month != b.month \
            else '%d-%d %s %d' % (a.day, b.day, m[b.month - 1], b.year)
    return ('du %d %s au %d %s %d' % (a.day, m[a.month - 1], b.day, m[b.month - 1], b.year)) if a.month != b.month \
        else 'du %d au %d %s %d' % (a.day, b.day, m[b.month - 1], b.year)


def month_year(lang):
    return '%s %d' % (MONTHS[lang][GEN.month - 1], GEN.year)


def views():
    """slug -> customer_view, only for items that pass the publication rule."""
    by_q = {r['q']: r['view'] for r in DATA['results'] if r.get('ok')}
    out = {}
    for it in ITEMS:
        if it.get('skip'):
            continue  # one price would mislead (see price_items.json)
        v = by_q.get(it['query'])
        if v and v.get('display_verdict') == 'ok' and v.get('confidence') in ('medium', 'high') \
                and (v.get('sample_size') or 0) >= MIN_LISTINGS and v.get('typical_cents') and v.get('range_cents'):
            out[it['slug']] = v
    return out


V = views()
PUB = [it for it in ITEMS if it['slug'] in V]
for it in PUB:
    key = 'pg:' + it['slug']
    SLUGS[key] = {l: HUB[l] + '/' + it['slug'] for l in LANGS}
    PAGE_MODIFIED[key] = GEN.isoformat()
SLUGS['guide'] = dict(HUB)
PAGE_MODIFIED['guide'] = GEN.isoformat()


def item_url(it, lang):
    return HUB[lang] + '/' + it['slug']


def alert_href(it, lo_cents):
    return '/signup?' + urllib.parse.urlencode({'hunt': it['query'], 'max': lo_cents // 100})


def cond_rows(v, lang):
    rows, notes = [], []
    for c in v.get('by_condition') or []:
        label = COND.get(c.get('condition_label'), {}).get(lang, c.get('condition_label'))
        n = c.get('sample_size') or 0
        if n < MIN_COND:
            continue
        ok = c.get('verdict') == 'ok' and c.get('typical_cents') and c.get('range_cents')
        if ok:
            r = c['range_cents']
            rows.append([label, num(n, lang), money(c['typical_cents'], lang), '%s &ndash; %s' % (money(r['low'], lang), money(r['high'], lang))])
        else:
            rows.append([label, num(n, lang), '&ndash;', {'en': 'too spread out for one price', 'fr': 'prix trop dispersés pour un chiffre'}[lang]])
    return rows


def cond_compare(v, lang):
    """One sentence comparing the best-new and the 'very good' condition, when both are solid."""
    by = {c.get('condition_label'): c for c in v.get('by_condition') or []
          if c.get('verdict') == 'ok' and (c.get('sample_size') or 0) >= MIN_COND and c.get('typical_cents')}
    new = by.get('New, with tag') or by.get('New, no tag')
    used = by.get('Very good')
    if not new or not used or used['typical_cents'] <= 0:
        return ''
    diff = round(100.0 * (new['typical_cents'] - used['typical_cents']) / used['typical_cents'])
    nl = COND[new['condition_label']][lang]
    if diff == 0:
        return {'en': '<p>%s and very good listings ask about the same.</p>' % nl,
                'fr': '<p>Les annonces « %s » et « Très bon état » demandent à peu près le même prix.</p>' % nl}[lang]
    more = diff > 0
    return {'en': '<p>%s listings ask about %d%% %s than very good ones (%s against %s).</p>'
                  % (nl, abs(diff), 'more' if more else 'less', money(new['typical_cents'], 'en'), money(used['typical_cents'], 'en')),
            'fr': '<p>Les annonces «&nbsp;%s&nbsp;» demandent environ %d&nbsp;%% %s que celles en «&nbsp;Très bon état&nbsp;» (%s contre %s).</p>'
                  % (nl, abs(diff), 'de plus' if more else 'de moins', money(new['typical_cents'], 'fr'), money(used['typical_cents'], 'fr'))}[lang]


def dataset_ld(it, v, lang, url):
    name = {'en': '%s asking prices on Vinted (vinted.be, %s)' % (it['name'], window('en')),
            'fr': 'Prix demandés pour %s sur Vinted (vinted.be, %s)' % (it['name'], window('fr'))}[lang]
    desc = {'en': 'Median and 25th-75th percentile asking price of %s listings on vinted.be that matched SNYPD users\' searches, overall and by condition. Asking prices, not sale prices.' % it['name'],
            'fr': 'Prix demandé médian et 25e-75e centile des annonces %s sur vinted.be correspondant aux recherches des utilisateurs de SNYPD, au total et par état. Prix demandés, pas prix de vente.' % it['name']}[lang]
    return {'@context': 'https://schema.org', '@type': 'Dataset', 'name': name, 'description': desc, 'url': SITE + url,
            'creator': DATASET_CREATOR, 'license': DATASET_LICENSE, 'inLanguage': lang, 'isAccessibleForFree': True,
            'temporalCoverage': '%s/%s' % (WIN_FROM.isoformat(), GEN.isoformat()), 'spatialCoverage': 'Belgium',
            'variableMeasured': ['asking price (median)', 'asking price (25th percentile)', 'asking price (75th percentile)', 'listing count'],
            'measurementTechnique': 'Listings collected by SNYPD from vinted.be search results',
            'dateModified': GEN.isoformat()}


def related(it, lang):
    same = [x for x in PUB if x['cat'] == it['cat'] and x['slug'] != it['slug']]
    same.sort(key=lambda x: (x['brand'] != it['brand'], -V[x['slug']]['sample_size']))
    links = ''.join('<li><a href="%s">%s</a>%s: %s</li>' % (item_url(x, lang), esc(x.get('name_fr', x['name']) if lang == 'fr' else x['name']), ' ' if lang == 'fr' else '', money(V[x['slug']]['typical_cents'], lang)) for x in same[:8])
    return '<ul>%s</ul>' % links if links else ''


def page_item(it, lang):
    v = V[it['slug']]
    name, typ, lo, hi = it.get('name_fr', it['name']) if lang == 'fr' else it['name'], v['typical_cents'], v['range_cents']['low'], v['range_cents']['high']
    n, sellers, out_pct = v['sample_size'], v.get('distinct_sellers') or 0, v.get('outlier_pct')
    url = item_url(it, lang)
    rows = cond_rows(v, lang)
    fee = fee_cents(typ)
    win = window(lang)
    if lang == 'en':
        faq = [
            ('How much does %s cost on Vinted?' % name,
             'The typical asking price on vinted.be is %s (median of %s listings, %s). Half of the listings ask between %s and %s.' % (money(typ, 'en'), num(n, 'en'), win, money(lo, 'en'), money(hi, 'en'))),
            ('Is this what %s sells for on Vinted?' % name,
             'No. These are asking prices: what sellers list it for. Vinted does not publish what an item finally sold for, and buyers can make offers below the asking price.'),
            ('What is a good price for %s on Vinted?' % name,
             'Below %s is in the cheapest quarter of the %s listings SNYPD saw. Check the condition and photos: the cheapest listings are often the most worn.' % (money(lo, 'en'), num(n, 'en'))),
        ]
        outl = ('<li><strong>Expensive outliers:</strong> %s%% of listings were priced far above the rest; the median ignores them.</li>' % out_pct) if out_pct and out_pct >= 5 else ''
        body = f"""
<section id="glance">
  <h2>{esc(name)} on Vinted at a glance</h2>
  <div class="lg-box lg-mint"><ul>
    <li><strong>Typical asking price (median):</strong> {money(typ, 'en')}</li>
    <li><strong>Middle half of listings:</strong> {money(lo, 'en')} &ndash; {money(hi, 'en')}</li>
    <li><strong>Listings:</strong> {num(n, 'en')} from {num(sellers, 'en')} different sellers</li>
    <li><strong>Where and when:</strong> vinted.be, {win}</li>{outl}
  </ul></div>
</section>
<section id="condition">
  <h2>{esc(name)} price by condition</h2>
  {table(['CONDITION', 'LISTINGS', 'TYPICAL ASKING PRICE', 'MIDDLE HALF'], rows)}
  {cond_compare(v, 'en')}
  <p>Condition is the seller's own label on Vinted.</p>
</section>
<section id="good-price">
  <h2>What is a good price for {esc(name)}?</h2>
  <p>A quarter of the listings ask {money(lo, 'en')} or less, half ask between {money(lo, 'en')} and {money(hi, 'en')}, and a quarter ask more than {money(hi, 'en')}. Under {money(lo, 'en')} is the cheapest quarter. Use it as a filter, not as proof of a bargain: a cheap listing can be more worn, a different colourway, a kids&rsquo; size or a fake, so check the photos and details.</p>
  <p>At the typical {money(typ, 'en')}, the buyer pays {money(typ, 'en')} plus {money(fee, 'en')} Vinted Buyer Protection, so {money(typ + fee, 'en')} before shipping (<a href="{FEE_SRC['fr_list']}" rel="nofollow">Vinted's price list</a>, checked {FEES_CHECKED['en']}). Selling is free for private sellers (<a href="{FEE_SRC['free_en']}" rel="nofollow">Vinted help</a>). Work out any other price with the <a href="{SLUGS['fees']['en']}">Vinted fee calculator</a>.</p>
</section>
<section id="alert">
  <h2>Get an alert for a cheap {esc(name)}</h2>
  <p>SNYPD checks a Vinted search about every 30 seconds and sends new matches to your phone, so you don't have to keep refreshing Vinted. Start the search below with a maximum of {money(lo, 'en')}, the cheapest quarter, and change it any time.</p>
  <div class="ct-actions"><a class="ct-btn" href="{esc(alert_href(it, lo))}">ALERT ME UNDER {money(lo, 'en')}</a><a class="ct-btn ct-ghost" href="{SLUGS['bot']['en']}">HOW SNYPD WORKS</a></div>
  <p class="ct-note">Free: one search, 24/7 for the first @@trial_days@@ days. No card.</p>
</section>
<section id="method">
  <h2>How these numbers are made</h2>
  <p>SNYPD collects new vinted.be listings for the searches its users run. This page uses the {num(n, 'en')} {esc(name)} listings it saw {win}: the typical price is the median asking price, the middle half runs from the 25th to the 75th percentile. These are asking prices, not sale prices: Vinted does not publish what items sell for. Prices on other Vinted sites can differ. Updated monthly; the figures are free to reuse with a link to this page (<a href="{DATASET_LICENSE}" rel="license">CC BY 4.0</a>).</p>
</section>
<section id="faq">
  <h2>Questions</h2>
  {faq_html(faq)}
</section>
<section id="more">
  <h2>More Vinted prices</h2>
  {related(it, 'en')}
  <p>Every item: <a href="{HUB['en']}">the Vinted price guide</a>.</p>
</section>"""
        title = '%s price on Vinted: %s typical (%s) | SNYPD' % (name, plain_eur(typ, 'en'), month_year('en'))
        desc = ('What %s costs on Vinted: typical asking price %s, half of %s listings between %s and %s, by condition. vinted.be, %s.'
                % (name, plain_eur(typ, 'en'), num(n, 'en'), plain_eur(lo, 'en'), plain_eur(hi, 'en'), win))
        lead = ('The typical asking price for %s on Vinted is <strong>%s</strong>. Half of the %s listings SNYPD saw on vinted.be (%s) asked between %s and %s. These are asking prices from %s sellers, not sale prices.'
                % (esc(name), money(typ, 'en'), num(n, 'en'), win, money(lo, 'en'), money(hi, 'en'), num(sellers, 'en')))
        toc = [('glance', 'At a glance'), ('condition', 'By condition'), ('good-price', 'Good price'), ('alert', 'Get an alert'), ('method', 'Method'), ('faq', 'Questions')]
        return gc.page('pg:' + it['slug'], 'en', title, desc, 'VINTED PRICE GUIDE', 'What %s costs on Vinted' % esc(name), lead, toc, body,
                       [faq_ld(faq), dataset_ld(it, v, 'en', url)], parent=('Vinted price guide', HUB['en']))
    # ---------------------------------------------------------------- French
    nb = ' '
    faq = [
        ('Combien coûte %s sur Vinted%s?' % (name, nb),
         'Le prix demandé typique sur vinted.be est de %s (médiane de %s annonces, %s). La moitié des annonces demandent entre %s et %s.' % (money(typ, 'fr'), num(n, 'fr'), win, money(lo, 'fr'), money(hi, 'fr'))),
        ('Est-ce le prix auquel %s se vend sur Vinted%s?' % (name, nb),
         'Non. Ce sont des prix demandés, ceux affichés par les vendeurs. Vinted ne publie pas le prix final d’une vente, et les acheteurs peuvent faire des offres en dessous.'),
        ('Quel est un bon prix pour %s sur Vinted%s?' % (name, nb),
         'Sous %s, on est dans le quart le moins cher des %s annonces vues par SNYPD. Regarde bien l’état et les photos%s: les annonces les moins chères sont souvent les plus usées.' % (money(lo, 'fr'), num(n, 'fr'), nb)),
    ]
    outl = ('<li><strong>Prix aberrants%s:</strong> %s%s%% des annonces demandaient bien plus que les autres%s; la médiane n’en tient pas compte.</li>' % (nb, str(out_pct).replace('.', ','), nb, nb)) if out_pct and out_pct >= 5 else ''
    body = f"""
<section id="resume">
  <h2>{esc(name)} sur Vinted en bref</h2>
  <div class="lg-box lg-mint"><ul>
    <li><strong>Prix demandé typique (médiane){nb}:</strong> {money(typ, 'fr')}</li>
    <li><strong>Moitié centrale des annonces{nb}:</strong> {money(lo, 'fr')} &ndash; {money(hi, 'fr')}</li>
    <li><strong>Annonces{nb}:</strong> {num(n, 'fr')}, de {num(sellers, 'fr')} vendeurs différents</li>
    <li><strong>Où et quand{nb}:</strong> vinted.be, {win}</li>{outl}
  </ul></div>
</section>
<section id="etat">
  <h2>Prix de {esc(name)} selon l’état</h2>
  {table(['ÉTAT', 'ANNONCES', 'PRIX DEMANDÉ TYPIQUE', 'MOITIÉ CENTRALE'], rows)}
  {cond_compare(v, 'fr')}
  <p>L’état est celui indiqué par le vendeur sur Vinted.</p>
</section>
<section id="bon-prix">
  <h2>Quel est un bon prix pour {esc(name)}{nb}?</h2>
  <p>Un quart des annonces demandent {money(lo, 'fr')} ou moins, la moitié entre {money(lo, 'fr')} et {money(hi, 'fr')}, et un quart plus de {money(hi, 'fr')}. Sous {money(lo, 'fr')}, c’est le quart le moins cher. Sers-t’en comme filtre, pas comme preuve d’une bonne affaire{nb}: une annonce moins chère peut être plus usée, d’un autre coloris, en taille enfant ou une contrefaçon, alors regarde bien les photos et les détails.</p>
  <p>Au prix typique de {money(typ, 'fr')}, l’acheteur paie {money(typ, 'fr')} plus {money(fee, 'fr')} de protection acheteurs Vinted, soit {money(typ + fee, 'fr')} hors livraison (<a href="{FEE_SRC['fr_list']}" rel="nofollow">grille tarifaire de Vinted</a>, vérifiée le {FEES_CHECKED['fr']}). Vendre est gratuit pour les particuliers (<a href="{FEE_SRC['free_fr']}" rel="nofollow">aide Vinted</a>). Calcule n’importe quel autre prix avec le <a href="{SLUGS['fees']['fr']}">calculateur de frais Vinted</a>.</p>
</section>
<section id="alerte">
  <h2>Reçois une alerte pour {esc(name)} pas cher</h2>
  <p>SNYPD vérifie une recherche Vinted environ toutes les 30 secondes et envoie les nouvelles annonces sur ton téléphone, sans que tu aies à rafraîchir Vinted. Lance la recherche ci-dessous avec un maximum de {money(lo, 'fr')}, le quart le moins cher, et change-le quand tu veux.</p>
  <div class="ct-actions"><a class="ct-btn" href="{esc(alert_href(it, lo))}">M’ALERTER SOUS {money(lo, 'fr')}</a><a class="ct-btn ct-ghost" href="{SLUGS['bot']['fr']}">COMMENT MARCHE SNYPD</a></div>
  <p class="ct-note">Gratuit{nb}: une recherche, 24h/24 pendant les @@trial_days@@ premiers jours. Sans carte. Inscription en français{nb}; le paiement (Whop) est en anglais.</p>
</section>
<section id="methode">
  <h2>D’où viennent ces chiffres</h2>
  <p>SNYPD collecte les nouvelles annonces vinted.be pour les recherches de ses utilisateurs. Cette page utilise les {num(n, 'fr')} annonces {esc(name)} vues {win}{nb}: le prix typique est le prix demandé médian, la moitié centrale va du 25e au 75e centile. Ce sont des prix demandés, pas des prix de vente{nb}: Vinted ne publie pas le prix auquel les articles se vendent. Les prix peuvent différer sur les autres sites Vinted. Mis à jour chaque mois{nb}; les chiffres sont libres de réutilisation avec un lien vers cette page (<a href="{DATASET_LICENSE}" rel="license">CC BY 4.0</a>).</p>
</section>
<section id="questions">
  <h2>Questions</h2>
  {faq_html(faq)}
</section>
<section id="plus">
  <h2>Autres prix Vinted</h2>
  {related(it, 'fr')}
  <p>Tous les articles{nb}: <a href="{HUB['fr']}">le guide des prix Vinted</a>.</p>
</section>"""
    title = 'Prix %s sur Vinted%s: %s typique (%s) | SNYPD' % (name, nb, plain_eur(typ, 'fr'), month_year('fr'))
    desc = ('Combien coûte %s sur Vinted%s: prix demandé typique %s, la moitié des %s annonces entre %s et %s, selon l’état. vinted.be, %s.'
            % (name, nb, plain_eur(typ, 'fr'), num(n, 'fr').replace(' ', nb), plain_eur(lo, 'fr'), plain_eur(hi, 'fr'), win))
    lead = ('Le prix demandé typique pour %s sur Vinted est de <strong>%s</strong>. La moitié des %s annonces vues par SNYPD sur vinted.be (%s) demandaient entre %s et %s. Ce sont les prix demandés par %s vendeurs, pas des prix de vente.'
            % (esc(name), money(typ, 'fr'), num(n, 'fr'), win, money(lo, 'fr'), money(hi, 'fr'), num(sellers, 'fr')))
    toc = [('resume', 'En bref'), ('etat', 'Selon l’état'), ('bon-prix', 'Bon prix'), ('alerte', 'Alerte'), ('methode', 'Méthode'), ('questions', 'Questions')]
    return gc.page('pg:' + it['slug'], 'fr', title, desc, 'GUIDE DES PRIX VINTED', 'Combien coûte %s sur Vinted' % esc(name), lead, toc, body,
                   [faq_ld(faq), dataset_ld(it, v, 'fr', url)], parent=('Guide des prix Vinted', HUB['fr']))


def method(lang):
    """What the code does, in words (work order 18, step 3). Keep in step with price_guide_batch.py,
    backend market_report.py (_derive: confidence) and market_snapshot (migration 023: verdicts)."""
    skipped = sum(1 for it in ITEMS if it.get('skip'))
    if lang == 'en':
        return ('<section id="method"><h2>How these prices are made</h2><ul>'
                '<li><strong>Sample.</strong> Listings on vinted.be that matched the searches SNYPD users watch, in euros. It is not all of Vinted, '
                'and the listings are not necessarily from Belgian sellers.</li>'
                '<li><strong>Matching.</strong> A listing counts for an item when its title contains every word of the item&rsquo;s search; '
                'common synonyms count too (jumper, sweater, pull).</li>'
                '<li><strong>Typical price</strong> is the median asking price. <strong>Middle half</strong> runs from the 25th to the 75th percentile: '
                'a quarter of listings ask less, a quarter ask more.</li>'
                '<li><strong>Window.</strong> Listings SNYPD saw at least once in the %d days before the update (it deletes listing data %d days after it last sees a listing).</li>'
                '<li><strong>One listing counts once.</strong> Each Vinted listing id is counted once. A seller who deletes an item and lists it again gets a new id, so it counts again.</li>'
                '<li><strong>No price</strong> when there are fewer than 8 listings, when the dearest quarter starts at more than 3 times the price where the cheapest quarter ends, '
                'or when one seller has more than 40%% of the listings.</li>'
                '<li><strong>Confidence.</strong> High when none of these warnings apply; medium when prices skew to the high side (the trimmed average sits 25%% or more above the median) '
                'or 5%% or more of listings are priced far above the rest. This guide only publishes items with a clear price, medium or high confidence and at least %d listings.</li>'
                '<li><strong>Mixed items are left out by hand</strong> even when the numbers pass: a brand name alone, several models in one search, trading cards of many sets (%d searches this month).</li>'
                '<li><strong>Conditions.</strong> A condition gets its own price only with at least %d listings and a clear price. A missing condition means too little data, not no listings.</li>'
                '<li><strong>Updates.</strong> Monthly. Each month&rsquo;s numbers are kept as a dated snapshot, and the <a href="/vinted-market-report">Vinted Market Report</a> is built from it.</li>'
                '<li><strong>Asking prices, not sale prices.</strong> Vinted does not publish what items sell for.</li></ul>'
                '<h3>NOT HANDLED YET</h3><ul>'
                '<li>Kids&rsquo; and adult sizes are counted together.</li>'
                '<li>Bundles and lots are counted as one listing at the bundle price.</li>'
                '<li>Colourways and variants of one model share one price.</li>'
                '<li>Fakes are not removed; they only show up as a warning when many listings sit far above the rest.</li></ul></section>'
                % (WIN_DAYS, WIN_DAYS, MIN_LISTINGS, skipped, MIN_COND))
    nb = '\u00a0'
    return ('<section id="methode"><h2>Comment ces prix sont calculés</h2><ul>'
            '<li><strong>Échantillon.</strong> Les annonces vinted.be qui correspondent aux recherches suivies par les utilisateurs de SNYPD, en euros. Ce n’est pas tout Vinted, '
            'et les annonces ne viennent pas forcément de vendeurs belges.</li>'
            '<li><strong>Correspondance.</strong> Une annonce compte pour un article quand son titre contient tous les mots de la recherche de l’article'
            '%s; les synonymes courants comptent aussi (jumper, sweater, pull).</li>'
            '<li><strong>Prix typique</strong>%s: le prix demandé médian. <strong>Moitié centrale</strong>%s: du 25e au 75e centile, donc un quart des annonces demandent moins et un quart plus.</li>'
            '<li><strong>Période.</strong> Les annonces vues au moins une fois par SNYPD dans les %d jours avant la mise à jour (il efface les données d’une annonce %d jours après l’avoir vue pour la dernière fois).</li>'
            '<li><strong>Une annonce compte une fois.</strong> Chaque identifiant d’annonce Vinted compte une fois. Un vendeur qui supprime un article et le remet en vente obtient un nouvel identifiant, donc il compte à nouveau.</li>'
            '<li><strong>Pas de prix</strong> quand il y a moins de 8 annonces, quand le quart le plus cher commence à plus de 3 fois le prix où finit le quart le moins cher, '
            'ou quand un seul vendeur a plus de 40%s%% des annonces.</li>'
            '<li><strong>Fiabilité.</strong> Élevée quand aucun de ces signaux n’apparaît%s; moyenne quand les prix tirent vers le haut (la moyenne tronquée dépasse la médiane de 25%s%% ou plus) '
            'ou quand 5%s%% des annonces ou plus sont nettement plus chères que les autres. Ce guide ne publie que les articles avec un prix clair, une fiabilité moyenne ou élevée et au moins %d annonces.</li>'
            '<li><strong>Les articles mélangés sont écartés à la main</strong> même quand les chiffres passent%s: un nom de marque seul, plusieurs modèles dans une recherche, des cartes de nombreuses séries (%d recherches ce mois-ci).</li>'
            '<li><strong>États.</strong> Un état n’a son propre prix qu’avec au moins %d annonces et un prix clair. Un état absent veut dire trop peu de données, pas zéro annonce.</li>'
            '<li><strong>Mises à jour.</strong> Chaque mois. Les chiffres de chaque mois sont gardés dans une copie datée, et le <a href="/fr/rapport-marche-vinted">Rapport du marché Vinted</a> en est tiré.</li>'
            '<li><strong>Prix demandés, pas prix de vente.</strong> Vinted ne publie pas le prix auquel les articles se vendent.</li></ul>'
            '<h3>PAS ENCORE PRIS EN COMPTE</h3><ul>'
            '<li>Les tailles enfant et adulte sont comptées ensemble.</li>'
            '<li>Les lots sont comptés comme une seule annonce, au prix du lot.</li>'
            '<li>Les coloris et variantes d’un même modèle partagent un seul prix.</li>'
            '<li>Les contrefaçons ne sont pas retirées%s; elles n’apparaissent que comme un avertissement quand beaucoup d’annonces sont bien plus chères que les autres.</li></ul></section>'
            % (nb, nb, nb, WIN_DAYS, WIN_DAYS, nb, nb, nb, nb, MIN_LISTINGS, nb, skipped, MIN_COND, nb))


def page_hub(lang):
    cats = ['sneakers', 'clothing', 'accessories', 'collectibles']
    head = {'en': ['ITEM', 'TYPICAL ASKING PRICE', 'MIDDLE HALF', 'LISTINGS'],
            'fr': ['ARTICLE', 'PRIX DEMANDÉ TYPIQUE', 'MOITIÉ CENTRALE', 'ANNONCES']}[lang]
    sections, toc = [], []
    for c in cats:
        its = [it for it in PUB if it['cat'] == c]
        if not its:
            continue
        rows = [['<a href="%s">%s</a>' % (item_url(it, lang), esc(it.get('name_fr', it['name']) if lang == 'fr' else it['name'])), money(V[it['slug']]['typical_cents'], lang),
                 '%s &ndash; %s' % (money(V[it['slug']]['range_cents']['low'], lang), money(V[it['slug']]['range_cents']['high'], lang)),
                 num(V[it['slug']]['sample_size'], lang)] for it in its]
        sections.append('<section id="%s"><h2>%s</h2>%s</section>' % (c, CAT[c][lang], table(head, rows)))
        toc.append((c, CAT[c][lang]))
    total = sum(V[it['slug']]['sample_size'] for it in PUB)
    win = window(lang)
    nb = ' '
    if lang == 'en':
        intro = ('<section id="about"><h2>What this guide is</h2><div class="lg-box lg-mint"><p>Typical Vinted asking prices for %d popular items, from %s vinted.be listings that SNYPD saw %s. '
                 'Each item page shows the median asking price, the middle half of listings and prices by condition. Asking prices, not sale prices: Vinted does not publish what items sell for. '
                 'Only items with at least %d listings and a clear price are included. Updated monthly; free to reuse with a link (CC BY 4.0). Trends, condition premium and price cuts: <a href="/vinted-market-report">the monthly Vinted Market Report</a>.</p></div></section>' % (len(PUB), num(total, 'en'), win, MIN_LISTINGS))
        tail = ('<section id="alerts"><h2>Found your price?</h2><p>A good price only helps if you see the listing first. SNYPD checks your Vinted search about every 30 seconds and sends new matches to your phone. '
                'Each item page has a button that starts that search with the cheapest-quarter price as the maximum.</p>%s</section>' % gc.cta('en'))
        title = 'Vinted price guide: typical prices for %d items (%s) | SNYPD' % (len(PUB), month_year('en'))
        desc = 'How much things cost on Vinted: typical asking prices and price ranges by condition for %d popular sneakers, clothes and accessories, from %s vinted.be listings.' % (len(PUB), num(total, 'en'))
        return gc.page('guide', 'en', title, desc, 'VINTED PRICE GUIDE', 'What things cost on Vinted',
                       'Typical asking prices for %d popular items, from %s listings SNYPD saw on vinted.be (%s). Pick an item for prices by condition.' % (len(PUB), num(total, 'en'), win),
                       [('about', 'About')] + toc + [('method', 'Method'), ('alerts', 'Alerts')], intro + ''.join(sections) + method('en') + tail)
    intro = ('<section id="about"><h2>Ce qu’est ce guide</h2><div class="lg-box lg-mint"><p>Les prix demandés typiques sur Vinted pour %d articles populaires, à partir de %s annonces vinted.be vues par SNYPD %s. '
             'Chaque page article montre le prix demandé médian, la moitié centrale des annonces et les prix selon l’état. Ce sont des prix demandés, pas des prix de vente%s: Vinted ne publie pas le prix auquel les articles se vendent. '
             'Seuls les articles avec au moins %d annonces et un prix clair sont inclus. Mis à jour chaque mois%s; libre de réutilisation avec un lien (CC BY 4.0). Écart selon l’état et baisses de prix%s: <a href="/fr/rapport-marche-vinted">le rapport mensuel du marché Vinted</a>.</p></div></section>' % (len(PUB), num(total, 'fr'), win, nb, MIN_LISTINGS, nb, nb))
    tail = ('<section id="alertes"><h2>Tu as trouvé ton prix%s?</h2><p>Un bon prix ne sert que si tu vois l’annonce en premier. SNYPD vérifie ta recherche Vinted environ toutes les 30 secondes et envoie les nouvelles annonces sur ton téléphone. '
            'Chaque page article a un bouton qui lance cette recherche avec le prix du quart le moins cher comme maximum.</p>%s</section>' % (nb, gc.cta('fr')))
    title = 'Guide des prix Vinted%s: prix typiques de %d articles (%s) | SNYPD' % (nb, len(PUB), month_year('fr'))
    desc = 'Combien coûtent les articles sur Vinted%s: prix demandés typiques et fourchettes selon l’état pour %d sneakers, vêtements et accessoires populaires, à partir de %s annonces vinted.be.' % (nb, len(PUB), num(total, 'fr').replace(' ', nb))
    return gc.page('guide', 'fr', title, desc, 'GUIDE DES PRIX VINTED', 'Combien coûtent les articles sur Vinted',
                   'Les prix demandés typiques de %d articles populaires, à partir de %s annonces vues par SNYPD sur vinted.be (%s). Choisis un article pour voir les prix selon l’état.' % (len(PUB), num(total, 'fr'), win),
                   [('about', 'En bref')] + toc + [('methode', 'Méthode'), ('alertes', 'Alertes')], intro + ''.join(sections) + method('fr') + tail)


def sitemap_pages():
    """(path, file, hreflang alternates) for prepublish.py."""
    out = []
    for key in ['guide'] + ['pg:' + it['slug'] for it in PUB]:
        alts = {l: SLUGS[key][l] for l in LANGS}
        alts['x-default'] = SLUGS[key]['en']
        out += [(SLUGS[key][l], SLUGS[key][l].lstrip('/') + '.html', alts) for l in LANGS]
    return out


if __name__ == '__main__':
    print('items published: %d of %d (min %d listings)' % (len(PUB), len(ITEMS), MIN_LISTINGS))
    for lang in LANGS:
        write(HUB[lang].lstrip('/') + '.html', page_hub(lang))
        for it in PUB:
            write(item_url(it, lang).lstrip('/') + '.html', page_item(it, lang))
