"""footnotes: turn [label](url) citations inside an HTML page into numbered superscript footnotes.

usage: footnotes.py <in.html> <out.html>
The source list replaces <!--SOURCES--> (put it in a "Sources" section at the end). Repeated URLs share a number.
"""
import html, re, sys
from urllib.parse import urlsplit

src = open(sys.argv[1], encoding="utf-8").read()
link = re.compile(r"\[([^\]\n]+)\]\((https?://(?:[^()\s]|\([^()\s]*\))+)\)")  # one level of parens in URLs
nums, order = {}, []


def cite(m):
    label, url = m.group(1), m.group(2)
    if url not in nums:
        nums[url] = len(order) + 1
        order.append((label, url))
    return f'<sup class="c"><a href="#s{nums[url]}" title="{html.escape(label, quote=True)}">{nums[url]}</a></sup>'


body = link.sub(cite, src).replace('</a></sup><sup class="c"><a', '</a>,<a')
items = "\n".join(f'<li id="s{i}"><a href="{u}">{html.escape(l)}</a> · '
                  f'{html.escape(urlsplit(u.replace("&amp;", "&")).netloc.removeprefix("www."))}</li>'
                  for i, (l, u) in enumerate(order, 1))
body = body.replace("<!--SOURCES-->", f"<p>{len(order)} sources, numbered in the order they are cited.</p><ol>\n{items}\n</ol>")
if "](http" in body:
    sys.exit("a citation was not converted: look for '](http' in the output")
open(sys.argv[2], "w", encoding="utf-8").write(body)
print(f"{len(order)} sources, {body.count('class=\"c\"')} citation marks")
