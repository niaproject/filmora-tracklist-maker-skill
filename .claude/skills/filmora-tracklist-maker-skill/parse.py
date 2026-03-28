#!/usr/bin/env python3
"""
Filmora .wfp project file parser
Usage: python parse.py <path-to-file.wfp> [options]
  --ext=<ext>          Output file extension (default: txt)
  --no-seq             Hide sequential numbers
  --min-duration=<sec> Exclude clips shorter than this (default: 10)
  --repeat-below=<N>   Collapse entries from N onward into "Repeat" (default: 0=off)
"""

import sys
import json
import zipfile
import os
import re
import math

def usage():
    print('Usage: python parse.py <path-to-file.wfp> [--ext=txt] [--no-seq] [--min-duration=10] [--repeat-below=0]', file=sys.stderr)
    sys.exit(1)

if len(sys.argv) < 2:
    usage()

wfp = sys.argv[1]
args = sys.argv[2:]

# --- Parse options ---
def get_opt(prefix, default):
    for a in args:
        if a.startswith(prefix):
            return a[len(prefix):]
    return default

ext          = get_opt('--ext=', 'txt')
show_seq     = '--no-seq' not in args
min_duration = float(get_opt('--min-duration=', '10'))
repeat_below = int(get_opt('--repeat-below=', '0'))

# --- Open .wfp as ZIP ---
try:
    zf = zipfile.ZipFile(wfp, 'r')
except FileNotFoundError:
    print(f'Error: File not found: {wfp}', file=sys.stderr)
    sys.exit(1)
except zipfile.BadZipFile:
    print(f'Error: Not a valid .wfp file: {wfp}', file=sys.stderr)
    sys.exit(1)

def read_json(inner_path):
    with zf.open(inner_path) as f:
        return json.load(f)

def format_time(units):
    """units are in 100-nanosecond intervals"""
    total_sec = int(units // 10_000_000)
    h = total_sec // 3600
    m = (total_sec % 3600) // 60
    s = total_sec % 60
    return f'{h:02d}:{m:02d}:{s:02d}'

def clip_duration_sec(clip):
    tl_end   = clip.get('tlEnd')
    tl_begin = clip.get('tlBegin')
    if tl_end is not None and tl_begin is not None:
        return (tl_end - tl_begin) / 10_000_000
    duration = clip.get('duration')
    if duration is not None:
        return duration / 10_000_000
    return math.inf  # unknown — include by default

TRACK_TYPE = {1: 'video', 2: 'audio'}

# --- Load project_info.json ---
try:
    info = read_json('ProjectFolder/project_info.json')
except KeyError:
    print('Error: project_info.json not found in the .wfp file.', file=sys.stderr)
    sys.exit(1)

# --- Load medias_info.json ---
try:
    medias_info = read_json('ProjectFolder/Medias/medias_info.json')
except KeyError:
    print('Error: medias_info.json not found in the .wfp file.', file=sys.stderr)
    sys.exit(1)

# --- Find timeline.wesproj ---
names = zf.namelist()
tl_match = next((n for n in names if re.match(r'ProjectFolder/Medias/[^/]+/timeline\.wesproj', n)), None)
if not tl_match:
    print('Error: timeline.wesproj not found in the .wfp file.', file=sys.stderr)
    sys.exit(1)
timeline = read_json(tl_match)

# --- Build resource map: sourceUuid -> resource info ---
resource_map = {r['sourceUuid']: r for r in (timeline.get('resources') or [])}

# --- Build media name map ---
media_names = {m['id']: m['name'] for m in (medias_info.get('media_items') or {}).values()}

# --- Find main timeline ---
current_tl_id = timeline.get('currentTimelineId')
main_tl = next((t for t in timeline.get('timelineInfos', []) if t.get('timelineId') == current_tl_id), None)
if not main_tl:
    print('Error: Main timeline not found.', file=sys.stderr)
    sys.exit(1)

# --- Output ---
project_name   = info.get('project_file_name') or os.path.splitext(os.path.basename(wfp))[0]
fps_num, fps_den = (info.get('project_timeline_framerate') or [30, 1])
fps            = fps_num / fps_den
w, h           = (info.get('project_timeline_resolution') or [0, 0])
total_duration = format_time(info.get('project_timeline_duration') or 0)

lines = []
def out(s=''):
    lines.append(s)

out('=' * 60)
out(f'Project : {project_name}')
out(f'Duration: {total_duration}')
out(f'FPS     : {int(fps) if fps == int(fps) else fps}')
out(f'Res     : {w}x{h}')
out('=' * 60)

audio_track_num = 0

for track in main_tl.get('trackInfos', []):
    track_type = TRACK_TYPE.get(track.get('trackType'), 'other')
    if track_type != 'audio':
        continue

    all_clips = [c for c in (track.get('clipList') or []) if c.get('tlBegin') is not None]
    audio_track_num += 1

    if audio_track_num > 1:
        continue  # only output the first audio track

    clips = [c for c in all_clips if clip_duration_sec(c) >= min_duration]
    if not clips:
        continue

    out('')
    out(f'[AUDIO Track {audio_track_num}]')
    repeat_appended = False

    for ci, clip in enumerate(clips):
        num = ci + 1
        if repeat_below > 0 and num >= repeat_below:
            if not repeat_appended:
                seq = f'{num:>2}. ' if show_seq else ''
                out(f'  {seq}Repeat')
                repeat_appended = True
            continue

        res      = resource_map.get(clip.get('sourceUuid'), {})
        raw_name = res.get('filename') or clip.get('filename') or ''
        name     = os.path.splitext(os.path.basename(raw_name))[0] if raw_name else '(unknown)'
        start    = format_time(clip.get('tlBegin', 0))
        seq      = f'{num:>2}. ' if show_seq else ''
        out(f'  {seq}{start}  {name}')

out('')
out('=' * 60)

output = '\n'.join(lines)
print(output)

out_path = os.path.join(os.path.dirname(os.path.abspath(wfp)), os.path.splitext(os.path.basename(wfp))[0] + '.' + ext)
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(output)
print(f'\nSaved: {out_path}', file=sys.stderr)
