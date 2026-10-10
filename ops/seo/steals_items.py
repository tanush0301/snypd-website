"""Print the published price-guide items as [{"slug", "query"}] for steals_batch.py (same 38 items and the
same publication rule as the guide: gen_price_guide.PUB)."""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_price_guide  # noqa: E402

print(json.dumps([{'slug': it['slug'], 'query': it['query']} for it in gen_price_guide.PUB], ensure_ascii=False))
