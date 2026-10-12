"""Synthesises the 15-second soundtrack: a music-box arrangement of "Jingle Bells"
(public domain) with sleigh bells, a soft pad, a bottle-opening fizz and sparkle chimes.
Usage: python3 audio.py out.wav
"""
import sys
import wave
import numpy as np

SR = 48000
DUR = 15.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
L = np.zeros(N)
R = np.zeros(N)


def add(sig, t0, gain=1.0, pan=0.0):
    i0 = int(t0 * SR)
    if i0 >= N:
        return
    sig = sig[: N - i0]
    l = np.cos((pan + 1) * np.pi / 4)
    r = np.sin((pan + 1) * np.pi / 4)
    L[i0:i0 + len(sig)] += sig * gain * l
    R[i0:i0 + len(sig)] += sig * gain * r


def note_hz(name):
    names = {'C': -9, 'D': -7, 'E': -5, 'F': -4, 'G': -2, 'A': 0, 'B': 2}
    n = names[name[0]]
    rest = name[1:]
    if rest.startswith('#'):
        n += 1
        rest = rest[1:]
    octave = int(rest)
    return 440.0 * 2 ** ((n + (octave - 4) * 12) / 12)


def bell(f, dur=2.2, bright=1.0):
    t = np.arange(int(dur * SR)) / SR
    partials = [(1, 1.0, 1.6), (2.0, 0.45 * bright, 2.6), (3.01, 0.22 * bright, 3.8),
                (4.17, 0.12 * bright, 5.0), (5.43, 0.07 * bright, 6.5)]
    s = sum(a * np.sin(2 * np.pi * f * m * t + rng.random() * 6) * np.exp(-t * d) for m, a, d in partials)
    s *= np.minimum(t / 0.002, 1)
    return s


def pluck_bass(f, dur=0.9):
    t = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)
    return s * np.exp(-t * 4.5) * np.minimum(t / 0.004, 1)


def pad(freqs, dur):
    t = np.arange(int(dur * SR)) / SR
    s = np.zeros_like(t)
    for f in freqs:
        for det in (-0.12, 0.0, 0.11):
            ff = f * 2 ** (det / 12)
            ph = rng.random() * 6
            s += sum(np.sin(2 * np.pi * ff * k * t + ph) / k ** 1.4 for k in range(1, 6))
    env = np.minimum(t / 0.35, 1) * np.minimum((dur - t) / 0.4, 1)
    return s * np.clip(env, 0, 1) / (len(freqs) * 3)


def jingle(dur=0.25, level=1.0):
    t = np.arange(int(dur * SR)) / SR
    s = np.zeros_like(t)
    for _ in range(6):
        f = rng.uniform(4800, 9500)
        s += np.sin(2 * np.pi * f * t + rng.random() * 6) * np.exp(-t * rng.uniform(18, 35))
    noise = rng.standard_normal(len(t))
    noise = np.diff(noise, prepend=0)  # high-pass tilt
    s += noise * 0.25 * np.exp(-t * 40)
    return s * level * 0.12


# ---------------- music ----------------
BPM = 136.0
beat = 60.0 / BPM
start = 0.70
melody = [
    ('E5', 1), ('E5', 1), ('E5', 2),
    ('E5', 1), ('E5', 1), ('E5', 2),
    ('E5', 1), ('G5', 1), ('C5', 1.5), ('D5', 0.5),
    ('E5', 4),
    ('F5', 1), ('F5', 1), ('F5', 1.5), ('F5', 0.5),
    ('F5', 1), ('E5', 1), ('E5', 1), ('E5', 0.5), ('E5', 0.5),
    ('G5', 1), ('G5', 1), ('F5', 1), ('D5', 1),
    ('C5', 4),
]
t = start
for i, (n, b) in enumerate(melody):
    f = note_hz(n)
    last = i == len(melody) - 1
    add(bell(f, 3.5 if last else 2.0), t, 0.30, -0.1)
    add(bell(f * 2, 1.4, 0.6), t, 0.07, 0.25)  # glockenspiel octave
    t += b * beat

chords = [['C4', 'E4', 'G4'], ['C4', 'E4', 'G4'], ['C4', 'E4', 'G4'], ['C4', 'E4', 'G4'],
          ['F3', 'A3', 'C4', 'F4'], ['C4', 'E4', 'G4'], ['G3', 'B3', 'D4', 'F4'], ['C4', 'E4', 'G4', 'C5']]
bass = ['C3', 'C3', 'C3', 'C3', 'F2', 'C3', 'G2', 'C3']
bass5 = ['G2', 'G2', 'G2', 'G2', 'C3', 'G2', 'D3', 'G2']
for bar in range(8):
    tb = start + bar * 4 * beat
    last = bar == 7
    add(pad([note_hz(n) for n in chords[bar]], 4 * beat + (1.6 if last else 0.15)), tb, 0.10 if bar < 4 else 0.13)
    add(pluck_bass(note_hz(bass[bar])), tb, 0.22)
    if not last:
        add(pluck_bass(note_hz(bass5[bar])), tb + 2 * beat, 0.18)
    else:
        add(pluck_bass(note_hz('C2'), 2.5), tb, 0.25)

# sleigh bells on eighth notes (accent on beats), entering softly
tt = start
while tt < start + 28 * beat + 0.01:
    k = round((tt - start) / (beat / 2))
    lvl = (1.0 if k % 2 == 0 else 0.6) * min(1.0, 0.35 + (tt - start) / 3.0)
    add(jingle(0.22, lvl), tt + rng.normal(0, 0.004), 1.0, 0.45)
    tt += beat / 2
# final shake
roll = np.concatenate([jingle(0.05, 0.8) for _ in range(30)])
add(roll * np.linspace(1, 0, len(roll)), start + 28 * beat, 0.9, 0.45)

# ---------------- sound design ----------------
# opening magic: harp-like rising arpeggio
for i, n in enumerate(['C5', 'E5', 'G5', 'C6', 'E6', 'G6', 'C7']):
    add(bell(note_hz(n), 2.5, 0.5), 0.05 + i * 0.07, 0.06, -0.6 + i * 0.2)

# bottle opening "pssst" + fizz at the cut to the macro shot
def fizz(t0):
    n = int(2.8 * SR)
    t = np.arange(n) / SR
    w = rng.standard_normal(n)
    hp = np.diff(np.diff(w, prepend=0), prepend=0)
    psst = hp * np.exp(-t * 6.0) * np.minimum(t / 0.01, 1) * 0.10
    pops = np.zeros(n)
    for _ in range(420):
        i = int(rng.uniform(0.05, 2.7) * SR)
        ln = int(0.004 * SR)
        if i + ln < n:
            pops[i:i + ln] += rng.standard_normal(ln) * np.exp(-np.arange(ln) / 40) * rng.uniform(0.2, 1.0)
    pops *= np.exp(-t * 0.8) * 0.06
    add(psst, t0, 1.0, 0.0)
    add(pops, t0 + 0.05, 1.0, 0.15)
fizz(4.80)

# soft whoosh into the end card + sparkle when the logo appears
n = int(1.2 * SR)
t = np.arange(n) / SR
wn = rng.standard_normal(n)
wn = np.convolve(wn, np.ones(40) / 40, mode='same')
whoosh = wn * np.sin(np.pi * t / 1.2) ** 2 * 0.25
add(whoosh, 9.4, 1.0, -0.3)
for i, n_ in enumerate(['G6', 'C7', 'E7', 'G7', 'C8']):
    add(bell(note_hz(n_), 1.8, 0.3), 11.3 + i * 0.05, 0.05, 0.5 - i * 0.2)

# ---------------- simple reverb + master ----------------
def reverb(x, seconds=1.8, mix=0.22, seed=0):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR * 3.2)
    ir[0] = 0
    ir /= np.sqrt(np.sum(ir ** 2))
    m = len(x) + n
    y = np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(ir, m), m)[: len(x)]
    return x * (1 - mix) + y * mix * 0.7

L = reverb(L, seed=1)
R = reverb(R, seed=2)
fade = np.ones(N)
fi = int(0.05 * SR)
fade[:fi] = np.linspace(0, 1, fi)
fo = int(0.6 * SR)
fade[-fo:] = np.linspace(1, 0, fo) ** 1.5
L *= fade
R *= fade
peak = max(np.abs(L).max(), np.abs(R).max())
L = np.tanh(L / peak * 1.2) * 0.89 / np.tanh(1.2)
R = np.tanh(R / peak * 1.2) * 0.89 / np.tanh(1.2)

out = sys.argv[1] if len(sys.argv) > 1 else 'soundtrack.wav'
data = (np.stack([L, R], axis=1) * 32767).astype('<i2')
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(data.tobytes())
print('wrote', out)
