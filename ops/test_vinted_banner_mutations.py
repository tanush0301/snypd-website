"""Deliberate breaks of the "Can't reach Vinted" rule: each must make ops/test_vinted_banner.cjs fail.
Run from the repo root: python ops/test_vinted_banner_mutations.py
Edits dashboard.html in place and always restores it.
"""
import subprocess
import sys

PATH = "dashboard.html"
raw = open(PATH, "rb").read()
src = raw.decode("utf-8")

MUTS = [
    ("last find used again", "if (hbKnowsChecks) {", "if (false) {"),
    ("never stale on last_ok",
     "if (hbLastOkMs != null) vintedStale = (Date.now() - hbLastOkMs) > limitMs;",
     "if (hbLastOkMs != null) vintedStale = false;"),
    ("no-answer rule dropped",
     "else if (hbNoAnswerSinceMs != null) vintedStale = (Date.now() - hbNoAnswerSinceMs) > limitMs;", ""),
    ("server clock trusted",
     "hbLastOkMs = Date.now() - Math.max(0, j.now - j.last_ok) * 1000;", "hbLastOkMs = j.last_ok * 1000;"),
    ("no fallback to the old rule",
     "if (!j || typeof j.searches !== 'number') { hbKnowsChecks = false; return; }",
     "if (!j) { hbKnowsChecks = false; return; }"),
    ("no-answer timer restarts each beat",
     "if (j.searches > 0) { if (hbNoAnswerSinceMs == null) hbNoAnswerSinceMs = Date.now(); }",
     "if (j.searches > 0) { hbNoAnswerSinceMs = Date.now(); }"),
    ("zero searches counted as no answer",
     "if (j.searches > 0) { if (hbNoAnswerSinceMs == null)", "if (j.searches >= 0) { if (hbNoAnswerSinceMs == null)"),
    ("answer does not clear no-answer", "      hbNoAnswerSinceMs = null;\r\n    } else {", "    } else {"),
]

caught = 0
try:
    for name, a, b in MUTS:
        assert src.count(a) == 1, "anchor not unique: " + name
        open(PATH, "wb").write(src.replace(a, b).encode("utf-8"))
        r = subprocess.run(["node", "ops/test_vinted_banner.cjs"], capture_output=True, text=True)
        bad = r.returncode != 0
        caught += bad
        print(("caught" if bad else "MISSED"), "-", name)
finally:
    open(PATH, "wb").write(raw)

print("caught %d of %d" % (caught, len(MUTS)))
sys.exit(0 if caught == len(MUTS) else 1)
