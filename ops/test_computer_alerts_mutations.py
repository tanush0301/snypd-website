"""Deliberate breaks of the new-listing signals: each must make ops/test_computer_alerts.cjs fail.
Run from the repo root: python ops/test_computer_alerts_mutations.py
Edits dashboard.html in place and always restores it.
"""
import subprocess
import sys

PATH = "dashboard.html"
raw = open(PATH, "rb").read()
src = raw.decode("utf-8")

MUTS = [
    ("signal never fired",
     "    feedSignal(unseenRows.filter(r => !(uploadedTimeMs(r) < prevOldestMs)).length);\r\n", ""),
    ("big batch compared with the cards after the refresh",
     "feedSignal(unseenRows.filter(r => !(uploadedTimeMs(r) < prevOldestMs)).length);",
     "feedSignal(unseenRows.filter(r => !(uploadedTimeMs(r) < Math.min(...rows.map(uploadedTimeMs)) + 1)).length);"),
    ("title counts while in front", "      if (!front) {\r\n        feedUnseen += n;", "      if (true) {\r\n        feedUnseen += n;"),
    ("title never counts", "      if (!front) {\r\n        feedUnseen += n;", "      if (false) {\r\n        feedUnseen += n;"),
    ("no 99+ cap", "(feedUnseen > 99 ? '99+' : feedUnseen)", "(feedUnseen)"),
    ("focus does not reset the title", "  window.addEventListener('focus', feedClearUnseen);\r\n", ""),
    ("no sound throttle", "Date.now() - feedLastBeep < 10000", "Date.now() - feedLastBeep < 0"),
    ("sound ignores the switch", "if (!feedSoundOn() || Date.now()", "if (Date.now()"),
    ("switch choice not stored", "localStorage.setItem(FEED_SOUND_KEY, on ? 'on' : 'off');", ""),
    ("no test sound when switched on", "if (on) { feedLastBeep = 0; feedBeep(); }", ""),
    ("notice never hides", "feedNoteTimer = setTimeout(() => { note.hidden = true; }, 5000);", ""),
    ("notice always plural", "n === 1 ? '1 new listing' : n + ' new listings'", "n + ' new listings'"),
    ("sound off by default", "localStorage.getItem(FEED_SOUND_KEY) !== 'off'", "localStorage.getItem(FEED_SOUND_KEY) === 'on'"),
]

caught = 0
try:
    for name, a, b in MUTS:
        assert src.count(a) == 1, "anchor not unique: " + name
        open(PATH, "wb").write(src.replace(a, b).encode("utf-8"))
        r = subprocess.run(["node", "ops/test_computer_alerts.cjs"], capture_output=True, text=True)
        bad = r.returncode != 0
        caught += bad
        print(("caught" if bad else "MISSED"), "-", name)
finally:
    open(PATH, "wb").write(raw)

print("caught %d of %d" % (caught, len(MUTS)))
sys.exit(0 if caught == len(MUTS) else 1)
