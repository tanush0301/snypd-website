# Runs INSIDE the backend container: the exact Market Report output (customer_view) for every
# item of ops/seo/price_items.json, read-only. typical_cents = median asking price, range_cents =
# 25th-75th percentile (market_report.py), over the listings SNYPD saw in the last 14 days.
#
# Run from the site repo root in Git Bash (writes the data file the generator reads):
#   python -c "import json;print(json.dumps([i['query'] for i in json.load(open('ops/seo/price_items.json',encoding='utf-8'))['items']]))" | ssh snypd-vps "cat > /tmp/q.json" && tr -d '\r' < ops/seo/price_guide_batch.py | ssh snypd-vps "cat > /tmp/pgb.py && docker cp /tmp/q.json backend:/tmp/q.json && docker cp /tmp/pgb.py backend:/tmp/pgb.py && docker exec backend python /tmp/pgb.py /tmp/q.json" > ops/seo/data/price-guide.json
import asyncio, json, sys, datetime
sys.path.insert(0, '/app')
from src import market_report as mr


async def main(queries):
    out = []
    for q in queries:
        try:
            out.append({"q": q, "ok": True, "view": mr.customer_view(await mr.build_report(q, redis_client=None, log=None))})
        except Exception as e:
            out.append({"q": q, "ok": False, "error": type(e).__name__ + ": " + str(e)[:200]})
    print(json.dumps({"generated_at": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
                      "window_days": 14, "marketplace": "vinted.be", "results": out}, default=str))


asyncio.run(main(json.load(open(sys.argv[1], encoding="utf-8"))))
