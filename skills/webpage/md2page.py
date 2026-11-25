#!/usr/bin/env python3
"""md2page: wrap a Markdown file in the house style used for unlisted share pages (noindex, self-contained, printable).

usage: md2page.py <input.md> <output.html> [--title "Page title"] [--subtitle "prepared by … · date"] [--footer "…"]
Uses the 'markdown' package; installs it into a private venv next to this script on first run.
"""
import argparse, html, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VENV = HERE / ".venv"
if not (VENV / "bin" / "python").exists() and "MD2PAGE_BOOTSTRAPPED" not in os.environ:
    subprocess.check_call([sys.executable, "-m", "venv", str(VENV)])
    subprocess.check_call([str(VENV / "bin" / "pip"), "install", "-q", "markdown"])
if sys.executable != str(VENV / "bin" / "python") and (VENV / "bin" / "python").exists():
    os.execve(str(VENV / "bin" / "python"), [str(VENV / "bin" / "python"), __file__, *sys.argv[1:]], {**os.environ, "MD2PAGE_BOOTSTRAPPED": "1"})
import markdown  # noqa: E402

CSS = """
  :root { --ink:#1f2328; --muted:#59636e; --line:#d9dee3; --soft:#f4f6f8; --accent:#8b1e2d }
  * { box-sizing:border-box }
  body { margin:0; padding:32px 20px 64px; font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; color:var(--ink); background:#fff }
  main { max-width:960px; margin:0 auto }
  h1 { font-size:30px; line-height:1.2; margin:0 0 6px }
  h2 { font-size:22px; margin:44px 0 12px; padding-top:18px; border-top:2px solid var(--line) }
  h3 { font-size:17px; margin:26px 0 8px }
  p { margin:0 0 12px } .sub { color:var(--muted); margin-bottom:26px }
  .wrap { overflow-x:auto; margin:12px 0 }
  table { border-collapse:collapse; width:100%; font-size:14px }
  th, td { text-align:left; padding:8px 10px; border-bottom:1px solid var(--line); vertical-align:top }
  th { background:var(--soft); font-weight:600; white-space:nowrap }
  ul, ol { padding-left:22px } li { margin-bottom:8px }
  blockquote { border-left:4px solid var(--accent); background:var(--soft); padding:12px 16px; margin:16px 0; border-radius:0 8px 8px 0 }
  code { background:var(--soft); padding:1px 5px; border-radius:4px; font-size:90% }
  .note { font-size:13px; color:var(--muted); margin-top:40px }
  a { color:var(--accent) }
  @media print { body{padding:0} h2{break-after:avoid} tr{break-inside:avoid} }
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst")
    ap.add_argument("--title"); ap.add_argument("--subtitle", default="")
    ap.add_argument("--footer", default="This page is unlisted. Please don't forward the link beyond the people it names.")
    a = ap.parse_args()
    text = Path(a.src).read_text(encoding="utf-8")
    lines = text.splitlines()
    title = a.title
    if not title and lines and lines[0].startswith("# "):
        title = lines[0][2:].strip(); lines = lines[1:]
    body = markdown.markdown("\n".join(lines), extensions=["tables", "sane_lists", "smarty"])
    body = body.replace("<table>", '<div class="wrap"><table>').replace("</table>", "</table></div>")
    sub = f'<p class="sub">{html.escape(a.subtitle)}</p>' if a.subtitle else ""
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow"><title>{html.escape(title or Path(a.src).stem)}</title><style>{CSS}</style></head>
<body><main><h1>{html.escape(title or '')}</h1>{sub}
{body}
<p class="note">{html.escape(a.footer)}</p></main></body></html>
"""
    Path(a.dst).write_text(page, encoding="utf-8")
    print(a.dst)

if __name__ == "__main__":
    main()
