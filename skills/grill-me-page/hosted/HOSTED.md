# Hosting a grill-me page on a PHP host

Use this when the person answering is not at the machine running the session: a staff member, a client, you on a phone away from home. The page goes on a web host; `submit.php` beside it is the collector, with the same API as `collect.py serve`, so the page behaves the same way and the session gets the answers back with `collect.py watch`.

## Deploy

Any host that runs PHP 7 or later and lets `.htaccess` work. Put three files in one directory of their own:

| File here | Name on the host | What it is |
|---|---|---|
| `<dir>/index.html` | `index.html` | The built page |
| `hosted/submit.php` | `submit.php` | The collector |
| `hosted/htaccess` | `.htaccess` | Turns off directory listing and search indexing, and denies web reads of `answers.jsonl` |

Give the directory an unguessable name (a slug plus a random hex string). Unlisted means anyone who has the link can open the page, so keep passwords, keys and private messages off it.

The PHP process needs write permission in that directory: it appends to `answers.jsonl`. Check the first Go with a browser: `https://host/dir/submit.php?acks=1` should return `{}` or a JSON object, and after an answer is saved `https://host/dir/submit.php?page=<PAGE>&version=<VERSION>` returns the newest record.

## What the files hold

`answers.jsonl` has one JSON line per save: `{"at": "<ISO time>", "data": {...}}`, where `data` is what the page posted. Drafts post as the person works (`final: false`); Go posts `final: true` with `submit_id`, `summary_text` and `questions`. The web cannot read this file; `.htaccess` denies it.

The three status files are small JSON objects the session writes beside the page over SSH or SFTP. `submit.php?acks=1` returns them as `received`, `applied` and `alive`.

| File | Written when | Shape |
|---|---|---|
| `watch-alive.json` | Each poll of a watcher that can write to the host | `{"at": ISO, "page": PAGE, "version": V, "owner": "who"}` |
| `ack-received.json` | A watcher finds the Go | `{"stage": "received", "page": PAGE, "version": V, "submit_id": "...", "at": ISO, "message": ""}` |
| `ack-applied.json` | The session has acted on the answers | `{"stage": "applied", "page": PAGE, "version": V, "submit_id": "...", "at": ISO, "message": "Round 2 is up"}` |

The page matches an ack to its own send by `submit_id`, and `page` and `version` must match too, so an old ack never lights up a new round. The heartbeat drives the "a session is watching this page" line; it counts as alive for three minutes.

## Getting the answers back

```bash
python3 collect.py watch https://host/dir <PAGE> <VERSION> grills/<slug>/answers-v<VERSION>.json
```

`watch` with a URL polls `submit.php?final=1&page=&version=` every five seconds and exits with the record when a matching Go lands. It cannot write the status files over HTTP, so with only a URL the page shows "Sent" and then "no session is watching". To light the lights, write the files yourself over SSH or SFTP: `collect.py ack <local copy of dir> ... --record <out.json>` produces the right JSON locally, and you copy it up; or run `watch` on the host itself against the directory, which writes the heartbeat and `ack-received.json` in place.

Three failed polls in a row (host down, DNS gone) make `watch` exit with a message; run it again when the host is back. It is idempotent: a Go that already landed is returned at once.

## When you cannot write files on the host

Set `const ACKS = false;` in `config.js` before building. The page then says "Sent, kept on the page" after Go and never polls for acks or promises receipt. The watcher still works, and the person sees nothing misleading.

## CORS

`submit.php` sends `Access-Control-Allow-Origin: *`. That is deliberate: it lets forms on other sites you run post into the same collector with the same rules. If none of yours do, delete that header line. The local collector never sends it.

With the header in place, anyone who can reach the URL can append records; the ones the page reads are filtered by `page`, `version`, `client_id` and `name`, and `--locked` validates the shape, but a stranger with the link could still post noise. An unguessable directory name is the defence.

## Several people

`MULTI = true` pages work the same way hosted. `submit.php?page=&version=&name=<Name>` returns that person's newest record (case-insensitive, trimmed), and `?client=<id>` returns one browser's. Read `answers.jsonl` on the host for everyone's final answers.
