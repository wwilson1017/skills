#!/usr/bin/env python3
"""The local collector for a grill-me page. Standard library only.

  collect.py serve <dir> [--port 8765] [--bind 127.0.0.1]
      Serves <dir>/index.html at / and the collector API at /submit.php; nothing else in <dir> is reachable.
      --bind 0.0.0.0 lets a phone on the same network (or tailnet) answer the page.
  collect.py watch <dir|URL> <PAGE> <VERSION> <out.json> [--hours 48]
      Waits for a Go (a final record for that page and version), writes it to out.json and exits 0; exits 2
      on timeout. With a dir it also writes ack-received.json and a heartbeat (watch-alive.json) every poll.
      With a URL (a hosted page) it only polls submit.php; acks need a write channel to the host.
      Idempotent: if the Go is already there it returns at once.
  collect.py ack <dir> <PAGE> <VERSION> received|applied "message" --record <out.json>
      Lights the page's status strip. The submit id comes from the record the session actually processed.

API (same as hosted/submit.php):
  POST /submit.php          JSON object body -> appended to answers.jsonl as {"at": ISO, "data": body}
  GET  /submit.php?page=&version=[&final=1][&client=ID][&name=NAME]   newest record whose data matches
  GET  /submit.php?acks=1   {"received": …, "applied": …, "alive": …} from the ack and heartbeat files
"""
import argparse, datetime, ipaddress, json, os, socket, sys, time, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MAX_BODY = 300_000   # per request; # simplification: no cap on answers.jsonl as a whole, a page is one person's answers
ACK_FILES = {"received": "ack-received.json", "applied": "ack-applied.json", "alive": "watch-alive.json"}


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def records(path: Path):
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        try:
            rec = json.loads(line)
            if isinstance(rec, dict) and isinstance(rec.get("data"), dict):
                out.append(rec)
        except json.JSONDecodeError:
            pass
    return out


def matches(d: dict, page=None, version=None, final=False, client=None, name=None) -> bool:
    if page is not None and d.get("page") != page: return False
    if version is not None and str(d.get("version")) != str(version): return False
    if final and not d.get("final"): return False
    if client is not None and d.get("client_id") != client: return False
    if name is not None and (d.get("name") or "").strip().lower() != name.strip().lower(): return False
    return True


def newest(path: Path, **f):
    for rec in reversed(records(path)):
        if matches(rec["data"], **f):
            return rec
    return None


def read_acks(d: Path) -> dict:
    out = {}
    for k, f in ACK_FILES.items():
        p = d / f
        if p.exists():
            try: out[k] = json.loads(p.read_text())
            except json.JSONDecodeError: pass
    return out


def write_json(p: Path, obj):
    tmp = p.with_suffix(p.suffix + ".tmp"); tmp.write_text(json.dumps(obj)); os.replace(tmp, p)


def own_addresses():
    names = {"localhost", "127.0.0.1", "::1", socket.gethostname().lower()}
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            names.add(info[4][0])
    except socket.gaierror:
        pass
    return names


class Handler(BaseHTTPRequestHandler):
    root: Path
    bind: str
    hosts = own_addresses()

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (now(), fmt % args))

    def send(self, code, body=b"", ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Robots-Tag", "noindex")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]").lower()
        if not host: return False
        if host in self.hosts or host == self.bind: return True
        try:
            ipaddress.ip_address(host); return True   # a bare IP a phone typed (LAN or tailnet address of this machine)
        except ValueError:
            return host.endswith(".local") or host.endswith(".ts.net")

    def do_OPTIONS(self):
        self.send(405)   # no preflight is ever granted: a foreign page's JSON POST never reaches do_POST

    def do_GET(self):
        if not self.host_ok(): return self.send(400, b'{"ok":false,"error":"host"}')
        u = urllib.parse.urlsplit(self.path)
        if u.path in ("/", "/index.html"):
            p = self.root / "index.html"
            if not p.exists(): return self.send(404, b"no index.html", "text/plain")
            return self.send(200, p.read_bytes(), "text/html; charset=utf-8")
        if u.path != "/submit.php":
            return self.send(404, b'{"ok":false}')
        q = dict(urllib.parse.parse_qsl(u.query))
        if "acks" in q:
            return self.send(200, json.dumps(read_acks(self.root)).encode())
        rec = newest(self.root / "answers.jsonl", page=q.get("page"), version=q.get("version"),
                     final="final" in q, client=q.get("client"), name=q.get("name"))
        self.send(200, json.dumps(rec or {}).encode())

    def do_POST(self):
        if not self.host_ok(): return self.send(400, b'{"ok":false,"error":"host"}')
        u = urllib.parse.urlsplit(self.path)
        if u.path != "/submit.php": return self.send(404, b'{"ok":false}')
        if not (self.headers.get("Content-Type") or "").lower().startswith("application/json"):
            return self.send(415, b'{"ok":false,"error":"content-type"}')
        origin = self.headers.get("Origin")
        if origin and urllib.parse.urlsplit(origin).netloc.lower() != (self.headers.get("Host") or "").lower():
            return self.send(403, b'{"ok":false,"error":"origin"}')
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_BODY: return self.send(413, b'{"ok":false,"error":"too big"}')
        try:
            data = json.loads(self.rfile.read(n))
        except (json.JSONDecodeError, UnicodeDecodeError):
            data = None
        if not isinstance(data, dict): return self.send(400, b'{"ok":false,"error":"json object"}')
        at = now()
        with open(self.root / "answers.jsonl", "a") as f:
            f.write(json.dumps({"at": at, "data": data}) + "\n")
        self.send(200, json.dumps({"ok": True, "at": at}).encode())


def serve(a):
    Handler.root = Path(a.dir).resolve(); Handler.bind = a.bind
    if not (Handler.root / "index.html").exists():
        sys.exit(f"{a.dir}/index.html not found; run build.py first")
    with socket.socket() as probe:   # SO_REUSEADDR lets two servers share a port on macOS, so check before binding
        if probe.connect_ex(("127.0.0.1" if a.bind == "0.0.0.0" else a.bind, a.port)) == 0:
            sys.exit(f"port {a.port} is already in use; pick another with --port")
    srv = ThreadingHTTPServer((a.bind, a.port), Handler)
    print(f"serving {Handler.root}/index.html at http://{'localhost' if a.bind == '127.0.0.1' else a.bind}:{a.port}/", flush=True)
    if a.bind != "127.0.0.1":
        print("bound to every interface: anyone on this network can read and answer this page", flush=True)
    srv.serve_forever()


def fetch_json(url: str):
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.loads(r.read())


def watch(a):
    is_url = a.where.startswith("http://") or a.where.startswith("https://")
    d = None if is_url else Path(a.where)
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    end = time.time() + a.hours * 3600
    fails = 0
    while True:
        try:
            if is_url:
                rec = fetch_json(a.where.rstrip("/") + "/submit.php?" + urllib.parse.urlencode({"final": 1, "page": a.page, "version": a.version}))
                rec = rec if rec and matches(rec.get("data") or {}, page=a.page, version=a.version, final=True) else None
            else:
                rec = newest(d / "answers.jsonl", page=a.page, version=a.version, final=True)
            fails = 0
        except Exception as e:   # the host or the dir is unreachable
            fails += 1; rec = None
            print(f"watch: poll failed ({e}); {fails}/3", file=sys.stderr)
            if fails >= 3: sys.exit(f"watch: 3 polls in a row failed; restart it when {a.where} is back")
        if rec:   # simplification: exits on the first Go; for MULTI pages read answers.jsonl with GET ?name= per person, or add a --count N flag
            write_json(out, rec)
            if d is not None:
                write_json(d / ACK_FILES["received"], {"stage": "received", "page": a.page, "version": a.version,
                                                        "submit_id": rec["data"].get("submit_id"), "at": now(), "message": ""})
            print(f"GO RECEIVED -> {out}\n{rec.get('at')}\n{rec['data'].get('summary_text', '')}")
            return
        if time.time() > end:
            sys.exit(2)
        if d is not None:
            write_json(d / ACK_FILES["alive"], {"at": now(), "page": a.page, "version": a.version, "owner": a.owner})
        time.sleep(a.every)


def ack(a):
    rec = json.load(open(a.record))
    data = rec.get("data", rec)
    if not matches(data, page=a.page, version=a.version, final=True):
        sys.exit(f"ack: {a.record} is not a Go for {a.page} v{a.version}")
    write_json(Path(a.dir) / ACK_FILES[a.stage], {"stage": a.stage, "page": a.page, "version": a.version,
                                                   "submit_id": data.get("submit_id"), "at": now(), "message": a.message})
    print(f"ack {a.stage} posted for {a.page} v{a.version}" + (f": {a.message}" if a.message else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve"); s.add_argument("dir"); s.add_argument("--port", type=int, default=8765); s.add_argument("--bind", default="127.0.0.1"); s.set_defaults(fn=serve)
    w = sub.add_parser("watch"); w.add_argument("where", help="the page dir, or the URL of a hosted page"); w.add_argument("page"); w.add_argument("version"); w.add_argument("out")
    w.add_argument("--hours", type=float, default=48); w.add_argument("--every", type=int, default=5, help="seconds between polls")
    w.add_argument("--owner", default=socket.gethostname(), help="who is watching, shown in the heartbeat"); w.set_defaults(fn=watch)
    k = sub.add_parser("ack"); k.add_argument("dir"); k.add_argument("page"); k.add_argument("version"); k.add_argument("stage", choices=["received", "applied"])
    k.add_argument("message", nargs="?", default=""); k.add_argument("--record", required=True, help="the out.json that watch wrote for the Go being acknowledged"); k.set_defaults(fn=ack)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
