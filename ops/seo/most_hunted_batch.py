# Runs INSIDE the backend container, read-only: the monthly "Most hunted on Vinted" snapshot (website outreach/46).
# Counts the ACTIVE SNYPD hunts by brand / model, as distinct users, with the same word lists the Market board's
# "What hunters watch" and the hunt coach use (backend market_board.HUNTER_BRANDS, hunt_coach.MODELS). Never the
# search words themselves. Users who left hunter statistics (users.hunter_stats_opt_out, migration 079) and test
# accounts are not counted. Rows under MIN_USERS distinct users are dropped here, before anything leaves the box,
# and a typical max price is given only from MIN_USERS users who set one on a euro site (the median of each
# user's own median max).
#
# Run from the site repo root in Git Bash (writes the dated data file the generator reads):
#   tr -d '\r' < ops/seo/most_hunted_batch.py | ssh snypd-vps "cat > /tmp/mhb.py && docker cp /tmp/mhb.py backend:/tmp/mhb.py && docker exec backend python /tmp/mhb.py" > ops/seo/data/most-hunted-$(date -u +%F).json
# Then add the file to EDITIONS in ops/seo/gen_most_hunted.py and regenerate.
import datetime, json, statistics, sys
sys.path.insert(0, '/app')
from src import hunt_coach as hc
from src import market_board as mb
from src.database import pg_direct

MIN_USERS = 10   # public bar (Tanush, 7 Nov 2026); the app uses 5

SQL = ("select s.user_id::text as u, s.vinted_url from public.user_searches s join public.users u on u.id = s.user_id"
       " where s.is_active and not coalesce(u.hunter_stats_opt_out, false) and not coalesce(u.is_test_account, false)")


def main():
    ok, rows = pg_direct.run("most_hunted", lambda c: pg_direct.fetch_dicts(c, SQL))
    if not ok:
        raise SystemExit("database read failed: %s" % (rows,))
    names = [(b, b, b, al) for b, al in mb.HUNTER_BRANDS] + [(en, en, fr, al) for _k, en, fr, al in hc.MODELS]
    users, caps, sites = {}, {}, {}
    hunters = set()
    for r in rows:
        hunters.add(r["u"])
        h = hc.parse_hunt(r["vinted_url"])
        sites.setdefault(h["host"], set()).add(r["u"])
        for key, _en, _fr, al in names:
            if any(hc._has(h["words"], a) for a in al):
                users.setdefault(key, set()).add(r["u"])
                if h["currency"] == "EUR" and h["price_to"]:
                    caps.setdefault(key, {}).setdefault(r["u"], []).append(h["price_to"])
    out = []
    for key, en, fr, _al in names:
        n = len(users.get(key, ()))
        if n < MIN_USERS:
            continue
        per_user = [statistics.median(v) for v in caps.get(key, {}).values()]
        typical = round(statistics.median(per_user) * 2) / 2 if len(per_user) >= MIN_USERS else None
        out.append({"key": key, "name_en": en, "name_fr": fr[:1].upper() + fr[1:],
                    "type": "model" if key in {m[1] for m in hc.MODELS} else "brand",
                    "hunters": n, "with_max_eur": len(per_user), "typical_max_eur": typical})
    out.sort(key=lambda x: (-x["hunters"], x["key"]))
    print(json.dumps({"generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                      "min_users": MIN_USERS, "active_hunts": len(rows), "hunters": len(hunters),
                      # where hunters hunt: Vinted sites with MIN_USERS+ distinct users only
                      "sites": dict(sorted(((k, len(v)) for k, v in sites.items() if k and len(v) >= MIN_USERS), key=lambda x: -x[1])),
                      "rows": out},
                     ensure_ascii=False, indent=1))


main()
