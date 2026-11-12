#!/usr/bin/env python3
"""Assemble a grill-me page.

    build.py <dir> --title "Title" [--locked prev-answers] [--what "one line"] [--audience Name] [--issue N]   ->  <dir>/index.html

<dir> holds:
  body.html     the intro: lead box, stat tiles, diagrams, answers to last round's notes.
                Put <!--LOCKED--> where the previous round's answers table should go.
  config.js     const PAGE, VERSION, SECTIONS, Q (and optionally MULTI, NEXT, ACKS).
  visuals.html  optional <template id="vis-..."> blocks, used by Q[].vis or <div data-vis="vis-...">.
  after.html    optional content after the questions (e.g. the build plan).

--locked takes the previous round's answers in any of three forms: the record as the page sent it, the
collector's {at, data} envelope (what collect.py watch writes), or the text a person pasted back from the
copy box (the JSON after the "ANSWERS JSON (for the next round):" line).
"""
import argparse, html, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MARKER = "ANSWERS JSON (for the next round):"


def grill_audience(audience):
    """Who answers this page. An omitted --audience means Will, not a staff name."""
    return audience or "will"


def load_record(path: str) -> dict:
    text = Path(path).read_text()
    if MARKER in text:
        text = text.split(MARKER, 1)[1].strip().splitlines()[0]
    try:
        rec = json.loads(text)
    except json.JSONDecodeError as e:
        raise SystemExit(f"--locked: {path} is not JSON ({e}); expected the page's record, the collector's envelope, or the pasted copy box")
    d = rec.get("data", rec) if isinstance(rec, dict) else None
    if not isinstance(d, dict) or not isinstance(d.get("questions"), list) or not isinstance(d.get("answers"), dict):
        raise SystemExit(f"--locked: {path} has no questions list and answers object; is it a Go record from the page?")
    return d


def locked_table(d: dict) -> str:
    """The ★ rule, shared with engine.js summaryText(): ★ is implied only when nothing is picked AND nothing is written."""
    qs, answers = d["questions"], d["answers"]
    rows = []
    for q in qs:
        a = answers.get(q["id"], {})
        labels = {o[0]: o[1] for o in q["o"]}
        rec = [o[1] for o in q["o"] if o[2]]
        picked, own = a.get("picked") or [], (a.get("answer") or "").strip()
        pills = []
        if picked:
            answer = "; ".join(labels.get(v, v) for v in picked)
            if rec and set(picked) != {o[0] for o in q["o"] if o[2]}:
                pills.append('<span class="pill warn">changed</span>')
        elif own:
            answer = ""
            pills.append('<span class="pill info">own answer</span>')
        else:
            answer = "(none ticked)" if q.get("none_rec") or not rec else "★ " + "; ".join(rec)
        if own:
            answer = (html.escape(answer) + " · " if answer else "") + "<i>" + html.escape(own) + "</i>"
        else:
            answer = html.escape(answer)
        rows.append(f'<tr><td>{html.escape(q["id"])}</td><td>{html.escape(q["t"])} {" ".join(pills)}</td>'
                    f'<td>{answer}</td><td class="small">{html.escape(a.get("note") or "")}</td></tr>')
    extra = "".join(f'<p class="small"><b>{label}:</b> {html.escape(d[k])}</p>'
                    for k, label in (("my_questions", "Your questions"), ("missing", "Missed / first")) if d.get(k))
    return (f'<details class="decided"><summary>Your v{html.escape(str(d.get("version", "?")))} answers, locked ({len(qs)})</summary>'
            '<div style="overflow-x:auto;margin-top:8px"><table class="mt"><thead><tr><th>#</th><th>Question</th>'
            '<th>Your answer</th><th>Your note</th></tr></thead><tbody>' + "".join(rows) +
            f'</tbody></table></div>{extra}</details>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--title", required=True)
    ap.add_argument("--locked", help="the previous round's answers: the page's record, collect.py's envelope, or the pasted copy box")
    ap.add_argument("--audience", default="", help="who answers, when it is not the person running the session (a first name)")
    ap.add_argument("--what", default="", help="one line saying what this page asks (the page's description meta tag)")
    ap.add_argument("--issue", help="an issue number this page unblocks, kept in a meta tag")
    a = ap.parse_args()
    dash = (HERE / "dashboard.url").read_text().strip() if (HERE / "dashboard.url").exists() else ""   # an optional "all your pages" link
    meta = (f'<meta name="grill-audience" content="{html.escape(grill_audience(a.audience))}">'
            + (f'\n<meta name="description" content="{html.escape(a.what)}">' if a.what else "")
            + (f'\n<meta name="grill-issue" content="{html.escape(a.issue)}">' if a.issue else ""))
    dashlink = (f'<a class="dash" href="{html.escape(dash)}">All <span class="long">your </span>pages →</a>'
                if not a.audience and dash else "")
    src = Path(a.dir)
    part = lambda name: (src / name).read_text() if (src / name).exists() else ""
    body = part("body.html")
    if a.locked:
        if "<!--LOCKED-->" not in body:
            raise SystemExit("--locked given but body.html has no <!--LOCKED--> marker")
        body = body.replace("<!--LOCKED-->", locked_table(load_record(a.locked)))
    page = (HERE / "template.html").read_text()
    for key, val in (("TITLE", html.escape(a.title)), ("META", meta), ("DASHLINK", dashlink), ("BODY", body), ("AFTER", part("after.html")),
                     ("VISUALS", part("visuals.html")), ("CONFIG", part("config.js")),
                     ("ENGINE", (HERE / "engine.js").read_text())):
        page = page.replace("{{" + key + "}}", val)
    out = src / "index.html"
    out.write_text(page)
    print(out, len(page), "bytes")


if __name__ == "__main__":
    main()
