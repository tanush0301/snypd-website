# Runs INSIDE the backend container, READ-ONLY: for one ISO week (Europe/Brussels), how many vinted.be
# listings of each published price-guide item were asked at <= 60% of the item's typical price for the
# SAME condition (Market Report, the guide's own numbers). Prints JSON; writes nothing anywhere.
#
# Item matching is the guide's: market_snapshot's `to_tsvector('simple', title) @@ to_tsquery('simple',
# synonyms.build_tsquery(q))` on marketplace 'eu', here through PostgREST's fts(simple) filter (the same
# expression). Typical prices: market_report.build_report + customer_view at run time (14-day window).
#
# Excluded before counting: conditions the report has no typical for, kids' sizes (EU < 35, "ans",
# "years", "mois", "months", "cm"), lots/bundles in the title (lot, lots, x2, x3, bundle, set), business sellers.
# Output per below-typical listing: size, condition, asking price, typical, % under, day first seen.
# NEVER output listing_id, url, title, seller fields or photo fields (they are read only to filter/dedupe).
#
# Run from the site repo root in Git Bash (week = ISO week, e.g. 2026-W40):
#   python ops/seo/steals_items.py > /tmp/si.json && cat /tmp/si.json | ssh snypd-vps "cat > /tmp/si.json" && tr -d '\r' < ops/seo/steals_batch.py | ssh snypd-vps "cat > /tmp/sb.py && docker cp /tmp/si.json backend:/tmp/si.json && docker cp /tmp/sb.py backend:/tmp/sb.py && docker exec backend python /tmp/sb.py /tmp/si.json 2026-W40" > ops/seo/data/steals-2026-W40.json
# price_history keeps 14 days: a week must be captured within ~7 days of its end (the VPS cron does it).
import asyncio, datetime, json, re, statistics, sys
from zoneinfo import ZoneInfo

sys.path.insert(0, '/app')
from src import market_report as mr, synonyms  # noqa: E402
from src.database.supabase_connection import get_client  # noqa: E402

RULE = 0.60
TZ = ZoneInfo('Europe/Brussels')
RAW_TO_LABEL = dict(mr.MARKET_RESEARCH_KNOWN_CONDITIONS)
LOT = re.compile(r'\b(lot|lots|x2|x3|bundle|set)\b', re.I)  # not 'pack': New Balance 'Protection Pack' is a model
KID_WORDS = re.compile(r'(ans|years|mois|months|cm)', re.I)
KID_EU = re.compile(r'^\s*(EU\s*)?([12][0-9]|3[0-4])([.,]5)?\s*$')
COLS = 'listing_id,price_cents,condition_raw,size_title,seller_is_business,title,first_seen_at'


def week_bounds(iso_week):
    y, w = iso_week.split('-W')
    start = datetime.datetime.combine(datetime.date.fromisocalendar(int(y), int(w), 1), datetime.time(0), TZ)
    return start, start + datetime.timedelta(days=7)


def fetch(q, start, end):
    norm = ' '.join(q.split()).lower()
    tsq = synonyms.build_tsquery(norm) if mr.SYNONYMS_ENABLED else None
    op, val = ('fts(simple)', tsq) if tsq else ('plfts(simple)', norm)
    rows, last = [], 0
    while True:
        r = (get_client().table('price_history').select(COLS).eq('marketplace', 'eu').filter('title', op, val)
             .gte('first_seen_at', start.isoformat()).lt('first_seen_at', end.isoformat())
             .gt('listing_id', last).order('listing_id').limit(1000).execute())
        rows.extend(r.data)
        if len(r.data) < 1000:
            return rows, tsq or norm
        last = r.data[-1]['listing_id']


def is_kid(size):
    return bool(size) and bool(KID_WORDS.search(size) or KID_EU.match(size))


async def item(it, start, end):
    view = mr.customer_view(await mr.build_report(it['query'], redis_client=None, log=None))
    typ = {c['condition_label']: c['typical_cents'] for c in view.get('by_condition') or [] if c.get('typical_cents')}
    rows, matcher = fetch(it['query'], start, end)
    ex = {'no_typical_for_condition': 0, 'kids_size': 0, 'lot_or_bundle': 0, 'business_seller': 0}
    eligible, below = 0, []
    for r in rows:
        label = RAW_TO_LABEL.get(r['condition_raw'])
        if label not in typ:
            ex['no_typical_for_condition'] += 1
        elif is_kid(r['size_title']):
            ex['kids_size'] += 1
        elif LOT.search(r['title'] or ''):
            ex['lot_or_bundle'] += 1
        elif r['seller_is_business']:
            ex['business_seller'] += 1
        else:
            eligible += 1
            t, p = typ[label], r['price_cents']
            if p is not None and p <= RULE * t:
                day = datetime.datetime.fromisoformat(r['first_seen_at'].replace('Z', '+00:00')).astimezone(TZ).date()
                below.append({'size': r['size_title'], 'condition': label, 'price_cents': p, 'typical_cents': t,
                              'pct_under': round(100 * (t - p) / t), 'day': day.isoformat()})
    below.sort(key=lambda x: (x['day'], x['condition'], x['price_cents']))
    return {'slug': it['slug'], 'query': it['query'], 'matcher': matcher,
            'report': {'display_verdict': view.get('display_verdict'), 'confidence': view.get('confidence'),
                       'sample_size': view.get('sample_size'), 'typical_cents_by_condition': typ},
            'listings_in_week': len(rows), 'excluded': ex, 'eligible': eligible, 'below_rule': len(below),
            'share_below_pct': round(100 * len(below) / eligible, 1) if eligible else None,
            'median_pct_under': statistics.median([b['pct_under'] for b in below]) if below else None,
            'rows': below}


async def main(items, iso_week):
    start, end = week_bounds(iso_week)
    out = []
    for it in items:
        try:
            out.append(await item(it, start, end))
        except Exception as e:
            out.append({'slug': it['slug'], 'query': it['query'], 'error': type(e).__name__ + ': ' + str(e)[:200]})
    print(json.dumps({'week': iso_week, 'from': start.isoformat(), 'to': end.isoformat(),
                      'generated_at': datetime.datetime.utcnow().isoformat(timespec='seconds') + 'Z',
                      'marketplace': 'vinted.be', 'currency': 'EUR',
                      'rule': 'asking price <= 60% of the Market Report typical for the same condition; '
                              'kids sizes, lots/bundles, business sellers and conditions without a typical excluded',
                      'note': 'Asking prices, not sale prices. SNYPD cannot tell whether these listings sold.',
                      'items': out}, ensure_ascii=False))


asyncio.run(main(json.load(open(sys.argv[1], encoding='utf-8')), sys.argv[2]))
