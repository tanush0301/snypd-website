"""Deliberate breaks of the no-alert-channel notice: each must make ops/test_no_channel.cjs fail.
Run from the repo root, alone and without a time limit: python ops/test_no_channel_mutations.py
Edits dashboard.html in place and always restores it.
"""
import subprocess
import sys

PATH = "dashboard.html"
raw = open(PATH, "rb").read()
src = raw.decode("utf-8")

MUTS = [
    ("Free accounts see it too", "const always = effectivePlan !== 'free' ||", "const always = true ||"),
    ("a running trial is not counted", "const always = effectivePlan !== 'free' ||\r\n          (profile.free_trial_started_at && trialEndMs(profile) > Date.now()) || bonusActive(profile);", "const always = effectivePlan !== 'free';"),
    ("devices on the account ignored", "Array.isArray(body.devices) && body.devices.length === 0);", "Array.isArray(body.devices));"),
    ("asks only once", "if (none) { await new Promise(r => setTimeout(r, 4000)); none = await noDevices(); }", ""),
    ("a status answer without a device list counts as no devices", "Array.isArray(body.devices) && body.devices.length === 0", "!(body.devices && body.devices.length)"),
    ("a failed status call counts as no devices", "const body = res.ok ? await res.json() : null;", "const body = res.ok ? await res.json() : { ready: true, devices: [] };"),
    ("Discord link ignored", "if (dc && !dc.error && !(dc.data && dc.data.enabled)) show = true;", "show = true;"),
    ("hidden for 30 days instead of one", "localStorage.setItem(NO_CHANNEL_KEY, String(Date.now() + 86400000))", "localStorage.setItem(NO_CHANNEL_KEY, String(Date.now() + 30 * 86400000))"),
    ("hide choice forgotten", "function noChannelHidden() { try { return Number(localStorage.getItem(NO_CHANNEL_KEY) || 0) > Date.now(); } catch (e) { return false; } }", "function noChannelHidden() { return false; }"),
    ("alerts button does nothing", "if (ncAlerts) ncAlerts.addEventListener('click', () => { window.SNYPD.showAlertsStep(); });", ""),
    ("Discord button does not open Profile", "const tab = document.querySelector('[data-view=\"profile\"]'); if (tab) tab.click();", ""),
    ("per-device card shown beside the notice", "        if (show && setupCard) setupCard.style.display = 'none';\r\n", ""),
]

caught = 0
try:
    for name, a, b in MUTS:
        if src.count(a) != 1:
            print("ANCHOR NOT UNIQUE (%d) - %s" % (src.count(a), name))
            continue
        open(PATH, "wb").write(src.replace(a, b).encode("utf-8"))
        r = subprocess.run(["node", "ops/test_no_channel.cjs"], capture_output=True, text=True)
        bad = r.returncode != 0
        caught += bad
        print(("caught" if bad else "MISSED"), "-", name, flush=True)
finally:
    open(PATH, "wb").write(raw)

print("caught %d of %d" % (caught, len(MUTS)))
sys.exit(0 if caught == len(MUTS) else 1)
