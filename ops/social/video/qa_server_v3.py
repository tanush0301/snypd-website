"""Local-only static server for the homepage product video (v3): same as qa_server.py, but serves
the checkout this file lives in (not a hard-wired path) on 127.0.0.1:8902.
/dashboard.qa.html = dashboard.html with the Supabase CDN tag swapped for /qa_mock.js, built in memory.
Nothing is written into the repo."""
import http.server
import os
import socketserver

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
CDN = '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>'
PORT = 8902


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=REPO, **k)

    def _send(self, body, ctype):
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/dashboard.qa.html':
            html = open(os.path.join(REPO, 'dashboard.html'), 'rb').read()
            assert CDN.encode() in html, 'Supabase CDN tag not found'
            return self._send(html.replace(CDN.encode(), b'<script src="/qa_mock.js"></script>'), 'text/html; charset=utf-8')
        if path == '/qa_mock.js':
            js = open(os.path.join(REPO, 'ops', 'qa_mock.js'), 'rb').read().decode('utf-8')
            # video only, in memory: the ?pr=1 listings get realistic titles, sizes and local photos
            old = ("title: 'Price check QA listing ' + i,", "brand_title: 'Ralph Lauren', size_title: 'M', status: 'Very good',", "content_source: 'search', image_url: '',")
            new = ("title: VT[i % VT.length][0],", "brand_title: VT[i % VT.length][3], size_title: VT[i % VT.length][1], status: 'Very good',",
                   "content_source: 'search', image_url: 'http://127.0.0.1:8902/assets/home/feed/' + VT[i % VT.length][2] + '.webp',")
            start = js.find(old[0])
            assert start >= 0 and js.count(old[0]) == 1, 'price-check listing block not found exactly once'
            head, block, tail = js[:start], js[start:start + 700], js[start + 700:]
            for o, n in zip(old, new):
                assert block.count(o) == 1, 'mock line not found exactly once in the block: ' + o
                block = block.replace(o, n)
            js = head + block + tail
            vt = ("var VT = [['Polo Ralph Lauren cable knit jumper', 'L', 'knit', 'Ralph Lauren'], ['Supreme hoodie navy', 'XXL', 'hoodie', 'Supreme'],"
                  " ['PlayStation 5 with controller', 'One size', 'console', 'Sony'], ['Jordan 1 Low Travis Scott', '43', 'sneaker', 'Jordan'],"
                  " ['Polo Ralph Lauren cable knit jumper', 'M', 'knit', 'Ralph Lauren']];" + chr(10))
            return self._send((vt + js).encode('utf-8'), 'application/javascript')
        return super().do_GET()

    def log_message(self, *a):
        pass


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('127.0.0.1', PORT), H) as s:
    print('serving', REPO, 'on', PORT, flush=True)
    s.serve_forever()
