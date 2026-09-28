#!/usr/bin/env python3
"""Tell IndexNow engines (Bing, and through Bing: Copilot and ChatGPT search's
Microsoft index; also Yandex, Seznam, Naver, Yep) that pages changed.

Run AFTER the deploy is live, never before (they fetch the page straight away):
    python ops/seo/indexnow.py                 # every URL in sitemap.xml
    python ops/seo/indexnow.py /faq /plans     # only these paths

The key file must be live at https://www.snypd.store/<KEY>.txt containing only
the key; it proves we own the host. Google does not use IndexNow - use Search
Console's URL inspection for Google.
Protocol: https://www.indexnow.org/documentation (200 or 202 = accepted).
"""
import json, os, re, sys, urllib.error, urllib.request

KEY = 'b3e58593b1181964d61c5eb9969c6217'
HOST = 'www.snypd.store'
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    if len(sys.argv) > 1:
        urls = ['https://' + HOST + (p if p.startswith('/') else '/' + p) for p in sys.argv[1:]]
    else:
        sm = open(os.path.join(ROOT, 'sitemap.xml'), encoding='utf-8').read()
        urls = re.findall(r'<loc>([^<]+)</loc>', sm)
    key_url = f'https://{HOST}/{KEY}.txt'
    live_key = urllib.request.urlopen(key_url, timeout=20).read().decode('utf-8').strip()
    if live_key != KEY:
        sys.exit(f'{key_url} does not serve the key yet; deploy first')
    body = json.dumps({'host': HOST, 'key': KEY, 'keyLocation': key_url, 'urlList': urls}).encode('utf-8')
    req = urllib.request.Request('https://api.indexnow.org/indexnow', data=body, method='POST',
                                 headers={'Content-Type': 'application/json; charset=utf-8'})
    try:
        r = urllib.request.urlopen(req, timeout=30)
        print(f'IndexNow HTTP {r.status} for {len(urls)} URLs')
    except urllib.error.HTTPError as e:
        sys.exit(f'IndexNow HTTP {e.code}: {e.read().decode("utf-8", "replace")[:300]}')
    for u in urls:
        print('  ', u)


if __name__ == '__main__':
    main()
