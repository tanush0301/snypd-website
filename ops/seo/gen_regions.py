#!/usr/bin/env python3
"""Rewrite the plan-fact regions of the hand-written pages (index.html, plans.html) from
ops/seo/data/plans.json. Run by prepublish.py; safe to run any time (idempotent).

A region is everything between two markers:
    HTML        <!--plans:NAME-->...<!--/plans:NAME-->
    JavaScript  /*plans:NAME*/.../*/plans:NAME*/      (filled with plain characters)
NAME is a key of TEMPLATES (the same name may appear several times). Templates use the
tokens of ops/seo/plans.py (@@price:pro@@ ...) or are functions returning finished HTML.
Three things have no markers because JSON and attributes cannot hold comments: the JSON-LD
Offer prices and the plan prices in meta descriptions (both rewritten by plan name), and the
Organization description in index.html (rewritten from ops/seo/data/brand.json, the only
copy of the boilerplate on the site; outreach/00-fact-sheet.md quotes it verbatim).

/plans: the comparison table and the FAQ are written into the HTML here (before 10 Oct
2026 only JavaScript drew them, so AI crawlers that do not run JS never saw them). The
page's JS keeps the interactive parts. The French for every English text below lives in
ops/i18n/fr.py (keyed by the English): after a copy change, run the collector, add the
French, run python ops/i18n/gen_i18n.py and node ops/i18n/test_i18n.js.

Byte-level edits: the pages are UTF-8 with CRLF; nothing outside the regions changes.
"""
import difflib, html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import plans  # noqa: E402

P = plans.PLANS


def esc(s):
    """Same escaping as the page's JS esc(); non-ASCII as entities so the files stay byte-safe."""
    s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
    return ''.join(c if ord(c) < 128 else '&#%d;' % ord(c) for c in s)


def per_search():
    """Elite's price per search, which the card claims is the lowest of any plan."""
    paid = [k for k in plans.ORDER if float(P[k]['price']) > 0]
    cost = {k: float(P[k]['price']) / P[k]['searches'] for k in paid}
    if min(cost, key=cost.get) != 'elite':
        sys.exit('gen_regions: Elite is no longer the cheapest per search; rewrite the card line')
    return '&euro;%.2f per search a month, the lowest of any plan' % cost['elite']


# ----------------------------------------------------------------- /plans comparison table
# Every row is checked against the product (the reason is next to each fact):
#   searches        plan_limit_for() (migration 030)
#   24/7            always-on is PAID_PLANS-gated; Free gets it for the trial length from the
#                   first saved search (migration 042, helpers.in_free_trial; plans.json free_trial)
#   check speed     adaptive polling, one global floor/ceiling, no tier (check-interval.json)
#   push            push.py has no tier gate; Free only polls 24/7 during the trial, then
#                   while the dashboard is open, so it only has something to push then
#   one alert       existing_current_ads_keys(): once per user per listing id
#   Market Report   ELITE_PLANS = (pro, elite); per hour / per day limits in plans.json
#   paid Discord    Whop gives the Discord roles per product; SOLO (18 Oct 2026) has none
# Removed 10 Oct 2026: "Quiet hours: no pushes overnight" -- users cannot write
# public.users (RLS: SELECT only), so the dashboard toggle never saves.
Y, N = ('y', 'Included'), ('n', 'Not included')


def T(t):
    return ('t', t)


def W(t):
    return ('w', t)


def cmp_groups():
    sea = [T(str(P[k]['searches'])) for k in plans.ORDER]
    price = [T(plans.price(k, 'en', entities=False)) for k in plans.ORDER]
    d = plans.TRIAL_DAYS
    mr = [Y if P[k]['market_report'] else N for k in plans.ORDER]
    mr_day = [T(str(plans.MR['per_day'])) if P[k]['market_report'] else N for k in plans.ORDER]
    discord = [Y if P[k]['paid_discord'] else N for k in plans.ORDER]
    card = [T('Yes' if P[k]['card'] else 'No') for k in plans.ORDER]
    paid = [float(P[k]['price']) > 0 for k in plans.ORDER]
    n = len(plans.ORDER)
    return [
        ('MONITORING', [
            ('Active Vinted searches', 'Pause one any time to free the slot.', sea),
            ('Runs with your dashboard closed',
             'Free: 24/7 for the first %d days after you save your first search, then only while your dashboard is open.' % d,
             [W('First %d days only' % d) if not p else Y for p in paid]),
            ('Check speed', 'About every %d s (measured median), up to 5 min on quiet searches. Same on every plan.' % plans.MEDIAN_S,
             [T('Same')] * n),
            ('Every Vinted site in Europe and the US', '26 sites. Prices in that site’s currency.', [Y] * n),
        ]),
        ('ALERTS', [
            ('Matches in your dashboard', 'Kept about 30 minutes while the listing is up.', [Y] * n),
            ('Push notifications', 'Phone and desktop. On iPhone, add SNYPD to your Home Screen first.',
             [W('24/7 for %d days, then dashboard open' % d) if not p else T('24/7') for p in paid]),
            ('One alert per listing', 'The same listing never alerts you twice.', [Y] * n),
        ]),
        ('PRICE DATA', [
            ('Market Report price checks',
             'Typical asking price and range, split by condition. Shows no price when the data is too thin.', mr),
            ('Price checks per day', 'Up to %d an hour.' % plans.MR['per_hour'], mr_day),
        ]),
        ('COMMUNITY', [
            ('Free Discord community', '', [Y] * n),
            ('Paid Discord channels', '', discord),
        ]),
        ('BILLING', [
            ('Price per month', 'VAT included.', price),
            ('Card needed', '', card),
            ('Renews', 'Until you cancel.', [T('—') if not p else T('Monthly') for p in paid]),
            ('%d-day refund' % plans.REFUND_DAYS, 'On your first payment for a plan.', [T('—') if not p else Y for p in paid]),
            ('Cancel any time', 'Access runs to the end of the paid month.', [T('Nothing to cancel') if not p else Y for p in paid]),
        ]),
    ]


def cell(c, i):
    cls = 'pc c%d' % i + (' is-pro' if plans.ORDER[i] == 'pro' else '')
    kind, text = c
    if kind == 'y':
        return '<td class="%s"><span class="y" aria-hidden="true">&#10003;</span><span class="sr">%s</span></td>' % (cls, text)
    if kind == 'n':
        return '<td class="%s"><span class="n" aria-hidden="true">&#8212;</span><span class="sr">%s</span></td>' % (cls, text)
    if kind == 'w':
        return '<td class="%s"><span class="w">%s</span></td>' % (cls, esc(text))
    return '<td class="%s">%s</td>' % (cls, esc(text))


def cmp_html():
    out = []
    for title, rows in cmp_groups():
        out.append('<tr class="grp"><th scope="colgroup" colspan="%d">%s</th></tr>' % (len(plans.ORDER) + 1, title))
        for r in rows:
            label, note, cells = r[0], r[1], r[2]
            out.append('<tr><th scope="row"><span class="fl">%s</span>%s</th>%s</tr>' % (
                esc(label), '<span class="fn">%s</span>' % esc(note) if note else '',
                ''.join(cell(c, i) for i, c in enumerate(cells))))
    return '\r\n'.join(out)


# ----------------------------------------------------------------- /plans FAQ
def faqs():
    so, k, pr, el = (plans.price(x, 'en', entities=False) for x in ('solo', 'kickstart', 'pro', 'elite'))
    d, r, h, x = plans.TRIAL_DAYS, plans.REFUND_DAYS, plans.TRIAL_HOURS, plans.TRIAL_EXT_DAYS
    return [
        ('Is Free actually free?', 'Yes. No card and no time limit. One search: for the first %d days after you save it, it runs 24/7 with alerts like a paid plan; after that it is checked while your dashboard is open.' % d),
        ('Do paid plans find listings faster?', 'No. Every plan checks about every %d seconds (measured median), up to 5 minutes on quiet searches. Paid plans add searches and keep checking with your dashboard closed.' % plans.MEDIAN_S),
        ('Is there a free trial?', 'Yes. Free runs your first search 24/7 with alerts for %d days (%d h), counted from when you save it, with no card. If it finds nothing in that time, we add %d more days once. After that, Free keeps that one search for as long as you like, checked while your dashboard is open.' % (d, h, x)),
        ('Does the price include VAT?', 'Yes. %s, %s, %s and %s a month are the full prices, VAT included. Buying for a company? Tick "buying on behalf of a company" at checkout.' % (so, k, pr, el)),
        ('How do I pay?', 'By card, or Apple Pay or Google Pay on devices that support them, through Whop’s secure checkout on this page. SNYPD never sees your card details.'),
        ('Does my plan renew automatically?', 'Yes, every month, until you cancel. Cancel any time in your Whop account. The Hunt Pass is the exception: it is paid once and ends after %d days.' % plans.PASS_DAYS),
        ('Can I pay once, without a subscription?', pass_faq()),
        ('What happens when I cancel?', 'Your plan keeps running to the end of the month you paid for, then your account goes back to Free.'),
        ('Can I get a refund?', 'Yes. Email help@snypd.store within %d days of your first payment for a plan and we refund that payment in full.' % r),
        ('Can I change plan later?', 'Upgrade here any time. To move between paid plans, manage your subscription in Whop, or email help@snypd.store and we will help you switch.'),
        ('What is a founding member?', 'The first %d SNYPD accounts, free accounts included. All of those places are taken. If the Pro price ever goes up, founding members can keep Pro at %s a month for as long as their account exists.'
         % (plans.DATA['founding']['accounts'], plans.price('founding', 'en', entities=False))),
        ('Do you need my Vinted login?', 'Never. SNYPD reads public listings only. It never logs in, buys or messages anyone.'),
    ]


def pass_faq():
    hp = plans.PASSES['pass']
    return ('Yes: the Hunt Pass. One payment of %s, VAT included, and 1 Vinted search is watched 24/7 with push alerts for %d days, '
            'like Solo. Then it simply ends: no renewal, no subscription, nothing to cancel. It suits hunting one specific item, '
            'like a console or a jacket in your size. Full refund within %d days of the payment. For ongoing hunting, Solo is %s a month.'
            % (plans.price('pass', 'en', entities=False), hp['days'], plans.REFUND_DAYS, plans.price('solo', 'en', entities=False)))


# ----------------------------------------------------------------- /plans Hunt Pass note under the table
# The 5-column monthly table stays as it is; the one-time pass gets its own line right under it.
def pass_cmp():
    return ('<p class="cmp-pass"><span class="cmp-pass__h">%s</span> <span>%s</span></p>' % (
        esc('HUNT PASS · %s ONCE' % plans.price('pass', 'en', entities=False)),
        esc('Everything in the Solo column for %d days, paid once, VAT included. No renewal, nothing to cancel. '
            'Full refund within %d days of the payment.' % (plans.PASSES['pass']['days'], plans.REFUND_DAYS))))


def faq_html():
    mail = '<a href="mailto:help@snypd.store">help@snypd.store</a>'
    return '\r\n'.join('<details><summary>%s</summary><p>%s</p></details>' % (esc(q), esc(a).replace('help@snypd.store', mail, 1))
                       for q, a in faqs())


# ----------------------------------------------------------------- homepage price data
# A few items from the price guide (ops/seo/data/price-guide.json via gen_price_guide.py) and the
# latest Market Report edition, as two links under the homepage's price-check demo (v7; the demo shows the items).


def home_data():
    import gen_price_guide as pg
    import gen_market_report as mr
    from gen_content import num
    total = sum(pg.V[it['slug']]['sample_size'] for it in pg.PUB)
    ed = mr.EDITIONS[-1]
    listings = mr.load(ed)[1]['listings']
    return ('\r\n        <div class="hp-pc-links"><a href="%s">All %d items in the free Vinted price guide &rarr;</a>'
            '<a href="%s/%s">Vinted Market Report, %s: %s listings &rarr;</a>'
            '<span>%s listings behind the guide&rsquo;s prices, vinted.be, %s.</span></div>\r\n        '
            % (pg.HUB['en'], len(pg.PUB), mr.HUB['en'], ed['slug']['en'], ed['name']['en'], num(listings, 'en'), num(total, 'en'), pg.window('en')))


# ----------------------------------------------------------------- homepage footer links
# Built from gen_content's page list, so every guide and every language version gets a link from
# the homepage (Google's strongest page here; 88 URLs were "discovered, not indexed" on 18 Oct 2026).
HOME_FOOT_EN = [('bot', 'Vinted bot'), ('monitor', 'Vinted monitor'), ('notify', 'Vinted notifications'),
                ('notwork', 'Vinted notifications not working'), ('saved', 'Vinted saved searches'),
                ('pricedrop', 'Vinted price drop alerts'), ('compare', 'Vinted bots compared'),
                ('/vinted-price-guide', 'Vinted price guide'), ('checker', 'Vinted price checker'),
                ('sold', 'Can you see sold items on Vinted?'), ('/vinted-market-report', 'Vinted market report'),
                ('deals', 'Vinted deals'), ('fees', 'Vinted fees')]


def home_foot_links():
    import gen_content as gc
    a = '<a href="%s"%s style="font-size:12px;">%s</a>'
    out = [a % (gc.href(k, 'en'), '', t) for k, t in HOME_FOOT_EN]
    for lang in gc.live_langs('bot'):
        if lang == 'en':
            continue
        name = gc.UI[lang]['foot'][0][1]  # the language's own name for its bot page
        out.append(a % (gc.SLUGS['bot'][lang], ' hreflang="%s" lang="%s"' % (lang, lang), '%s (%s)' % (name, lang.upper())))
    return ''.join(out)


# ----------------------------------------------------------------- homepage: Check a price demo + Market board sample
# home-demo: the price-check demo's first item, written into the HTML so the numbers are on the page without
# JavaScript (the page script then lets the visitor pick any item of assets/data/price-index.json).
# home-market: a dated sample of the Market board with one real chart, from ops/seo/data/home-market-sample.json
# (ops/seo/home_market_sample.sql + the board as the dashboard showed it that day). Numbers only from those files.
HOME_DEMO_ITEM = 'nike-dunk-low'
HOME_DEMO_MARGIN = 40


def _day(iso):
    y, m, d = iso.split('-')
    return '%d %s %s' % (int(d), ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec'][int(m) - 1], y)


def home_demo():
    import gen_price_guide as pg
    from gen_content import money, num
    it = next((x for x in pg.PUB if x['slug'] == HOME_DEMO_ITEM), None)
    if it is None:
        sys.exit('gen_regions: the homepage demo item is not published in the price guide; edit HOME_DEMO_ITEM')
    v = pg.V[it['slug']]
    lo, mid, hi = v['range_cents']['low'], v['typical_cents'], v['range_cents']['high']
    pay = int(round(mid * (100 - HOME_DEMO_MARGIN) / 100.0))
    alert = '/signup?hunt=%s&amp;max=%d' % (it['query'].replace(' ', '+'), max(1, lo // 100))
    return (
        '\r\n          <div class="hp-pc-res" id="pc-res" data-id="%s" data-n-items="%d">\r\n'
        '            <div class="hp-pc-name"><b id="pc-name">%s</b><span id="pc-meta">%s listings &middot; vinted.be &middot; %s</span></div>\r\n'
        '            <div class="hp-pc-three">\r\n'
        '              <div><span class="k">QUICK SALE</span><span class="v" id="pc-lo">%s</span><span class="d">a quarter of listings ask less</span></div>\r\n'
        '              <div class="mid"><span class="k">TYPICAL</span><span class="v" id="pc-mid">%s</span><span class="d">half ask less, half ask more</span></div>\r\n'
        '              <div><span class="k">PATIENT</span><span class="v" id="pc-hi">%s</span><span class="d">a quarter of listings ask more</span></div>\r\n'
        '            </div>\r\n'
        '            <div class="hp-pc-pay"><label for="pc-margin">Your margin</label><input id="pc-margin" type="number" inputmode="numeric" min="0" max="90" step="5" value="%d"><span>%%</span>'
        '<span class="arrow">&rarr;</span><span class="out">Pay at most <b id="pc-pay">%s</b></span></div>\r\n'
        '            <div class="hp-pc-go"><a class="hp-btn" id="pc-alert" href="%s">ALERT ME UNDER <span id="pc-alert-p">%s</span></a>'
        '<a class="hp-btn ghost" id="pc-more" href="%s">PRICES BY CONDITION</a></div>\r\n'
        '          </div>\r\n          '
        % (it['slug'], len(pg.PUB), html.escape(it['name']), num(v['sample_size'], 'en'), pg.window('en'),
           money(lo, 'en'), money(mid, 'en'), money(hi, 'en'), HOME_DEMO_MARGIN, money(pay, 'en'),
           alert, money((lo // 100) * 100, 'en'), pg.item_url(it, 'en')))


def home_market():
    from gen_content import money, num
    d = json.load(open(os.path.join(HERE, 'data', 'home-market-sample.json'), encoding='utf-8'))
    b, c = d['board'], d['chart']
    ser = c['series']
    if len(ser) < 21 or ser[-1][0] != b['date']:
        sys.exit('gen_regions: home-market-sample.json: chart and board are not from the same day')
    # chart geometry: 600 x 200 plot, band = middle half, line = typical asking price, bars = listings
    W, H, PAD_T, PAD_B = 600.0, 150.0, 8.0, 46.0
    lo = min(r[2] for r in ser)
    hi = max(r[3] for r in ser)
    span = float(hi - lo) or 1.0
    n_max = float(max(r[4] for r in ser)) or 1.0
    step = W / (len(ser) - 1)
    x = lambda i: round(i * step, 1)
    y = lambda cents: round(PAD_T + (hi - cents) / span * (H - PAD_T), 1)
    line = ' '.join('%s%s,%s' % ('M' if i == 0 else 'L', x(i), y(r[1])) for i, r in enumerate(ser))
    band = ('M' + ' L'.join('%s,%s' % (x(i), y(r[3])) for i, r in enumerate(ser))
            + ' L' + ' L'.join('%s,%s' % (x(i), y(r[2])) for i, r in reversed(list(enumerate(ser)))) + ' Z')
    bw = max(2.0, round(step * 0.6, 1))
    bars = ''.join('<rect x="%s" y="%s" width="%s" height="%s"/>' % (round(x(i) - bw / 2, 1), round(H + PAD_B - 4 - r[4] / n_max * 30, 1), bw, round(r[4] / n_max * 30, 1))
                   for i, r in enumerate(ser))
    last = ser[-1]

    def rows(items, cls):
        return ''.join('<li><span class="n">%s<small>%s</small></span><span class="p">%s</span><span class="c %s">%s%d%%</span></li>'
                       % (html.escape(i['name']), html.escape(i['cat']), money(i['typical_cents'], 'en'), cls,
                          '+' if i['change_pct'] > 0 else '&minus;', abs(i['change_pct'])) for i in items)
    sign = '+' if c['change_pct'] > 0 else '&minus;'
    return (
        '\r\n        <div class="hp-mb" id="mb-sample" data-date="%s">\r\n'
        '          <div class="hp-mb-list">\r\n'
        '            <div class="hp-mb-top"><b>What&rsquo;s moving</b><span>EU asking prices (EUR) &middot; board of %s</span></div>\r\n'
        '            <span class="hp-mb-h up">ASKING PRICES RISING</span><ul>%s</ul>\r\n'
        '            <span class="hp-mb-h down">ASKING PRICES FALLING</span><ul>%s</ul>\r\n'
        '            <p class="hp-mb-note">%d items were on the board that day; %d more were hidden because their mix of listings changed too much to call a direction.</p>\r\n'
        '          </div>\r\n'
        '          <figure class="hp-chart">\r\n'
        '            <figcaption><b>%s</b><span>%s to %s &middot; <i class="%s">%s%d%%</i></span></figcaption>\r\n'
        '            <svg viewBox="0 0 600 200" preserveAspectRatio="none" role="img" aria-label="%s: typical asking price per day from %s to %s, with the normal range and the number of listings">'
        '<path class="band" d="%s"/><g class="bars">%s</g><path class="line" pathLength="1" d="%s"/></svg>\r\n'
        '            <div class="hp-chart-axis"><span>%s</span><span>%s</span></div>\r\n'
        '            <p class="hp-chart-key">Line: typical asking price. Band: normal range (the middle half of asking prices). Bars: listings seen.</p>\r\n'
        '            <div class="hp-chart-tiles"><div><b>%s</b><span>Typical now</span></div><div><b>%s&ndash;%s</b><span>Normal range</span></div>'
        '<div><b>%s</b><span>Listings (7 days)</span></div><div><b>%s</b><span>Sellers</span></div></div>\r\n'
        '            <p class="hp-chart-say">%s</p>\r\n'
        '          </figure>\r\n'
        '        </div>\r\n        '
        % (b['date'], _day(b['date']), rows(b['rising'], 'up'), rows(b['falling'], 'down'), b['items_on_board'], b['hidden_mixed'],
           html.escape(c['name']), _day(ser[0][0]), _day(last[0]), 'up' if c['change_pct'] > 0 else 'down', sign, abs(c['change_pct']),
           html.escape(c['name']), _day(ser[0][0]), _day(last[0]), band, bars, line,
           _day(ser[0][0]), _day(last[0]),
           money(last[1], 'en'), money(last[2], 'en'), money(last[3], 'en'), num(last[4], 'en'), num(last[5], 'en'),
           ('Sellers now ask %d%% more than 8 to 21 days ago. Good time to list if you hold some; sourcing costs more than it did.'
            if c['change_pct'] > 0 else
            'Sellers now ask %d%% less than 8 to 21 days ago. Cheaper to source than it was; harder to sell at the old price.') % abs(c['change_pct'])))


# ----------------------------------------------------------------- templates
TEMPLATES = {
    'home-foot-links': home_foot_links,
    # shared
    **{'price:%s' % k: '@@price:%s@@' % k for k in list(plans.ORDER) + list(plans.PASSES)},
    **{'price-mo:%s' % k: '@@price:%s@@ / mo' % k for k in plans.ORDER},
    # index.html
    'home-pro-searches': '@@searches:pro@@ active Vinted searches',
    'home-pro-change': '@@searches:free@@ &rarr; @@searches:pro@@',
    'home-free-line': '@@searches:free@@ search &middot; 24/7 for @@trial_days@@ days, then while your dashboard is open &middot; free Discord',
    'home-solo-line': '@@searches:solo@@ search &middot; runs 24/7, even with your dashboard closed',
    'home-pass-line': '@@searches:pass@@ search &middot; 24/7 for @@pass_days@@ days &middot; paid once, no subscription',
    'home-kickstart-line': '@@searches:kickstart@@ searches &middot; runs 24/7, even with your dashboard closed',
    'home-elite-line': 'Everything in Pro + @@searches:elite@@ searches',
    'home-hero-trial': 'Free: your first search runs 24/7 with alerts for @@trial_days@@ days (@@trial_hours@@ h). No card.',
    'home-data': home_data,
    'home-demo': home_demo,
    'home-market': home_market,
    'home-faq-free-q': 'Does it run with my laptop closed?',
    'home-faq-free-a': 'Paid plans, always. Free: 24/7 for the first @@trial_days@@ days after you save your first search, then only while your dashboard is open.',
    'home-faq-speed-a': 'About every @@median_s@@ s (measured median), up to 5 min on quiet searches. Same on every plan. One batched push.',
    'home-walk-intro': "'After your @@trial_days@@-day trial, Free stops when you close the tab. Paid doesn\\'t.'",
    'home-walk-stopped': "'After the @@trial_days@@-day trial, Free only watches while the dashboard is open.'",
    'home-walk-foot': "'Free: one search, 24/7 for @@trial_days@@ days, then dashboard open. Price checks: Pro and Elite.'",
    # plans.html
    'plans-free-searches': '@@searches:free@@ active Vinted search',
    'plans-free-trial': '24/7 for the first @@trial_days@@ days, then while your dashboard is open',
    'plans-solo-searches': '@@searches:solo@@ active Vinted search',
    'plans-kickstart-searches': '@@searches:kickstart@@ active Vinted searches, not @@searches:solo@@',
    'plans-pro-searches': '@@searches:pro@@ active Vinted searches, not @@searches:kickstart@@',
    'plans-elite-searches': '@@searches:elite@@ active Vinted searches, not @@searches:pro@@',
    'plans-elite-per-search': per_search,
    'plans-pro-mr-day': 'Up to @@mr_day@@ price checks a day',
    'plans-under': 'Paid plans renew every month until you cancel. Cancel any time. Full refund within @@refund_days@@ days of your first payment. The Hunt Pass is paid once and does not renew.',
    'plans-pass-for': 'One item to find? Pay once and hunt it for @@pass_days@@ days.',
    'plans-pass-plus': 'Same as Solo, for @@pass_days@@ days:',
    'plans-pass-end': 'Ends after @@pass_days@@ days: no renewal, nothing to cancel',
    'plans-pass-cmp': pass_cmp,
    'plans-fit-pass': 'One item, no subscription? Hunt Pass: @@price:pass@@ once, @@pass_days@@ days &rarr;',
    'plans-refund-h': '@@refund_days@@-DAY REFUND',
    'plans-refund-p': ' within @@refund_days@@ days of your first payment for a plan and we refund it in full.',
    'plans-cmp': cmp_html,
    'plans-faq': faq_html,
    'plans-js': ("var PRICE = { " + ", ".join("%s: '@@price:%s@@'" % (k, k) for k in list(plans.ORDER) + list(plans.PASSES)) + " };\r\n"
                 "  var SEARCHES = { " + ", ".join("%s: @@searches:%s@@" % (k, k) for k in list(plans.ORDER) + list(plans.PASSES)) + " };\r\n"
                 "  var PASS_DAYS = @@pass_days@@;"),
    # inside WHOP_PLANS: the Hunt Pass's Whop plan id comes from plans.json, typed nowhere else
    'plans-whop-pass': "pass: '@@whop:pass@@'",
}
FILES = ['index.html', 'plans.html']

HTML_RE = re.compile(r'(<!--plans:([a-z0-9:-]+)-->)(.*?)(<!--/plans:\2-->)', re.S)
JS_RE = re.compile(r'(/\*plans:([a-z0-9:-]+)\*/)(.*?)(/\*/plans:\2\*/)', re.S)
LD_RE = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)
META_RE = re.compile(r'(<meta [^>]*content=")([^"]*)(")')


def render(name, plain):
    t = TEMPLATES.get(name)
    if t is None:
        sys.exit(f'gen_regions: no template for region "{name}"')
    return t() if callable(t) else plans.fill(t, 'en', plain=plain)


def render_region(m, plain):
    """Preserve each region's existing line endings when inserting generated text."""
    newline = '\r\n' if '\r\n' in m.group(3) else '\n'
    content = render(m.group(2), plain).replace('\r\n', '\n').replace('\n', newline)
    return m.group(1) + content + m.group(4)


def offers(ld):
    """Set every schema.org Offer's prices (price + priceSpecification) to plans.json."""
    by_name = {p['name']: p['price'] for p in plans.DATA['plans'] + plans.DATA.get('passes', [])}
    parts = re.split(r'(?=\{ "@type": "Offer")', ld)
    for i, part in enumerate(parts):
        m = re.match(r'\{ "@type": "Offer", "name": "([^"]+)"', part)
        if m and m.group(1) in by_name:
            parts[i] = re.sub(r'("price": ")[^"]*(")', lambda x: x.group(1) + by_name[m.group(1)] + x.group(2), part)
    return ''.join(parts)


def meta_prices(content):
    """'Kickstart &#8364;14.99' style mentions in meta descriptions."""
    for p in plans.DATA['plans'] + plans.DATA.get('passes', []):
        if float(p['price']) > 0:
            content = re.sub(r'(\b%s (?:&#8364;|&euro;|€))[0-9.]+' % p['name'], lambda x: x.group(1) + p['price'], content)
    return content


BRAND = json.load(open(os.path.join(HERE, 'data', 'brand.json'), encoding='utf-8'))
_interval = json.load(open(os.path.join(HERE, 'data', 'check-interval.json'), encoding='utf-8'))
if 'once a minute' in BRAND['boilerplate'] and _interval['median_seconds'] != 60:
    sys.exit('gen_regions: the boilerplate says "about once a minute" but check-interval.json median is %s s'
             % _interval['median_seconds'])
ORG_RE = re.compile(r'("@type": "Organization",\s*"@id": "https://www\.snypd\.store/#org",)((?:\s*"description": "(?:[^"\\]|\\.)*",)?)(\s*"name")')


def org_description(m):
    nl = '\r\n' if '\r\n' in m.group(3) else '\n'
    indent = m.group(3)[len(nl):m.group(3).index('"')]
    return m.group(1) + nl + indent + '"description": ' + json.dumps(BRAND['boilerplate'], ensure_ascii=False) + ',' + m.group(3)


def run(check=False):
    changed = []
    for name in FILES:
        path = os.path.join(ROOT, name)
        raw = open(path, 'rb').read()
        text = raw.decode('utf-8')
        n = [0]

        def sub_html(m):
            n[0] += 1
            return render_region(m, False)

        def sub_js(m):
            n[0] += 1
            return render_region(m, True)

        out = HTML_RE.sub(sub_html, text)
        out = JS_RE.sub(sub_js, out)
        out = LD_RE.sub(lambda m: m.group(1) + offers(m.group(2)) + m.group(3), out)
        out = META_RE.sub(lambda m: m.group(1) + meta_prices(m.group(2)) + m.group(3), out)
        out = ORG_RE.sub(org_description, out)
        if n[0] == 0:
            sys.exit(f'gen_regions: {name} has no plan regions (markers lost?)')
        if out != text:
            changed.append(name)
            if check:
                for line in difflib.unified_diff(text.splitlines(), out.splitlines(), fromfile=name, tofile=name + " (generated)", lineterm=""):
                    print(line)
                if text.splitlines() == out.splitlines():
                    print(f"{name}: generated content matches; line endings differ")
            if not check:
                open(path, 'wb').write(out.encode('utf-8'))
        print(f'regions {name}: {n[0]} regions, {"changed" if out != text else "unchanged"}')
    return changed


if __name__ == '__main__':
    sys.exit(1 if run(check='--check' in sys.argv) and '--check' in sys.argv else 0)
