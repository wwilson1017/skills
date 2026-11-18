#!/usr/bin/env python3
"""Make a smaller copy of a deck folder using ffmpeg and ffprobe."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import quote


IMAGES = {'.jpg', '.jpeg', '.png', '.webp'}
VIDEOS = {'.mp4', '.m4v', '.mov', '.mkv', '.webm', '.avi', '.mpg', '.mpeg', '.ogv', '.ts'}
TEXT = {'.html', '.htm', '.css', '.js', '.mjs', '.json', '.svg', '.md', '.txt'}


def run(command):
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f'{command[0]} failed:\n{result.stderr[-2000:]}')
    return result.stdout


def probe(path):
    info = json.loads(run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))
    stream = next((s for s in info.get('streams', []) if s.get('codec_type') == 'video'), None)
    if stream is None:
        raise RuntimeError(f'No video/image stream in {path.name}')
    width, height = stream['width'], stream['height']
    rotation = float(stream.get('tags', {}).get('rotate', 0))
    for side in stream.get('side_data_list', []):
        rotation = float(side.get('rotation', rotation))
    if round(rotation) % 180:
        width, height = height, width
    rate = stream.get('bit_rate') or info.get('format', {}).get('bit_rate')
    try:
        rate = float(rate)
    except (TypeError, ValueError):
        duration = float(info.get('format', {}).get('duration', 0))
        rate = path.stat().st_size * 8 / duration if duration else 0
    return width, height, rate


def rewrite(text, mapping):
    # Match literal local references, including URL-encoded names, without changing
    # similarly named files. Dynamic JS path construction needs a manual check.
    for old, new in sorted(mapping.items(), key=lambda pair: len(pair[0]), reverse=True):
        for before, after in {(old, new), (quote(old), quote(new))}:
            text = re.sub(r'(?<![\w./%:-])' + re.escape(before) + r'(?=[\s\x22\x27<>?#),;]|$)',
                          lambda _: after, text)
    return text


def shrink(folder, output):
    for tool in ('ffmpeg', 'ffprobe'):
        if shutil.which(tool) is None:
            raise RuntimeError(f'{tool} is missing. Install ffmpeg (including ffprobe) and retry.')
    folder, output = folder.resolve(), output.resolve()
    if not folder.is_dir():
        raise RuntimeError('The input must be a directory')
    if output == folder or folder in output.parents or output in folder.parents:
        raise RuntimeError('The output must be separate from the input directory')
    if output.exists():
        raise RuntimeError('The output already exists; choose a new --out directory')
    sources = sorted(folder.rglob('*'))
    if any(p.is_symlink() for p in sources):
        raise RuntimeError('Symlinks are not supported; copy the intended files into the folder first')
    output.mkdir(parents=True)
    rows, renamed = [], {}
    for source in sources:
        rel = source.relative_to(folder)
        target = output / rel
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        if not source.is_file():
            raise RuntimeError(f'Not a regular file: {rel}')
        target.parent.mkdir(parents=True, exist_ok=True)
        before = source.stat().st_size
        action = 'copied'
        suffix = source.suffix.lower()
        command = None
        if suffix in IMAGES | VIDEOS:
            width, height, rate = probe(source)
            if suffix in IMAGES and max(width, height) > 1600:
                command = ['-vf', 'scale=w=min(1600\\,iw):h=min(1600\\,ih):force_original_aspect_ratio=decrease',
                           '-frames:v', '1']
                action = f'image {width}x{height} -> within 1600x1600'
            elif suffix in VIDEOS and (height > 1080 or rate > 8_000_000):
                # H.264/AAC cannot be stored in WebM/Ogg. Use MP4 for containers
                # other than MP4, MOV and Matroska, then repair literal references.
                if suffix not in {'.mp4', '.m4v', '.mov', '.mkv'}:
                    target = target.with_suffix('.mp4')
                    new_rel = target.relative_to(output)
                    if (folder / new_rel).exists() or target.exists():
                        raise RuntimeError(f'Converted filename would collide: {new_rel}')
                    renamed[rel.as_posix()] = new_rel.as_posix()
                command = ['-map', '0:v:0', '-map', '0:a:0?',
                           '-vf', 'scale=w=trunc(iw*min(1\\,1080/ih)/2)*2:h=trunc(min(ih\\,1080)/2)*2',
                           '-c:v', 'libx264', '-crf', '23', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart']
                action = f'video {width}x{height}, {rate / 1_000_000:.1f} Mbit/s -> H.264, height <=1080'
        if command is None:
            shutil.copy2(source, target)
        else:
            run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-n', '-i', str(source),
                 *command, str(target)])
        rows.append([rel.as_posix(), before, target, action])

    if renamed:
        for row in rows:
            target = row[2]
            if target.suffix.lower() not in TEXT:
                continue
            original = target.read_text(encoding='utf-8')
            mapping = {}
            for old, new in renamed.items():
                # Handle root-relative, document-relative and explicit ./ paths.
                a = Path(os.path.relpath(output / old, target.parent)).as_posix()
                b = Path(os.path.relpath(output / new, target.parent)).as_posix()
                mapping.update({a: b, './' + a: './' + b, '/' + old: '/' + new})
            updated = rewrite(original, mapping)
            if updated != original:
                target.write_text(updated, encoding='utf-8')
                row[3] = 'media references updated'
        for old, new in renamed.items():
            print(f'Renamed {old} -> {new}; updated literal text references. Check dynamically constructed paths.')

    print(f"{'File':40} {'Before (bytes)':>14} {'After (bytes)':>14}  Change")
    before_total = after_total = 0
    for name, before, target, action in rows:
        after = target.stat().st_size
        before_total += before
        after_total += after
        print(f'{name:40} {before:14,d} {after:14,d}  {action}')
    print(f"{'TOTAL':40} {before_total:14,d} {after_total:14,d}")
    print(f'Output: {output}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dir', type=Path)
    parser.add_argument('--out', type=Path, help='New output folder (default: <dir>-small)')
    args = parser.parse_args()
    output = args.out or args.dir.resolve().with_name(args.dir.resolve().name + '-small')
    try:
        shrink(args.dir, output)
    except (RuntimeError, OSError, ValueError, KeyError) as exc:
        print(f'Error: {exc}\nInput was not changed. Any partial output is not ready to publish.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
