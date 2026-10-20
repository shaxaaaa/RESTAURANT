#!/usr/bin/env python3
"""Adds the Uzbek voice-over to the finished video.

It reads narration.json (the same file the subtitles were built from), creates one
audio clip per narration segment, fits every clip into its subtitle time slot,
ducks the ambient soundscape under the voice and muxes the result into a new MP4.

Two voice sources are supported:

  1) Neural Uzbek TTS (Microsoft Edge "uz-UZ" voices, free, needs internet):
       pip install edge-tts numpy
       python3 add_voiceover.py --video asmo_binti_abu_bakr.mp4 --voice uz-UZ-SardorNeural
     (female voice: --voice uz-UZ-MadinaNeural)

  2) A human narrator: record each segment as seg_01.wav, seg_02.wav, ... (the order of
     narration.json / NARRATION_SCRIPT.md) and run
       python3 add_voiceover.py --video asmo_binti_abu_bakr.mp4 --recordings ./my_takes

Requires ffmpeg on PATH.
"""
import argparse
import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import wave

import numpy as np

SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))

# Spellings that help the TTS engine pronounce names and terms naturally.
TTS_FIXES = [
    ('ʻ', "'"), ('’', "'"), ('ʼ', "'"),
    ('“', ''), ('”', ''), (' — ', ', '),
    ('Zotun-nitoqayn', 'Zotun nitoqayn'),
    ('sollallohu alayhi vasallam', 'sollallohu alayhi va sallam'),
]


def tts_text(s):
    for a, b in TTS_FIXES:
        s = s.replace(a, b)
    return re.sub(r'\s+', ' ', s).strip()


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def read_wav(path):
    with wave.open(path) as w:
        n = w.getnframes(); ch = w.getnchannels()
        x = np.frombuffer(w.readframes(n), dtype='<i2').astype(np.float64) / 32768
    return x.reshape(-1, ch).mean(axis=1) if ch > 1 else x


def to_wav(src, dst, tempo=1.0):
    af = ['-af', f'atempo={tempo:.4f}'] if abs(tempo - 1) > 1e-3 else []
    run(['ffmpeg', '-y', '-i', src, *af, '-ac', '1', '-ar', str(SR), '-sample_fmt', 's16', dst])


def trim(x, thr=0.01):
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(0.03 * SR)); b = min(len(x), idx[-1] + int(0.08 * SR))
    return x[a:b]


async def synth_all(segments, voice, rate, outdir):
    import edge_tts
    paths = []
    for i, s in enumerate(segments, 1):
        p = os.path.join(outdir, f'seg_{i:02d}.mp3')
        await edge_tts.Communicate(tts_text(s['text']), voice, rate=rate).save(p)
        print(f'  TTS {i:02d}/{len(segments)}: {s["text"][:60]}…')
        paths.append(p)
    return paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--video', required=True)
    ap.add_argument('--out', default=None)
    ap.add_argument('--voice', default='uz-UZ-SardorNeural')
    ap.add_argument('--rate', default='-6%', help='TTS speaking rate, e.g. -10%% (slower) or +0%%')
    ap.add_argument('--recordings', default=None, help='folder with seg_01.wav … from a human narrator')
    ap.add_argument('--soundscape', default=None, help='optional separate ambience WAV (defaults to the video audio)')
    ap.add_argument('--voice-gain-db', type=float, default=0.0)
    a = ap.parse_args()
    if not shutil.which('ffmpeg'):
        sys.exit('ffmpeg is required')
    nar = json.load(open(os.path.join(HERE, 'narration.json'), encoding='utf-8'))
    segs = nar['segments']
    dur = float(nar['duration'])
    tmp = tempfile.mkdtemp(prefix='vo_')

    if a.recordings:
        srcs = [os.path.join(a.recordings, f'seg_{i:02d}.wav') for i in range(1, len(segs) + 1)]
        missing = [p for p in srcs if not os.path.exists(p)]
        if missing:
            sys.exit('missing recordings: ' + ', '.join(missing))
    else:
        try:
            import edge_tts  # noqa: F401
        except ImportError:
            sys.exit('pip install edge-tts   (or use --recordings)')
        print(f'Synthesising {len(segs)} segments with {a.voice} …')
        srcs = asyncio.run(synth_all(segs, a.voice, a.rate, tmp))

    n = int(dur * SR)
    voice = np.zeros(n)
    report = []
    for i, (s, src) in enumerate(zip(segs, srcs)):
        w = os.path.join(tmp, f'v{i:02d}.wav')
        to_wav(src, w)
        x = trim(read_wav(w))
        nxt = segs[i + 1]['start'] if i + 1 < len(segs) else dur - 1.0
        slot = max(nxt - s['start'] - 0.15, 0.5)
        tempo = 1.0
        if len(x) / SR > slot:
            tempo = min(len(x) / SR / slot, 1.20)
            to_wav(src, w, tempo)
            x = trim(read_wav(w))
        x = x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * 0.09 * 10 ** (a.voice_gain_db / 20)
        i0 = int(s['start'] * SR)
        x = x[: n - i0]
        voice[i0:i0 + len(x)] += x
        report.append((i + 1, s['start'], len(x) / SR, slot, tempo))

    # ambience: either a given WAV or the audio track of the video
    amb_path = a.soundscape
    if not amb_path:
        amb_path = os.path.join(tmp, 'amb.wav')
        run(['ffmpeg', '-y', '-i', a.video, '-vn', '-ac', '2', '-ar', str(SR), '-sample_fmt', 's16', amb_path])
    with wave.open(amb_path) as wv:
        amb = np.frombuffer(wv.readframes(wv.getnframes()), dtype='<i2').astype(np.float64).reshape(-1, wv.getnchannels()) / 32768
    if amb.shape[1] == 1:
        amb = np.repeat(amb, 2, axis=1)
    amb = np.pad(amb, ((0, max(0, n - len(amb))), (0, 0)))[:n]

    # ducking envelope (attack ~60 ms, release ~400 ms)
    env = np.abs(voice) > 0.004
    k = int(0.4 * SR)
    env = np.convolve(env.astype(float), np.ones(k) / k, mode='same')
    env = np.clip(env * 3, 0, 1)
    duck = 1 - 0.6 * env
    mix = amb * duck[:, None] + voice[:, None]
    peak = np.abs(mix).max()
    if peak > 0.97:
        mix *= 0.97 / peak
    mix_path = os.path.join(tmp, 'mix.wav')
    with wave.open(mix_path, 'wb') as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR)
        wv.writeframes((mix * 32767).astype('<i2').tobytes())

    out = a.out or os.path.splitext(a.video)[0] + '_ovozli.mp4'
    run(['ffmpeg', '-y', '-i', a.video, '-i', mix_path, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
         '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out])
    print('\nSegment  start   voice  slot   tempo')
    for r in report:
        flag = '  <-- tight, consider a slower/shorter take' if r[4] >= 1.19 else ''
        print(f'  {r[0]:02d}   {r[1]:6.1f}  {r[2]:5.1f}  {r[3]:5.1f}  x{r[4]:.2f}{flag}')
    print('\nDone:', out)


if __name__ == '__main__':
    main()
