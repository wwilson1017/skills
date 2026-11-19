#!/usr/bin/env python3
"""Connect to Simple Sites and publish a static folder. Python standard library only."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit, unquote
from urllib.request import Request, urlopen


SECRETS = set()
ROUNDS = 5


class SyncError(Exception):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def remember(secret):
    SECRETS.add(secret)
    parts = urlsplit(secret)
    if parts.scheme:
        SECRETS.update(unquote(p) for p in parts.path.split('/') if len(p) >= 16)
        SECRETS.update(v for k, v in parse_qsl(parts.query)
                       if v and (len(v) >= 16 or k.lower() in {'token', 'key', 'secret', 'signature'}))


def safe(text):
    text = str(text)
    for secret in sorted(SECRETS, key=len, reverse=True):
        if secret:
            text = text.replace(secret, '[redacted]')
    text = re.sub(r'https?://[^\s<>"\']+', '[address withheld]', text)
    return ''.join(c for c in text if c.isprintable() or c in '\n\t')[:2000]


def detail(result):
    return '; '.join(safe(result[k]) for k in ('error', 'detail') if result.get(k)) or 'Request refused'


def request(url, *, body=None, method='POST', headers=None, timeout=300, as_json=True):
    try:
        with urlopen(Request(url, data=body, method=method, headers=headers or {}), timeout=timeout) as response:
            if not as_json:
                response.read()
                return None
            result = json.load(response)
    except HTTPError as exc:
        try:
            result = json.loads(exc.read(65536))
            message = detail(result) if isinstance(result, dict) else 'Request failed'
        except (ValueError, OSError):
            message = 'Request failed'
        finally:
            exc.close()
        raise SyncError(f'HTTP {exc.code}: {message}', exc.code) from None
    except (URLError, OSError, ValueError):
        raise SyncError('Network request failed or returned invalid JSON (address withheld)') from None
    if not isinstance(result, dict):
        raise SyncError('Expected a JSON object from the server')
    if result.get('ok') is False or result.get('error'):
        raise SyncError(detail(result))
    return result


def post(url, payload, **kwargs):
    return request(url, body=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'}, **kwargs)


def link_file():
    return Path.home() / '.config' / 'simplesites' / 'link'


def validate_url(url):
    parts = urlsplit(url)
    if parts.scheme not in ('http', 'https') or not parts.netloc:
        raise SyncError('Expected an HTTP(S) address (value withheld)')
    return parts


def save_link(link):
    validate_url(link)
    target = link_file()
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.link-', dir=target.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(link + '\n')
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)


def connect():
    base = os.environ.get('SIMPLESITES_URL', 'https://simplesites.app').rstrip('/')
    validate_url(base)
    result = post(base + '/api/connect', {})
    token = result['device_token']
    remember(token)
    interval, lifetime = float(result['interval']), float(result['expires_in'])
    if not all(math.isfinite(x) and x > 0 for x in (interval, lifetime)):
        raise SyncError('Invalid connection timing from the server')
    deadline = time.monotonic() + lifetime
    # This is the approval URL, never the agent link or device token.
    approval_url = result['url'].replace(token, '[redacted]')
    print(f"Open {approval_url}\nCode: {safe(result['user_code'])}\nApprove the connection in your browser.", flush=True)
    while time.monotonic() < deadline:
        time.sleep(min(interval, max(0, deadline - time.monotonic())))
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        try:
            result = post(base + '/api/connect/poll', {'device_token': token}, timeout=min(60, remaining))
        except SyncError as exc:
            if exc.status == 404:
                break
            raise
        if result.get('status') == 'approved':
            remember(result['agent_url'])
            save_link(result['agent_url'])
            print('Connected. Saved credentials to ~/.config/simplesites/link (mode 600).')
            return
        if result.get('status') != 'pending':
            raise SyncError('Unexpected connection status; run connect again')
    raise SyncError('Connection expired or is no longer available. Run connect again for a new code.')


def describe(folder):
    manifest, sources = [], {}
    if not folder.is_dir():
        raise SyncError('The source must be a directory')
    for root, dirs, files in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if not d.startswith('.'))
        for name in dirs + files:
            if not name.startswith('.') and (Path(root) / name).is_symlink():
                raise SyncError('Symlinks are not published; copy the intended files into the folder')
        for name in sorted(files):
            if name.startswith('.'):
                continue
            source = Path(root) / name
            if not source.is_file():
                raise SyncError('The folder contains a non-regular file')
            sha, size = hashlib.sha256(), 0
            with source.open('rb') as stream:
                while chunk := stream.read(1024 * 1024):
                    sha.update(chunk)
                    size += len(chunk)
            digest = sha.hexdigest()
            manifest.append({'path': source.relative_to(folder).as_posix(), 'size': size, 'sha256': digest})
            sources[digest] = (source, size)
    if not any(f['path'] == 'index.html' for f in manifest):
        raise SyncError('The folder needs index.html at its root')
    return sorted(manifest, key=lambda f: f['path']), sources


def sync(folder, name=None, site_id=None):
    folder = folder.resolve()
    manifest, sources = describe(folder)
    try:
        link = link_file().read_text().strip()
    except FileNotFoundError:
        raise SyncError('Not connected. Run sitesync.py connect first.') from None
    remember(link)
    parts = validate_url(link)
    params = dict(parse_qsl(parts.query))
    params.pop('id', None)
    params['cmd'] = 'SITE_SYNC'
    if site_id is not None:
        params['id'] = str(site_id)
    url = urlunsplit(parts._replace(query=urlencode(params), fragment=''))
    payload = {'manifest': manifest, 'name': name,
               'client_ref': 'deck-' + hashlib.sha256(str(folder).encode()).hexdigest()}

    def upload(entry):
        source, size = sources[entry['sha256']]
        put = entry['put']
        with source.open('rb') as stream:
            request(put['url'], method='PUT', body=stream,
                    headers={**put['headers'], 'Content-Length': str(size)}, as_json=False)

    for _ in range(ROUNDS):
        result = post(url, payload)
        if result.get('status') == 'published':
            site = result['site']
            print(f"Published: {site['address']}\nSite id: {site['id']}")
            return
        if result.get('status') != 'upload':
            raise SyncError('Unexpected sync status from the server')
        missing = result['missing']
        for entry in missing:
            if entry['sha256'] not in sources:
                raise SyncError('Server requested a file outside the manifest')
            remember(entry['put']['url'])
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(upload, missing))
    raise SyncError(f'Sync did not publish after {ROUNDS} rounds. Retry the same command; its reference is stable.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('connect', help='Approve a connection once in your browser')
    publish = commands.add_parser('publish', help='Publish a folder; retries reuse the same site')
    publish.add_argument('dir', type=Path)
    publish.add_argument('name', help='Site name: up to 20 lowercase letters, digits and hyphens')
    update = commands.add_parser('update', help='Update an existing site in place')
    update.add_argument('id', type=int)
    update.add_argument('dir', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'connect':
            connect()
        else:
            sync(args.dir, getattr(args, 'name', None), getattr(args, 'id', None))
    except SyncError as exc:
        print(f'Error: {safe(exc)}', file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError):
        print('Error: could not read/write local files or process the server response (details withheld).', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('Cancelled.', file=sys.stderr)
        return 130
    return 0


if __name__ == '__main__':
    sys.exit(main())
