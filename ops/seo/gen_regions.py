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
import html, json, os, re, sys

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
#   24/7            always-on is PAID_PLANS-gated; Free gets it for FREE_TRIAL_DAYS from the
#                   first saved search (migration 042, helpers.in_free_trial)
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
            ('Founding member', 'First %d accounts, free included. Keep Pro at %s a month for life.'
             % (plans.DATA['founding']['accounts'], plans.price('founding', 'en', entities=False)), [Y] * n, 'founding'),
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
            attr = ' data-founding-row' if len(r) > 3 else ''
            out.append('<tr%s><th scope="row"><span class="fl">%s</span>%s</th>%s</tr>' % (
                attr, esc(label), '<span class="fn">%s</span>' % esc(note) if note else '',
                ''.join(cell(c, i) for i, c in enumerate(cells))))
    return '\r\n'.join(out)


# ----------------------------------------------------------------- /plans FAQ
def faqs():
    so, k, pr, el = (plans.price(x, 'en', entities=False) for x in ('solo', 'kickstart', 'pro', 'elite'))
    d, r = plans.TRIAL_DAYS, plans.REFUND_DAYS
    return [
        ('Is Free actually free?', 'Yes. No card and no time limit. One search: for the first %d days after you save it, it runs 24/7 with alerts like a paid plan; after that it is checked while your dashboard is open.' % d),
        ('Do paid plans find listings faster?', 'No. Every plan checks about every %d seconds (measured median), up to 5 minutes on quiet searches. Paid plans add searches and keep checking with your dashboard closed.' % plans.MEDIAN_S),
        ('Is there a free trial?', 'Yes. Free runs your first search 24/7 with alerts for %d days, counted from when you save it, with no card. After that, Free keeps that one search for as long as you like, checked while your dashboard is open.' % d),
        ('Does the price include VAT?', 'Yes. %s, %s, %s and %s a month are the full prices, VAT included. Buying for a company? Tick "buying on behalf of a company" at checkout.' % (so, k, pr, el)),
        ('How do I pay?', 'By card, or Apple Pay or Google Pay on devices that support them, through Whop’s secure checkout on this page. SNYPD never sees your card details.'),
        ('Does my plan renew automatically?', 'Yes, every month, until you cancel. Cancel any time in your Whop account.'),
        ('What happens when I cancel?', 'Your plan keeps running to the end of the month you paid for, then your account goes back to Free.'),
        ('Can I get a refund?', 'Yes. Email snypd@gmail.com within %d days of your first payment for a plan and we refund that payment in full.' % r),
        ('Can I change plan later?', 'Upgrade here any time. To move between paid plans, manage your subscription in Whop, or email snypd@gmail.com and we will help you switch.'),
        ('What is a founding member?', 'The first %d SNYPD accounts, free accounts included. If the Pro price ever goes up, founding members can keep Pro at %s a month for as long as their account exists.'
         % (plans.DATA['founding']['accounts'], plans.price('founding', 'en', entities=False))),
        ('Do you need my Vinted login?', 'Never. SNYPD reads public listings only. It never logs in, buys or messages anyone.'),
    ]


def faq_html():
    mail = '<a href="mailto:snypd@gmail.com">snypd@gmail.com</a>'
    return '\r\n'.join('<details><summary>%s</summary><p>%s</p></details>' % (esc(q), esc(a).replace('snypd@gmail.com', mail, 1))
                       for q, a in faqs())


# ----------------------------------------------------------------- homepage price data
# A few items from the price guide (ops/seo/data/price-guide.json via gen_price_guide.py) and the
# latest Market Report edition. Numbers only from those generators; the item list is a choice.
HOME_ITEMS = ['nike-dunk-low', 'jordan-4', 'ralph-lauren-polo', 'adidas-samba']


def home_data():
    import gen_price_guide as pg
    import gen_market_report as mr
    from gen_content import money, num
    items = [it for slug in HOME_ITEMS for it in pg.PUB if it['slug'] == slug]
    if len(items) < 3:
        sys.exit('gen_regions: fewer than 3 homepage items are published in the price guide; edit HOME_ITEMS')
    total = sum(pg.V[it['slug']]['sample_size'] for it in pg.PUB)
    ed = mr.EDITIONS[-1]
    listings = mr.load(ed)[1]['listings']
    cards = ''.join(
        '<a href="%s" style="background:#0A0A0B;padding:18px;display:flex;flex-direction:column;gap:8px;color:#E8EAEB;">'
        '<span style="font-size:12.5px;color:#E8EAEB;">%s</span>'
        '<span style="font-family:\'Cabinet Grotesk\',\'DM Mono\',sans-serif;font-weight:900;font-size:30px;line-height:1;letter-spacing:-.02em;color:#FFFFFF;">%s</span>'
        '<span style="font-size:12px;color:#8B9094;line-height:1.5;">middle half %s&ndash;%s &middot; %s listings</span></a>'
        % (pg.item_url(it, 'en'), html.escape(it['name']), money(pg.V[it['slug']]['typical_cents'], 'en'),
           money(pg.V[it['slug']]['range_cents']['low'], 'en'), money(pg.V[it['slug']]['range_cents']['high'], 'en'),
           num(pg.V[it['slug']]['sample_size'], 'en')) for it in items)
    report = ('<a href="%s/%s" style="font-size:12px;letter-spacing:.05em;padding:14px 0;">Vinted Market Report, %s%s &rarr;</a>'
              % (mr.HUB['en'], ed['slug']['en'], ed['name']['en'], ': %s listings, condition premium, price cuts' % num(listings, 'en')))
    return (
        '\r\n  <div style="max-width:1320px;margin:0 auto;padding:64px 20px;display:flex;flex-direction:column;gap:22px;">\r\n'
        '    <div style="display:flex;flex-direction:column;gap:12px;max-width:760px;">\r\n'
        '      <span style="font-size:11px;letter-spacing:.16em;color:#00E5A0;">FREE PRICE DATA</span>\r\n'
        '      <h2 style="margin:0;font-family:\'Cabinet Grotesk\',\'DM Mono\',sans-serif;font-weight:900;font-size:clamp(32px,5vw,50px);line-height:1;letter-spacing:-.04em;color:#FFFFFF;text-wrap:balance;">'
        'What things cost on Vinted, from %s listings</h2>\r\n'
        '      <p style="margin:0;font-size:16px;line-height:1.6;color:#A6ADB1;">Typical asking prices for %d popular items, from vinted.be listings SNYPD saw from %s. '
        'Asking prices, not sale prices: Vinted does not publish what items sell for.</p>\r\n'
        '    </div>\r\n'
        '    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(230px,100%%),1fr));gap:1px;background:#1D1D20;border:1px solid #1D1D20;">%s</div>\r\n'
        '    <div style="display:flex;gap:18px;flex-wrap:wrap;align-items:baseline;">\r\n'
        '      <a href="%s" style="font-size:12px;letter-spacing:.05em;padding:14px 0;">All %d items in the Vinted price guide &rarr;</a>\r\n'
        '      %s\r\n'
        '    </div>\r\n'
        '  </div>\r\n  ' % (num(total, 'en'), len(pg.PUB), pg.window('en'), cards, pg.HUB['en'], len(pg.PUB), report))


# ----------------------------------------------------------------- homepage footer links
# Built from gen_content's page list, so every guide and every language version gets a link from
# the homepage (Google's strongest page here; 88 URLs were "discovered, not indexed" on 18 Oct 2026).
HOME_FOOT_EN = [('bot', 'Vinted bot'), ('monitor', 'Vinted monitor'), ('notify', 'Vinted notifications'),
                ('notwork', 'Vinted notifications not working'), ('compare', 'Vinted bots compared'),
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


# ----------------------------------------------------------------- templates
TEMPLATES = {
    'home-foot-links': home_foot_links,
    # shared
    **{'price:%s' % k: '@@price:%s@@' % k for k in plans.ORDER},
    **{'price-mo:%s' % k: '@@price:%s@@ / mo' % k for k in plans.ORDER},
    # index.html
    'home-pro-searches': '@@searches:pro@@ active Vinted searches',
    'home-pro-change': '@@searches:free@@ &rarr; @@searches:pro@@',
    'home-free-line': '@@searches:free@@ search &middot; 24/7 for @@trial_days@@ days, then while your dashboard is open &middot; free Discord',
    'home-solo-line': '@@searches:solo@@ search &middot; runs 24/7, even with your dashboard closed',
    'home-kickstart-line': '@@searches:kickstart@@ searches &middot; runs 24/7, even with your dashboard closed',
    'home-elite-line': 'Everything in Pro + @@searches:elite@@ searches',
    'home-hero-trial': 'Free: your first search runs 24/7 with alerts for @@trial_days@@ days. No card.',
    'home-data': home_data,
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
    'plans-under': 'Paid plans renew every month until you cancel. Cancel any time. Full refund within @@refund_days@@ days of your first payment.',
    'plans-refund-h': '@@refund_days@@-DAY REFUND',
    'plans-refund-p': ' within @@refund_days@@ days of your first payment for a plan and we refund it in full.',
    'plans-cmp': cmp_html,
    'plans-faq': faq_html,
    'plans-js': ("var PRICE = { " + ", ".join("%s: '@@price:%s@@'" % (k, k) for k in plans.ORDER) + " };\r\n"
                 "  var SEARCHES = { " + ", ".join("%s: @@searches:%s@@" % (k, k) for k in plans.ORDER) + " };"),
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


def offers(ld):
    """Set every schema.org Offer's prices (price + priceSpecification) to plans.json."""
    by_name = {p['name']: p['price'] for p in plans.DATA['plans']}
    parts = re.split(r'(?=\{ "@type": "Offer")', ld)
    for i, part in enumerate(parts):
        m = re.match(r'\{ "@type": "Offer", "name": "([^"]+)"', part)
        if m and m.group(1) in by_name:
            parts[i] = re.sub(r'("price": ")[^"]*(")', lambda x: x.group(1) + by_name[m.group(1)] + x.group(2), part)
    return ''.join(parts)


def meta_prices(content):
    """'Kickstart &#8364;14.99' style mentions in meta descriptions."""
    for p in plans.DATA['plans']:
        if float(p['price']) > 0:
            content = re.sub(r'(\b%s (?:&#8364;|&euro;|€))[0-9.]+' % p['name'], lambda x: x.group(1) + p['price'], content)
    return content


BRAND = json.load(open(os.path.join(HERE, 'data', 'brand.json'), encoding='utf-8'))
_interval = json.load(open(os.path.join(HERE, 'data', 'check-interval.json'), encoding='utf-8'))
if '30 seconds' in BRAND['boilerplate'] and _interval['median_seconds'] != 30:
    sys.exit('gen_regions: the boilerplate says "about every 30 seconds" but check-interval.json median is %s s'
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
            return m.group(1) + render(m.group(2), False) + m.group(4)

        def sub_js(m):
            n[0] += 1
            return m.group(1) + render(m.group(2), True) + m.group(4)

        out = HTML_RE.sub(sub_html, text)
        out = JS_RE.sub(sub_js, out)
        out = LD_RE.sub(lambda m: m.group(1) + offers(m.group(2)) + m.group(3), out)
        out = META_RE.sub(lambda m: m.group(1) + meta_prices(m.group(2)) + m.group(3), out)
        out = ORG_RE.sub(org_description, out)
        if n[0] == 0:
            sys.exit(f'gen_regions: {name} has no plan regions (markers lost?)')
        if out != text:
            changed.append(name)
            if not check:
                open(path, 'wb').write(out.encode('utf-8'))
        print(f'regions {name}: {n[0]} regions, {"changed" if out != text else "unchanged"}')
    return changed


if __name__ == '__main__':
    sys.exit(1 if run(check='--check' in sys.argv) and '--check' in sys.argv else 0)
