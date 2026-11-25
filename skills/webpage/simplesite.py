#!/usr/bin/env python3
"""simplesite — publish a page on Simple Sites (simplesites.app) through the account's agent link.

  simplesite publish <file.md|file.html> <name> [title]   new page at simplesites.app/<name>-<code>; prints the address
  simplesite update  <id> <file>                           same address, new content
  simplesite shorten <url> <name> [title]                  short address that redirects to url (e.g. a deck)
  simplesite list                                          every page and link: id, status, address, title
  simplesite remove  <id>                                  take it down (kept: restore brings it back)
  simplesite restore <id>

<name> is up to 10 of a-z, 0-9 and -; longer or odd slugs are folded to fit. The title defaults to the first
# heading or the HTML <title>. The agent link is read from ~/.config/simplesites/link (chmod 600), never from
this repo: it reads and writes the linked Simple Sites account (todos, notes, projects, pages).
"""
import json, os, re, sys, urllib.error, urllib.request

LINK_FILE = os.path.expanduser("~/.config/simplesites/link")


def call(cmd, body=None, **args):
    link = open(LINK_FILE).read().strip()
    query = "&".join([f"cmd={cmd}"] + [f"{k}={v}" for k, v in args.items()])
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(f"{link}?{query}", data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            answer = json.load(resp)
    except urllib.error.HTTPError as e:
        text = e.read().decode(errors="replace")
        try:
            answer = json.loads(text)
        except ValueError:
            sys.exit(f"HTTP {e.code}: {text[:300]}")
    if not answer.get("ok"):
        sys.exit(f"refused: {answer.get('error')}")
    return answer


def content(path):
    fmt = "html" if path.lower().endswith((".html", ".htm")) else "markdown"
    return {"content": open(path, encoding="utf-8").read(), "format": fmt}


def done(site):
    req = urllib.request.Request(site["address"], method="HEAD")  # HEAD: not counted as a view
    try:
        status = urllib.request.urlopen(req, timeout=20).status
    except urllib.error.HTTPError as e:
        status = e.code
    print(f"HTTP {status}  id {site['id']}  {site['status']}")
    print(site["address"])


if not os.path.exists(LINK_FILE):
    sys.exit(f"no agent link at {LINK_FILE}: paste the Simple Sites agent link there and chmod 600 it")
op, rest = (sys.argv[1] if len(sys.argv) > 1 else ""), sys.argv[2:]
if op == "publish" and len(rest) in (2, 3):
    name = re.sub(r"[^a-z0-9-]+", "-", rest[1].lower())[:10].strip("-")
    body = {**content(rest[0]), "name": name, **({"title": rest[2]} if len(rest) == 3 else {})}
    done(call("PUBLISH", body)["page"])
elif op == "shorten" and len(rest) in (2, 3):
    name = re.sub(r"[^a-z0-9-]+", "-", rest[1].lower())[:10].strip("-")
    done(call("SHORTEN", {"url": rest[0], "name": name, **({"title": rest[2]} if len(rest) == 3 else {})})["link"])
elif op == "update" and len(rest) == 2:
    done(call("PUBLISH", content(rest[1]), id=rest[0])["page"])
elif op in ("remove", "restore") and len(rest) == 1:
    done(call("UNPUBLISH" if op == "remove" else "REPUBLISH", {}, id=rest[0])["site"])
elif op == "list" and not rest:
    for s in call("SITES")["sites"]:
        print(f"{s['id']:>4}  {s['kind']:<4}  {s['status']:<11}  {s['address']}  {s.get('title') or ''}")
else:
    sys.exit(__doc__)
