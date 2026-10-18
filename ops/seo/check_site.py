#!/usr/bin/env python3
"""Release guard for the public site:  python ops/seo/check_site.py   (prepublish.py runs it)

Fails (exit 1) on anything that would put a wrong or broken fact in front of a visitor or
a crawler:
  1. stale plan wording, in any language (the Free plan before the 7-day trial, French
     "sign-up is in English" notes, placeholder counters, a counter "As of" date that is old)
  2. a plan price next to a plan name that is not the price in ops/seo/data/plans.json
     (visible text, meta tags, JSON-LD Offers)
  3. banned claims from outreach/00-fact-sheet.md ("instant", "real-time", "fastest",
     "undetectable", "allowed by Vinted", "safe", "sold prices", catch times, ms speeds,
     the suspicious-photo badge), in the six site languages
  4. duplicate <title>s among the sitemap pages
  5. hreflang that is not reciprocal (A lists B but B does not list A back)
  6. internal links to pages that do not exist or that redirect (.html, trailing slash,
     vercel.json redirects, the apex domain)
  7. JSON-LD that does not parse
Warnings (W) are printed but do not fail. ops/ is in .vercelignore: never deploys.
"""
import datetime, html, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import plans  # noqa: E402

SITE = 'https://www.snypd.store'
SKIP_DIRS = {'ops', 'marketing', 'node_modules', '.git', '.vercel', '.claude'}
COUNTER_PAGES = {'index.html', 'signup.html', 'login.html', 'reset-password.html'}  # keep in step with prepublish.COUNTER_PAGES
COUNTER_MAX_AGE_DAYS = 7

# 1. Stale wording. Searched in the page source with entities decoded (scripts included:
#    the homepage walkthrough and the /plans table live in JS or come from it).
STALE = [
    (r'laptop open', 'Free runs 24/7 for the first 7 days: "laptop open" is wrong'),
    (r'Tab open only', 'Free runs 24/7 for the first 7 days'),
    (r'On Free, yes', 'Free runs 24/7 for the first 7 days'),
    (r'Free stops when you do', 'Free runs 24/7 for the first 7 days'),
    (r"(?<!trial, )Free only watches while the dashboard is open", 'say "after the 7-day trial"'),
    (r'Free: one search, dashboard open', 'Free runs 24/7 for the first 7 days'),
    (r'There is no trial', 'there is a 7-day trial'),
    (r'[Ii]nscription(?! en français)[^.<]{0,60}en anglais', 'sign-up is in French since 9 Oct 2026 (only Whop checkout is English)'),
    (r'tarifs</a> \(en anglais\)', '/plans is in French for French browsers since 9 Oct 2026'),
    (r'paiement \(Whop\) est en anglais', 'the Whop checkout is French for French users since 18 Oct 2026 (site 5ad832b)'),
]
PLACEHOLDER_COUNTER = re.compile(r'id="(?:stat-listings|au-listings)"[^>]*>\s*(?:&mdash;|—|-)?\s*<')
ASOF = re.compile(r'id="(?:stat-listings-asof|au-asof)"[^>]*>([^<]*)<')
MONTHS = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'June': 6, 'July': 7, 'Aug': 8, 'Sept': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

# 3. Banned claims, checked on visible text + meta + JSON-LD. A hit is allowed only when a
#    negation sits right before it ("not sold prices") or the exact sentence is in ALLOW.
BANNED = [
    r'\binstant(?:ly|aneous)?\b', r'\breal[- ]?time\b', r'\bfastest\b', r'\bundetectable\b', r'allowed by Vinted',
    r'\bsafe\b', r'\bsold prices?\b', r'\bsells? for\b', r'\bcatch time\b', r'\b\d+ ?ms\b', r'\bsuspicious\b',
    r'\binstantan[ée]', r'\btemps r[ée]el\b', r'\ble plus rapide\b', r'\bind[ée]tectable\b', r'autoris[ée] par Vinted',
    r'\bprix vendus?\b', r'\bEchtzeit\b', r'\bschnellste', r'\bunauff[äa]llig\b', r'\bsofort\b',
    r'\brealtime\b', r'\bsnelste\b', r'\btempo reale\b', r'\bistantane', r'\bpi[ùu] veloce\b',
    r'\btiempo real\b', r'\binstant[áa]ne', r'\bm[áa]s r[áa]pido\b',
]
NEGATION = re.compile(r'(?:\bnot|\bno|\bnever|\bnicht|\bkein\w*|\bniet|\bgeen|\bnon|\bpas d[eu]s?|\bne pas|\bni)\s+(?:\w+\s+){0,2}$', re.I)
# (file or '*', regex that must match the text around the hit, why it is allowed)
ALLOW = [
    ('affiliate.html', r'Do not promise', 'partner rules list the claims partners must not make'),
    ('*', r'Vinted does not publish what items sell for', 'honesty note on price pages'),
    ('*', r'Is this what .{0,60} sells for on Vinted\?', 'price-guide FAQ whose answer is "No. These are asking prices"'),
    ('vinted-bot-comparison.html', r'Telvin advertises alerts in 750 ms|Crazed “temps réel” \(real time\)',
     "a competitor's own claim, attributed, followed by 'those are each vendor's own figures'"),
    ('fr/comparatif-bot-vinted.html', r'Telvin annonce des alertes en 750 ms|Crazed du «\s?temps réel\s?»',
     "a competitor's own claim, attributed"),
    ('vinted-bot-comparison.html', r'Which Vinted bot is the fastest\?', 'FAQ question answered "there is no fair way to say"'),
    ('fr/comparatif-bot-vinted.html', r'Quel est le bot Vinted le plus rapide', 'FAQ question answered "impossible de le dire"'),
    # comparison pages in every language quote these vendor claims, in quotes, attributed, then say they can't be compared
    ('*', r'Telvin\W{1,3}750 ?ms', "Telvin's own claim, quoted and attributed"),
    ('*', r'Resell Vault\W{1,3}0\.14 ?ms', "Resell Vault's own claim, quoted and attributed"),
    # work order 18 step 5 (Tanush OK 10 Oct 2026): the question people type, on its own page only, always answered "No"
    ('vinted-sold-items.html', r'(?:Can you see|Does Vinted show) (?:sold items and )?sold prices(?: on Vinted)?\?',
     'the sold-items page asks the searched question and answers "No"'),
]

# 2. Price next to a plan name.
EUR = r'(?:€\s?(\d+(?:[.,]\d{2})?)|(\d+(?:[.,]\d{2})?)\s?€)'
PRICE_NEAR = re.compile(r'\b(Solo|SOLO|Kickstart|KICKSTART|Pro|PRO|Elite|ELITE)\b(?:\s?\(|[\s:,]| | (?:at|à|kostet|costs?|coûte|cuesta|costa|for|est|ist|is|plan,?|tarif|piano|abonnement)\b){0,4}\s*' + EUR)


def files():
    """HTML that is or would be deployed: tracked + untracked-not-ignored, minus ops/
    (.vercelignore) and folders that must never be committed (CLAUDE.md: marketing/)."""
    out = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '--', '*.html'],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
    for rel in out:
        if rel.split('/')[0] not in SKIP_DIRS and os.path.isfile(os.path.join(ROOT, rel)):
            yield rel


def url_of(rel):
    p = '/' + rel[:-5]
    if p.endswith('/index'):
        p = p[:-6] or '/'
    return '/' if p == '/index' else p


def visible(src):
    """Visible text + title/meta content + JSON-LD, entities decoded, whitespace collapsed."""
    ld = ' '.join(re.findall(r'<script type="application/ld\+json">(.*?)</script>', src, re.S))
    meta = ' '.join(re.findall(r'<meta [^>]*content="([^"]*)"', src))
    body = re.sub(r'<(script|style)\b.*?</\1>', ' ', src, flags=re.S)
    body = re.sub(r'<!--.*?-->', '', body, flags=re.S)
    body = re.sub(r'<[^>]+>', ' ', body)
    return re.sub(r'\s+', ' ', html.unescape(body + ' ' + meta + ' ' + ld.replace('\\"', '"')))


def norm_price(s):
    return s.replace(',', '.')


def main():
    errors, warns = [], []
    pages = {rel: open(os.path.join(ROOT, rel), encoding='utf-8-sig').read() for rel in files()}
    expected = {p['name'].lower(): p['price'] for p in plans.DATA['plans']}
    founding = plans.DATA['founding']['price']
    today = datetime.date.today()

    for rel, src in sorted(pages.items()):
        dec = html.unescape(src)
        # 1. stale wording + counters
        for pat, why in STALE:
            for m in re.finditer(pat, dec):
                errors.append(f'{rel}: stale "{m.group(0)}" ({why})')
        if PLACEHOLDER_COUNTER.search(src):
            (errors if rel in COUNTER_PAGES else warns).append(f'{rel}: listings counter has no figure (run prepublish.py)')
        for m in ASOF.finditer(src):
            d = re.match(r'As of (\d{1,2}) (\w+) (\d{4})$', html.unescape(m.group(1)).strip())
            if not d or d.group(2) not in MONTHS:
                (errors if rel in COUNTER_PAGES else warns).append(f'{rel}: counter date unreadable: "{m.group(1)}"')
                continue
            age = (today - datetime.date(int(d.group(3)), MONTHS[d.group(2)], int(d.group(1)))).days
            if age > COUNTER_MAX_AGE_DAYS:
                (errors if rel in COUNTER_PAGES else warns).append(f'{rel}: counter "{m.group(1)}" is {age} days old')

        text = visible(src)
        # 2. prices next to plan names
        for m in PRICE_NEAR.finditer(text):
            name, val = m.group(1).lower(), norm_price(m.group(2) or m.group(3))
            want = expected[name]
            ok = val in (want, want.rstrip('0').rstrip('.'))
            if not ok and name == 'pro' and val == founding and re.search(r'life|vie|founding|fondateur', text[m.end():m.end() + 80], re.I):
                ok = True  # the founding promise keeps its own price
            if not ok:
                errors.append(f'{rel}: "{m.group(0)}" but plans.json says {name} = {want}')
        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', src, re.S):
            try:
                data = json.loads(block)
            except ValueError as e:
                errors.append(f'{rel}: JSON-LD does not parse ({e})')
                continue
            stack = [data]
            while stack:
                o = stack.pop()
                if isinstance(o, list):
                    stack.extend(o)
                elif isinstance(o, dict):
                    if o.get('@type') == 'Offer' and str(o.get('name', '')).lower() in expected:
                        want = expected[str(o['name']).lower()]
                        prices = [o.get('price')] + [o.get('priceSpecification', {}).get('price')]
                        for pr in prices:
                            if pr is not None and str(pr) != want:
                                errors.append(f'{rel}: JSON-LD Offer {o["name"]} price {pr}, plans.json {want}')
                    stack.extend(o.values())
        # 3. banned claims
        for pat in BANNED:
            for m in re.finditer(pat, text, re.I):
                ctx = text[max(0, m.start() - 60):m.end() + 60]
                if NEGATION.search(text[max(0, m.start() - 40):m.start()]):
                    continue
                wide = text[max(0, m.start() - 120):m.end() + 120]
                if any(f in ('*', rel) and re.search(a, wide) for f, a, _ in ALLOW):
                    continue
                errors.append(f'{rel}: banned "{m.group(0)}" in "...{ctx.strip()}..."')

    # 4. duplicate titles among sitemap pages
    sm = open(os.path.join(ROOT, 'sitemap.xml'), encoding='utf-8').read()
    locs = [u[len(SITE):] or '/' for u in re.findall(r'<loc>([^<]+)</loc>', sm)]
    by_url = {url_of(rel): rel for rel in pages}
    titles = {}
    for u in locs:
        rel = by_url.get(u)
        if not rel:
            errors.append(f'sitemap: {u} has no file')
            continue
        t = re.search(r'<title>(.*?)</title>', pages[rel], re.S)
        t = html.unescape(t.group(1)).strip() if t else ''
        if not t:
            errors.append(f'{rel}: no <title>')
        titles.setdefault(t, []).append(rel)
    for t, rels in titles.items():
        if t and len(rels) > 1:
            errors.append(f'duplicate title "{t}": {", ".join(rels)}')

    # 5. hreflang reciprocity
    alt_re = re.compile(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"')
    alts = {rel: dict(alt_re.findall(src)) for rel, src in pages.items()}
    for rel, a in alts.items():
        if not a:
            continue
        me = SITE + url_of(rel)
        if me not in a.values():
            errors.append(f'{rel}: hreflang set does not include the page itself ({me})')
        for lang, href in a.items():
            if lang == 'x-default' or href == me:
                continue
            other = by_url.get(href[len(SITE):] or '/') if href.startswith(SITE) else None
            if not other:
                errors.append(f'{rel}: hreflang {lang} -> {href} has no file')
            elif me not in alts[other].values():
                errors.append(f'{rel}: hreflang {lang} -> {href}, which does not link back')

    # 6. internal links
    vj = json.load(open(os.path.join(ROOT, 'vercel.json'), encoding='utf-8'))
    redirects = {r['source'] for r in vj.get('redirects', [])}
    rewrites = {r['source'] for r in vj.get('rewrites', [])}
    href_re = re.compile(r'<(?:a|link)\b[^>]*\bhref="([^"]+)"')
    indexable = {by_url[u] for u in locs if u in by_url}
    for rel, src in pages.items():
        redir = errors if rel in indexable else warns  # a redirect costs SEO only on indexable pages
        body = re.sub(r'<script\b(?![^>]*ld\+json).*?</script>', ' ', src, flags=re.S)  # JS-built links are not crawled as such
        for href in set(href_re.findall(body)):
            h = html.unescape(href)
            if h.startswith(('https://snypd.store', 'http://snypd.store', 'http://www.snypd.store')):
                redir.append(f'{rel}: link {h} redirects (use {SITE})')
                continue
            if h.startswith(SITE):
                h = h[len(SITE):] or '/'
            if not h.startswith('/') or h.startswith('//'):
                continue
            path = re.split(r'[?#]', h)[0] or '/'
            if path in rewrites:
                continue
            if path in redirects:
                redir.append(f'{rel}: link {h} redirects (vercel.json)')
            elif path != '/' and path.endswith('/'):
                redir.append(f'{rel}: link {h} has a trailing slash (redirects)')
            elif path.endswith('.html'):
                redir.append(f'{rel}: link {h} ends in .html (cleanUrls redirects it)')
            elif path == '/':
                continue
            elif os.path.splitext(path)[1]:
                if not os.path.isfile(os.path.join(ROOT, path.lstrip('/'))):
                    errors.append(f'{rel}: link {h} -> file missing')
            elif not (os.path.isfile(os.path.join(ROOT, path.lstrip('/') + '.html'))
                      or os.path.isfile(os.path.join(ROOT, path.lstrip('/'), 'index.html'))):
                errors.append(f'{rel}: link {h} -> 404')

    # 7. 404.html is served for every unknown path: it must never claim a URL of its own
    if '404.html' in pages:
        s404 = pages['404.html']
        if '<meta name="robots" content="noindex">' not in s404:
            errors.append('404.html: no robots noindex')
        if 'rel="canonical"' in s404 or '<link rel="alternate"' in s404 or 'application/ld+json' in s404:
            errors.append('404.html: has a canonical, hreflang or JSON-LD (it is served at every unknown path)')
        if '/404' in locs:
            errors.append('sitemap: /404 must not be listed')

    for w in sorted(set(warns)):
        print('W', w)
    for e in sorted(set(errors)):
        print('E', e)
    print(f'check_site: {len(pages)} pages, {len(set(errors))} errors, {len(set(warns))} warnings')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
