"""Deliberate breaks of the dashboard's flood offer link: each must make ops/test_flood_offer.cjs fail.
Run from the repo root: python ops/test_flood_offer_mutations.py
Edits dashboard.html in place and always restores it.
"""
import subprocess
import sys

PATH = "dashboard.html"
raw = open(PATH, "rb").read()
src = raw.decode("utf-8")

MUTS = [
    ("offer never checked", "      if (!floodChecked) await noteFloodOffer().catch(e => console.error('SNYPD: flood offer failed', e));\r\n", ""),
    ("parameter left in the address", "        q.delete('flood');\r\n", ""),
    ("other parameters dropped", "location.pathname + (qs ? '?' + qs : '') + location.hash);\r\n      }\r\n    } catch (e) { id = null; }",
     "location.pathname + location.hash);\r\n      }\r\n    } catch (e) { id = null; }"),
    ("shown for a Calm or cheap search", "    if (!row || row.is_active !== true || (row.push_mode || 'every') !== 'every') return;\r\n",
     "    if (!row) return;\r\n"),
    ("shown for an unknown id", "    const row = rows.find(r => String(r.id) === String(id));\r\n", "    const row = rows.find(r => String(r.id) === String(id)) || rows[0];\r\n"),
    ("buttons act on no search", "    broadHunt = row;\r\n    broadSig = savedSearchSignature(row.vinted_url);", "    broadHunt = null;\r\n    broadSig = savedSearchSignature(row.vinted_url);"),
    ("Keep not remembered", "    broadHunt = row;\r\n    broadSig = savedSearchSignature(row.vinted_url);", "    broadHunt = row;\r\n    broadSig = null;"),
    ("cheap-only offered on Free", "    coachButtons(free ? ['broad-hunt-calm', 'broad-hunt-edit', 'broad-hunt-keep']", "    coachButtons(false ? ['broad-hunt-calm', 'broad-hunt-edit', 'broad-hunt-keep']"),
    ("cheap sentence on Free", "    if (!free) sentences.push('Or get an alert only for the cheap finds.');", "    sentences.push('Or get an alert only for the cheap finds.');"),
    ("title not set", "    title.textContent = 'This search is very busy';\r\n", ""),
    ("card kind not set", "    card.dataset.kind = 'flood';\r\n", ""),
    ("broad card replaces the offer", "    if (floodShown) return;   // the flood offer has the card\r\n    if (!card || !text || !feed", "    if (!card || !text || !feed"),
    ("Calm-all button left visible", "    if (all) all.style.display = 'none';\r\n", "    if (all) all.style.display = '';\r\n"),
]

caught = 0
try:
    for name, a, b in MUTS:
        assert src.count(a) == 1, "anchor not unique: " + name
        open(PATH, "wb").write(src.replace(a, b).encode("utf-8"))
        try:
            r = subprocess.run(["node", "ops/test_flood_offer.cjs"], capture_output=True, text=True, timeout=300)
            bad = r.returncode != 0
        except subprocess.TimeoutExpired:
            bad = True
        caught += bad
        print(("caught" if bad else "MISSED"), "-", name)
finally:
    open(PATH, "wb").write(raw)

print("caught %d of %d" % (caught, len(MUTS)))
sys.exit(0 if caught == len(MUTS) else 1)
