#!/usr/bin/env python3
# Measures how often SNYPD really checks each hunt, from the scraper's own log
# (one QUEUE_CONSUME line per check, with the hunt's search_key). The SEO pages
# quote this file's numbers (ops/seo/gen_content.py), never a typed figure.
#
#   ssh snypd-vps "docker logs --since 24h snypd-scraper-worker-2 2>&1 | grep '\"QUEUE_CONSUME\"'" \
#     | python ops/seo/check_interval.py > ops/seo/data/check-interval.json
#
# It measures the gap between two checks of the same hunt. It is NOT the time
# from a seller listing an item to the alert: Vinted itself shows a new listing
# in its search 3-15 min after the time on the item page (CLAUDE.md section 3),
# so never present these numbers as a catch time.
import json, statistics, sys
from datetime import datetime

by_key = {}
for line in sys.stdin:
    try:
        d = json.loads(line)
    except ValueError:
        continue
    if d.get('event') != 'QUEUE_CONSUME' or not d.get('search_key'):
        continue
    t = datetime.fromisoformat(d['ts'].replace('Z', '+00:00'))
    by_key.setdefault(d['search_key'], []).append(t)

gaps, first, last = [], None, None
for ts in by_key.values():
    ts.sort()
    first = ts[0] if first is None or ts[0] < first else first
    last = ts[-1] if last is None or ts[-1] > last else last
    g = [(b - a).total_seconds() for a, b in zip(ts, ts[1:])]
    gaps += [x for x in g if x > 1]  # same-second duplicates are retries, not checks

if len(gaps) < 500:
    sys.exit('only %d gaps: too few to publish' % len(gaps))
gaps.sort()
share = lambda s: round(100 * sum(x <= s for x in gaps) / len(gaps))
json.dump({
    'measured_from': first.strftime('%Y-%m-%dT%H:%MZ'),
    'measured_to': last.strftime('%Y-%m-%dT%H:%MZ'),
    'hunts': sum(1 for ts in by_key.values() if len(ts) > 1),
    'checks': len(gaps) + len(by_key),
    'median_seconds': round(statistics.median(gaps)),
    'p90_seconds': round(gaps[int(0.9 * len(gaps))]),
    'max_seconds': round(gaps[-1]),
    'share_within_60s': share(60),
    'share_within_120s': share(120),
}, sys.stdout, indent=1)
print()
