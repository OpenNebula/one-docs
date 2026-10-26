"""Loopback-only HTTP API and static React bundle for a single offline review session."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json
import mimetypes
from pathlib import Path
import secrets
from urllib.parse import parse_qs, unquote, urlparse
import webbrowser

from .review import ReviewError, ReviewSession, _contained


UI_DIRECTORY = Path(__file__).resolve().parents[1] / 'review-ui' / 'dist'


def make_server(session, port=8765, ui_directory=UI_DIRECTORY):
    ui_directory = Path(ui_directory).resolve()
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            if args and str(args[1] if len(args) > 1 else '').startswith('5'):
                super().log_message(format, *args)

        def trusted(self):
            hosts = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
            if self.headers.get('Host') not in hosts:
                self.json_response(421, dict(error='Use the loopback review URL.'))
                return False
            origin = self.headers.get('Origin')
            if origin and origin not in {f'http://{h}' for h in hosts}:
                self.json_response(403, dict(error='Cross-origin review requests are not allowed.'))
                return False
            return True

        def send_bytes(self, status, data, content_type, extra=None):
            try:
                self.write_response(status, data, content_type, extra)
            except (BrokenPipeError, ConnectionResetError):
                # Navigation can cancel an in-flight image response.
                self.close_connection = True

        def write_response(self, status, data, content_type, extra=None):
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; object-src 'none'")
            if extra:
                for key, value in extra.items():
                    self.send_header(key, value)
            self.end_headers()
            self.wfile.write(data)

        def json_response(self, status, payload, extra=None):
            self.send_bytes(status, json.dumps(payload, allow_nan=False).encode(), 'application/json; charset=utf-8', extra)

        def do_GET(self):
            if not self.trusted():
                return
            url = urlparse(self.path)
            try:
                if url.path == '/api/review':
                    self.json_response(200, dict(session.view(), csrf_token=token))
                elif url.path == '/api/substitutions':
                    data = session._load_selections()
                    data['stale_selection_ids'] = session.view()['stale']
                    self.json_response(200, data, {'Content-Disposition': 'attachment; filename="substitutions.json"'})
                elif url.path.startswith('/api/images/'):
                    parts = url.path.split('/')
                    if len(parts) != 5:
                        raise ReviewError('Unknown image URL.')
                    path = session.image_path(parts[3], parts[4])
                    from PIL import Image
                    with Image.open(path) as image:
                        image = image.convert('RGBA')
                        if parse_qs(url.query).get('thumbnail') == ['1']:
                            image.thumbnail((760, 460))
                        output = BytesIO()
                        image.save(output, format='PNG')
                    self.send_bytes(200, output.getvalue(), 'image/png')
                elif url.path.startswith('/api/'):
                    self.json_response(404, dict(error='Unknown API endpoint.'))
                else:
                    name = unquote(url.path).lstrip('/') or 'index.html'
                    path = _contained(ui_directory, ui_directory / name)
                    if not path.is_file():
                        self.json_response(404, dict(error='Review UI not found; build review-ui with npm run build.'))
                        return
                    content_type = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
                    self.send_bytes(200, path.read_bytes(), content_type)
            except (OSError, ValueError, KeyError) as exc:
                self.json_response(409 if isinstance(exc, ReviewError) else 400, dict(error=str(exc)))

        def do_POST(self):
            if not self.trusted():
                return
            if not secrets.compare_digest(self.headers.get('X-Review-Token', ''), token):
                self.json_response(403, dict(error='Review token is missing or invalid.'))
                return
            try:
                if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                    raise ReviewError('Expected application/json.')
                length = int(self.headers.get('Content-Length', '0'))
                if length < 0 or length > 8192:
                    raise ReviewError('Request body is too large.')
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ReviewError('Expected a JSON object.')
                if self.path == '/api/substitutions':
                    data = session.nominate(body.get('id'), body.get('selected'), body.get('baseline_sha256'), body.get('candidate_sha256'))
                elif self.path == '/api/refresh':
                    data = session.refresh()
                elif self.path == '/api/clear':
                    data = session.clear()
                else:
                    self.json_response(404, dict(error='Unknown API endpoint.'))
                    return
                self.json_response(200, dict(data, csrf_token=token))
            except (OSError, ValueError, KeyError, TypeError) as exc:
                self.json_response(409, dict(error=str(exc)))

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def serve_review(repo_root, run_dir, inventory, replacement_root=None, manifest=None, port=8765, open_browser=True):
    if not 0 <= port <= 65535:
        raise ReviewError('Review port must be between 0 and 65535.')
    if not (UI_DIRECTORY / 'index.html').is_file():
        raise ReviewError('Build the React app first: cd tools/sunstone-screenshots/review-ui && npm install && npm run build')
    try:
        import PIL
        import skimage
    except ImportError as exc:
        raise ReviewError('Install the review dependencies: python3 -m pip install -r tools/sunstone-screenshots/requirements-review.txt') from exc
    print('Building review comparisons...', flush=True)
    session = ReviewSession(repo_root, run_dir, inventory, replacement_root, manifest)
    server = make_server(session, port)
    url = f'http://127.0.0.1:{server.server_port}'
    print(f'Sunstone screenshot review: {url}', flush=True)
    print(f'Substitution intentions: {session.selection_file}', flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
