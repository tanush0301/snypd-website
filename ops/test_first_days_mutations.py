"""Deliberate breaks of the first-days layout: each must make ops/test_first_days.cjs fail.
Run from the repo root: python ops/test_first_days_mutations.py
Edits dashboard.html in place and always restores it.
"""
import subprocess
import sys

PATH = "dashboard.html"
raw = open(PATH, "rb").read()
src = raw.decode("utf-8")

MUTS = [
    ("every account treated as new",
     "Date.now() - joinedMs < 3 * 86400000", "Date.now() - joinedMs < 3000 * 86400000"),
    ("no account treated as new",
     "Date.now() - joinedMs < 3 * 86400000", "Date.now() - joinedMs < 0"),
    ("flag not set",
     "document.body.setAttribute('data-first-days', '1');", ""),
    ("cards not moved",
     "if (el && anchor && anchor.parentNode) anchor.parentNode.insertBefore(el, anchor);", ""),
    ("claim hint left above the feed",
     "['email-optin-card', 'dc-join', 'claim-hint'].forEach(id => {",
     "['email-optin-card', 'dc-join'].forEach(id => {"),
    ("email card left above the feed",
     "['email-optin-card', 'dc-join', 'claim-hint'].forEach(id => {",
     "['dc-join', 'claim-hint'].forEach(id => {"),
    ("alerts card not compact on phones",
     "body[data-first-days] #alerts-setup-card .elite-banner__text { display: none; }", ""),
    ("alerts card compact on every screen",
     "@media (max-width: 600px) {\r\n  body[data-first-days] #alerts-setup-card { padding",
     "@media (max-width: 6000px) {\r\n  body[data-first-days] #alerts-setup-card { padding"),
]

caught = 0
try:
    for name, a, b in MUTS:
        assert src.count(a) == 1, "anchor not unique: " + name
        open(PATH, "wb").write(src.replace(a, b).encode("utf-8"))
        r = subprocess.run(["node", "ops/test_first_days.cjs"], capture_output=True, text=True)
        bad = r.returncode != 0
        caught += bad
        print(("caught" if bad else "MISSED"), "-", name)
finally:
    open(PATH, "wb").write(raw)

print("caught %d of %d" % (caught, len(MUTS)))
sys.exit(0 if caught == len(MUTS) else 1)
