"""Writes Uzbek subtitles (SRT) from narration.json with the same timing the video uses.
Usage: python3 make_srt.py [out.srt]"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
nar = json.load(open(os.path.join(HERE, 'narration.json'), encoding='utf-8'))


def ts(x):
    h, r = divmod(x, 3600); m, s = divmod(r, 60)
    return f'{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}'


cues = []
for seg in nar['segments']:
    total = sum(len(x) for x in seg['subs'])
    t = seg['start']
    for line in seg['subs']:
        d = (seg['end'] - seg['start']) * len(line) / total
        cues.append((t, t + d, line)); t += d
cues.append((175.6, 179.5, 'Ilm — omonat. Uni asrash va yetkazish — mas’uliyat.'))
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'asmo_binti_abu_bakr.uz.srt')
with open(out, 'w', encoding='utf-8') as f:
    for i, (a, b, txt) in enumerate(cues, 1):
        f.write(f'{i}\n{ts(a)} --> {ts(b)}\n{txt}\n\n')
print('wrote', out, len(cues), 'cues')
