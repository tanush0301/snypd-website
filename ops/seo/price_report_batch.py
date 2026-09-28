# Runs INSIDE the backend container: exact Market Report output (customer_view), read-only.
import asyncio, json, sys, datetime
sys.path.insert(0, '/app')
from src import market_report as mr

QUERIES = [
    "jordan 1 mid", "jordan 1 low", "jordan 4", "nike dunk low", "nike air force 1",
    "air max 90", "air max 95", "adidas samba", "adidas gazelle", "adidas campus",
    "new balance 550", "new balance 9060", "new balance 2002r", "salomon xt-6", "asics gel kayano",
    "yeezy 350", "stone island jumper", "carhartt detroit jacket", "arcteryx beta",
    "patagonia fleece", "the north face nuptse", "ralph lauren quarter zip",
]

async def main():
    out = []
    for q in QUERIES:
        try:
            rep = await mr.build_report(q, redis_client=None, log=None)
            cv = mr.customer_view(rep)
            out.append({"q": q, "ok": True, "view": cv})
        except Exception as e:
            out.append({"q": q, "ok": False, "error": type(e).__name__ + ": " + str(e)[:200]})
    print(json.dumps({"generated_at": datetime.datetime.utcnow().isoformat() + "Z", "results": out}, default=str))

asyncio.run(main())
