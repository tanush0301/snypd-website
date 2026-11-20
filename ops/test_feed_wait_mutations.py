"""Deliberate breaks of the dashboard's live feed wait: each must make ops/test_feed_wait.cjs fail.
Run from the repo root: python ops/test_feed_wait_mutations.py
Edits dashboard.html in place and always restores it.
"""
import subprocess
import sys

PATH = "dashboard.html"
raw = open(PATH, "rb").read()
src = raw.decode("utf-8")

MUTS = [
    ("loop never started", "    feedWaitLoop().catch(() => {});\r\n", ""),
    ("no reload on a change", "                await loadAds();\r\n              }\r\n              if (j && typeof j.retry", "              }\r\n              if (j && typeof j.retry"),
    ("reloads at start for an old marker", "if (j && j.changed === true && !first && running", "if (j && j.changed === true && running"),
    ("marker never remembered", "if (j && typeof j.tick === 'number' && j.tick > (feedWaitTick || 0)) feedWaitTick = j.tick;", ""),
    ("no login sent", "{ headers: { Authorization: 'Bearer ' + t } });\r\n            if (!res.ok) { pause = res.status === 404", "{});\r\n            if (!res.ok) { pause = res.status === 404"),
    ("no pause after a 404 or an error", "if (!res.ok) { pause = res.status === 404 ? 600000 : 60000; }", "if (!res.ok) { pause = 200; }"),
    ("retry answer ignored", "if (j && typeof j.retry === 'number') pause = Math.max(5, Math.min(600, j.retry)) * 1000;\r\n              else if", "if (false) pause = 0;\r\n              else if"),
    ("always asks since 0", "FEED_WAIT_URL + '?since=' + (feedWaitTick || 0)", "FEED_WAIT_URL + '?since=0'"),
]

caught = 0
try:
    for name, a, b in MUTS:
        assert src.count(a) == 1, "anchor not unique: " + name
        open(PATH, "wb").write(src.replace(a, b).encode("utf-8"))
        try:
            r = subprocess.run(["node", "ops/test_feed_wait.cjs"], capture_output=True, text=True, timeout=240)
            bad = r.returncode != 0
        except subprocess.TimeoutExpired:
            bad = True
        caught += bad
        print(("caught" if bad else "MISSED"), "-", name)
finally:
    open(PATH, "wb").write(raw)

print("caught %d of %d" % (caught, len(MUTS)))
sys.exit(0 if caught == len(MUTS) else 1)
