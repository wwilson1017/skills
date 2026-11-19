#!/usr/bin/env python3
"""pptx2slides: rebuild a range of slides from an unzipped .pptx as deck <section>s, same words, same pictures, same layout.

usage: pptx2slides.py <unzipped-pptx-dir> <first> <last> <out.html>
Every picture, text box and line is placed absolutely at its original geometry (scaled to the 1600x900 stage).
Handles: crops, rotation, run highlight, shape fill/border/glow, autofit fontScale, layout-inherited title size/font,
click animations (entrance -> .step, exit -> .out), YouTube videos (iframe over the poster). Skips slide numbers.
"""
import base64, html, mimetypes, os, re, sys
import xml.etree.ElementTree as ET

P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
ns = {'p': P, 'a': A}
root_dir, first, last, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
cx = int(re.search(r'<p:sldSz[^>]*cx="(\d+)"', open(f'{root_dir}/ppt/presentation.xml').read()).group(1))
K = 1600 / cx                      # EMU -> stage px
PT = 1600 / (cx / 12700)           # pt  -> stage px
theme = {'dk1': '#000000', 'lt1': '#ffffff', 'dk2': '#d9d9d9', 'lt2': '#efefef'}
FONTS = {}  # Original font names use local faces, with a sans-serif fallback.
img_cache = {}


def color(el):
    if el is None: return None
    c = el.find('a:srgbClr', ns)
    if c is not None: return '#' + c.get('val')
    c = el.find('a:schemeClr', ns)
    return theme.get(c.get('val')) if c is not None else None


def image_uri(path):
    if path not in img_cache:
        # Preserve the original image and transparency; no platform-specific helper.
        # Resize large assets in the extracted folder with shrink.py before importing.
        mime = mimetypes.guess_type(path)[0] or 'application/octet-stream'
        with open(path, 'rb') as stream:
            data = stream.read()
        img_cache[path] = f'data:{mime};base64,' + base64.b64encode(data).decode()
    return img_cache[path]


def box(el):
    x = el.find('.//a:xfrm', ns)
    if x is None or x.find('a:off', ns) is None: return None
    o, e = x.find('a:off', ns), x.find('a:ext', ns)
    g = dict(l=int(o.get('x')) * K, t=int(o.get('y')) * K, w=int(e.get('cx')) * K, h=int(e.get('cy')) * K,
             rot=int(x.get('rot', 0)) / 60000, fh=x.get('flipH') == '1', fv=x.get('flipV') == '1')
    return g


def place(g, extra=''):
    rot = f'transform:rotate({g["rot"]:.2f}deg);' if g['rot'] else ''
    return f'left:{g["l"]:.1f}px;top:{g["t"]:.1f}px;width:{g["w"]:.1f}px;height:{g["h"]:.1f}px;{rot}{extra}'


def layout_defaults(n):
    rel = open(f'{root_dir}/ppt/slides/_rels/slide{n}.xml.rels').read()
    lay = ET.parse(f'{root_dir}/ppt/slideLayouts/' + re.search(r'slideLayout\d+\.xml', rel).group(0)).getroot()
    d = {}
    for sp in lay.iter(f'{{{P}}}sp'):
        ph = sp.find('.//p:ph', ns)
        if ph is None: continue
        l1 = sp.find('.//a:lvl1pPr', ns)
        if l1 is None: continue
        rp, ls = l1.find('a:defRPr', ns), l1.find('a:lnSpc/a:spcPct', ns)
        lat = l1.find('.//a:latin', ns) if l1.find('.//a:latin', ns) is not None else l1.find('a:buFont', ns)   # Google's export names the title face only on buFont
        d[ph.get('type', 'body')] = dict(sz=int(rp.get('sz')) if rp is not None and rp.get('sz') else None,
                                         font=lat.get('typeface') if lat is not None else None,
                                         ln=int(ls.get('val')) / 100000 if ls is not None else 1.0, algn=l1.get('algn'))
    return d


def text_shape(sp, g, defaults, cls):
    ph = sp.find('.//p:ph', ns)
    d = defaults.get(ph.get('type', 'body'), {}) if ph is not None else {}
    body = sp.find('p:txBody/a:bodyPr', ns)
    fit = body.find('a:normAutofit', ns) if body is not None else None
    scale = int(fit.get('fontScale', 100000)) / 100000 if fit is not None else 1
    shrink_ln = int(fit.get('lnSpcReduction', 0)) / 100000 if fit is not None else 0
    anchor = {'t': 'flex-start', 'ctr': 'center', 'b': 'flex-end'}[body.get('anchor', 't') if body is not None else 't']
    pad = int(body.get('lIns', 91440)) * K if body is not None else 16
    paras = []
    for p in sp.findall('p:txBody/a:p', ns):
        ppr = p.find('a:pPr', ns)
        algn = {'l': 'left', 'ctr': 'center', 'r': 'right'}.get((ppr.get('algn') if ppr is not None else None) or d.get('algn') or 'l', 'left')
        ls = ppr.find('a:lnSpc/a:spcPct', ns) if ppr is not None else None
        ln = (int(ls.get('val')) / 100000 if ls is not None else d.get('ln', 1.0)) - shrink_ln
        runs, size = [], None
        for r in p:
            tag = r.tag.split('}')[1]
            if tag == 'br': runs.append('<br>'); continue
            if tag != 'r': continue
            rp = r.find('a:rPr', ns)
            sz = (int(rp.get('sz')) if rp is not None and rp.get('sz') else d.get('sz') or 1800) * scale / 100 * PT
            size = size or sz
            lat = rp.find('a:latin', ns) if rp is not None else None
            face = (lat.get('typeface') if lat is not None else None) or d.get('font') or 'Arial'
            fam, wt = FONTS.get(face, (face, 700 if rp is not None and rp.get('b') == '1' else 400))
            st = f'font-family:\'{fam}\',sans-serif;font-weight:{wt};font-size:{sz:.1f}px;'
            c = color(rp.find('a:solidFill', ns)) if rp is not None else None
            if c: st += f'color:{c};'
            if rp is not None and rp.get('i') == '1': st += 'font-style:italic;'
            hl = color(rp.find('a:highlight', ns)) if rp is not None else None
            if hl: st += f'background:{hl};box-decoration-break:clone;-webkit-box-decoration-break:clone;'
            runs.append(f'<span style="{st}">{html.escape(r.find("a:t", ns).text or "")}</span>')
        if not runs:                                   # empty paragraph keeps its line
            e = p.find('a:endParaRPr', ns)
            size = (int(e.get('sz')) if e is not None and e.get('sz') else d.get('sz') or 1800) * scale / 100 * PT
            runs = ['&nbsp;']
        paras.append(f'<div style="text-align:{algn};line-height:{ln * 1.2:.3f};font-size:{size:.1f}px">{"".join(runs)}</div>')
    st = f'display:flex;flex-direction:column;justify-content:{anchor};padding:{pad:.1f}px;'
    pr = sp.find('p:spPr', ns)
    fill = color(pr.find('a:solidFill', ns)) if pr is not None else None
    if fill: st += f'background:{fill};'
    ln_el = pr.find('a:ln', ns) if pr is not None else None
    if ln_el is not None and color(ln_el.find('a:solidFill', ns)):
        st += f'border:{max(1, int(ln_el.get("w", 9525)) * K):.1f}px solid {color(ln_el.find("a:solidFill", ns))};'
    sh = pr.find('.//a:outerShdw', ns) if pr is not None else None
    if sh is not None: st += f'box-shadow:0 0 {int(sh.get("blurRad", 0)) * K:.0f}px {color(sh)}80;'
    if body is not None and body.find('a:spAutoFit', ns) is not None: st += 'height:auto;'
    return f'<div class="el{cls}" style="{place(g, st)}">{"".join(paras)}</div>'


def line_shape(el, g, cls):
    ln = el.find('p:spPr/a:ln', ns)
    c = color(ln.find('a:solidFill', ns)) if ln is not None else None
    if not c: return ''
    w = max(2, int(ln.get('w', 9525)) * K)
    x1, x2 = (g['w'], 0) if g['fh'] else (0, g['w'])
    y1, y2 = (g['h'], 0) if g['fv'] else (0, g['h'])
    head = ln.find('a:headEnd', ns); tail = ln.find('a:tailEnd', ns)
    mk = lambda e: e is not None and e.get('type', 'none') != 'none'
    mid = f'm{abs(hash((g["l"], g["t"])))}'
    defs = f'<defs><marker id="{mid}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker></defs>'
    ends = (f' marker-start="url(#{mid})"' if mk(head) else '') + (f' marker-end="url(#{mid})"' if mk(tail) else '')
    return (f'<svg class="el{cls}" style="{place(g, "overflow:visible;")}" viewBox="0 0 {max(g["w"], 1):.1f} {max(g["h"], 1):.1f}" preserveAspectRatio="none">'
            f'{defs}<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{c}" stroke-width="{w:.1f}"{ends}/></svg>')


def pic_shape(el, g, rels, cls, links):
    path = os.path.normpath(f'{root_dir}/ppt/slides/' + rels[el.find('.//a:blip', ns).get(f'{{{R}}}embed')])
    sr = el.find('.//a:srcRect', ns)
    l, t, r, b = [int(sr.get(k, 0)) / 100000 if sr is not None else 0 for k in 'ltrb']
    iw, ih = g['w'] / (1 - l - r), g['h'] / (1 - t - b)
    alt = html.escape(el.find('.//p:cNvPr', ns).get('descr') or '')
    am = el.find('.//a:alphaModFix', ns)                # picture transparency (how the original dims a photo behind text)
    op = f'opacity:{int(am.get("amt")) / 100000:.2f};' if am is not None and am.get("amt") else ''
    inner = f'<img alt="{alt}" src="{image_uri(path)}" style="{op}position:absolute;left:{-l * iw:.1f}px;top:{-t * ih:.1f}px;width:{iw:.1f}px;height:{ih:.1f}px">'
    yt = next((re.search(r'v=([\w-]+)', u).group(1) for u in links if 'youtube' in u), None)
    if yt and el.find('.//a:videoFile', ns) is not None or (yt and g['w'] > 1500):
        inner += f'<iframe data-src="https://www.youtube.com/embed/{yt}?rel=0" title="video" allow="autoplay; fullscreen" style="position:absolute;inset:0;width:100%;height:100%;border:0"></iframe>'
    return f'<div class="el{cls}" style="{place(g, "overflow:hidden;")}">{inner}</div>'


sections = []
for n in range(first, last + 1):
    raw = open(f'{root_dir}/ppt/slides/slide{n}.xml').read()
    root = ET.fromstring(raw)
    relroot = ET.parse(f'{root_dir}/ppt/slides/_rels/slide{n}.xml.rels').getroot()
    rels = {r.get('Id'): r.get('Target') for r in relroot}
    links = [r.get('Target') for r in relroot if r.get('TargetMode') == 'External']
    defaults = layout_defaults(n)
    anim = {}                                          # shape id -> 'step' (entrance on click) | 'out' (exit on click)
    if '<p:timing' in raw:
        tm = raw[raw.index('<p:timing'):]
        ev = sorted([(m.start(), 'c', m.group(1)) for m in re.finditer(r'<p:cTn [^>]*presetClass="(\w+)"', tm)] + [(m.start(), 's', m.group(1)) for m in re.finditer(r'spid="(\d+)"', tm)])
        cur = None
        for _, kind, v in ev:
            if kind == 'c': cur = v
            elif cur: anim.setdefault(v, 'step' if cur == 'entr' else 'out')
    parts = []
    for el in root.find('p:cSld/p:spTree', ns):
        tag = el.tag.split('}')[1]
        if tag not in ('pic', 'sp', 'cxnSp'): continue
        ph = el.find('.//p:ph', ns)
        if ph is not None and ph.get('type') == 'sldNum': continue
        g = box(el)
        if g is None: continue
        cls = {'step': ' step', 'out': ' out'}.get(anim.get(el.find('.//p:cNvPr', ns).get('id')), '')
        if tag == 'pic': parts.append(pic_shape(el, g, rels, cls, links))
        elif tag == 'cxnSp': parts.append(line_shape(el, g, cls))
        elif el.find('.//a:t', ns) is not None or el.find('p:spPr/a:solidFill', ns) is not None: parts.append(text_shape(el, g, defaults, cls))
    sections.append(f'  <!-- source slide {n} -->\n  <section class="abs">\n    ' + '\n    '.join(p for p in parts if p) + '\n  </section>\n')
open(out, 'w').write('\n'.join(sections))
print(f'{len(sections)} slides, {len(img_cache)} images, {os.path.getsize(out) // 1024} KB')
