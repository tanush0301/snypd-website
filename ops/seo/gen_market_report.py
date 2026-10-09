#!/usr/bin/env python3
# Monthly "Vinted Market Report" (Belgium, vinted.be asking prices): one permanent page per edition
# plus a hub, English and French, and a CSV per edition.
#
#   python ops/seo/gen_market_report.py          (then python ops/seo/prepublish.py)
#
# Every number comes from two files of the edition, never typed by hand:
#   - the dated price-guide snapshot (ops/seo/data/price-guide-<date>.json, price_guide_batch.py)
#   - the SQL output (ops/seo/data/market-report-<edition>.json, market_report_stats.sql, md5-checked)
# New edition: run both, add a line to EDITIONS, regenerate. An edition's page never changes after
# publication except for wording fixes: it is meant to be cited.
import csv, datetime, io, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_content as gc  # noqa: E402
import gen_price_guide as pg  # noqa: E402
from gen_content import SITE, SLUGS, PAGE_MODIFIED, esc, table, money, num, write, DATASET_CREATOR, DATASET_LICENSE  # noqa: E402

ROOT = gc.ROOT
DATA = os.path.join(ROOT, 'ops', 'seo', 'data')
EDITIONS = [
    {'id': '2026-10', 'published': '2026-10-09', 'guide': 'price-guide-2026-10-09.json', 'stats': 'market-report-2026-10.json',
     'slug': {'en': 'october-2026', 'fr': 'octobre-2026'}, 'name': {'en': 'October 2026', 'fr': 'octobre 2026'}},
]
HUB = {'en': '/vinted-market-report', 'fr': '/fr/rapport-marche-vinted'}
LANGS = ('en', 'fr')
NB = ' '
COND_ORDER = ['Neuf avec étiquette', 'Neuf sans étiquette', 'Très bon état', 'Bon état', 'Satisfaisant']
COND_NAME = {'Neuf avec étiquette': {'en': 'New with tags', 'fr': 'Neuf avec étiquette'},
             'Neuf sans étiquette': {'en': 'New without tags', 'fr': 'Neuf sans étiquette'},
             'Très bon état': {'en': 'Very good', 'fr': 'Très bon état'},
             'Bon état': {'en': 'Good', 'fr': 'Bon état'}, 'Satisfaisant': {'en': 'Satisfactory', 'fr': 'Satisfaisant'}}


def load(ed):
    g = json.load(open(os.path.join(DATA, ed['guide']), encoding='utf-8'))
    st = json.load(open(os.path.join(DATA, ed['stats']), encoding='utf-8'))
    by_q = {r['q']: r['view'] for r in g['results'] if r.get('ok')}
    items = []
    for it in pg.ITEMS:  # same publication rule as the price guide
        v = by_q.get(it['query'])
        if it.get('skip') or not v or v.get('display_verdict') != 'ok' or v.get('confidence') not in ('medium', 'high') \
                or (v.get('sample_size') or 0) < pg.MIN_LISTINGS or not v.get('typical_cents') or not v.get('range_cents'):
            continue
        conds = {c['condition_label']: c for c in v.get('by_condition') or []
                 if c.get('verdict') == 'ok' and (c.get('sample_size') or 0) >= pg.MIN_COND and c.get('typical_cents')}
        new = conds.get('New, with tag')
        vg = conds.get('Very good')
        items.append(dict(it=it, v=v, typ=v['typical_cents'], lo=v['range_cents']['low'], hi=v['range_cents']['high'],
                          n=v['sample_size'], sellers=v.get('distinct_sellers') or 0,
                          nwt=new['typical_cents'] if new else None, vg=vg['typical_cents'] if vg else None))
    return g, st, items


def median(xs):
    xs = sorted(xs)
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2.0


def findings(st, items):
    prem = [(x, round(100.0 * (x['nwt'] - x['vg']) / x['vg'])) for x in items if x['nwt'] and x['vg']]
    spread = sorted(items, key=lambda x: -x['hi'] / float(x['lo']))
    known = {k: st['condition_mix'].get(k, 0) for k in COND_ORDER}
    tot_known = sum(known.values())
    return dict(
        prem=prem, prem_median=round(median([p for _, p in prem])) if prem else None,
        spread=spread[:3],
        top=max(items, key=lambda x: x['typ']), bottom=min(items, key=lambda x: x['typ']),
        cut_share=round(100.0 * st['price_cut'] / st['seen_twice'], 1),
        known=known, tot_known=tot_known,
        new_share=round(100.0 * (known['Neuf avec étiquette'] + known['Neuf sans étiquette']) / tot_known),
        vg_share=round(100.0 * known['Très bon état'] / tot_known))


def nm(x, lang):
    return x['it'].get('name_fr', x['it']['name']) if lang == 'fr' else x['it']['name']


def pct(v, lang):
    s = ('%.1f' % v) if isinstance(v, float) and v != int(v) else '%d' % v
    return (s.replace('.', ',') + NB + '%') if lang == 'fr' else s + '%'


def d_txt(iso, lang):
    return gc.date_txt(iso[:10], lang)


def csv_path(ed):
    return 'vinted-market-report-%s.csv' % ed['id']


def write_csv(ed, items, st):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator='\n')
    w.writerow(['item', 'search', 'category', 'typical_asking_eur', 'p25_eur', 'p75_eur', 'listings', 'sellers',
                'new_with_tags_typical_eur', 'very_good_typical_eur'])
    for x in items:
        w.writerow([x['it']['name'], x['it']['query'], x['it']['cat'], x['typ'] / 100, x['lo'] / 100, x['hi'] / 100, x['n'], x['sellers'],
                    (x['nwt'] / 100) if x['nwt'] else '', (x['vg'] / 100) if x['vg'] else ''])
    buf.write('# Source: SNYPD Vinted Market Report %s, %s/vinted-market-report/%s. Asking prices (median, 25th and 75th percentile) of vinted.be listings that matched SNYPD users\' searches, %s to %s. Not sale prices. CC BY 4.0.\n'
              % (ed['name']['en'], SITE, ed['slug']['en'], st['window_start'][:10], st['window_end'][:10]))
    write(csv_path(ed), buf.getvalue())


def page_edition(ed, lang):
    g, st, items = load(ed)
    f = findings(st, items)
    key = 'mr:' + ed['id']
    url = SLUGS[key][lang]
    win = '%s %s %s' % (d_txt(st['window_start'], lang), 'to' if lang == 'en' else 'au', d_txt(st['window_end'], lang))
    if lang == 'fr':
        win = 'du ' + win
    cite_url = SITE + url
    cats = ['sneakers', 'clothing', 'accessories', 'collectibles']
    rows_by_cat = []
    for c in cats:
        xs = [x for x in items if x['it']['cat'] == c]
        if not xs:
            continue
        head = {'en': ['ITEM', 'TYPICAL ASKING PRICE', 'CHEAPEST QUARTER BELOW', 'MIDDLE HALF', 'LISTINGS'],
                'fr': ['ARTICLE', 'PRIX DEMANDÉ TYPIQUE', 'QUART LE MOINS CHER SOUS', 'MOITIÉ CENTRALE', 'ANNONCES']}[lang]
        rows = [['<a href="%s">%s</a>' % (pg.item_url(x['it'], lang), esc(nm(x, lang))), money(x['typ'], lang), money(x['lo'], lang),
                 '%s &ndash; %s' % (money(x['lo'], lang), money(x['hi'], lang)), num(x['n'], lang)] for x in xs]
        rows_by_cat.append('<h3>%s</h3>%s' % (pg.CAT[c][lang].upper(), table(head, rows)))
    prem_rows = [[esc(nm(x, lang)), money(x['nwt'], lang), money(x['vg'], lang), ('+' if p >= 0 else '') + pct(p, lang)]
                 for x, p in sorted(f['prem'], key=lambda t: -t[1])]
    cond_rows = [[COND_NAME[k][lang], num(f['known'][k], lang), pct(round(100.0 * f['known'][k] / f['tot_known']), lang)] for k in COND_ORDER]
    sp = f['spread']
    if lang == 'en':
        k = [
            'New with tags asks a median <strong>%s more</strong> than very good condition, across the %d items where both have a clear price.' % (pct(f['prem_median'], 'en'), len(f['prem'])),
            '<strong>%s</strong> of the listings SNYPD saw more than once had their price cut while it watched; the median cut was <strong>%s</strong> (half of the cuts between %s and %s). %s listings had their price raised instead.'
            % (pct(f['cut_share'], 'en'), pct(st['cut_pct_median'], 'en'), pct(st['cut_pct_p25'], 'en'), pct(st['cut_pct_p75'], 'en'), num(st['price_raised'], 'en')),
            'Widest price spread, so the most room for a bargain: <strong>%s</strong>, where the dearest quarter asks %s or more and the cheapest quarter %s or less.' % (esc(nm(sp[0], 'en')), money(sp[0]['hi'], 'en'), money(sp[0]['lo'], 'en')),
            '%s of listings with a condition are very good, %s are new (with or without tags).' % (pct(f['vg_share'], 'en'), pct(f['new_share'], 'en')),
            'Highest typical asking price of the %d items: %s at %s. Lowest: %s at %s.' % (len(items), esc(nm(f['top'], 'en')), money(f['top']['typ'], 'en'), esc(nm(f['bottom'], 'en')), money(f['bottom']['typ'], 'en')),
        ]
        cite = 'Source: SNYPD Vinted Market Report, %s (%s). Asking prices on vinted.be, %s.' % (ed['name']['en'], cite_url, win)
        body = f"""
<section id="findings">
  <h2>Key findings</h2>
  <div class="lg-box lg-mint"><ol>{''.join('<li>%s</li>' % s for s in k)}</ol></div>
  <p>Based on {num(st['listings'], 'en')} vinted.be listings from {num(st['sellers'], 'en')} sellers, {win}. This is SNYPD&rsquo;s first monthly report; from November it adds the change since the month before.</p>
</section>
<section id="prices">
  <h2>Typical asking prices of {len(items)} popular items</h2>
  <p>The typical price is the median asking price; a listing below the &ldquo;cheapest quarter&rdquo; price is cheaper than three in four listings of that item. Each item links to its page in the <a href="{pg.HUB['en']}">Vinted price guide</a>, with prices by condition.</p>
  {''.join(rows_by_cat)}
</section>
<section id="condition">
  <h2>What condition is worth</h2>
  <p>Typical asking price of new-with-tags listings against very good ones, for every item where both are clear:</p>
  {table(['ITEM', 'NEW WITH TAGS', 'VERY GOOD', 'DIFFERENCE'], prem_rows)}
</section>
<section id="cuts">
  <h2>Price cuts</h2>
  <p>A price change is visible only for listings SNYPD saw more than once: {num(st['seen_twice'], 'en')} of the {num(st['listings'], 'en')}. Of those, {num(st['price_cut'], 'en')} were cut ({pct(f['cut_share'], 'en')}) and {num(st['price_raised'], 'en')} were raised. A quarter of the cuts were {pct(st['cut_pct_p25'], 'en')} or less, half {pct(st['cut_pct_median'], 'en')} or less, three quarters {pct(st['cut_pct_p75'], 'en')} or less.</p>
</section>
<section id="mix">
  <h2>Condition mix</h2>
  {table(['CONDITION', 'LISTINGS', 'SHARE'], cond_rows)}
  <p>Shares of the {num(f['tot_known'], 'en')} listings with a condition; {num(st['condition_mix'].get('unknown', 0), 'en')} had none SNYPD could read.</p>
</section>
<section id="method">
  <h2>Method and limits</h2>
  <p>SNYPD collects new listings from vinted.be for the searches its users run, so this covers what those searches return, not all of Vinted. All prices are asking prices: Vinted does not publish what items sell for. Item prices use SNYPD&rsquo;s Market Report: median and 25th&ndash;75th percentile, with outliers flagged; an item is included only with at least {pg.MIN_LISTINGS} listings and a clear price. Prices on other Vinted sites can differ.</p>
</section>
<section id="cite">
  <h2>Use these numbers</h2>
  <p>Free to reuse with credit (<a href="{DATASET_LICENSE}" rel="license">CC BY 4.0</a>). Download the item table as <a href="/{csv_path(ed)}">CSV</a>. Suggested citation:</p>
  <div class="lg-box"><p>{esc(cite)}</p></div>
</section>
<section id="alerts">
  <h2>Catch the cheapest quarter</h2>
  <p>SNYPD checks your Vinted search about every 30 seconds and sends new matches to your phone. Every item page in the price guide has a button that starts that search with its cheapest-quarter price as the maximum.</p>
  {gc.cta('en')}
</section>"""
        title = 'Vinted Market Report %s: asking prices in Belgium | SNYPD' % ed['name']['en']
        desc = 'Vinted asking prices in %s: %d items, condition premium, price cuts and condition mix, from %s vinted.be listings. Free data (CC BY 4.0).' % (ed['name']['en'], len(items), num(st['listings'], 'en'))
        h1 = 'Vinted Market Report: %s' % ed['name']['en']
        lead = 'What %s vinted.be listings from %s sellers say about Vinted asking prices, %s.' % (num(st['listings'], 'en'), num(st['sellers'], 'en'), win)
        toc = [('findings', 'Key findings'), ('prices', 'Prices'), ('condition', 'Condition'), ('cuts', 'Price cuts'), ('mix', 'Condition mix'), ('method', 'Method'), ('cite', 'Use the data')]
        parent = ('Vinted Market Report', HUB['en'])
    else:
        k = [
            'Le neuf avec étiquette demande en médiane <strong>%s de plus</strong> que le très bon état, sur les %d articles où les deux ont un prix clair.' % (pct(f['prem_median'], 'fr'), len(f['prem'])),
            '<strong>%s</strong> des annonces vues plus d’une fois par SNYPD ont baissé leur prix pendant qu’il les suivait%s; la baisse médiane était de <strong>%s</strong> (la moitié des baisses entre %s et %s). %s annonces ont au contraire vu leur prix augmenter.'
            % (pct(f['cut_share'], 'fr'), NB, pct(st['cut_pct_median'], 'fr'), pct(st['cut_pct_p25'], 'fr'), pct(st['cut_pct_p75'], 'fr'), num(st['price_raised'], 'fr')),
            'Plus grand écart de prix, donc le plus de place pour une bonne affaire%s: <strong>%s</strong>, où le quart le plus cher demande %s ou plus et le quart le moins cher %s ou moins.' % (NB, esc(nm(sp[0], 'fr')), money(sp[0]['hi'], 'fr'), money(sp[0]['lo'], 'fr')),
            '%s des annonces avec un état sont en très bon état, %s sont neuves (avec ou sans étiquette).' % (pct(f['vg_share'], 'fr'), pct(f['new_share'], 'fr')),
            'Prix demandé typique le plus haut des %d articles%s: %s à %s. Le plus bas%s: %s à %s.' % (len(items), NB, esc(nm(f['top'], 'fr')), money(f['top']['typ'], 'fr'), NB, esc(nm(f['bottom'], 'fr')), money(f['bottom']['typ'], 'fr')),
        ]
        cite = 'Source%s: SNYPD, Rapport du marché Vinted, %s (%s). Prix demandés sur vinted.be, %s.' % (NB, ed['name']['fr'], cite_url, win)
        body = f"""
<section id="resultats">
  <h2>Résultats clés</h2>
  <div class="lg-box lg-mint"><ol>{''.join('<li>%s</li>' % s for s in k)}</ol></div>
  <p>À partir de {num(st['listings'], 'fr')} annonces vinted.be de {num(st['sellers'], 'fr')} vendeurs, {win}. C’est le premier rapport mensuel de SNYPD{NB}; dès novembre, il ajoute l’évolution depuis le mois précédent.</p>
</section>
<section id="prix">
  <h2>Prix demandés typiques de {len(items)} articles populaires</h2>
  <p>Le prix typique est le prix demandé médian{NB}; une annonce sous le prix du «{NB}quart le moins cher{NB}» est moins chère que trois annonces sur quatre de cet article. Chaque article renvoie à sa page du <a href="{pg.HUB['fr']}">guide des prix Vinted</a>, avec les prix selon l’état.</p>
  {''.join(rows_by_cat)}
</section>
<section id="etat">
  <h2>Ce que vaut l’état</h2>
  <p>Prix demandé typique des annonces neuves avec étiquette face à celles en très bon état, pour chaque article où les deux sont clairs{NB}:</p>
  {table(['ARTICLE', 'NEUF AVEC ÉTIQUETTE', 'TRÈS BON ÉTAT', 'ÉCART'], prem_rows)}
</section>
<section id="baisses">
  <h2>Baisses de prix</h2>
  <p>Un changement de prix n’est visible que pour les annonces vues plus d’une fois par SNYPD{NB}: {num(st['seen_twice'], 'fr')} sur {num(st['listings'], 'fr')}. Parmi elles, {num(st['price_cut'], 'fr')} ont baissé ({pct(f['cut_share'], 'fr')}) et {num(st['price_raised'], 'fr')} ont augmenté. Un quart des baisses faisaient {pct(st['cut_pct_p25'], 'fr')} ou moins, la moitié {pct(st['cut_pct_median'], 'fr')} ou moins, les trois quarts {pct(st['cut_pct_p75'], 'fr')} ou moins.</p>
</section>
<section id="repartition">
  <h2>Répartition par état</h2>
  {table(['ÉTAT', 'ANNONCES', 'PART'], cond_rows)}
  <p>Parts des {num(f['tot_known'], 'fr')} annonces avec un état{NB}; {num(st['condition_mix'].get('unknown', 0), 'fr')} n’en avaient pas de lisible par SNYPD.</p>
</section>
<section id="methode">
  <h2>Méthode et limites</h2>
  <p>SNYPD collecte les nouvelles annonces de vinted.be pour les recherches de ses utilisateurs{NB}: ce rapport couvre ce que ces recherches renvoient, pas tout Vinted. Tous les prix sont des prix demandés{NB}: Vinted ne publie pas le prix auquel les articles se vendent. Les prix par article viennent du Market Report de SNYPD{NB}: médiane et 25e&ndash;75e centile, valeurs aberrantes signalées{NB}; un article n’est inclus qu’avec au moins {pg.MIN_LISTINGS} annonces et un prix clair. Les prix peuvent différer sur les autres sites Vinted.</p>
</section>
<section id="citer">
  <h2>Utiliser ces chiffres</h2>
  <p>Libres de réutilisation avec mention de la source (<a href="{DATASET_LICENSE}" rel="license">CC BY 4.0</a>). Télécharge le tableau des articles en <a href="/{csv_path(ed)}">CSV</a> (en anglais). Citation suggérée{NB}:</p>
  <div class="lg-box"><p>{esc(cite)}</p></div>
</section>
<section id="alertes">
  <h2>Attrape le quart le moins cher</h2>
  <p>SNYPD vérifie ta recherche Vinted environ toutes les 30 secondes et envoie les nouvelles annonces sur ton téléphone. Chaque page du guide des prix a un bouton qui lance cette recherche avec le prix du quart le moins cher comme maximum.</p>
  {gc.cta('fr')}
</section>"""
        title = 'Rapport du marché Vinted %s%s: prix demandés en Belgique | SNYPD' % (ed['name']['fr'], NB)
        desc = 'Les prix demandés sur Vinted en %s%s: %d articles, écart neuf/occasion, baisses de prix et répartition par état, à partir de %s annonces vinted.be. Données libres (CC BY 4.0).' % (ed['name']['fr'], NB, len(items), num(st['listings'], 'fr').replace(' ', NB))
        h1 = 'Rapport du marché Vinted%s: %s' % (NB, ed['name']['fr'])
        lead = 'Ce que disent %s annonces vinted.be de %s vendeurs sur les prix demandés sur Vinted, %s.' % (num(st['listings'], 'fr'), num(st['sellers'], 'fr'), win)
        toc = [('resultats', 'Résultats clés'), ('prix', 'Prix'), ('etat', 'État'), ('baisses', 'Baisses de prix'), ('repartition', 'Répartition'), ('methode', 'Méthode'), ('citer', 'Utiliser les données')]
        parent = ('Rapport du marché Vinted', HUB['fr'])
    ds = {'@context': 'https://schema.org', '@type': 'Dataset',
          'name': ('Vinted Market Report %s (vinted.be asking prices)' % ed['name']['en']) if lang == 'en' else ('Rapport du marché Vinted %s (prix demandés vinted.be)' % ed['name']['fr']),
          'description': ('Median, 25th and 75th percentile asking prices of %d items, condition premium, price cuts and condition mix, from %s vinted.be listings that matched SNYPD users\' searches. Asking prices, not sale prices.' % (len(items), st['listings'])) if lang == 'en'
          else ('Prix demandés médians, 25e et 75e centiles de %d articles, écart selon l’état, baisses de prix et répartition par état, à partir de %s annonces vinted.be correspondant aux recherches des utilisateurs de SNYPD. Prix demandés, pas prix de vente.' % (len(items), st['listings'])),
          'url': SITE + url, 'creator': DATASET_CREATOR, 'license': DATASET_LICENSE, 'inLanguage': lang, 'isAccessibleForFree': True,
          'temporalCoverage': '%s/%s' % (st['window_start'][:10], st['window_end'][:10]), 'spatialCoverage': 'Belgium',
          'distribution': [{'@type': 'DataDownload', 'encodingFormat': 'text/csv', 'contentUrl': SITE + '/' + csv_path(ed)}],
          'datePublished': ed['published']}
    return gc.page(key, lang, title, desc, 'VINTED MARKET REPORT' if lang == 'en' else 'RAPPORT DU MARCHÉ VINTED', h1, lead, toc, body, [ds], parent=parent)


def page_hub(lang):
    li = []
    for ed in reversed(EDITIONS):
        g, st, items = load(ed)
        li.append('<li><a href="%s">%s</a>%s: %s %s, %s %s</li>' % (
            SLUGS['mr:' + ed['id']][lang], {'en': 'Vinted Market Report ', 'fr': 'Rapport du marché Vinted, '}[lang] + ed['name'][lang], NB if lang == 'fr' else '',
            num(st['listings'], lang), {'en': 'listings', 'fr': 'annonces'}[lang], len(items), {'en': 'items', 'fr': 'articles'}[lang]))
    latest = SLUGS['mr:' + EDITIONS[-1]['id']][lang]
    if lang == 'en':
        body = ('<section id="editions"><h2>Editions</h2><ul>%s</ul></section>'
                '<section id="about"><h2>What this is</h2><p>Each month SNYPD publishes what the vinted.be listings it collects for its users&rsquo; searches say about Vinted asking prices: typical prices of popular items, what condition is worth, how often and how much sellers cut prices. '
                'Asking prices, not sale prices. Each edition keeps its own address so it can be cited; the data is free to reuse with credit (CC BY 4.0).</p>'
                '<p>Item by item prices: <a href="%s">the Vinted price guide</a>.</p></section>' % (''.join(li), pg.HUB['en']))
        return gc.page('mreport', 'en', 'Vinted Market Report: monthly Vinted asking-price data | SNYPD',
                       'Monthly report on Vinted asking prices in Belgium: typical prices of popular items, condition premium, price cuts. Free data (CC BY 4.0).',
                       'VINTED MARKET REPORT', 'Vinted Market Report', 'A monthly look at Vinted asking prices on vinted.be. Latest: <a href="%s">%s</a>.' % (latest, EDITIONS[-1]['name']['en']),
                       [('editions', 'Editions'), ('about', 'About')], body)
    body = ('<section id="editions"><h2>Éditions</h2><ul>%s</ul></section>'
            '<section id="apropos"><h2>Ce que c’est</h2><p>Chaque mois, SNYPD publie ce que disent les annonces vinted.be qu’il collecte pour les recherches de ses utilisateurs sur les prix demandés sur Vinted%s: prix typiques d’articles populaires, valeur de l’état, fréquence et ampleur des baisses de prix. '
            'Ce sont des prix demandés, pas des prix de vente. Chaque édition garde sa propre adresse pour pouvoir être citée%s; les données sont libres de réutilisation avec mention de la source (CC BY 4.0).</p>'
            '<p>Les prix article par article%s: <a href="%s">le guide des prix Vinted</a>.</p></section>' % (''.join(li), NB, NB, NB, pg.HUB['fr']))
    return gc.page('mreport', 'fr', 'Rapport du marché Vinted%s: données mensuelles des prix demandés | SNYPD' % NB,
                   'Rapport mensuel sur les prix demandés sur Vinted en Belgique%s: prix typiques d’articles populaires, écart selon l’état, baisses de prix. Données libres (CC BY 4.0).' % NB,
                   'RAPPORT DU MARCHÉ VINTED', 'Rapport du marché Vinted', 'Un regard mensuel sur les prix demandés sur vinted.be. Dernière édition%s: <a href="%s">%s</a>.' % (NB, latest, EDITIONS[-1]['name']['fr']),
                   [('editions', 'Éditions'), ('apropos', 'Ce que c’est')], body)


SLUGS['mreport'] = dict(HUB)
PAGE_MODIFIED['mreport'] = EDITIONS[-1]['published']
for _ed in EDITIONS:
    SLUGS['mr:' + _ed['id']] = {l: HUB[l] + '/' + _ed['slug'][l] for l in LANGS}
    PAGE_MODIFIED['mr:' + _ed['id']] = _ed['published']


def sitemap_pages():
    out = []
    for key in ['mreport'] + ['mr:' + e['id'] for e in EDITIONS]:
        alts = {l: SLUGS[key][l] for l in LANGS}
        alts['x-default'] = SLUGS[key]['en']
        out += [(SLUGS[key][l], SLUGS[key][l].lstrip('/') + '.html', alts) for l in LANGS]
    return out


if __name__ == '__main__':
    for ed in EDITIONS:
        g, st, items = load(ed)
        write_csv(ed, items, st)
        for lang in LANGS:
            write(SLUGS['mr:' + ed['id']][lang].lstrip('/') + '.html', page_edition(ed, lang))
    for lang in LANGS:
        write(HUB[lang].lstrip('/') + '.html', page_hub(lang))
