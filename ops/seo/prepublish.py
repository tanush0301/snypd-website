#!/usr/bin/env python3
"""Run before committing a release of the public site:  python ops/seo/prepublish.py

1. Refreshes the static listings figure on the homepage(s). The page updates it
   with JavaScript, but crawlers that do not run JavaScript (OpenAI, Anthropic,
   Perplexity) only ever see the number written in the HTML, so it should be
   recent and carry its own date.
2. Rewrites sitemap.xml. lastmod is the date of the file's last commit, or today
   when the file has uncommitted changes (Bing and Google both ask for an accurate
   lastmod; a stale one teaches them to ignore it). Pages with language versions
   get hreflang alternates.

Byte-level edits only (these files are UTF-8 with CRLF; never re-encode them).
Afterwards, once the deploy is live:  python ops/seo/indexnow.py
"""
import datetime, json, os, re, subprocess, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = 'https://www.snypd.store'
SUPABASE = 'https://igbuqanjocfmahlzzupc.supabase.co'
ANON = ('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlnYnVxYW5qb2NmbWFobHp6dXBjIiwic'
        'm9sZSI6ImFub24iLCJpYXQiOjE3NTYzMTY4OTgsImV4cCI6MjA3MTg5Mjg5OH0.iAF7dzPqrfbd3YZmnhKOTnMcNVslR5AMo8cBxxwpaJQ')

# (url path, source file, {hreflang: path} or None). Only public, indexable pages.
# Keep in sync with vercel.json's noindex list: nothing noindexed belongs here.
PAGES = [
    ('/',        'index.html',   None),
    ('/plans',   'plans.html',   None),
    ('/faq',     'faq.html',     None),
    ('/signup',  'signup.html',  None),
    ('/support', 'support.html', None),
    ('/cookies', 'cookies.html', None),
    ('/vinted-bot',                 'vinted-bot.html',                 None),
    ('/vinted-saved-search-alerts', 'vinted-saved-search-alerts.html', None),
    ('/vinted-bot-comparison',      'vinted-bot-comparison.html',      None),
    ('/vinted-prices',              'vinted-prices.html',              None),
]
# French versions are added only while gen_content.FR_LIVE is True (they are held
# until SNYPD polls vinted.fr). Each pair gets hreflang alternates both ways.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_content import FR_LIVE, SLUGS  # noqa: E402
if FR_LIVE:
    _done = []
    for key, s_ in SLUGS.items():
        alts = {'en': s_['en'], 'fr': s_['fr'], 'x-default': s_['en']}
        _done.append((s_['fr'], s_['fr'].lstrip('/') + '.html', alts))
        PAGES[:] = [(u, f, alts if u == s_['en'] else a) for (u, f, a) in PAGES]
    PAGES.extend(_done)
# Pages that carry the static listings figure, with the language of their "As of" line.
COUNTER_PAGES = [('index.html', 'en')]
MONTHS = {'en': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec'],
          'fr': ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.']}
ASOF = {'en': 'As of {d} {m} {y}', 'fr': 'Au {d} {m} {y}'}
GROUP = {'en': ',', 'fr': ' '}  # fr: narrow no-break space


def git_date(path):
    dirty = subprocess.run(['git', 'status', '--porcelain', '--', path], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if dirty:
        return datetime.date.today().isoformat()
    d = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', path], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return d or datetime.date.today().isoformat()


def refresh_counter():
    req = urllib.request.Request(SUPABASE + '/rest/v1/public_stats?select=value,as_of&key=eq.listings_matched',
                                 headers={'apikey': ANON, 'Authorization': 'Bearer ' + ANON})
    rows = json.load(urllib.request.urlopen(req, timeout=20))
    if not rows or not isinstance(rows[0].get('value'), int) or rows[0]['value'] <= 0:
        sys.exit('public_stats returned nothing usable; counter left unchanged')
    value = rows[0]['value']
    when = datetime.datetime.fromisoformat(rows[0]['as_of'].replace('Z', '+00:00')).astimezone(datetime.timezone.utc)
    for name, lang in COUNTER_PAGES:
        path = os.path.join(ROOT, name)
        b = open(path, 'rb').read()
        num = f'{value:,}'.replace(',', GROUP[lang]).encode('utf-8')
        asof = ASOF[lang].format(d=when.day, m=MONTHS[lang][when.month - 1], y=when.year).encode('utf-8')
        b2, n1 = re.subn(rb'(id="stat-listings">)[^<]*(<)', lambda m: m.group(1) + num + m.group(2), b)
        b2, n2 = re.subn(rb'(id="stat-listings-asof">)[^<]*(<)', lambda m: m.group(1) + asof + m.group(2), b2)
        if n1 != 1 or n2 != 1:
            sys.exit(f'{name}: expected one counter and one date, found {n1}/{n2}')
        if b2 != b:
            open(path, 'wb').write(b2)
        print(f'counter {name}: {num.decode()} / {asof.decode()}')


def write_sitemap():
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for url, src, alts in PAGES:
        if not os.path.isfile(os.path.join(ROOT, src)):
            sys.exit(f'sitemap: {src} does not exist')
        lines.append('  <url>')
        lines.append(f'    <loc>{SITE}{url}</loc>')
        lines.append(f'    <lastmod>{git_date(src)}</lastmod>')
        if alts:
            for lang, p in alts.items():
                lines.append(f'    <xhtml:link rel="alternate" hreflang="{lang}" href="{SITE}{p}"/>')
        lines.append('  </url>')
    lines.append('</urlset>')
    data = ('\n'.join(lines) + '\n').encode('utf-8')
    open(os.path.join(ROOT, 'sitemap.xml'), 'wb').write(data)
    print(f'sitemap.xml: {len(PAGES)} URLs')


if __name__ == '__main__':
    refresh_counter()
    write_sitemap()
