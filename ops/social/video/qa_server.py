"""Local-only static server for driving the real dashboard against ops/qa_mock.js.
Serves the site repo, except /dashboard.qa.html (dashboard.html with the Supabase CDN tag
swapped for qa_mock.js, built in memory) and /qa_mock.js (ops/qa_mock.js). Nothing is written
into the repo."""
import http.server
import os
import socketserver

REPO = r'C:\Users\Tanus\.gemini\antigravity\scratch\snypd-website'
CDN = '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>'


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
            return self._send(open(os.path.join(REPO, 'ops', 'qa_mock.js'), 'rb').read(), 'application/javascript')
        return super().do_GET()

    def log_message(self, *a):
        pass


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('127.0.0.1', 8900), H) as s:
    s.serve_forever()
