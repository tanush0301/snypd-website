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
from gen_content import MONTHS_TXT  # noqa: E402,F401

ROOT = gc.ROOT
DATA = os.path.join(ROOT, 'ops', 'seo', 'data')
EDITIONS = [
    {'id': '2026-10', 'published': '2026-10-09', 'guide': 'price-guide-2026-10-09.json', 'stats': 'market-report-2026-10.json',
     'slug': {'en': 'october-2026', 'fr': 'octobre-2026'}, 'name': {'en': 'October 2026', 'fr': 'octobre 2026'}},
    {'id': '2026-11', 'published': '2026-11-01', 'guide': 'price-guide-2026-11-01.json', 'stats': 'market-report-2026-11.json',
     'slug': {'en': 'november-2026', 'fr': 'novembre-2026'}, 'name': {'en': 'November 2026', 'fr': 'novembre 2026'}},
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


def previous(ed):
    i = [e['id'] for e in EDITIONS].index(ed['id'])
    return EDITIONS[i - 1] if i > 0 else None


def changes(ed, items):
    """Month on month: each item published in this edition AND the one before, typical asking price then and now.
    Both editions use the same method and 14-day windows, so the change is comparable, but it can also come from a
    different mix of listings (sizes, colourways, condition), which the page says. None for the first edition."""
    pe = previous(ed)
    if not pe:
        return None
    _, pst, pitems = load(pe)
    prev = {x['it']['slug']: x for x in pitems}
    rows = [(x, prev[x['it']['slug']], round(100.0 * (x['typ'] - prev[x['it']['slug']]['typ']) / prev[x['it']['slug']]['typ'], 1))
            for x in items if x['it']['slug'] in prev]
    if not rows:
        return None
    ch = [c for _, _, c in rows]
    rows.sort(key=lambda r: -r[2])
    return dict(ed=pe, st=pst, rows=rows, median=round(median(ch), 1), up=sum(c > 0 for c in ch), down=sum(c < 0 for c in ch),
                rise=rows[0] if rows[0][2] > 0 else None, fall=rows[-1] if rows[-1][2] < 0 else None)


def sgn(v, lang):
    return ('+' if v > 0 else '') + pct(v, lang)


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
    mom = changes(ed, items)
    prev = {x['it']['slug']: (px['typ'], c) for x, px, c in mom['rows']} if mom else {}
    w.writerow(['item', 'search', 'category', 'typical_asking_eur', 'p25_eur', 'p75_eur', 'listings', 'sellers',
                'new_with_tags_typical_eur', 'very_good_typical_eur'] + (['previous_typical_asking_eur', 'change_pct'] if mom else []))
    for x in items:
        p = prev.get(x['it']['slug'])
        w.writerow([x['it']['name'], x['it']['query'], x['it']['cat'], x['typ'] / 100, x['lo'] / 100, x['hi'] / 100, x['n'], x['sellers'],
                    (x['nwt'] / 100) if x['nwt'] else '', (x['vg'] / 100) if x['vg'] else '']
                   + (([p[0] / 100, p[1]] if p else ['', '']) if mom else []))
    buf.write('# Source: SNYPD Vinted Market Report %s, %s/vinted-market-report/%s. Asking prices (median, 25th and 75th percentile) of vinted.be listings that matched SNYPD users\' searches, %s to %s. Not sale prices. CC BY 4.0.\n'
              % (ed['name']['en'], SITE, ed['slug']['en'], st['window_start'][:10], st['window_end'][:10]))
    write(csv_path(ed), buf.getvalue())


def mom_point(m, lang):
    big = []
    if lang == 'en':
        if m['rise']:
            big.append('biggest rise %s (%s)' % (esc(nm(m['rise'][0], 'en')), sgn(m['rise'][2], 'en')))
        if m['fall']:
            big.append('biggest fall %s (%s)' % (esc(nm(m['fall'][0], 'en')), sgn(m['fall'][2], 'en')))
        return ('Since %s, the typical asking price rose for <strong>%d</strong> and fell for <strong>%d</strong> of the %d items in both reports; median change <strong>%s</strong>%s.'
                % (m['ed']['name']['en'], m['up'], m['down'], len(m['rows']), sgn(m['median'], 'en'), (': ' + ', '.join(big)) if big else ''))
    if m['rise']:
        big.append('plus forte hausse' + NB + ': %s (%s)' % (esc(nm(m['rise'][0], 'fr')), sgn(m['rise'][2], 'fr')))
    if m['fall']:
        big.append('plus forte baisse' + NB + ': %s (%s)' % (esc(nm(m['fall'][0], 'fr')), sgn(m['fall'][2], 'fr')))
    return ('Depuis %s, le prix demandé typique a augmenté pour <strong>%d</strong> et baissé pour <strong>%d</strong> des %d articles présents dans les deux rapports%s; évolution médiane <strong>%s</strong>%s.'
            % (m['ed']['name']['fr'], m['up'], m['down'], len(m['rows']), NB, sgn(m['median'], 'fr'), (' (' + ', '.join(big) + ')') if big else ''))


def key_points(st, items, f, lang, mom=None):
    """The edition's key findings (also shown on the hub for the latest edition); the month-on-month line first."""
    return ([mom_point(mom, lang)] if mom else []) + _key_points(st, items, f, lang)


def _key_points(st, items, f, lang):
    sp = f['spread']
    if lang == 'en':
        return [
        'New with tags asks a median <strong>%s more</strong> than very good condition, across the %d items where both have a clear price.' % (pct(f['prem_median'], 'en'), len(f['prem'])),
        '<strong>%s</strong> of the listings SNYPD saw more than once had their price cut while it watched; the median cut was <strong>%s</strong> (half of the cuts between %s and %s). %s listings had their price raised instead.'
        % (pct(f['cut_share'], 'en'), pct(st['cut_pct_median'], 'en'), pct(st['cut_pct_p25'], 'en'), pct(st['cut_pct_p75'], 'en'), num(st['price_raised'], 'en')),
        'Widest price spread: <strong>%s</strong>, where the dearest quarter asks %s or more and the cheapest quarter %s or less.' % (esc(nm(sp[0], 'en')), money(sp[0]['hi'], 'en'), money(sp[0]['lo'], 'en')),
        '%s of listings with a condition are very good, %s are new (with or without tags).' % (pct(f['vg_share'], 'en'), pct(f['new_share'], 'en')),
        'Highest typical asking price of the %d items: %s at %s. Lowest: %s at %s.' % (len(items), esc(nm(f['top'], 'en')), money(f['top']['typ'], 'en'), esc(nm(f['bottom'], 'en')), money(f['bottom']['typ'], 'en')),
        ]
    return [
        'Le neuf avec étiquette demande en médiane <strong>%s de plus</strong> que le très bon état, sur les %d articles où les deux ont un prix clair.' % (pct(f['prem_median'], 'fr'), len(f['prem'])),
        '<strong>%s</strong> des annonces vues plus d’une fois par SNYPD ont baissé leur prix pendant qu’il les suivait%s; la baisse médiane était de <strong>%s</strong> (la moitié des baisses entre %s et %s). %s annonces ont au contraire vu leur prix augmenter.'
        % (pct(f['cut_share'], 'fr'), NB, pct(st['cut_pct_median'], 'fr'), pct(st['cut_pct_p25'], 'fr'), pct(st['cut_pct_p75'], 'fr'), num(st['price_raised'], 'fr')),
        'Plus grand écart de prix%s: <strong>%s</strong>, où le quart le plus cher demande %s ou plus et le quart le moins cher %s ou moins.' % (NB, esc(nm(sp[0], 'fr')), money(sp[0]['hi'], 'fr'), money(sp[0]['lo'], 'fr')),
        '%s des annonces avec un état sont en très bon état, %s sont neuves (avec ou sans étiquette).' % (pct(f['vg_share'], 'fr'), pct(f['new_share'], 'fr')),
        'Prix demandé typique le plus haut des %d articles%s: %s à %s. Le plus bas%s: %s à %s.' % (len(items), NB, esc(nm(f['top'], 'fr')), money(f['top']['typ'], 'fr'), NB, esc(nm(f['bottom'], 'fr')), money(f['bottom']['typ'], 'fr')),
    ]


def page_edition(ed, lang):
    g, st, items = load(ed)
    f = findings(st, items)
    mom = changes(ed, items)
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
    mom_html, mom_toc = '', []
    if mom:
        pe = mom['ed']
        pe_url = SLUGS['mr:' + pe['id']][lang]
        mom_rows = [['<a href="%s">%s</a>' % (pg.item_url(x['it'], lang), esc(nm(x, lang))), money(px['typ'], lang), money(x['typ'], lang), sgn(c, lang)]
                    for x, px, c in mom['rows']]
        if lang == 'en':
            mom_toc = [('change', 'Since last month')]
            mom_html = ('<section id="change"><h2>Change since last month</h2>'
                        '<p>Typical asking price of the %d items published in both this report and the <a href="%s">%s report</a>, highest rise first. '
                        'Both use the same method and a 14-day window. A change can also come from a different mix of listings (sizes, colourways, condition), '
                        'so treat one month as a signal, not a trend.</p>%s</section>'
                        % (len(mom['rows']), pe_url, pe['name']['en'], table(['ITEM', pe['name']['en'].upper(), ed['name']['en'].upper(), 'CHANGE'], mom_rows)))
        else:
            mom_toc = [('evolution', 'Depuis le mois dernier')]
            mom_html = ('<section id="evolution"><h2>Évolution depuis le mois dernier</h2>'
                        '<p>Prix demandé typique des %d articles publiés à la fois dans ce rapport et dans le <a href="%s">rapport %s</a>, plus forte hausse en premier. '
                        'Les deux utilisent la même méthode et une fenêtre de 14 jours. Une évolution peut aussi venir d’un autre mélange d’annonces (tailles, coloris, état) : '
                        'un mois donne un signal, pas une tendance.</p>%s</section>'
                        % (len(mom['rows']), pe_url, ('d’' if pe['name']['fr'][0] in 'aeiouéh' else 'de ') + pe['name']['fr'], table(['ARTICLE', pe['name']['fr'].upper(), ed['name']['fr'].upper(), 'ÉVOLUTION'], mom_rows)))
    if lang == 'en':
        k = key_points(st, items, f, lang, mom)
        cite = 'Source: SNYPD Vinted Market Report, %s (%s). Asking prices on vinted.be, %s.' % (ed['name']['en'], cite_url, win)
        body = f"""
<section id="findings">
  <h2>Key findings</h2>
  <div class="lg-box lg-mint"><ol>{''.join('<li>%s</li>' % s for s in k)}</ol></div>
  <p>Based on {num(st['listings'], 'en')} vinted.be listings from {num(st['sellers'], 'en')} sellers, {win}.{'' if mom else ' This is SNYPD&rsquo;s first monthly report; from November it adds the change since the month before.'}</p>
</section>{mom_html}
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
        toc = [('findings', 'Key findings')] + mom_toc + [('prices', 'Prices'), ('condition', 'Condition'), ('cuts', 'Price cuts'), ('mix', 'Condition mix'), ('method', 'Method'), ('cite', 'Use the data')]
        parent = ('Vinted Market Report', HUB['en'])
    else:
        k = key_points(st, items, f, lang, mom)
        cite = 'Source%s: SNYPD, Rapport du marché Vinted, %s (%s). Prix demandés sur vinted.be, %s.' % (NB, ed['name']['fr'], cite_url, win)
        body = f"""
<section id="resultats">
  <h2>Résultats clés</h2>
  <div class="lg-box lg-mint"><ol>{''.join('<li>%s</li>' % s for s in k)}</ol></div>
  <p>À partir de {num(st['listings'], 'fr')} annonces vinted.be de {num(st['sellers'], 'fr')} vendeurs, {win}.{'' if mom else ' C’est le premier rapport mensuel de SNYPD' + NB + '; dès novembre, il ajoute l’évolution depuis le mois précédent.'}</p>
</section>{mom_html}
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
        toc = [('resultats', 'Résultats clés')] + mom_toc + [('prix', 'Prix'), ('etat', 'État'), ('baisses', 'Baisses de prix'), ('repartition', 'Répartition'), ('methode', 'Méthode'), ('citer', 'Utiliser les données')]
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
    """Latest findings, every edition (CSV each), how to cite, where the method is explained."""
    ed = EDITIONS[-1]
    g, st, items = load(ed)
    f = findings(st, items)
    latest = SLUGS['mr:' + ed['id']][lang]
    pts = key_points(st, items, f, lang, changes(ed, items))[:3]
    rows = []
    for e in reversed(EDITIONS):
        _, est, eitems = load(e)
        rows.append(['<a href="%s">%s</a>' % (SLUGS['mr:' + e['id']][lang], e['name'][lang]), num(est['listings'], lang), str(len(eitems)),
                     {'en': 'by condition, price cuts', 'fr': 'par état, baisses de prix'}[lang], '<a href="/%s">CSV</a>' % csv_path(e)])
    rows.append(['<a href="%s">%s</a>' % (SLUGS['mr:2026-09'][lang], SEPT['name'][lang]), {'en': 'not counted', 'fr': 'non compté'}[lang], str(len(SEPT_ITEMS)),
                 {'en': 'first edition, all conditions mixed', 'fr': 'première édition, états mélangés'}[lang], '<a href="/%s">CSV</a>' % REPORT_CSV])
    cite_url = SITE + latest
    if lang == 'en':
        win = '%s to %s' % (d_txt(st['window_start'], 'en'), d_txt(st['window_end'], 'en'))
        cite = 'Source: SNYPD Vinted Market Report, %s (%s). Asking prices on vinted.be, %s.' % (ed['name']['en'], cite_url, win)
        body = ('<section id="latest"><h2>Latest: %s</h2><div class="lg-box lg-mint"><ol>%s</ol></div>'
                '<p>From %s vinted.be listings by %s sellers, %s. <a href="%s">Read the full %s report</a>.</p></section>'
                % (ed['name']['en'], ''.join('<li>%s</li>' % x for x in pts), num(st['listings'], 'en'), num(st['sellers'], 'en'), win, latest, ed['name']['en'])
                + '<section id="editions"><h2>All editions</h2>%s<p class="ct-note">Each edition keeps its own address and never changes after publication, except wording fixes, so it can be cited.</p></section>'
                % table(['EDITION', 'LISTINGS', 'ITEMS', 'WHAT IT COVERS', 'DATA'], rows)
                + '<section id="cite"><h2>Use and cite the data</h2><p>Free to reuse with credit (<a href="%s" rel="license">CC BY 4.0</a>). Every edition has a CSV of its item table. Suggested citation for the latest edition:</p>'
                  '<div class="lg-box"><p>%s</p></div></section>' % (DATASET_LICENSE, esc(cite))
                + '<section id="method"><h2>Method</h2><p>All figures are asking prices of vinted.be listings that matched SNYPD users&rsquo; searches: not all of Vinted, and not sale prices. '
                  'How typical prices, ranges, confidence and refusals are worked out, and what the numbers do not handle yet (kids&rsquo; sizes, bundles, colourways, fakes): '
                  '<a href="%s#method">method of the Vinted price guide</a>. Item by item prices: <a href="%s">the Vinted price guide</a>.</p></section>' % (pg.HUB['en'], pg.HUB['en']))
        return gc.page('mreport', 'en', 'Vinted Market Report: monthly Vinted asking-price data | SNYPD',
                       'Monthly report on Vinted asking prices in Belgium: typical prices of popular items, condition premium, price cuts. Every edition with CSV, free data (CC BY 4.0).',
                       'VINTED MARKET REPORT', 'Vinted Market Report',
                       'A monthly look at Vinted asking prices on vinted.be. Latest: <a href="%s">%s</a>.' % (latest, ed['name']['en']),
                       [('latest', 'Latest'), ('editions', 'All editions'), ('cite', 'Cite'), ('method', 'Method')], body)
    win = 'du %s au %s' % (d_txt(st['window_start'], 'fr'), d_txt(st['window_end'], 'fr'))
    cite = 'Source%s: Rapport du marché Vinted de SNYPD, %s (%s). Prix demandés sur vinted.be, %s.' % (NB, ed['name']['fr'], cite_url, win)
    body = ('<section id="derniere"><h2>Dernière édition%s: %s</h2><div class="lg-box lg-mint"><ol>%s</ol></div>'
            '<p>À partir de %s annonces vinted.be de %s vendeurs, %s. <a href="%s">Lire le rapport complet de %s</a>.</p></section>'
            % (NB, ed['name']['fr'], ''.join('<li>%s</li>' % x for x in pts), num(st['listings'], 'fr'), num(st['sellers'], 'fr'), win, latest, ed['name']['fr'])
            + '<section id="editions"><h2>Toutes les éditions</h2>%s<p class="ct-note">Chaque édition garde sa propre adresse et ne change plus après publication, sauf corrections de formulation, pour pouvoir être citée.</p></section>'
            % table(['ÉDITION', 'ANNONCES', 'ARTICLES', 'CONTENU', 'DONNÉES'], rows)
            + '<section id="citer"><h2>Utiliser et citer les données</h2><p>Libres de réutilisation avec mention de la source (<a href="%s" rel="license">CC BY 4.0</a>). Chaque édition a un CSV de son tableau d’articles (en anglais). Citation suggérée pour la dernière édition%s:</p>'
              '<div class="lg-box"><p>%s</p></div></section>' % (DATASET_LICENSE, NB, esc(cite))
            + '<section id="methode"><h2>Méthode</h2><p>Tous les chiffres sont des prix demandés d’annonces vinted.be correspondant aux recherches des utilisateurs de SNYPD%s: pas tout Vinted, et pas des prix de vente. '
              'Comment les prix typiques, les fourchettes, la fiabilité et les refus sont calculés, et ce que les chiffres ne prennent pas encore en compte (tailles enfant, lots, coloris, contrefaçons)%s: '
              '<a href="%s#methode">méthode du guide des prix Vinted</a>. Les prix article par article%s: <a href="%s">le guide des prix Vinted</a>.</p></section>' % (NB, NB, pg.HUB['fr'], NB, pg.HUB['fr']))
    return gc.page('mreport', 'fr', 'Rapport du marché Vinted%s: données mensuelles des prix demandés | SNYPD' % NB,
                   'Rapport mensuel sur les prix demandés sur Vinted en Belgique%s: prix typiques d’articles populaires, écart selon l’état, baisses de prix. Chaque édition en CSV, données libres (CC BY 4.0).' % NB,
                   'RAPPORT DU MARCHÉ VINTED', 'Rapport du marché Vinted',
                   'Un regard mensuel sur les prix demandés sur vinted.be. Dernière édition%s: <a href="%s">%s</a>.' % (NB, latest, ed['name']['fr']),
                   [('derniere', 'Dernière édition'), ('editions', 'Éditions'), ('citer', 'Citer'), ('methode', 'Méthode')], body)


# ------------------------------------------------------------------ archived edition: September 2026
# Published 28 Sept 2026 as /vinted-prices (first price page, before the price guide existed), moved
# here on 10 Oct 2026; /vinted-prices and /fr/prix-vinted 308 to it (vercel.json). Different data
# shape from the monthly editions (one Market Report run of 19 searches, all conditions mixed), so it
# keeps its own renderer. Frozen: wording fixes only.
SEPT = {'id': '2026-09', 'published': '2026-09-28', 'modified': '2026-10-10',
        'slug': {'en': 'september-2026', 'fr': 'septembre-2026'}, 'name': {'en': 'September 2026', 'fr': 'septembre 2026'}}
REPORT = os.path.join(DATA, 'price-report-2026-09.json')
REPORT_CSV = 'vinted-prices-2026-09.csv'  # the address it was first published at; kept so citations work
SEPT_ITEMS = [  # query as run in the Market Report, display name, group
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
SEPT_REFUSED = [('jordan 1 low', 'Air Jordan 1 Low'), ('jordan 4', 'Air Jordan 4'), ('yeezy 350', 'Yeezy 350')]


def load_report():
    d = json.load(open(REPORT, encoding='utf-8'))
    by_q = {r['q']: r for r in d['results']}
    gen = datetime.datetime.fromisoformat(d['generated_at'].replace('Z', '+00:00'))
    return by_q, gen


def price_rows(lang):
    by_q, gen = load_report()
    rows, csv_rows = [], []
    for q, name, group in SEPT_ITEMS:
        r = by_q[q]
        v = r['view']
        if not r['ok'] or v.get('display_verdict') != 'ok' or not v.get('show_headline'):
            sys.exit(f'{q}: not a trustworthy price in the report ({v.get("display_verdict")}); move it to SEPT_REFUSED')
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
    for q, name in SEPT_REFUSED:
        v = by_q[q]['view']
        if v.get('show_headline'):
            sys.exit(f'{q}: now has a price; move it to SEPT_ITEMS')
        o = v.get('observed_cents') or {}
        refused.append((name, q, v['sample_size'], o.get('low'), o.get('high'), v.get('display_verdict')))
    first = by_q[SEPT_ITEMS[0][0]]['view']
    return rows, csv_rows, refused, gen, first


def page_september(lang):
    rows, csv_rows, refused, gen, first = price_rows(lang)
    f_typ, f_lo, f_hi = first['typical_cents'], first['range_cents']['low'], first['range_cents']['high']
    end = gen.date()
    start = end - datetime.timedelta(days=14)
    if lang == 'en':
        head = ['ITEM', 'TYPICAL ASKING PRICE', 'MIDDLE HALF OF PRICES', 'LISTINGS', 'NOTE']
        ref = ''.join(f'<li><strong>{n}</strong> ({num(c, "en")} listings, {money(lo, "en")} to {money(hi, "en")}): too spread out for one honest price.</li>' for n, q, c, lo, hi, vd in refused)
        dataset = {'@context': 'https://schema.org', '@type': 'Dataset', 'name': 'Typical Vinted asking prices for resale items, September 2026',
                   'description': 'Median asking price and interquartile range for 19 sneaker and streetwear searches, from listings SNYPD saw on vinted.be in the 14 days to 28 September 2026. Asking prices, not sold prices.',
                   'url': SITE + SLUGS['mr:2026-09']['en'], 'temporalCoverage': f'{start.isoformat()}/{end.isoformat()}', 'isAccessibleForFree': True,
                   'creator': DATASET_CREATOR, 'license': DATASET_LICENSE, 'inLanguage': 'en', 'variableMeasured': ['median asking price (EUR)', '25th percentile (EUR)', '75th percentile (EUR)', 'number of listings', 'number of sellers'],
                   'distribution': [{'@type': 'DataDownload', 'encodingFormat': 'text/csv', 'contentUrl': SITE + '/' + REPORT_CSV}]}
        body = f"""
<div class="lg-box"><p><strong>Archived edition.</strong> SNYPD published these prices on 28 September 2026; the page is kept unchanged so it can still be cited. For current prices, see the <a href="/vinted-price-guide">Vinted price guide</a>. Latest report: <a href="{HUB['en']}/{EDITIONS[-1]['slug']['en']}">{EDITIONS[-1]['name']['en']}</a>.</p></div>
<section id="answer">
  <h2>Short answer</h2>
  <div class="lg-box lg-mint"><p>These are typical <strong>asking</strong> prices on Vinted, not sold prices: the median price of every listing SNYPD saw on vinted.be for each search in the 14 days to {end.day} September {end.year}, all sizes and conditions together. For example, an Air Jordan 1 Mid was typically listed at {money(f_typ, 'en')}, with the middle half of listings between {money(f_lo, 'en')} and {money(f_hi, 'en')}.</p></div>
  <p>Looking for what Vinted charges on top of the price? See the <a href="{SLUGS['fees']['en']}">Vinted fee calculator</a>.</p>
</section>
<section id="table">
  <h2>September 2026 prices</h2>
  <h3>SNEAKERS</h3>
  {table(head, [r for r, (q, n, g) in zip(rows, SEPT_ITEMS) if g == 'sneakers'])}
  <h3>CLOTHING</h3>
  {table(head, [r for r, (q, n, g) in zip(rows, SEPT_ITEMS) if g == 'clothing'])}
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
  <p>The Market Report in SNYPD Pro and Elite does this for any search you type, broken down by condition, and refuses to show a number when the data is too thin or too mixed. Pro is @@price:pro@@ a month and also watches 5 Vinted searches 24/7. <a href="/plans">See plans</a>.</p>
  {gc.figure('market', 'en')}
  {gc.cta('en')}
</section>"""
        out = gc.page('mr:2026-09', 'en', 'Vinted Market Report, September 2026 (archive): typical asking prices | SNYPD',
                   'Archived September 2026 edition: typical Vinted asking prices for 19 sneakers and streetwear items, median, middle half and number of listings, from vinted.be listings.',
                   'VINTED MARKET REPORT &middot; ARCHIVE', 'Vinted Market Report: September 2026',
                   f'Median asking prices for 19 resale items, from listings SNYPD saw on vinted.be in the 14 days to {end.day} September {end.year}. The number of listings behind each price is in the table. This is the September 2026 edition. Asking prices, not sold prices.',
                   [('answer', 'Short answer'), ('table', 'September prices'), ('refused', 'No price'), ('method', 'Method and limits'), ('report', 'Price any item')],
                   body, [dataset], parent=('Vinted Market Report', HUB['en']))
        return out, csv_rows
    head = ['ARTICLE', 'PRIX DEMANDÉ TYPIQUE', 'MOITIÉ CENTRALE DES PRIX', 'ANNONCES', 'REMARQUE']
    ref = ''.join(f'<li><strong>{n}</strong> ({num(c, "fr")} annonces, de {money(lo, "fr")} à {money(hi, "fr")}) : trop dispersé pour un prix honnête.</li>' for n, q, c, lo, hi, vd in refused)
    dataset = {'@context': 'https://schema.org', '@type': 'Dataset', 'name': 'Prix demandés typiques sur Vinted pour des articles de revente, septembre 2026',
               'description': 'Prix demandé médian et écart interquartile pour 19 recherches de sneakers et streetwear, d’après les annonces vues par SNYPD sur vinted.be sur les 14 jours au 28 septembre 2026. Prix demandés, pas prix de vente.',
               'url': SITE + SLUGS['mr:2026-09']['fr'], 'temporalCoverage': f'{start.isoformat()}/{end.isoformat()}', 'isAccessibleForFree': True,
               'creator': DATASET_CREATOR, 'license': DATASET_LICENSE, 'inLanguage': 'fr',
               'distribution': [{'@type': 'DataDownload', 'encodingFormat': 'text/csv', 'contentUrl': SITE + '/' + REPORT_CSV}]}
    body = f"""
<div class="lg-box"><p><strong>Édition archivée.</strong> SNYPD a publié ces prix le 28 septembre 2026{NB}; la page reste inchangée pour pouvoir être citée. Pour les prix actuels, voir le <a href="/fr/guide-prix-vinted">guide des prix Vinted</a>. Dernière édition{NB}: <a href="{HUB['fr']}/{EDITIONS[-1]['slug']['fr']}">{EDITIONS[-1]['name']['fr']}</a>.</p></div>
<section id="reponse">
  <h2>Réponse courte</h2>
  <div class="lg-box lg-mint"><p>Ce sont des prix <strong>demandés</strong> typiques sur Vinted, pas des prix de vente : le prix médian de toutes les annonces vues par SNYPD sur vinted.be pour chaque recherche, sur les 14 jours au {end.day} septembre {end.year}, toutes tailles et tous états confondus. Par exemple, une Air Jordan 1 Mid était typiquement mise en vente à {money(f_typ, 'fr')}, la moitié centrale des annonces se situant entre {money(f_lo, 'fr')} et {money(f_hi, 'fr')}.</p></div>
  <p>Tu cherches les frais que Vinted ajoute au prix ? Voir le <a href="{SLUGS['fees']['fr']}">calculateur des frais Vinted</a>.</p>
</section>
<section id="tableau">
  <h2>Les prix de septembre 2026</h2>
  <h3>SNEAKERS</h3>
  {table(head, [r for r, (q, n, g) in zip(rows, SEPT_ITEMS) if g == 'sneakers'])}
  <h3>VÊTEMENTS</h3>
  {table(head, [r for r, (q, n, g) in zip(rows, SEPT_ITEMS) if g == 'clothing'])}
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
  <p>Le Market Report de SNYPD Pro et Elite fait ce calcul pour n’importe quelle recherche, détaillé par état, et refuse d’afficher un chiffre quand les données sont trop maigres ou trop mélangées. Pro coûte @@price:pro@@ par mois et surveille aussi 5 recherches Vinted 24h/24. <a href="/plans">Voir les tarifs</a>.</p>
  {gc.figure('market', 'fr')}
  {gc.cta('fr')}
</section>"""
    out = gc.page('mr:2026-09', 'fr', 'Rapport du marché Vinted, septembre 2026 (archive) : prix demandés typiques | SNYPD',
               'Édition archivée de septembre 2026 : prix demandés typiques sur Vinted pour 19 sneakers et vêtements streetwear, médiane, moitié centrale et nombre d’annonces vinted.be.',
               'RAPPORT DU MARCHÉ VINTED &middot; ARCHIVE', 'Rapport du marché Vinted\xa0: septembre 2026',
               f'Prix demandés médians pour 19 articles de revente, d’après les annonces vues par SNYPD sur vinted.be sur les 14 jours au {end.day} septembre {end.year}. Le nombre d’annonces derrière chaque prix est dans le tableau. Édition de septembre 2026. Prix demandés, pas prix de vente.',
               [('reponse', 'Réponse courte'), ('tableau', 'Prix de septembre'), ('sans-prix', 'Sans prix'), ('methode', 'Méthode et limites'), ('market-report', 'Estimer un article')],
               body, [dataset], parent=('Rapport du marché Vinted', HUB['fr']))
    return out, csv_rows




def write_september():
    """The archived edition (EN + FR) and its CSV, at the CSV's original address."""
    csv_rows = None
    for lang in LANGS:
        html_out, csv_rows = page_september(lang)
        write(SLUGS['mr:2026-09'][lang].lstrip('/') + '.html', html_out)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator='\n')
    w.writerow(['item', 'search', 'group', 'typical_asking_eur', 'p25_eur', 'p75_eur', 'listings', 'sellers', 'confidence', 'outlier_high_pct'])
    w.writerows(csv_rows)
    buf.write('# Source: SNYPD Market Report (median asking price, not sold price), listings seen on vinted.be in the 14 days to 2026-09-28. %s%s\n'
              % (SITE, SLUGS['mr:2026-09']['en']))
    write(REPORT_CSV, buf.getvalue())


SLUGS['mreport'] = dict(HUB)
PAGE_MODIFIED['mreport'] = max(EDITIONS[-1]['published'], '2026-10-10')  # hub rebuilt 10 Oct (archive, citation, method)
for _ed in EDITIONS + [SEPT]:
    SLUGS['mr:' + _ed['id']] = {l: HUB[l] + '/' + _ed['slug'][l] for l in LANGS}
    PAGE_MODIFIED['mr:' + _ed['id']] = _ed.get('modified', _ed['published'])


def sitemap_pages():
    out = []
    for key in ['mreport'] + ['mr:' + e['id'] for e in EDITIONS + [SEPT]]:
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
    write_september()
    for lang in LANGS:
        write(HUB[lang].lstrip('/') + '.html', page_hub(lang))
