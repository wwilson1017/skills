"""Local protocol checks; never contacts Simple Sites or uses real credentials.

Run: python3 -m unittest discover -s tests -v
"""

import contextlib
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitesync', ROOT / 'skills/deck/tools/sitesync.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT, prefix='.deck-test-')
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / 'deck'
        self.folder.mkdir()
        (self.folder / 'index.html').write_text('<h1>Demo</h1>')
        self.link = Path(self.temp.name) / 'config/link'
        self.link_patch = patch.object(sync, 'link_file', return_value=self.link)
        self.link_patch.start()
        self.addCleanup(self.link_patch.stop)
        sync.SECRETS.clear()
        self.uploaded, self.calls, self.refs = {}, [], set()
        self.mode = ''
        self.polls = self.active = self.peak = 0
        self.lock = threading.Lock()
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def answer(self, result, code=200):
                body = json.dumps(result).encode()
                self.send_response(code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                if self.path == '/api/connect':
                    self.answer({'user_code': 'ABCD-EFGH', 'device_token': 'device-secret-123',
                                 'url': owner.base + '/connect?code=ABCD-EFGH',
                                 'interval': 0.01, 'expires_in': 0.025 if owner.mode == 'expiry' else 10})
                elif self.path == '/api/connect/poll':
                    owner.assertEqual(body, {'device_token': 'device-secret-123'})
                    owner.polls += 1
                    if owner.mode == '404':
                        self.answer({'detail': 'Expired device-secret-123'}, 404)
                    elif owner.polls == 1 or owner.mode == 'expiry':
                        self.answer({'status': 'pending'})
                    else:
                        self.answer({'status': 'approved', 'agent_url': owner.agent})
                else:
                    query = parse_qs(urlsplit(self.path).query)
                    owner.assertEqual(query['cmd'], ['SITE_SYNC'])
                    owner.assertEqual(query['keep'], ['1'])
                    owner.assertEqual(set(body), {'manifest', 'name', 'client_ref'})
                    owner.calls.append((query, body))
                    owner.refs.add(body['client_ref'])
                    if owner.mode == 'error':
                        self.answer({'error': 'Too big', 'detail': 'Limit is 10 MB; ' + owner.agent}, 413)
                        return
                    site = {'id': 42, 'address': owner.base + '/public/demo/'}
                    missing = {f['sha256'] for f in body['manifest']} - owner.uploaded.keys()
                    if missing or owner.mode == 'loop':
                        self.answer({'status': 'upload', 'site': site, 'missing': [
                            {'sha256': sha, 'put': {'url': owner.base + '/put/' + sha,
                                                  'headers': {'X-Upload-Check': sha}}}
                            for sha in sorted(missing)]})
                    else:
                        self.answer({'status': 'published', 'site': site})

            def do_PUT(self):
                sha = self.path.rsplit('/', 1)[1]
                owner.assertEqual(self.headers['X-Upload-Check'], sha)
                data = self.rfile.read(int(self.headers['Content-Length']))
                owner.assertEqual(hashlib.sha256(data).hexdigest(), sha)
                with owner.lock:
                    owner.active += 1
                    owner.peak = max(owner.peak, owner.active)
                time.sleep(0.03)
                with owner.lock:
                    owner.uploaded[sha] = data
                    owner.active -= 1
                self.answer({})

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.base = f'http://127.0.0.1:{self.server.server_port}'
        self.agent = self.base + '/agent/agent-secret-0123456789?keep=1'
        self.env_patch = patch.dict(os.environ, {'SIMPLESITES_URL': self.base})
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def test_connect_saves_private_link(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            sync.connect()
        self.assertIn('/connect?code=ABCD-EFGH', output.getvalue())
        self.assertNotIn(self.agent, output.getvalue())
        self.assertNotIn('device-secret', output.getvalue())
        self.assertEqual(self.link.read_text().strip(), self.agent)
        self.assertEqual(stat.S_IMODE(self.link.stat().st_mode), 0o600)
        self.link.chmod(0o644)
        sync.save_link(self.agent)
        self.assertEqual(stat.S_IMODE(self.link.stat().st_mode), 0o600)

    def test_connect_404_and_expiry(self):
        for mode in ('404', 'expiry'):
            self.mode, self.polls = mode, 0
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(sync.SyncError, 'connect again'):
                sync.connect()
            self.assertFalse(self.link.exists())

    def test_publish_retry_update_and_parallel_uploads(self):
        sync.save_link(self.agent)
        for i in range(12):
            (self.folder / f'asset-{i}.txt').write_text(str(i))
        (self.folder / '.secret').write_text('hidden')
        (self.folder / '.hidden').mkdir()
        (self.folder / '.hidden/file').write_text('hidden')
        (self.folder / 'duplicate.txt').write_text('0')
        with contextlib.redirect_stdout(io.StringIO()) as output:
            sync.sync(self.folder, 'demo')
        self.assertIn('Site id: 42', output.getvalue())
        self.assertNotIn(self.agent, output.getvalue())
        self.assertEqual(len(self.uploaded), 13)
        self.assertGreater(self.peak, 1)
        self.assertLessEqual(self.peak, 8)
        self.assertEqual(len(self.calls[0][1]['manifest']), 14)
        self.assertEqual(self.calls[0][1], self.calls[1][1])
        with contextlib.redirect_stdout(io.StringIO()):
            sync.sync(self.folder, 'demo')
        self.assertEqual(len(self.calls), 3)  # No uploads on an unchanged retry.
        (self.folder / 'index.html').write_text('<h1>Changed</h1>')
        (self.folder / 'duplicate.txt').unlink()
        with contextlib.redirect_stdout(io.StringIO()):
            sync.sync(self.folder, site_id=42)
        self.assertEqual(len(self.refs), 1)
        self.assertEqual(self.calls[-1][0]['id'], ['42'])
        self.assertIsNone(self.calls[-1][1]['name'])
        self.assertEqual(len(self.calls[-1][1]['manifest']), 13)
        self.assertEqual(len(self.uploaded), 14)

    def test_errors_keep_server_detail_but_redact_credentials(self):
        sync.save_link(self.agent)
        self.mode = 'error'
        with self.assertRaises(sync.SyncError) as raised:
            sync.sync(self.folder, 'demo')
        message = str(raised.exception)
        self.assertIn('HTTP 413', message)
        self.assertIn('Too big; Limit is 10 MB', message)
        self.assertNotIn('agent-secret', message)
        self.assertNotIn(self.agent, message)

    def test_round_limit(self):
        sync.save_link(self.agent)
        self.mode = 'loop'
        with self.assertRaisesRegex(sync.SyncError, 'after 5 rounds'):
            sync.sync(self.folder, 'demo')
        self.assertEqual(len(self.calls), 5)

    def test_require_index_and_reject_symlinks(self):
        (self.folder / 'index.html').unlink()
        with self.assertRaisesRegex(sync.SyncError, 'index.html'):
            sync.describe(self.folder)
        (self.folder / 'index.html').write_text('demo')
        (self.folder / 'outside').symlink_to(self.link)
        with self.assertRaisesRegex(sync.SyncError, 'Symlinks'):
            sync.describe(self.folder)


if __name__ == '__main__':
    unittest.main()
