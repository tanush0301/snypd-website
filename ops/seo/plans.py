"""Plan facts for every public page, from ops/seo/data/plans.json (+ check-interval.json).

Generators write tokens instead of plan numbers and gen_content.write() fills them in,
using the page's own <html lang>, so a price change is one edit in plans.json:

    @@price:kickstart@@   formatted price with the euro sign   (en EUR14.99, fr 14,99 EUR, nl EUR 14,99)
    @@num:kickstart@@     the number only, in the page's format (en 14.99, fr 14,99)
    @@searches:pro@@      active searches (5)
    @@trial_days@@        Free 24/7 trial length in days (3)
    @@trial_hours@@       the same in hours (72)
    @@trial_ext_days@@    days added once when the first hunt found nothing in the trial (2)
    @@refund_days@@       refund window (14)
    @@median_s@@          measured median check gap in seconds (30)
    @@mr_hour@@ @@mr_day@@ Market Report price checks per hour / per day (20 / 100)
    @@founding_price@@    the founding promise (Pro price for life), formatted like @@price@@;
                          it stays put when Pro's price changes

One-time passes (plans.json "passes", e.g. the Hunt Pass, key 'pass') take the same
@@price:pass@@ / @@num:pass@@ / @@searches:pass@@ tokens, plus:
    @@pass_days@@         how long the Hunt Pass runs from the purchase (30)
    @@whop:pass@@         its Whop plan id (plans.json whop_plan_id; 'plan_PENDING_PASS' until
                          the owner creates it -- check_site.py fails pages that offer it then)
Passes are NOT in PLANS/ORDER, so the monthly tables and loops stay the 5 monthly plans.

ops/ is in .vercelignore, so this file never deploys.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, 'data', 'plans.json'), encoding='utf-8'))
SPEED = json.load(open(os.path.join(HERE, 'data', 'check-interval.json'), encoding='utf-8'))
PLANS = {p['key']: p for p in DATA['plans']}
ORDER = [p['key'] for p in DATA['plans']]
PASSES = {p['key']: p for p in DATA.get('passes', [])}
if set(PASSES) & set(PLANS):
    raise ValueError('plans.json: a pass key is also a plan key')
PRICED = dict(PLANS, **PASSES)  # everything a @@price:KEY@@ token may name
PASS_DAYS = PASSES['pass']['days']
PASS_PENDING_ID = 'plan_PENDING_PASS'
TRIAL_DAYS = DATA['free_trial']['days']
TRIAL_HOURS = DATA['free_trial']['hours']
TRIAL_EXT_DAYS = DATA['free_trial']['extension']['days']
if TRIAL_HOURS != 24 * TRIAL_DAYS:
    raise ValueError('plans.json: free_trial.hours must be 24 x free_trial.days')
REFUND_DAYS = DATA['refund']['days']
MEDIAN_S = SPEED['median_seconds']
MR = DATA['market_report']

EURO_BEFORE = {'en', 'nl'}  # en: EUR14.99, nl: EUR 14,99; everyone else: 14,99 EUR


def num(key, lang):
    """'14.99' / '14,99'; Free is '0'."""
    p = PRICED[key]['price']
    return p if lang == 'en' else p.replace('.', ',')


def price(key, lang, entities=True):
    """Price with the euro sign as each language writes it. entities=False gives plain
    characters (for JS strings and JSON). key 'founding' is the founding promise."""
    eur, nb = ('&euro;', '&nbsp;') if entities else ('€', ' ')
    n = DATA['founding']['price'] if key == 'founding' else PRICED[key]['price']
    n = n if lang == 'en' else n.replace('.', ',')
    if lang == 'en':
        return eur + n
    if lang == 'nl':
        return eur + nb + n
    return n + nb + eur


TOKEN = re.compile(r'@@(price|num|searches|whop):([a-z]+)@@|@@(trial_days|trial_hours|trial_ext_days|refund_days|median_s|mr_hour|mr_day|founding_price|pass_days)@@')


LD_BLOCK = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)


def fill(text, lang, plain=False):
    """Replace every token. Inside JSON-LD blocks prices use plain characters, because
    JSON is not HTML-decoded (an &euro; there would reach Google as the literal text).
    plain=True: plain characters everywhere (JavaScript strings)."""
    if plain:
        return _fill(text, lang, False)
    text = LD_BLOCK.sub(lambda m: m.group(1) + _fill(m.group(2), lang, False) + m.group(3), text)
    return _fill(text, lang, True)


def _fill(text, lang, entities):
    def rep(m):
        if m.group(3) == 'founding_price':
            return price('founding', lang, entities)
        if m.group(3):
            return str({'trial_days': TRIAL_DAYS, 'trial_hours': TRIAL_HOURS, 'trial_ext_days': TRIAL_EXT_DAYS,
                        'refund_days': REFUND_DAYS, 'median_s': MEDIAN_S,
                        'mr_hour': MR['per_hour'], 'mr_day': MR['per_day'], 'pass_days': PASS_DAYS}[m.group(3)])
        kind, key = m.group(1), m.group(2)
        if key not in PRICED:
            raise KeyError(f'unknown plan in token {m.group(0)}')
        if kind == 'price':
            return price(key, lang, entities)
        if kind == 'num':
            return num(key, lang)
        if kind == 'whop':
            if key not in PASSES:
                raise KeyError(f'{m.group(0)}: only passes carry a Whop plan id in plans.json')
            return PASSES[key]['whop_plan_id']
        return str(PRICED[key]['searches'])
    out = TOKEN.sub(rep, text)
    if '@@' in out:
        left = re.findall(r'@@[^@\s]{1,40}@@', out)
        if left:
            raise ValueError(f'unfilled plan tokens: {left[:5]}')
    return out


def page_lang(text):
    m = re.search(r'<html[^>]*\blang="([a-z]{2})', text)
    return m.group(1) if m else 'en'
