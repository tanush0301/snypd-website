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
import copy_sold  # noqa: E402
from gen_content import SITE, SLUGS, PAGE_MODIFIED, esc, table, faq_ld, faq_html, money, num, fee_cents, FEE_SRC, \
    DATASET_CREATOR, DATASET_LICENSE, write  # noqa: E402

ROOT = gc.ROOT
ITEMS = json.load(open(os.path.join(ROOT, 'ops', 'seo', 'price_items.json'), encoding='utf-8'))['items']
DATA = json.load(open(os.path.join(ROOT, 'ops', 'seo', 'data', 'price-guide.json'), encoding='utf-8'))
MIN_LISTINGS = 100
MIN_COND = 10
LANGS = ('en', 'fr', 'nl')
HUB = {'en': '/vinted-price-guide', 'fr': '/fr/guide-prix-vinted', 'nl': '/nl/vinted-prijzen'}
# Dutch is built but held (gc.HOLD) until Tanush says "NL ok": written to ops/seo/preview/, kept out of
# the sitemap, hreflang, footers and price-index.json. Review text: outreach/19b-nl-review-step5.md.
NL_HELD = False  # Tanush: "publish now", 18 Oct 2026
INDEX = 'assets/data/price-index.json'  # public by design (Tanush OK 10 Oct): only what the pages show
FEES_CHECKED = dict(gc.FEES_CHECKED, nl=gc.date_txt('2026-10-02', 'nl'))

GEN = datetime.datetime.fromisoformat(DATA['generated_at'].replace('Z', '+00:00')).date()
WIN_DAYS = DATA.get('window_days', 14)
WIN_FROM = GEN - datetime.timedelta(days=WIN_DAYS)
MONTHS = gc.MONTHS_TXT
CAT = {'sneakers': {'en': 'Sneakers', 'fr': 'Sneakers', 'nl': 'Sneakers'}, 'clothing': {'en': 'Clothing', 'fr': 'Vêtements', 'nl': 'Kleding'},
       'accessories': {'en': 'Bags, watches and jewellery', 'fr': 'Sacs, montres et bijoux', 'nl': 'Tassen, horloges en sieraden'},
       'collectibles': {'en': 'Collectibles', 'fr': 'Objets de collection', 'nl': 'Verzamelobjecten'}}
COND = {'New, with tag': {'en': 'New with tags', 'fr': 'Neuf avec étiquette', 'nl': 'Nieuw met label'},
        'New, no tag': {'en': 'New without tags', 'fr': 'Neuf sans étiquette', 'nl': 'Nieuw zonder label'},
        'Very good': {'en': 'Very good', 'fr': 'Très bon état', 'nl': 'Zeer goed'},
        'Good': {'en': 'Good', 'fr': 'Bon état', 'nl': 'Goed'},
        'Satisfactory': {'en': 'Satisfactory', 'fr': 'Satisfaisant', 'nl': 'Redelijk'}}
# Dutch item names where the English one is not what a Dutch speaker types (Tanush reviews them).
NAME_NL = {'ralph-lauren-jumper': 'Ralph Lauren trui', 'ralph-lauren-shirt': 'Ralph Lauren hemd',
           'carhartt-detroit-jacket': 'Carhartt Detroit jas', 'pandora-bracelet': 'Pandora armband'}


def plain_eur(cents, lang):
    """Euro amount for <title>/description (no HTML entities)."""
    return money(cents, lang).replace('&euro;', '€').replace('&nbsp;', ' ')


def window(lang):
    a, b = WIN_FROM, GEN
    m = MONTHS[lang]
    if lang == 'en':
        return ('%d %s to %d %s %d' % (a.day, m[a.month - 1], b.day, m[b.month - 1], b.year)) if a.month != b.month \
            else '%d-%d %s %d' % (a.day, b.day, m[b.month - 1], b.year)
    if lang == 'nl':
        return ('van %d %s tot %d %s %d' % (a.day, m[a.month - 1], b.day, m[b.month - 1], b.year)) if a.month != b.month \
            else 'van %d tot %d %s %d' % (a.day, b.day, m[b.month - 1], b.year)
    if lang != 'fr':  # de/it/es: the shared date-span wording of gen_content
        return (gc._SPAN_TWO_MONTHS[lang] % (a.day, m[a.month - 1], b.day, m[b.month - 1], b.year)) if a.month != b.month \
            else gc._SPAN_SAME_MONTH[lang] % (a.day, b.day, m[b.month - 1], b.year)
    return ('du %d %s au %d %s %d' % (a.day, m[a.month - 1], b.day, m[b.month - 1], b.year)) if a.month != b.month \
        else 'du %d au %d %s %d' % (a.day, b.day, m[b.month - 1], b.year)


def month_year(lang):
    return '%s %d' % (MONTHS[lang][GEN.month - 1], GEN.year)


def iname(it, lang):
    """Item name in the page's language."""
    if lang == 'fr':
        return it.get('name_fr', it['name'])
    if lang == 'nl':
        return NAME_NL.get(it['slug'], it['name'])
    return it['name']


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
if NL_HELD:
    gc.HOLD.update({('guide', 'nl')} | {('pg:' + it['slug'], 'nl') for it in PUB})


def is_live(key, lang):
    return lang in gc.live_langs(key)


def out_path(key, lang):
    """Where a page is written: its public path, or ops/seo/preview/ while held."""
    rel = SLUGS[key][lang].lstrip('/') + '.html'
    return rel if is_live(key, lang) else 'ops/seo/preview/' + rel.replace('/', '-')


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
            rows.append([label, num(n, lang), '&ndash;', {'en': 'too spread out for one price', 'fr': 'prix trop dispersés pour un chiffre',
                                                           'nl': 'te verspreid voor één prijs'}[lang]])
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
                'fr': '<p>Les annonces « %s » et « Très bon état » demandent à peu près le même prix.</p>' % nl,
                'nl': '<p>Advertenties in staat “%s” en “Zeer goed” vragen ongeveer hetzelfde.</p>' % nl}[lang]
    more = diff > 0
    return {'en': '<p>%s listings ask about %d%% %s than very good ones (%s against %s).</p>'
                  % (nl, abs(diff), 'more' if more else 'less', money(new['typical_cents'], 'en'), money(used['typical_cents'], 'en')),
            'fr': '<p>Les annonces «&nbsp;%s&nbsp;» demandent environ %d&nbsp;%% %s que celles en «&nbsp;Très bon état&nbsp;» (%s contre %s).</p>'
                  % (nl, abs(diff), 'de plus' if more else 'de moins', money(new['typical_cents'], 'fr'), money(used['typical_cents'], 'fr')),
            'nl': '<p>Advertenties in staat “%s” vragen ongeveer %d%% %s dan advertenties in staat “Zeer goed” (%s tegenover %s).</p>'
                  % (nl, abs(diff), 'meer' if more else 'minder', money(new['typical_cents'], 'nl'), money(used['typical_cents'], 'nl'))}[lang]


def dataset_ld(it, v, lang, url):
    name = {'en': '%s asking prices on Vinted (vinted.be, %s)' % (it['name'], window('en')),
            'fr': 'Prix demandés pour %s sur Vinted (vinted.be, %s)' % (it['name'], window('fr')),
            'nl': 'Vraagprijzen voor %s op Vinted (vinted.be, %s)' % (iname(it, 'nl'), window('nl'))}[lang]
    desc = {'en': 'Median and 25th-75th percentile asking price of %s listings on vinted.be that matched SNYPD users\' searches, overall and by condition. Asking prices, not sale prices.' % it['name'],
            'fr': 'Prix demandé médian et 25e-75e centile des annonces %s sur vinted.be correspondant aux recherches des utilisateurs de SNYPD, au total et par état. Prix demandés, pas prix de vente.' % it['name'],
            'nl': 'Mediane vraagprijs en 25e-75e percentiel van advertenties voor %s op vinted.be die overeenkwamen met de zoekopdrachten van SNYPD-gebruikers, in totaal en per staat. Vraagprijzen, geen verkoopprijzen.' % iname(it, 'nl')}[lang]
    return {'@context': 'https://schema.org', '@type': 'Dataset', 'name': name, 'description': desc, 'url': SITE + url,
            'creator': DATASET_CREATOR, 'license': DATASET_LICENSE, 'inLanguage': lang, 'isAccessibleForFree': True,
            'temporalCoverage': '%s/%s' % (WIN_FROM.isoformat(), GEN.isoformat()), 'spatialCoverage': 'Belgium',
            'variableMeasured': ['asking price (median)', 'asking price (25th percentile)', 'asking price (75th percentile)', 'listing count'],
            'measurementTechnique': 'Listings collected by SNYPD from vinted.be search results',
            'dateModified': GEN.isoformat()}


def related(it, lang):
    same = [x for x in PUB if x['cat'] == it['cat'] and x['slug'] != it['slug']]
    same.sort(key=lambda x: (x['brand'] != it['brand'], -V[x['slug']]['sample_size']))
    links = ''.join('<li><a href="%s">%s</a>%s: %s</li>' % (item_url(x, lang), esc(iname(x, lang)), ' ' if lang == 'fr' else '', money(V[x['slug']]['typical_cents'], lang)) for x in same[:8])
    return '<ul>%s</ul>' % links if links else ''


def page_item(it, lang):
    v = V[it['slug']]
    name, typ, lo, hi = iname(it, lang), v['typical_cents'], v['range_cents']['low'], v['range_cents']['high']
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
  <p>SNYPD collects new vinted.be listings for the searches its users run. This page uses the {num(n, 'en')} {esc(name)} listings it saw {win}: the typical price is the median asking price, the middle half runs from the 25th to the 75th percentile. These are asking prices, not sale prices: Vinted does not publish what items sell for (<a href="{SLUGS['sold']['en']}">can you see sold items on Vinted?</a>). Prices on other Vinted sites can differ. Updated monthly; the figures are free to reuse with a link to this page (<a href="{DATASET_LICENSE}" rel="license">CC BY 4.0</a>).</p>
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
    if lang == 'nl':
        return page_item_nl(it, v, name, url, rows, fee, win)
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
  <p class="ct-note">Gratuit{nb}: une recherche, 24h/24 pendant les @@trial_days@@ premiers jours. Sans carte. Inscription et paiement en français.</p>
</section>
<section id="methode">
  <h2>D’où viennent ces chiffres</h2>
  <p>SNYPD collecte les nouvelles annonces vinted.be pour les recherches de ses utilisateurs. Cette page utilise les {num(n, 'fr')} annonces {esc(name)} vues {win}{nb}: le prix typique est le prix demandé médian, la moitié centrale va du 25e au 75e centile. Ce sont des prix demandés, pas des prix de vente{nb}: Vinted ne publie pas le prix auquel les articles se vendent (<a href="{SLUGS['sold']['fr']}">peut-on voir les articles vendus sur Vinted{nb}?</a>). Les prix peuvent différer sur les autres sites Vinted. Mis à jour chaque mois{nb}; les chiffres sont libres de réutilisation avec un lien vers cette page (<a href="{DATASET_LICENSE}" rel="license">CC BY 4.0</a>).</p>
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
    if lang == 'nl':
        return method_nl(skipped)
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
                '<li><strong>Asking prices, not sale prices.</strong> Vinted does not publish what items sell for '
                '(<a href="%s">can you see sold items on Vinted?</a>).</li></ul>'
                '<h3>NOT HANDLED YET</h3><ul>'
                '<li>Kids&rsquo; and adult sizes are counted together.</li>'
                '<li>Bundles and lots are counted as one listing at the bundle price.</li>'
                '<li>Colourways and variants of one model share one price.</li>'
                '<li>Fakes are not removed; they only show up as a warning when many listings sit far above the rest.</li></ul></section>'
                % (WIN_DAYS, WIN_DAYS, MIN_LISTINGS, skipped, MIN_COND, SLUGS['sold']['en']))
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
            '<li><strong>Prix demandés, pas prix de vente.</strong> Vinted ne publie pas le prix auquel les articles se vendent '
            '(<a href="%s">peut-on voir les articles vendus sur Vinted%s?</a>).</li></ul>'
            '<h3>PAS ENCORE PRIS EN COMPTE</h3><ul>'
            '<li>Les tailles enfant et adulte sont comptées ensemble.</li>'
            '<li>Les lots sont comptés comme une seule annonce, au prix du lot.</li>'
            '<li>Les coloris et variantes d’un même modèle partagent un seul prix.</li>'
            '<li>Les contrefaçons ne sont pas retirées%s; elles n’apparaissent que comme un avertissement quand beaucoup d’annonces sont bien plus chères que les autres.</li></ul></section>'
            % (nb, nb, nb, WIN_DAYS, WIN_DAYS, nb, nb, nb, nb, MIN_LISTINGS, nb, skipped, MIN_COND, SLUGS['sold']['fr'], nb, nb))


def page_hub(lang):
    cats = ['sneakers', 'clothing', 'accessories', 'collectibles']
    head = {'en': ['ITEM', 'TYPICAL ASKING PRICE', 'MIDDLE HALF', 'LISTINGS'],
            'fr': ['ARTICLE', 'PRIX DEMANDÉ TYPIQUE', 'MOITIÉ CENTRALE', 'ANNONCES'],
            'nl': ['ARTIKEL', 'TYPISCHE VRAAGPRIJS', 'MIDDELSTE HELFT', 'ADVERTENTIES']}[lang]
    sections, toc = [], []
    for c in cats:
        its = [it for it in PUB if it['cat'] == c]
        if not its:
            continue
        rows = [['<a href="%s">%s</a>' % (item_url(it, lang), esc(iname(it, lang))), money(V[it['slug']]['typical_cents'], lang),
                 '%s &ndash; %s' % (money(V[it['slug']]['range_cents']['low'], lang), money(V[it['slug']]['range_cents']['high'], lang)),
                 num(V[it['slug']]['sample_size'], lang)] for it in its]
        sections.append('<section id="%s"><h2>%s</h2>%s</section>' % (c, CAT[c][lang], table(head, rows)))
        toc.append((c, CAT[c][lang]))
    total = sum(V[it['slug']]['sample_size'] for it in PUB)
    win = window(lang)
    if lang == 'nl':
        return page_hub_nl(sections, toc, total, win)
    nb = ' '
    if lang == 'en':
        intro = ('<section id="about"><h2>What this guide is</h2>' + checker_box('en') + '<div class="lg-box lg-mint"><p>Typical Vinted asking prices for %d popular items, from %s vinted.be listings that SNYPD saw %s. '
                 'Each item page shows the median asking price, the middle half of listings and prices by condition. Asking prices, not sale prices: Vinted does not publish what items sell for. '
                 'Only items with at least %d listings and a clear price are included. Updated monthly; free to reuse with a link (CC BY 4.0). Trends, condition premium and price cuts: <a href="/vinted-market-report">the monthly Vinted Market Report</a>.</p></div></section>' % (len(PUB), num(total, 'en'), win, MIN_LISTINGS))
        tail = ('<section id="alerts"><h2>Found your price?</h2><p>A good price only helps if you see the listing first. SNYPD checks your Vinted search about every 30 seconds and sends new matches to your phone. '
                'Each item page has a button that starts that search with the cheapest-quarter price as the maximum.</p>%s</section>' % gc.cta('en'))
        title = 'Vinted price guide: typical prices for %d items (%s) | SNYPD' % (len(PUB), month_year('en'))
        desc = 'How much things cost on Vinted: typical asking prices and price ranges by condition for %d popular sneakers, clothes and accessories, from %s vinted.be listings.' % (len(PUB), num(total, 'en'))
        return gc.page('guide', 'en', title, desc, 'VINTED PRICE GUIDE', 'What things cost on Vinted',
                       'Typical asking prices for %d popular items, from %s listings SNYPD saw on vinted.be (%s). Pick an item for prices by condition.' % (len(PUB), num(total, 'en'), win),
                       [('about', 'About')] + toc + [('method', 'Method'), ('alerts', 'Alerts')], intro + ''.join(sections) + method('en') + tail)
    intro = ('<section id="about"><h2>Ce qu’est ce guide</h2>' + checker_box('fr') + '<div class="lg-box lg-mint"><p>Les prix demandés typiques sur Vinted pour %d articles populaires, à partir de %s annonces vinted.be vues par SNYPD %s. '
             'Chaque page article montre le prix demandé médian, la moitié centrale des annonces et les prix selon l’état. Ce sont des prix demandés, pas des prix de vente%s: Vinted ne publie pas le prix auquel les articles se vendent. '
             'Seuls les articles avec au moins %d annonces et un prix clair sont inclus. Mis à jour chaque mois%s; libre de réutilisation avec un lien (CC BY 4.0). Écart selon l’état et baisses de prix%s: <a href="/fr/rapport-marche-vinted">le rapport mensuel du marché Vinted</a>.</p></div></section>' % (len(PUB), num(total, 'fr'), win, nb, MIN_LISTINGS, nb, nb))
    tail = ('<section id="alertes"><h2>Tu as trouvé ton prix%s?</h2><p>Un bon prix ne sert que si tu vois l’annonce en premier. SNYPD vérifie ta recherche Vinted environ toutes les 30 secondes et envoie les nouvelles annonces sur ton téléphone. '
            'Chaque page article a un bouton qui lance cette recherche avec le prix du quart le moins cher comme maximum.</p>%s</section>' % (nb, gc.cta('fr')))
    title = 'Guide des prix Vinted%s: prix typiques de %d articles (%s) | SNYPD' % (nb, len(PUB), month_year('fr'))
    desc = 'Combien coûtent les articles sur Vinted%s: prix demandés typiques et fourchettes selon l’état pour %d sneakers, vêtements et accessoires populaires, à partir de %s annonces vinted.be.' % (nb, len(PUB), num(total, 'fr').replace(' ', nb))
    return gc.page('guide', 'fr', title, desc, 'GUIDE DES PRIX VINTED', 'Combien coûtent les articles sur Vinted',
                   'Les prix demandés typiques de %d articles populaires, à partir de %s annonces vues par SNYPD sur vinted.be (%s). Choisis un article pour voir les prix selon l’état.' % (len(PUB), num(total, 'fr'), win),
                   [('about', 'En bref')] + toc + [('methode', 'Méthode'), ('alertes', 'Alertes')], intro + ''.join(sections) + method('fr') + tail)


# ---------------------------------------------------------------- Dutch (held until Tanush says "NL ok")
def page_item_nl(it, v, name, url, rows, fee, win):
    typ, lo, hi = v['typical_cents'], v['range_cents']['low'], v['range_cents']['high']
    n, sellers, out_pct = v['sample_size'], v.get('distinct_sellers') or 0, v.get('outlier_pct')

    def m(c):
        return money(c, 'nl')
    faq = [
        ('Hoeveel kost %s op Vinted?' % name,
         'De typische vraagprijs op vinted.be is %s (mediaan van %s advertenties, %s). De helft van de advertenties vraagt tussen %s en %s.' % (m(typ), num(n, 'nl'), win, m(lo), m(hi))),
        ('Is dit wat %s op Vinted opbrengt?' % name,
         'Nee. Dit zijn vraagprijzen: wat verkopers ervoor vragen. Vinted publiceert niet voor welke prijs een artikel uiteindelijk verkocht is, en kopers kunnen een bod doen onder de vraagprijs.'),
        ('Wat is een goede prijs voor %s op Vinted?' % name,
         'Onder %s zit je in het goedkoopste kwart van de %s advertenties die SNYPD zag. Kijk goed naar de staat en de foto’s: de goedkoopste advertenties zijn vaak het meest gedragen.' % (m(lo), num(n, 'nl'))),
    ]
    outl = ('<li><strong>Uitschieters:</strong> %s%% van de advertenties vroeg veel meer dan de rest; de mediaan houdt er geen rekening mee.</li>'
            % str(out_pct).replace('.', ',')) if out_pct and out_pct >= 5 else ''
    body = f"""
<section id="overzicht">
  <h2>{esc(name)} op Vinted in het kort</h2>
  <div class="lg-box lg-mint"><ul>
    <li><strong>Typische vraagprijs (mediaan):</strong> {m(typ)}</li>
    <li><strong>Middelste helft van de advertenties:</strong> {m(lo)} &ndash; {m(hi)}</li>
    <li><strong>Advertenties:</strong> {num(n, 'nl')} van {num(sellers, 'nl')} verschillende verkopers</li>
    <li><strong>Waar en wanneer:</strong> vinted.be, {win}</li>{outl}
  </ul></div>
</section>
<section id="staat">
  <h2>Prijs van {esc(name)} per staat</h2>
  {table(['STAAT', 'ADVERTENTIES', 'TYPISCHE VRAAGPRIJS', 'MIDDELSTE HELFT'], rows)}
  {cond_compare(v, 'nl')}
  <p>De staat is wat de verkoper zelf op Vinted aangeeft.</p>
</section>
<section id="goede-prijs">
  <h2>Wat is een goede prijs voor {esc(name)}?</h2>
  <p>Een kwart van de advertenties vraagt {m(lo)} of minder, de helft tussen {m(lo)} en {m(hi)}, en een kwart meer dan {m(hi)}. Onder {m(lo)} zit je in het goedkoopste kwart. Gebruik dat als filter, niet als bewijs van een koopje: het artikel kan meer gedragen zijn, een andere kleur hebben, een kindermaat of namaak zijn, dus kijk goed naar de foto&rsquo;s en de details.</p>
  <p>Bij de typische {m(typ)} betaalt de koper {m(typ)} plus {m(fee)} Kopersbescherming van Vinted, dus {m(typ + fee)} zonder verzending (<a href="{FEE_SRC['fr_list']}" rel="nofollow">prijslijst van Vinted</a>, gecontroleerd op {FEES_CHECKED['nl']}). Verkopen is gratis voor particulieren (<a href="{FEE_SRC['free_en']}" rel="nofollow">Vinted-hulp</a>). Reken elke andere prijs uit met de <a href="{SLUGS['fees']['en']}">Vinted-kostencalculator</a> (Engels).</p>
</section>
<section id="melding">
  <h2>Krijg een melding bij een lage prijs voor {esc(name)}</h2>
  <p>SNYPD controleert een Vinted-zoekopdracht ongeveer elke 30 seconden en stuurt nieuwe resultaten naar je telefoon, zodat je Vinted niet steeds hoeft te vernieuwen. Start de zoekopdracht hieronder met een maximum van {m(lo)}, het goedkoopste kwart, en pas het aan wanneer je wilt.</p>
  <div class="ct-actions"><a class="ct-btn" href="{esc(alert_href(it, lo))}">MELD ME ONDER {m(lo)}</a><a class="ct-btn ct-ghost" href="{SLUGS['bot']['nl']}">HOE SNYPD WERKT</a></div>
  <p class="ct-note">Gratis: één zoekopdracht, 24/7 tijdens de eerste @@trial_days@@ dagen. Geen kaart. Registreren en betalen gaan voorlopig in het Engels.</p>
</section>
<section id="methode">
  <h2>Hoe deze cijfers tot stand komen</h2>
  <p>SNYPD verzamelt nieuwe vinted.be-advertenties voor de zoekopdrachten van zijn gebruikers. Deze pagina gebruikt de {num(n, 'nl')} advertenties voor {esc(name)} die het zag {win}: de typische prijs is de mediane vraagprijs, de middelste helft loopt van het 25e tot het 75e percentiel. Dit zijn vraagprijzen, geen verkoopprijzen: Vinted publiceert niet voor welke prijs artikelen verkocht worden. Prijzen op andere Vinted-sites kunnen verschillen. Maandelijks bijgewerkt; je mag de cijfers vrij hergebruiken met een link naar deze pagina (<a href="{DATASET_LICENSE}" rel="license">CC BY 4.0</a>).</p>
</section>
<section id="vragen">
  <h2>Vragen</h2>
  {faq_html(faq)}
</section>
<section id="meer">
  <h2>Meer Vinted-prijzen</h2>
  {related(it, 'nl')}
  <p>Alle artikelen: <a href="{HUB['nl']}">de Vinted-prijsgids</a>.</p>
</section>"""
    title = 'Prijs %s op Vinted: %s typisch (%s) | SNYPD' % (name, plain_eur(typ, 'nl'), month_year('nl'))
    desc = ('Wat %s kost op Vinted: typische vraagprijs %s, de helft van %s advertenties tussen %s en %s, per staat. vinted.be, %s.'
            % (name, plain_eur(typ, 'nl'), num(n, 'nl'), plain_eur(lo, 'nl'), plain_eur(hi, 'nl'), win))
    lead = ('De typische vraagprijs voor %s op Vinted is <strong>%s</strong>. De helft van de %s advertenties die SNYPD op vinted.be zag (%s) vroeg tussen %s en %s. Dit zijn vraagprijzen van %s verkopers, geen verkoopprijzen.'
            % (esc(name), m(typ), num(n, 'nl'), win, m(lo), m(hi), num(sellers, 'nl')))
    toc = [('overzicht', 'In het kort'), ('staat', 'Per staat'), ('goede-prijs', 'Goede prijs'), ('melding', 'Melding'), ('methode', 'Methode'), ('vragen', 'Vragen')]
    return gc.page('pg:' + it['slug'], 'nl', title, desc, 'VINTED-PRIJSGIDS', 'Wat %s kost op Vinted' % esc(name), lead, toc, body,
                   [faq_ld(faq), dataset_ld(it, v, 'nl', url)], parent=('Vinted-prijsgids', HUB['nl']))


def method_nl(skipped):
    return ('<section id="methode"><h2>Hoe deze prijzen berekend worden</h2><ul>'
            '<li><strong>Steekproef.</strong> Advertenties op vinted.be die overeenkwamen met de zoekopdrachten die SNYPD-gebruikers volgen, in euro. Het is niet heel Vinted, '
            'en de advertenties komen niet per se van Belgische verkopers.</li>'
            '<li><strong>Koppeling.</strong> Een advertentie telt voor een artikel als de titel elk woord van de zoekopdracht van het artikel bevat; '
            'gangbare synoniemen tellen ook (jumper, sweater, pull).</li>'
            '<li><strong>Typische prijs</strong> is de mediane vraagprijs. <strong>Middelste helft</strong> loopt van het 25e tot het 75e percentiel: '
            'een kwart van de advertenties vraagt minder, een kwart meer.</li>'
            '<li><strong>Periode.</strong> Advertenties die SNYPD minstens één keer zag in de %d dagen voor de update (het wist de gegevens van een advertentie %d dagen nadat het die voor het laatst zag).</li>'
            '<li><strong>Eén advertentie telt één keer.</strong> Elk Vinted-advertentienummer telt één keer. Een verkoper die een artikel verwijdert en opnieuw plaatst, krijgt een nieuw nummer, dus dan telt het opnieuw.</li>'
            '<li><strong>Geen prijs</strong> bij minder dan 8 advertenties, als het duurste kwart begint bij meer dan 3 keer de prijs waar het goedkoopste kwart eindigt, '
            'of als één verkoper meer dan 40%% van de advertenties heeft.</li>'
            '<li><strong>Betrouwbaarheid.</strong> Hoog als geen van deze signalen speelt; gemiddeld als de prijzen naar boven trekken (het afgeknotte gemiddelde ligt 25%% of meer boven de mediaan) '
            'of als 5%% of meer van de advertenties veel duurder is dan de rest. Deze gids publiceert alleen artikelen met een duidelijke prijs, gemiddelde of hoge betrouwbaarheid en minstens %d advertenties.</li>'
            '<li><strong>Gemengde artikelen laten we met de hand weg</strong>, ook als de cijfers kloppen: alleen een merknaam, meerdere modellen in één zoekopdracht, kaarten uit veel reeksen (%d zoekopdrachten deze maand).</li>'
            '<li><strong>Staat.</strong> Een staat krijgt alleen een eigen prijs met minstens %d advertenties en een duidelijke prijs. Ontbreekt een staat, dan zijn er te weinig gegevens, niet nul advertenties.</li>'
            '<li><strong>Updates.</strong> Maandelijks. De cijfers van elke maand worden bewaard als gedateerde momentopname, en het <a href="/vinted-market-report">Vinted-marktrapport</a> (Engels) wordt ervan gemaakt.</li>'
            '<li><strong>Vraagprijzen, geen verkoopprijzen.</strong> Vinted publiceert niet voor welke prijs artikelen verkocht worden.</li></ul>'
            '<h3>NOG NIET VERWERKT</h3><ul>'
            '<li>Kinder- en volwassenenmaten worden samen geteld.</li>'
            '<li>Bundels en partijen tellen als één advertentie, tegen de prijs van de bundel.</li>'
            '<li>Kleuren en varianten van één model delen één prijs.</li>'
            '<li>Namaak wordt niet verwijderd; die verschijnt alleen als waarschuwing wanneer veel advertenties ver boven de rest liggen.</li></ul></section>'
            % (WIN_DAYS, WIN_DAYS, MIN_LISTINGS, skipped, MIN_COND))


def page_hub_nl(sections, toc, total, win):
    intro = ('<section id="about"><h2>Wat deze gids is</h2>' + checker_box('nl') + '<div class="lg-box lg-mint"><p>Typische vraagprijzen op Vinted voor %d populaire artikelen, uit %s vinted.be-advertenties die SNYPD zag %s. '
             'Elke artikelpagina toont de mediane vraagprijs, de middelste helft van de advertenties en de prijzen per staat. Dit zijn vraagprijzen, geen verkoopprijzen: Vinted publiceert niet voor welke prijs artikelen verkocht worden. '
             'Alleen artikelen met minstens %d advertenties en een duidelijke prijs staan erin. Maandelijks bijgewerkt; vrij te hergebruiken met een link (CC BY 4.0). Trends, het verschil per staat en prijsverlagingen: <a href="/vinted-market-report">het maandelijkse Vinted-marktrapport</a> (Engels).</p></div></section>'
             % (len(PUB), num(total, 'nl'), win, MIN_LISTINGS))
    tail = ('<section id="meldingen"><h2>Je prijs gevonden?</h2><p>Een goede prijs helpt alleen als je de advertentie als eerste ziet. SNYPD controleert je Vinted-zoekopdracht ongeveer elke 30 seconden en stuurt nieuwe resultaten naar je telefoon. '
            'Op elke artikelpagina staat een knop die die zoekopdracht start met de prijs van het goedkoopste kwart als maximum.</p>%s</section>' % gc.cta('nl'))
    title = 'Vinted-prijzen: typische prijzen van %d artikelen (%s) | SNYPD' % (len(PUB), month_year('nl'))
    desc = 'Wat dingen kosten op Vinted: typische vraagprijzen en prijsklassen per staat voor %d populaire sneakers, kleding en accessoires, uit %s vinted.be-advertenties.' % (len(PUB), num(total, 'nl'))
    return gc.page('guide', 'nl', title, desc, 'VINTED-PRIJSGIDS', 'Wat dingen kosten op Vinted',
                   'Typische vraagprijzen voor %d populaire artikelen, uit %s advertenties die SNYPD op vinted.be zag (%s). Kies een artikel voor de prijzen per staat.' % (len(PUB), num(total, 'nl'), win),
                   [('about', 'Wat dit is')] + toc + [('methode', 'Methode'), ('meldingen', 'Meldingen')], intro + ''.join(sections) + method('nl') + tail)


# ---------------------------------------------------------------- price checker (work order 18, step 5)
# Words for assets/price-checker.js. {p}, {q}, {n} are filled in by the script; money is formatted there.
PC_TXT = {
    'en': dict(label='TYPE AN ITEM', ph='e.g. Samba, Nuptse, Longchamp', typical='Typical asking price', middle='Middle half of listings:',
               listings='Listings:', page='PRICES BY CONDITION', alert='ALERT ME UNDER {p}', note='Asking prices, not sale prices.',
               none='No item matches “{q}”. The checker covers {n} items: try a brand such as Nike, Ralph Lauren or Carhartt.',
               many='{n} items match. Pick one:'),
    'fr': dict(label='TAPE UN ARTICLE', ph='ex. Samba, Nuptse, Longchamp', typical='Prix demandé typique', middle='Moitié centrale des annonces\u00a0:',
               listings='Annonces\u00a0:', page='PRIX SELON L’ÉTAT', alert='M’ALERTER SOUS {p}', note='Prix demandés, pas prix de vente.',
               none='Aucun article pour «\u00a0{q}\u00a0». L’outil couvre {n} articles\u00a0: essaie une marque comme Nike, Ralph Lauren ou Carhartt.',
               many='{n} articles correspondent. Choisis-en un\u00a0:'),
    'nl': dict(label='TYP EEN ARTIKEL', ph='bv. Samba, Nuptse, Longchamp', typical='Typische vraagprijs', middle='Middelste helft van de advertenties:',
               listings='Advertenties:', page='PRIJZEN PER STAAT', alert='MELD ME ONDER {p}', note='Vraagprijzen, geen verkoopprijzen.',
               none='Geen artikel gevonden voor “{q}”. De zoekfunctie kent {n} artikelen: probeer een merk zoals Nike, Ralph Lauren of Carhartt.',
               many='{n} artikelen gevonden. Kies er een:'),
}


def checker_box(lang):
    """Search box over INDEX. Hidden until the script has loaded the index, so without JavaScript the page's
    own text and tables answer instead."""
    s = dict(PC_TXT[lang], where='vinted.be, ' + window(lang))
    data = json.dumps(s, ensure_ascii=False).replace('<', '\\u003c')
    return ('<div class="pc" data-pc data-lang="%s" data-index="/%s" hidden><label for="pc-q">%s</label>'
            '<input id="pc-q" type="search" autocomplete="off" spellcheck="false" placeholder="%s">'
            '<p class="pc-msg" aria-live="polite"></p><ul class="pc-list"></ul><div class="pc-res" aria-live="polite" hidden></div>'
            '<script type="application/json" class="pc-i18n">%s</script></div>'
            '<script src="/assets/price-checker.js" defer></script>') % (lang, INDEX, esc(s['label']), esc(s['ph']), data)


def index_dataset_ld(lang, url):
    return {'@context': 'https://schema.org', '@type': 'Dataset',
            'name': {'en': 'Vinted asking prices for %d items (vinted.be, %s)' % (len(PUB), window('en')),
                     'fr': 'Prix demandés sur Vinted pour %d articles (vinted.be, %s)' % (len(PUB), window('fr'))}[lang],
            'description': {'en': 'Median and 25th-75th percentile asking price and listing count for %d items, from vinted.be listings that matched SNYPD users\' searches. Asking prices, not sale prices.' % len(PUB),
                            'fr': 'Prix demandé médian, 25e-75e centile et nombre d\'annonces pour %d articles, à partir des annonces vinted.be correspondant aux recherches des utilisateurs de SNYPD. Prix demandés, pas prix de vente.' % len(PUB)}[lang],
            'url': SITE + url, 'creator': DATASET_CREATOR, 'license': DATASET_LICENSE, 'inLanguage': lang, 'isAccessibleForFree': True,
            'temporalCoverage': '%s/%s' % (WIN_FROM.isoformat(), GEN.isoformat()), 'spatialCoverage': 'Belgium',
            'variableMeasured': ['asking price (median)', 'asking price (25th percentile)', 'asking price (75th percentile)', 'listing count'],
            'distribution': [{'@type': 'DataDownload', 'encodingFormat': 'application/json', 'contentUrl': SITE + '/' + INDEX}],
            'dateModified': GEN.isoformat()}


def page_checker(lang):
    total = sum(V[it['slug']]['sample_size'] for it in PUB)
    win = window(lang)
    url = SLUGS['checker'][lang]
    sold = SLUGS['sold'][lang]
    az = sorted(PUB, key=lambda x: iname(x, lang).lower())

    def li(it):
        v = V[it['slug']]
        small = {'en': 'middle half %s &ndash; %s, %s listings', 'fr': 'moitié centrale %s &ndash; %s, %s annonces'}[lang]
        return '<li><a href="%s">%s</a>: %s <small>(%s)</small></li>' % (
            item_url(it, lang), esc(iname(it, lang)), money(v['typical_cents'], lang),
            small % (money(v['range_cents']['low'], lang), money(v['range_cents']['high'], lang), num(v['sample_size'], lang)))
    rows = ''.join(li(it) for it in az)
    if lang == 'en':
        body = f"""
<section id="check">
  <h2>Check a price</h2>
  <p>Type a model or a brand (for example Samba, Nuptse or Longchamp). The result links to the item&rsquo;s page with prices by condition, and has a button that starts a SNYPD alert under the cheapest-quarter price. The checker needs JavaScript; every item is also listed below.</p>
  {checker_box('en')}
</section>
<section id="all">
  <h2>All {len(PUB)} items, A to Z</h2>
  <ul class="pc-az">{rows}</ul>
</section>
<section id="read">
  <h2>How to read the result</h2>
  <ul>
    <li><strong>Typical asking price</strong> is the median: half of the listings ask less, half ask more.</li>
    <li><strong>Middle half of listings</strong> runs from the 25th to the 75th percentile. Below its lower end is the cheapest quarter: use it as a filter, not as proof of a bargain, since a cheap listing can be more worn, a different colourway, a kids&rsquo; size or a fake.</li>
    <li><strong>Listings</strong> is how many vinted.be listings the numbers come from. Every item has at least {MIN_LISTINGS}.</li>
    <li><strong>Condition matters.</strong> Each item page splits the price by the seller&rsquo;s condition label.</li>
    <li>Prices on other Vinted sites can differ.</li>
  </ul>
</section>
<section id="why">
  <h2>Why asking prices?</h2>
  <p>Because they are what Vinted shows. Vinted has no search for sold items and no record of what an item sold for: its help centre describes neither. And a buyer can offer up to 40% below the listed price (<a href="{copy_sold.HELP_BASE['en']}258" rel="nofollow">Vinted help, article 258</a>). More: <a href="{sold}">can you see sold items on Vinted?</a></p>
</section>
<section id="missing">
  <h2>Item not in the checker?</h2>
  <p>The checker only has the {len(PUB)} items with enough data for a clear price (at least {MIN_LISTINGS} listings, medium or high confidence, one model per search). For anything else, compare asking prices on Vinted yourself (<a href="{sold}#check">how</a>), or let SNYPD watch the search with your own maximum price.</p>
  {gc.cta('en')}
</section>
<section id="method">
  <h2>Where the numbers come from</h2>
  <p>SNYPD collects new vinted.be listings for the searches its users watch. The checker uses the same data as the <a href="{HUB['en']}">Vinted price guide</a>: listings seen over {WIN_DAYS} days ({win}), median and 25th to 75th percentile asking price per item. Full method: <a href="{HUB['en']}#method">how these prices are made</a>. The data file behind the checker is public: <a href="/{INDEX}">price-index.json</a> (<a href="{DATASET_LICENSE}" rel="license">CC BY 4.0</a>, with a link to this page).</p>
</section>"""
        title = 'Vinted price checker: typical asking prices of %d items (%s) | SNYPD' % (len(PUB), month_year('en'))
        desc = 'Check what an item costs on Vinted: type a model and get its typical asking price, the middle half of listings and the listing count, from %s vinted.be listings.' % num(total, 'en')
        lead = ('Type an item to see its typical asking price on Vinted, the range where the middle half of listings ask, and how many listings that is based on. '
                '%d popular items, from %s listings SNYPD saw on vinted.be (%s). Asking prices, not sale prices.' % (len(PUB), num(total, 'en'), win))
        toc = [('check', 'Check a price'), ('all', 'All items'), ('read', 'Reading the result'), ('why', 'Why asking prices'), ('missing', 'Item missing?'), ('method', 'Method')]
        return gc.page('checker', 'en', title, desc, 'VINTED PRICE CHECKER', 'Vinted price checker', lead, toc, body,
                       [index_dataset_ld('en', url)], parent=('Vinted price guide', HUB['en']))
    nb = '\u00a0'
    body = f"""
<section id="estimer">
  <h2>Estimer un prix</h2>
  <p>Tape un modèle ou une marque (par exemple Samba, Nuptse ou Longchamp). Le résultat renvoie vers la page de l’article avec les prix selon l’état, et propose un bouton qui lance une alerte SNYPD sous le prix du quart le moins cher. L’outil a besoin de JavaScript{nb}; tous les articles sont aussi listés plus bas.</p>
  {checker_box('fr')}
</section>
<section id="tous">
  <h2>Les {len(PUB)} articles, de A à Z</h2>
  <ul class="pc-az">{rows}</ul>
</section>
<section id="lire">
  <h2>Comment lire le résultat</h2>
  <ul>
    <li><strong>Prix demandé typique</strong>{nb}: la médiane, donc la moitié des annonces demandent moins et l’autre moitié plus.</li>
    <li><strong>Moitié centrale des annonces</strong>{nb}: du 25e au 75e centile. Sous le bas de la fourchette, c’est le quart le moins cher{nb}: sers-t’en comme filtre, pas comme preuve d’une bonne affaire, car une annonce moins chère peut être plus usée, d’un autre coloris, en taille enfant ou une contrefaçon.</li>
    <li><strong>Annonces</strong>{nb}: le nombre d’annonces vinted.be derrière les chiffres. Chaque article en a au moins {MIN_LISTINGS}.</li>
    <li><strong>L’état compte.</strong> Chaque page article sépare le prix selon l’état indiqué par le vendeur.</li>
    <li>Les prix peuvent différer sur les autres sites Vinted.</li>
  </ul>
</section>
<section id="pourquoi">
  <h2>Pourquoi des prix demandés{nb}?</h2>
  <p>Parce que c’est ce que Vinted affiche. Vinted n’a pas de recherche d’articles vendus ni de trace du prix auquel un article a été vendu{nb}: son centre d’aide ne décrit ni l’un ni l’autre. Et un acheteur peut proposer jusqu’à 40{nb}% sous le prix affiché (<a href="{copy_sold.HELP_BASE['fr']}258" rel="nofollow">aide Vinted, article 258</a>). Plus de détails{nb}: <a href="{sold}">peut-on voir les articles vendus sur Vinted{nb}?</a></p>
</section>
<section id="absent">
  <h2>Ton article n’y est pas{nb}?</h2>
  <p>L’outil ne contient que les {len(PUB)} articles avec assez de données pour un prix clair (au moins {MIN_LISTINGS} annonces, fiabilité moyenne ou élevée, un seul modèle par recherche). Pour le reste, compare toi-même les prix demandés sur Vinted (<a href="{sold}#estimer">comment</a>), ou laisse SNYPD surveiller la recherche avec ton propre prix maximum.</p>
  {gc.cta('fr')}
</section>
<section id="methode">
  <h2>D’où viennent les chiffres</h2>
  <p>SNYPD collecte les nouvelles annonces vinted.be pour les recherches suivies par ses utilisateurs. L’outil utilise les mêmes données que le <a href="{HUB['fr']}">guide des prix Vinted</a>{nb}: les annonces vues sur {WIN_DAYS} jours ({win}), prix demandé médian et du 25e au 75e centile par article. Méthode complète{nb}: <a href="{HUB['fr']}#methode">comment ces prix sont calculés</a>. Le fichier de données derrière l’outil est public{nb}: <a href="/{INDEX}">price-index.json</a> (<a href="{DATASET_LICENSE}" rel="license">CC BY 4.0</a>, avec un lien vers cette page).</p>
</section>"""
    title = 'Estimer un prix Vinted%s: prix demandés typiques de %d articles (%s) | SNYPD' % (nb, len(PUB), month_year('fr'))
    desc = 'Estime le prix d’un article sur Vinted%s: tape un modèle et obtiens son prix demandé typique, la moitié centrale des annonces et leur nombre, à partir de %s annonces vinted.be.' % (nb, num(total, 'fr').replace('\u202f', nb))
    lead = ('Tape un article pour voir son prix demandé typique sur Vinted, la fourchette de la moitié centrale des annonces et le nombre d’annonces derrière ces chiffres. '
            '%d articles populaires, à partir de %s annonces vues par SNYPD sur vinted.be (%s). Prix demandés, pas prix de vente.' % (len(PUB), num(total, 'fr'), win))
    toc = [('estimer', 'Estimer un prix'), ('tous', 'Tous les articles'), ('lire', 'Lire le résultat'), ('pourquoi', 'Pourquoi des prix demandés'), ('absent', 'Article absent'), ('methode', 'Méthode')]
    return gc.page('checker', 'fr', title, desc, 'ESTIMATION DE PRIX VINTED', 'Estimer un prix sur Vinted', lead, toc, body,
                   [index_dataset_ld('fr', url)], parent=('Guide des prix Vinted', HUB['fr']))


# ---------------------------------------------------------------- "Can you see sold items on Vinted?"
def examples():
    """Four items for the sold page: the best-covered item of each category, then the next best overall."""
    by_n = sorted(PUB, key=lambda x: -V[x['slug']]['sample_size'])
    pick = []
    for c in ('sneakers', 'clothing', 'accessories', 'collectibles'):
        pick += [x for x in by_n if x['cat'] == c][:1]
    pick += [x for x in by_n if x not in pick]
    return pick[:4]


def page_sold(lang):
    c = copy_sold.COPY[lang]
    qs = copy_sold.QUOTES[lang]
    gl = lang if lang in ('en', 'fr') else 'en'  # the price guide and checker exist in EN and FR
    total = sum(V[it['slug']]['sample_size'] for it in PUB)
    read = gc.date_txt(copy_sold.HELP_READ, lang)
    f = dict(items=len(PUB), listings=num(total, lang), window=window(lang), days=WIN_DAYS, read=read,
             guide=HUB[gl], checker=SLUGS['checker'][gl], method=HUB[gl] + ('#methode' if gl == 'fr' else '#method'))

    def F(s):
        return s.format(**f)
    base = copy_sold.HELP_BASE[lang]
    oq, cq = {'fr': ('«\u00a0', '\u00a0»'), 'de': ('„', '“')}.get(lang, ('“', '”'))

    def bq(aid, i=0):
        title, quotes = qs[aid]
        return ('<blockquote>%s%s%s<cite>%s, <a href="%s%d" rel="nofollow">%s</a> (%s %d)</cite></blockquote>'
                % (oq, esc(quotes[i]), cq, c['cite'], base, aid, esc(title), c['article'], aid))
    ids = [a for a, _ in c['toc']]
    rows = [['<a href="%s">%s</a>' % (item_url(it, gl), esc(iname(it, gl))), money(V[it['slug']]['typical_cents'], lang),
             '%s &ndash; %s' % (money(V[it['slug']]['range_cents']['low'], lang), money(V[it['slug']]['range_cents']['high'], lang)),
             num(V[it['slug']]['sample_size'], lang)] for it in examples()]
    faq = [(q, F(a)) for q, a in c['faq']]
    sources = ''.join('<li><a href="%s%d" rel="nofollow">%s</a> (%s %d)</li>' % (base, a, esc(qs[a][0]), c['article'], a) for a in (35, 214, 60, 258))
    body = f"""
<section id="{ids[0]}">
  <h2>{c['short_h']}</h2>
  <div class="lg-box lg-mint"><p><strong>{c['no']}</strong> {c['in_detail']}</p><ul>{''.join('<li>%s</li>' % F(s) for s in c['short'])}</ul></div>
</section>
<section id="{ids[1]}">
  <h2>{c['shows_h']}</h2>
  <p>{F(c['shows_intro'])}</p>
  {bq(35)}
  <p>{c['after'][35]}</p>
  {bq(214)}
  <p>{c['after'][214]}</p>
  {bq(60)}
  <p>{c['after'][60]}</p>
</section>
<section id="{ids[2]}">
  <h2>{c['paid_h']}</h2>
  {bq(258, 0)}
  {bq(258, 1)}
  <p>{c['paid_after']}</p>
</section>
<section id="{ids[3]}">
  <h2>{c['asking_h']}</h2>
  <p>{F(c['asking_p1'])}</p>
  {table(c['asking_head'], rows)}
  <p>{F(c['asking_p2'])}</p>
</section>
<section id="{ids[4]}">
  <h2>{c['check_h']}</h2>
  <ol>{''.join('<li>%s</li>' % F(s) for s in c['check'])}</ol>
</section>
<section id="{ids[5]}">
  <h2>{c['alert_h']}</h2>
  <p>{c['alert_p']}</p>
  {gc.cta(lang)}
</section>
<section id="{ids[6]}">
  <h2>{c['faq_h']}</h2>
  {faq_html(faq)}
</section>
<section id="{ids[7]}">
  <h2>{c['sources_h']}</h2>
  <p>{F(c['sources_intro'])}</p>
  <ul>{sources}</ul>
  <p>{F(c['sources_data'])}</p>
</section>"""
    parent = {'en': ('Vinted price guide', HUB['en']), 'fr': ('Guide des prix Vinted', HUB['fr'])}.get(lang)
    return gc.page('sold', lang, c['title'], c['desc'], c['eyebrow'], esc(c['h1']), F(c['lead']), c['toc'], body,
                   [faq_ld(faq)], parent=parent)


# ---------------------------------------------------------------- public data file + Dutch review
def price_index():
    """Only what the published pages already show: per item its names, page links, the search words of
    its alert button, typical price, 25th/75th percentile and listing count. No listing or seller data."""
    langs = [l for l in LANGS if is_live('guide', l)]
    items = []
    for it in sorted(PUB, key=lambda x: x['name'].lower()):
        v = V[it['slug']]
        items.append({'id': it['slug'], 'name': {l: iname(it, l) for l in langs}, 'brand': it['brand'], 'cat': it['cat'],
                      'q': it['query'], 'typical': v['typical_cents'], 'p25': v['range_cents']['low'], 'p75': v['range_cents']['high'],
                      'n': v['sample_size'], 'url': {l: item_url(it, l) for l in langs}})
    return {'about': 'Typical Vinted asking prices: median and 25th-75th percentile, in euro cents, of vinted.be listings that matched '
                     'SNYPD users\' searches. Asking prices, not sale prices. Method: ' + SITE + HUB['en'] + '#method',
            'source': 'vinted.be', 'currency': 'EUR', 'unit': 'cents',
            'window': {'from': WIN_FROM.isoformat(), 'to': GEN.isoformat()},
            'license': DATASET_LICENSE, 'attribution': SITE + HUB['en'], 'items': items}


def write_json(rel, obj):
    data = (json.dumps(obj, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.isfile(path) or open(path, 'rb').read() != data:
        open(path, 'wb').write(data)
    print('wrote', rel, len(data), 'bytes')


def nl_review_file(sample='adidas-samba'):
    """Plain-text Dutch for Tanush's review (website repo, never deployed): the hub, one item page (the other
    item pages use the same template), the item names, condition and category labels, the search-box words."""
    import html as _html
    import re as _re

    def text(page):
        main = page.split('<main>', 1)[1].split('</main>', 1)[0]
        main = _re.sub(r'<script\b.*?</script>', ' ', main, flags=_re.S)
        main = _re.sub(r'<(h1|h2|h3)[^>]*>', '\n\n## ', main)
        main = _re.sub(r'<(p|li|tr|blockquote)[^>]*>', '\n', main)
        main = _re.sub(r'<t[dh][^>]*>', ' | ', main)
        main = _re.sub(r'<[^>]+>', '', main)
        main = _re.sub(r'[ \t]+', ' ', _html.unescape(main))
        return _re.sub(r'\n\s*\n\s*\n+', '\n\n', main).strip()
    it = next(x for x in PUB if x['slug'] == sample)
    out = ['# Dutch review: price guide (work order 18, step 5)', '',
           'Written ' + datetime.date.today().isoformat() + '. Part of the same Dutch review as outreach/19-nl-review-step4.md: one "NL ok" publishes both.',
           'Built but NOT published (gen_price_guide.NL_HELD): /nl/vinted-prijzen + %d item pages /nl/vinted-prijzen/<item>.' % len(PUB),
           'Preview files (open in a browser, site repo): ops/seo/preview/nl-vinted-prijzen.html and ops/seo/preview/nl-vinted-prijzen-<item>.html.',
           'Read it as a Flemish reseller would. Reply "NL ok" or list the lines to change.', '',
           '## Points to check first',
           '- Condition names: are these the words your Vinted app shows in Dutch? ' + ', '.join(COND[k]['nl'] for k in COND),
           '- Category headings: ' + ', '.join(CAT[k]['nl'] for k in CAT),
           '- Item names changed for Dutch: ' + ', '.join('%s -> %s' % (x['name'], NAME_NL[x['slug']]) for x in PUB if x['slug'] in NAME_NL)
           + '. All other items keep their English name (brand + model).',
           '- Search box words: ' + ' / '.join('%s' % v for k, v in PC_TXT['nl'].items()),
           '- Not translated on purpose: the fee calculator, Market Report and FAQ links say "(Engels)"; sign-up and payment are in English (said on the page).',
           '', '---', '', '# /nl/vinted-prijzen (hub)', '', text(page_hub('nl')),
           '', '---', '', '# /nl/vinted-prijzen/%s (one item page; the other %d use the same sentences with their own numbers)' % (sample, len(PUB) - 1), '',
           text(page_item(it, 'nl'))]
    path = r'C:\Users\Tanus\website\outreach\19b-nl-review-step5.md'
    if os.path.isdir(os.path.dirname(path)):
        open(path, 'w', encoding='utf-8').write(gc.plans.fill('\n'.join(out) + '\n', 'nl'))
        print('wrote', path)


def sitemap_pages():
    """(path, file, hreflang alternates) for prepublish.py. Held languages stay out."""
    out = []
    for key in ['guide'] + ['pg:' + it['slug'] for it in PUB]:
        langs = gc.live_langs(key)
        alts = {l: SLUGS[key][l] for l in langs}
        alts['x-default'] = SLUGS[key]['en']
        out += [(SLUGS[key][l], SLUGS[key][l].lstrip('/') + '.html', alts) for l in langs]
    return out


if __name__ == '__main__':
    print('items published: %d of %d (min %d listings)' % (len(PUB), len(ITEMS), MIN_LISTINGS))
    for lang in LANGS:
        write(out_path('guide', lang), page_hub(lang))
        for it in PUB:
            write(out_path('pg:' + it['slug'], lang), page_item(it, lang))
    for lang in SLUGS['checker']:
        write(out_path('checker', lang), page_checker(lang))
    for lang in SLUGS['sold']:
        write(out_path('sold', lang), page_sold(lang))
    write_json(INDEX, price_index())
    if NL_HELD:
        nl_review_file()
