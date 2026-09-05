#!/usr/bin/env python3
"""Local site and single-image renderer. No repository writes or publishing."""
import argparse
import json
import secrets
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, unquote

from tsil_social import reading_data, story_html, post_html, approved_og_html, screenshot, ASCII_STYLES

ROOT = Path(__file__).resolve().parents[1]
RENDER_LOCK = threading.Lock()
TOKEN = secrets.token_urlsafe(32)


def render_one(slug, kind, lang, variant, output):
    items = json.loads((ROOT / 'data/readings.json').read_text())
    item = next((x for x in items if x['slug'] == slug), None)
    if item is None or kind not in ('story', 'post', 'link') or lang not in ('es', 'en'):
        raise ValueError('Invalid reading, format or language')
    if type(variant) is not int or not 0 <= variant < len(ASCII_STYLES):
        raise ValueError('Invalid variant')
    page = (ROOT / 'readings' / slug / 'index.html').read_text()
    d = reading_data(item, page)
    if kind == 'story':
        markup, size = story_html(d, lang, ASCII_STYLES[variant], render=True), (1080, 1920)
    elif kind == 'post':
        markup, size = post_html(d, lang, 'dense', render=True), (1080, 1350)
    else:
        markup, size = approved_og_html(d), (1200, 630)
    screenshot(markup, output, size)


class Handler(SimpleHTTPRequestHandler):
    def allowed_host(self):
        return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

    def json_response(self, code, value):
        body = json.dumps(value).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.allowed_host():
            return self.send_error(403)
        if self.path == '/api/local':
            return self.json_response(200, {'token': TOKEN})
        # Serve only the public site, never Git, backups or local scripts.
        path = unquote(urlsplit(self.path).path)
        target = (ROOT / path.lstrip('/')).resolve()
        if ROOT not in target.parents and target != ROOT:
            return self.send_error(403)
        rel = target.relative_to(ROOT)
        if any(part.startswith('.') for part in rel.parts):
            return self.send_error(404)
        if rel.parts and rel.parts[0] not in ('readings', 'data', 'assets', 'index.html', 'robots.txt', 'sitemap.xml', 'The Somatic Image Lab.png'):
            return self.send_error(404)
        if target.is_dir() and not (target / 'index.html').exists():
            return self.send_error(404)
        super().do_GET()

    def do_HEAD(self):
        self.send_error(405)

    def do_POST(self):
        origin = f'http://127.0.0.1:{self.server.server_port}'
        if not self.allowed_host() or self.headers.get('Origin') != origin or self.headers.get('X-TSIL-Token') != TOKEN:
            return self.json_response(403, {'error': 'Forbidden'})
        if self.path != '/api/render':
            return self.json_response(404, {'error': 'Not found'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 4096:
                raise ValueError('Invalid request size')
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError('Invalid request')
        except (ValueError, TypeError):
            return self.json_response(400, {'error': 'Invalid request'})
        if not RENDER_LOCK.acquire(blocking=False):
            return self.json_response(409, {'error': 'Renderer busy'})
        try:
            with tempfile.TemporaryDirectory(prefix='tsil-single-') as folder:
                output = Path(folder) / 'image.png'
                render_one(data.get('slug'), data.get('format'), data.get('lang'), data.get('variant', 0), output)
                image = output.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(image)))
            self.end_headers()
            self.wfile.write(image)
        except ValueError:
            self.json_response(400, {'error': 'Invalid selection'})
        except Exception as exc:
            print('Render error:', exc, flush=True)
            self.json_response(500, {'error': 'Render failed'})
        finally:
            RENDER_LOCK.release()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8001)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(Handler, directory=str(ROOT)))
    print(f'TSIL local: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
