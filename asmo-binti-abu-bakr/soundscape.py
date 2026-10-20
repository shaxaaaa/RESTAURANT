"""Vocal-free ambient soundscape for the 180 s documentary (no melodic instruments):
desert wind, a soft low drone that swells at key moments, night crickets, quill scratches,
page rustles, a soft cloth tear for the belt scene and gentle transition whooshes.
Mixed quietly so the narration can sit on top.  Usage: python3 soundscape.py out.wav
"""
import sys
import wave
import numpy as np

SR = 48000
DUR = 180.0
N = int(SR * DUR)
rng = np.random.default_rng(11)
t = np.arange(N) / SR


def band_noise(n, lo, hi, seed):
    r = np.random.default_rng(seed)
    spec = np.fft.rfft(r.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    mask = np.clip((f - lo * 0.7) / (lo * 0.3 + 1e-9), 0, 1) * np.clip((hi * 1.3 - f) / (hi * 0.3), 0, 1)
    out = np.fft.irfft(spec * mask, n)
    return out / (np.std(out) + 1e-12)


def env_points(points):
    """piecewise-linear envelope from (time, value) pairs"""
    ts, vs = zip(*points)
    return np.interp(t, ts, vs)


def smooth_lfo(rate, seed, depth=1.0):
    r = np.random.default_rng(seed)
    k = int(DUR * rate) + 4
    pts = r.random(k)
    x = np.linspace(0, DUR, k)
    v = np.interp(t, x, pts)
    # smooth further with a moving average
    w = int(SR / rate / 2)
    c = np.cumsum(np.insert(v, 0, 0))
    v = (c[w:] - c[:-w]) / w
    v = np.pad(v, (0, N - len(v)), mode='edge')
    return 1 - depth + depth * v


L = np.zeros(N)
R = np.zeros(N)

# ---------------- wind ----------------
desert = env_points([(0, 0.0), (1.5, 1.0), (14, 1.0), (16, 0.6), (22, 0.45), (30, 0.25), (39, 0.25), (40, 0.75), (48, 0.75),
                     (49, 0.15), (74, 0.15), (75, 0.08), (110, 0.08), (116, 0.15), (145, 0.15), (146, 0.95), (160, 0.95),
                     (161, 0.3), (180, 0.2)])
for i, (lo, hi, g) in enumerate([(80, 400, 1.0), (300, 1500, 0.55), (1200, 5000, 0.18)]):
    nL = band_noise(N, lo, hi, 100 + i)
    nR = band_noise(N, lo, hi, 200 + i)
    gust = smooth_lfo(0.12 + 0.05 * i, 30 + i, 0.8) ** 2
    L += nL * gust * g * desert * 0.030
    R += nR * gust[::-1] * g * desert * 0.030

# room tone for interiors
room = env_points([(0, 0), (22, 0), (24, 1), (39, 1), (40, 0), (48, 0), (49, 1), (145, 1), (146, 0), (160, 0), (162, 0.8), (180, 0.6)])
rt = band_noise(N, 60, 600, 400)
L += rt * room * 0.006
R += np.roll(rt, 2400) * room * 0.006

# ---------------- low drone (D) ----------------
drone_env = env_points([(0, 0), (3, 0.7), (14, 0.9), (16, 0.55), (39, 0.55), (41, 0.8), (66, 0.8), (68, 1.0), (75, 0.9),
                        (77, 0.55), (110, 0.6), (117, 0.75), (145, 0.7), (147, 0.85), (166, 0.85), (170, 1.0), (178, 0.8), (180, 0)])
drone = np.zeros(N)
for f, a in [(73.42, 1.0), (110.0, 0.55), (146.83, 0.45), (220.0, 0.16), (293.66, 0.08)]:
    for det in (-0.25, 0.25):
        drone += a * np.sin(2 * np.pi * (f + det) * t + rng.random() * 6)
drone *= 0.5 + 0.5 * smooth_lfo(0.05, 55, 0.6)
drone *= drone_env * 0.020
# brighter shimmer at the "Zotun-nitoqayn" reveal and at the final prayer
shim_env = env_points([(0, 0), (66.5, 0), (68.5, 1), (74.5, 0.6), (76, 0), (165.5, 0), (168, 0.8), (179, 0.4), (180, 0)])
shim = sum(np.sin(2 * np.pi * f * t + rng.random() * 6) * a for f, a in [(587.33, 1.0), (880.0, 0.6), (1174.66, 0.35)])
shim *= (0.6 + 0.4 * np.sin(2 * np.pi * 0.3 * t)) * shim_env * 0.0035
L += drone + shim
R += drone + np.roll(shim, 960)


def add(sig, t0, gain, pan=0.0):
    i0 = int(t0 * SR)
    sig = sig[: max(0, N - i0)]
    L[i0:i0 + len(sig)] += sig * gain * (1 - pan) * 0.5 * 2 ** 0.5
    R[i0:i0 + len(sig)] += sig * gain * (1 + pan) * 0.5 * 2 ** 0.5


# ---------------- night crickets (39–48 s) ----------------
for k in range(70):
    t0 = 39.5 + rng.random() * 8.5
    n = int(0.12 * SR)
    tt = np.arange(n) / SR
    chirp = np.sin(2 * np.pi * 4300 * tt) * (np.sin(2 * np.pi * 30 * tt) > 0) * np.exp(-tt * 18)
    add(chirp, t0, 0.0035, rng.uniform(-0.8, 0.8))

# ---------------- quill scratches (75–97 s) ----------------
def scratch(dur, seed):
    n = int(dur * SR)
    s = band_noise(n, 2500, 7000, seed)
    tt = np.arange(n) / SR
    strokes = (np.sin(2 * np.pi * rng.uniform(5, 9) * tt) > 0.2) * np.sin(np.pi * tt / dur)
    return s * strokes
for k, t0 in enumerate(np.arange(76.5, 96.0, 2.3)):
    add(scratch(rng.uniform(0.6, 1.3), 500 + k), t0 + rng.uniform(0, 0.8), 0.006, 0.3)

# ---------------- page rustles ----------------
def rustle(seed):
    n = int(0.9 * SR)
    s = band_noise(n, 800, 6000, seed)
    tt = np.arange(n) / SR
    return s * np.exp(-((tt - 0.35) / 0.18) ** 2) * (0.6 + 0.4 * band_noise(n, 5, 40, seed + 1))
for k, t0 in enumerate([30.6, 85.4, 116.8, 138.0]):
    add(rustle(700 + k), t0, 0.010, -0.2)

# ---------------- cloth being divided (58.6–62.4 s) ----------------
n = int(3.8 * SR)
tt = np.arange(n) / SR
tear = band_noise(n, 1500, 6000, 900) * (band_noise(n, 30, 120, 901) > 0.6)
tear *= np.sin(np.pi * tt / 3.8) ** 0.7
add(tear, 58.6, 0.010, 0.1)

# ---------------- gentle transition whooshes ----------------
def whoosh(dur=1.6, seed=0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    return band_noise(n, 150, 1200, seed) * np.sin(np.pi * tt / dur) ** 2
for k, t0 in enumerate([38.4, 74.4, 109.6, 144.6, 158.8]):
    add(whoosh(seed=1000 + k), t0, 0.012, (-1) ** k * 0.4)

# ---------------- master ----------------
fade = np.minimum(1, t / 1.5) * np.minimum(1, (DUR - t) / 2.0)
L *= fade
R *= fade
peak = max(np.abs(L).max(), np.abs(R).max())
target_peak = 0.35  # quiet bed; narration sits above it
L *= target_peak / peak
R *= target_peak / peak
out = sys.argv[1] if len(sys.argv) > 1 else 'soundscape.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.stack([L, R], 1) * 32767).astype('<i2').tobytes())
print('wrote', out)
