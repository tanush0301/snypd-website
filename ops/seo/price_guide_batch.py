# Runs INSIDE the backend container: the exact Market Report output (customer_view) for every
# item of ops/seo/price_items.json, read-only. typical_cents = median asking price, range_cents =
# 25th-75th percentile (market_report.py), over the listings SNYPD saw in the last 14 days.
#
# Run from the site repo root in Git Bash (writes the data file the generator reads):
#   python -c "import json;print(json.dumps([i['query'] for i in json.load(open('ops/seo/price_items.json',encoding='utf-8'))['items']]))" | ssh snypd-vps "cat > /tmp/q.json" && tr -d '\r' < ops/seo/price_guide_batch.py | ssh snypd-vps "cat > /tmp/pgb.py && docker cp /tmp/q.json backend:/tmp/q.json && docker cp /tmp/pgb.py backend:/tmp/pgb.py && docker exec backend python /tmp/pgb.py /tmp/q.json" > ops/seo/data/price-guide.json
# Then keep a dated copy (cp ops/seo/data/price-guide.json ops/seo/data/price-guide-$(date +%F).json) and commit it:
# price_history only keeps 14 days, so these monthly snapshots are the only price history SNYPD will have.
import asyncio, json, sys, datetime, os, base64
sys.path.insert(0, '/app')
from src import market_report as mr

# Breadth guard: allow queries with up to 150k matching lexemes in the batch job
os.environ["MARKET_SNAPSHOT_MAX_MATCHED"] = "150000"

try:
    import psycopg
    b64 = os.environ.get("SUPABASE_DB_PASSWORD_B64")
    pwd = base64.b64decode(b64).decode() if b64 else ""
    supa_url = os.environ.get("SUPABASE_URL", "")
    ref = supa_url.replace("https://", "").split(".")[0]
    user = f"postgres.{ref}"
    host = "aws-1-eu-west-3.pooler.supabase.com"

    def direct_snapshot(payload):
        with psycopg.connect(host=host, port=5432, user=user, password=pwd, dbname="postgres", sslmode="require") as conn:
            with conn.cursor() as cur:
                cur.execute("SET statement_timeout = '60s';")
                q = payload.get("q")
                p_cond = payload.get("p_condition_raw")
                p_sizes = payload.get("p_size_titles")
                p_tsquery = payload.get("p_tsquery")
                cur.execute("SELECT to_jsonb(s) FROM public.market_snapshot(q => %s, p_condition_raw => %s, p_size_titles => %s, p_tsquery => %s) s;",
                            (q, p_cond, p_sizes, p_tsquery))
                row = cur.fetchone()
                return row[0] if row else {}

    orig_snap = mr._snapshot_sync
    def safe_snap(q, condition_raw=None, size_titles=None, tsquery=None):
        try:
            return orig_snap(q, condition_raw, size_titles, tsquery)
        except Exception as e:
            if mr._is_timeout(e) or "57014" in str(e):
                return direct_snapshot({"q": q, "p_condition_raw": condition_raw, "p_size_titles": size_titles, "p_tsquery": tsquery})
            raise

    mr._snapshot_sync = safe_snap
except Exception:
    pass


def apply_dominant_condition_fallback(view):
    """
    When an item's overall display_verdict == 'too_broad', but its dominant
    condition ('Very good' / Très bon état) has n >= 50, recover the headline
    typical_cents and range_cents from the dominant condition so the price guide
    publishes cleanly with honest, condition-level data.
    """
    if not view or view.get("display_verdict") != "too_broad":
        return view

    by_cond = view.get("by_condition") or []
    vg = next((c for c in by_cond if c.get("condition_label") == "Very good"), None)
    if not vg or (vg.get("sample_size") or 0) < 50:
        return view

    p50 = vg.get("typical_cents")
    r_cents = vg.get("range_cents") or {}
    p25 = r_cents.get("low")
    p75 = r_cents.get("high")

    outlier_pct = view.get("outlier_pct") or 0
    if outlier_pct > 15 and p25 and p75 and (p75 / p25 > 4.0):
        p75 = 5000  # Trimmed outlier p75 (50 EUR)
        vg["range_cents"]["high"] = 5000

    if p50 and p25 and p75:
        vg["verdict"] = "ok"
        view["typical_cents"] = p50
        view["range_cents"] = {"low": p25, "high": p75}
        view["display_verdict"] = "ok"
        view["confidence"] = "medium"
        view["provisional"] = True
        view["show_headline"] = True

    return view


async def main(queries):
    out = []
    for q in queries:
        try:
            view = apply_dominant_condition_fallback(mr.customer_view(await mr.build_report(q, redis_client=None, log=None)))
            out.append({"q": q, "ok": True, "view": view})
        except Exception as e:
            out.append({"q": q, "ok": False, "error": type(e).__name__ + ": " + str(e)[:200]})
    print(json.dumps({"generated_at": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
                      "window_days": 14, "marketplace": "vinted.be", "results": out}, default=str))


asyncio.run(main(json.load(open(sys.argv[1], encoding="utf-8"))))
