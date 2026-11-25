"""Background score v2 — energetic, rhythm-led cinematic beds (original; no samples, no bells/chimes).

Usage:  python tools/make-score.py <out_dir> [bed ...]   -> <out_dir>/<bed>.wav (48 kHz stereo, seamless loops)
Encode: ffmpeg -i <bed>.wav -c:a libopus -b:a 160k assets/media/score/<bed>.ogg   (Opus = gapless looping)

Shared sonic identity: D-rooted keys, the same hybrid "pulse" synth, taiko/toms + spiccato strings + brass.
Energy rises section by section; every bed has a strong rhythmic foundation.

  prestige     D minor · 92  · opening / pre-reveal: taiko heartbeat, hybrid pulse, dark brass swells
  legacy       D major · 104 · Jain Group story: spiccato strings, piano, toms, uplifting horns
  momentum     D major · 116 · portfolio: driving 16ths, kick/snare, sidechained pulse, brass hits
  luxury       F major · 98  · Ananta specs: sleek kick/snare groove, warm pulse, piano, strings (aspirational)
  opportunity  E major · 124 · commercial: four-on-the-floor + claps, pumping synth bass, brass stabs (victorious)
  tension      A minor · 108 · rewards lead-in: low ostinato, taiko build every 4 bars, string tremolo
  honour       G major · 96  · awards & support: anthemic toms, strings, horns
  finale       D major · 128 · call to action: full drums, brass fanfare figures, strings, big toms (victorious)
"""
import os
import sys
import wave
import numpy as np
from scipy.signal import lfilter

SR = 48000
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(31)


# ---------------- DSP ----------------
def lp1(x, fc):
    fc = np.asarray(fc, float)
    if fc.ndim == 0:
        a = np.exp(-2 * np.pi * fc / SR)
        return lfilter([1 - a], [1, -a], x)
    y, zi = np.empty_like(x), np.zeros(1)
    for i in range(0, len(x), 256):
        a = np.exp(-2 * np.pi * float(fc[i:i + 256].mean()) / SR)
        y[i:i + 256], zi = lfilter([1 - a], [1, -a], x[i:i + 256], zi=zi)
    return y


def lp(x, fc, order=2):
    for _ in range(order):
        x = lp1(x, fc)
    return x


def hp(x, fc, order=2):
    return x - lp(x, fc, order)


def tax(d):
    return np.arange(int(d * SR)) / SR


def saw(f, t, ph=0.0):
    p = np.cumsum(np.broadcast_to(f, t.shape) / SR) + ph
    return 2 * (p % 1.0) - 1


def sq(f, t, ph=0.0):
    p = np.cumsum(np.broadcast_to(f, t.shape) / SR) + ph
    return np.where((p % 1.0) < 0.5, 1.0, -1.0)


def adsr(n, a, d, s, r):
    a, d, r = max(1, int(a * SR)), max(1, int(d * SR)), max(1, int(r * SR))
    sus = max(0, n - a - d - r)
    e = np.concatenate([np.linspace(0, 1, a), np.linspace(1, s, d), np.full(sus, s), np.linspace(s, 0, r)])
    return np.pad(e, (0, max(0, n - len(e))))[:n]


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def noise(n):
    return rng.standard_normal(n)


# ---------------- drums ----------------
def kick(vel=1.0, punch=1.0):
    t = tax(0.5)
    f = 46 + 120 * np.exp(-t * 28)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6.5)
    click = hp(noise(len(t)), 1500) * np.exp(-t * 180) * 0.35 * punch
    return np.tanh(1.6 * (body + click)) * 0.9 * vel


def snare(vel=1.0):
    t = tax(0.4)
    body = (np.sin(2 * np.pi * 185 * t) + 0.5 * np.sin(2 * np.pi * 330 * t)) * np.exp(-t * 22)
    wires = lp(hp(noise(len(t)), 1800), 9000) * np.exp(-t * 11)
    return (0.55 * body + 0.8 * wires) * 0.55 * vel


def clap(vel=1.0):
    t = tax(0.3)
    e = np.zeros_like(t)
    for o in (0, 0.009, 0.019, 0.03):
        i = int(o * SR)
        e[i:] += np.exp(-t[: len(t) - i] * 28)
    return lp(hp(noise(len(t)), 900), 7000) * e * 0.22 * vel


def hat(vel=1.0, open_=False):
    t = tax(0.25 if open_ else 0.06)
    return hp(noise(len(t)), 7000, 3) * np.exp(-t * (14 if open_ else 70)) * 0.13 * vel


def tom(n=45, vel=1.0):
    t = tax(0.7)
    f = midi(n) * (1 + 0.35 * np.exp(-t * 20))
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6) + lp(noise(len(t)), 1200) * np.exp(-t * 35) * 0.4) * 0.6 * vel


def taiko(vel=1.0):
    t = tax(1.2)
    f = 62 * (1 + 0.5 * np.exp(-t * 25))
    skin = lp(noise(len(t)), 600) * np.exp(-t * 30)
    return np.tanh(1.4 * (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.5) + skin)) * 0.85 * vel


def riser_noise(dur, vel=1.0):
    t = tax(dur)
    k = t / dur
    return lp(hp(noise(len(t)), 400 + 4000 * k), 2000 + 9000 * k) * k ** 2.2 * 0.16 * vel


# ---------------- tonal ----------------
def spic(n, dur, vel=1.0, bright=3200):
    t = tax(dur)
    x = sum(saw(midi(n) * (1 + d), t, rng.random()) for d in (-0.005, 0.0, 0.006)) / 3
    return lp(x, bright, 2) * adsr(len(t), 0.006, 0.07, 0.35, 0.05) * 0.5 * vel


def pad(notes, dur, att=0.8, rel=1.0, bright=2400):
    t = tax(dur)
    x = sum(saw(midi(n) * (1 + d), t, rng.random()) for n in notes for d in (-0.007, -0.002, 0.003, 0.008))
    return lp(x, bright, 2) / (len(notes) * 4) * 1.4 * adsr(len(t), att, 0.4, 0.85, rel)


def brass(notes, dur, vel=1.0, att=0.12, bright=1.0):
    t = tax(dur)
    x = sum(saw(midi(n) * (1 + d), t, rng.random()) for n in notes for d in (-0.003, 0.0, 0.004))
    e = adsr(len(t), att, 0.3, 0.75, 0.25)
    return lp(x, (700 + 2600 * e) * bright, 2) * e * 0.16 / len(notes) * 2 * vel


def stab(notes, vel=1.0):
    return brass(notes, 0.32, vel * 1.2, att=0.008, bright=1.3)


def pulse(n, dur, vel=1.0, cut=1800):
    t = tax(dur)
    x = 0.6 * saw(midi(n), t) + 0.4 * sq(midi(n) * 1.002, t)
    env = np.exp(-t * 14)
    return lp(x, cut * (0.35 + 0.65 * env), 2) * adsr(len(t), 0.003, 0.05, 0.6, 0.04) * 0.3 * vel


def subbass(n, dur, vel=1.0):
    t = tax(dur)
    x = np.sin(2 * np.pi * midi(n) * t) + 0.25 * np.tanh(3 * np.sin(2 * np.pi * midi(n) * t))
    return x * adsr(len(t), 0.005, 0.1, 0.85, 0.05) * 0.5 * vel


def piano(n, dur=2.2, vel=1.0):
    t = tax(dur)
    f = midi(n)
    x = sum(a * np.sin(2 * np.pi * f * k * (1 + 0.0004 * k * k) * t + rng.random()) * np.exp(-t * d * (0.6 + f / 900))
            for k, (a, d) in enumerate([(1.0, 2.2), (0.5, 3.0), (0.28, 4.2), (0.14, 5.5)], start=1))
    return lp(x, 3500, 1) * np.clip(t / 0.003, 0, 1) * 0.28 * vel


def trem(n, dur, vel=1.0):
    t = tax(dur)
    x = sum(saw(midi(n) * (1 + d), t, rng.random()) for d in (-0.004, 0.004)) / 2
    return lp(x, 2200, 2) * (0.55 + 0.45 * np.sin(2 * np.pi * 13 * t) ** 2) * adsr(len(t), 0.3, 0.2, 0.9, 0.3) * 0.35 * vel


# ---------------- arrangement ----------------
class Track:
    def __init__(self, bpm, bars):
        self.bpm, self.beat = bpm, 60 / bpm
        self.L = bars * 4 * self.beat
        n = int((self.L + 6) * SR)
        self.drums = np.zeros((2, n))
        self.music = np.zeros((2, n))
        self.kicks = []

    def put(self, sig, beat, pan=0.0, gain=1.0, bus='music'):
        buf = self.drums if bus == 'drums' else self.music
        i = int(beat * self.beat * SR)
        j = min(buf.shape[1], i + len(sig))
        if j <= i:
            return
        buf[0, i:j] += sig[: j - i] * np.cos((pan + 1) * np.pi / 4) * gain
        buf[1, i:j] += sig[: j - i] * np.sin((pan + 1) * np.pi / 4) * gain

    def kick(self, beat, vel=1.0):
        self.kicks.append(beat)
        self.put(kick(vel), beat, 0.0, 1.0, 'drums')

    def d(self, sig, beat, pan=0.0, gain=1.0):
        self.put(sig, beat, pan, gain, 'drums')

    def s(self, beats):
        return beats * self.beat


def reverb(buf, seconds=2.2, mix=0.22):
    n = int(seconds * SR)
    tt = np.arange(n) / SR
    out = []
    for ch in range(2):
        ir = noise(n) * np.exp(-tt * 6.9 / seconds)
        ir = lp(ir, 6000, 1)
        ir[: int(0.02 * SR)] = 0
        ir /= np.sqrt(np.sum(ir ** 2))
        L = buf.shape[1] + n
        F = 1 << (L - 1).bit_length()
        wet = np.fft.irfft(np.fft.rfft(buf[ch], F) * np.fft.rfft(ir, F), F)[:L]
        out.append(np.pad(buf[ch], (0, n)) * (1 - mix) + wet * mix * 1.4)
    return np.array(out)


def render(tr, name, duck=0.45, mix=0.22, verb=2.2, rms_db=-19.0, drums=2.4, music=0.6):
    # sidechain: music bus pumps against the kick (modern cinematic energy)
    n = tr.music.shape[1]
    sc = np.ones(n)
    for k in tr.kicks:
        i = int(k * tr.beat * SR)
        m = min(n - i, int(0.35 * SR))
        if m > 0:
            sc[i:i + m] = np.minimum(sc[i:i + m], 1 - duck * np.exp(-np.arange(m) / SR * 11))
    mus = reverb(tr.music * sc * music, verb, mix)
    drm = reverb(tr.drums * drums, 1.4, 0.12)
    full = np.zeros((2, max(mus.shape[1], drm.shape[1])))
    full[:, : mus.shape[1]] += mus
    full[:, : drm.shape[1]] += drm
    L = int(tr.L * SR)
    loop = full[:, :L].copy()
    tail = full[:, L:]
    loop[:, : tail.shape[1]] += tail[:, :L]  # seamless loop
    # glue: gentle compression via soft clip, then loudness target
    loop *= 10 ** (rms_db / 20) / np.sqrt(np.mean(loop ** 2))
    # transparent peak control: only the top ~2 dB is softly limited, so drum transients survive
    knee = 0.75
    a = np.abs(loop)
    loop = np.sign(loop) * np.where(a < knee, a, knee + (1 - knee) * np.tanh((a - knee) / (1 - knee)))
    loop *= min(1.0, 0.89 / np.max(np.abs(loop)))
    pcm = (np.clip(loop.T, -1, 1) * 32767).astype('<i2')
    with wave.open(os.path.join(OUT, name + '.wav'), 'wb') as w:
        w.setnchannels(2), w.setsampwidth(2), w.setframerate(SR), w.writeframes(pcm.tobytes())
    print(f'{name:12s} {tr.L:6.2f}s  {tr.bpm} bpm')


# =================== beds ===================
def prestige():
    tr = Track(92, 16)
    prog = [(50, [50, 57, 62, 65]), (46, [46, 53, 58, 62]), (43, [43, 50, 55, 58]), (45, [45, 52, 57, 61])]
    for b in range(16):
        root, ch = prog[b % 4]
        tr.put(pad(ch, tr.s(4.3), 0.6, 0.8, 1300), b * 4, 0.0, 0.8)
        for k in range(8):
            tr.put(pulse(ch[0] + 12 + (7 if k % 4 == 3 else 0), tr.s(0.45), 0.9 if k % 2 == 0 else 0.6, 1500), b * 4 + k * 0.5, -0.3 + 0.6 * (k % 2), 0.9)
        tr.put(subbass(root - 12, tr.s(3.9), 0.9), b * 4, 0.0, 0.9)
        tr.d(taiko(0.9), b * 4)
        tr.d(taiko(0.6), b * 4 + 2.5)
        tr.kick(b * 4, 0.6)
        tr.kick(b * 4 + 2, 0.5)
        tr.d(tom(40, 0.5), b * 4 + 3.5, 0.2)
        if b % 4 == 2:
            tr.put(brass([ch[0], ch[2]], tr.s(7.5), 0.9, att=0.9), b * 4, -0.1)
        if b % 4 == 3:
            tr.d(riser_noise(tr.s(4), 0.8), b * 4)
    render(tr, 'prestige', duck=0.35, mix=0.28, verb=2.8)


def legacy():
    tr = Track(104, 16)
    prog = [(50, [62, 66, 69]), (45, [61, 64, 69]), (47, [59, 62, 66]), (43, [59, 62, 67])]
    for b in range(16):
        root, ch = prog[b % 4]
        tr.put(pad([c - 12 for c in ch], tr.s(4.2), 0.4, 0.7, 2600), b * 4, 0.0, 0.7)
        for k in range(16):
            n = ch[[0, 1, 2, 1][k % 4]]
            tr.put(spic(n, tr.s(0.24), 1.0 if k % 4 == 0 else 0.7), b * 4 + k * 0.25, 0.4 if k % 2 else -0.4, 0.7)
        for k in range(4):
            tr.put(piano(ch[(k + 2) % 3] + 12, 1.6, 0.6), b * 4 + k + 0.5, 0.2, 0.7)
        tr.put(subbass(root - 12, tr.s(1.9), 0.8), b * 4, 0.0, 0.85)
        tr.put(subbass(root - 12, tr.s(1.9), 0.7), b * 4 + 2, 0.0, 0.85)
        tr.kick(b * 4, 0.75)
        tr.kick(b * 4 + 2.5, 0.6)
        tr.d(snare(0.7), b * 4 + 1)
        tr.d(snare(0.8), b * 4 + 3)
        for k in range(8):
            tr.d(hat(0.6 + 0.3 * (k % 2)), b * 4 + k * 0.5 + 0.5, 0.35)
        if b >= 8:
            tr.put(brass([ch[0], ch[2]], tr.s(3.8), 0.9, att=0.4), b * 4, -0.15)
        if b % 4 == 3:
            for k, n in enumerate((45, 43, 41, 38)):
                tr.d(tom(n, 0.8), b * 4 + 3 + k * 0.25, -0.3 + 0.2 * k)
    render(tr, 'legacy', duck=0.3, mix=0.24)


def momentum():
    tr = Track(116, 16)
    prog = [(50, [62, 66, 69]), (45, [61, 64, 69]), (47, [59, 62, 66]), (43, [59, 62, 67])]
    for b in range(16):
        root, ch = prog[b % 4]
        tr.put(pad([c - 12 for c in ch], tr.s(4.1), 0.2, 0.5, 2800), b * 4, 0.0, 0.6)
        for k in range(16):
            tr.put(spic(ch[[0, 2, 1, 2][k % 4]] + (12 if k >= 12 else 0), tr.s(0.22), 1.0 if k % 4 == 0 else 0.75), b * 4 + k * 0.25, -0.4 if k % 2 else 0.4, 0.7)
            tr.put(pulse(root + 12, tr.s(0.22), 0.8, 2200), b * 4 + k * 0.25, 0.0, 0.5)
        for k in range(8):
            tr.put(subbass(root - 12, tr.s(0.45), 0.9), b * 4 + k * 0.5, 0.0, 0.8)
        for k in range(4):
            tr.kick(b * 4 + k, 0.8)
        tr.d(snare(0.9), b * 4 + 1)
        tr.d(snare(0.9), b * 4 + 3)
        for k in range(16):
            tr.d(hat(0.5 + 0.4 * (k % 2)), b * 4 + k * 0.25, 0.35)
        if b % 2 == 1:
            tr.put(stab([ch[0], ch[2], ch[0] + 12]), b * 4 + 3.5, 0.0, 0.9)
        if b % 4 == 3:
            tr.d(riser_noise(tr.s(4), 0.8), b * 4)
            tr.d(taiko(0.9), b * 4 + 3.5)
    render(tr, 'momentum', duck=0.4, mix=0.2)


def luxury():
    tr = Track(98, 16)
    prog = [(41, [57, 60, 64, 67]), (38, [57, 60, 62, 65]), (46, [58, 62, 65, 69]), (36, [55, 60, 64, 67])]  # Fmaj7 Dm7 Bbmaj7 C
    for b in range(16):
        root, ch = prog[b % 4]
        tr.put(pad(ch, tr.s(4.2), 0.6, 0.8, 2000), b * 4, 0.0, 0.6)
        for k, hit in enumerate((0, 0.75, 1.5, 2.5, 3.0)):
            tr.put(pulse(ch[k % 4], tr.s(0.4), 0.8, 2600), b * 4 + hit, -0.35 + 0.17 * k, 0.6)
        for k in range(4):
            tr.put(piano(ch[(k + 1) % 4] + 12, 1.8, 0.55), b * 4 + k + 0.5, 0.25, 0.6)
        tr.put(subbass(root - 12 + 12 if root < 40 else root - 12, tr.s(1.4), 0.9), b * 4, 0.0, 0.85)
        tr.put(subbass(root - 12 + 12 if root < 40 else root - 12, tr.s(0.9), 0.8), b * 4 + 2.5, 0.0, 0.85)
        tr.kick(b * 4, 0.75)
        tr.kick(b * 4 + 2.5, 0.6)
        tr.d(snare(0.6), b * 4 + 1)
        tr.d(clap(0.7), b * 4 + 3)
        for k in range(8):
            tr.d(hat(0.45 + 0.35 * (k % 2)), b * 4 + k * 0.5 + 0.25, 0.4)
        if b >= 8 and b % 2 == 0:
            tr.put(trem(ch[-1] + 12, tr.s(8), 0.7), b * 4, 0.3)
    render(tr, 'luxury', duck=0.35, mix=0.26, verb=2.4)


def opportunity():
    tr = Track(124, 16)
    prog = [(52, [64, 68, 71]), (47, [63, 66, 71]), (49, [61, 64, 68]), (45, [61, 64, 69])]  # E B C#m A
    for b in range(16):
        root, ch = prog[b % 4]
        tr.put(pad(ch, tr.s(4.1), 0.15, 0.4, 3200), b * 4, 0.0, 0.55)
        seq = [ch[0], ch[1], ch[2], ch[1] + 12, ch[2], ch[1], ch[0] + 12, ch[2]]
        for k in range(16):
            tr.put(pulse(seq[k % 8], tr.s(0.2), 1.0 if k % 4 == 0 else 0.7, 3000), b * 4 + k * 0.25, -0.4 + 0.8 * ((k // 2) % 2), 0.65)
        for k in range(4):
            tr.kick(b * 4 + k, 0.9)
            tr.put(subbass(root - 12, tr.s(0.42), 1.0), b * 4 + k + 0.5, 0.0, 0.85)
            tr.d(hat(0.9, open_=True), b * 4 + k + 0.5, 0.3)
        tr.d(clap(1.0), b * 4 + 1)
        tr.d(clap(1.0), b * 4 + 3)
        tr.d(snare(0.5), b * 4 + 3)
        for k in range(16):
            tr.d(hat(0.35 + 0.3 * (k % 2)), b * 4 + k * 0.25, -0.3)
        if b % 2 == 1:
            tr.put(stab([ch[0], ch[1], ch[2]]), b * 4 + 2.5, 0.0, 0.9)
            tr.put(stab([ch[0], ch[1], ch[2]]), b * 4 + 3.0, 0.0, 0.9)
        if b >= 8:
            tr.put(brass([ch[0], ch[2], ch[0] + 12], tr.s(3.8), 0.8, att=0.3), b * 4, -0.1)
        if b % 4 == 3:
            tr.d(riser_noise(tr.s(4), 0.9), b * 4)
    render(tr, 'opportunity', duck=0.45, mix=0.18, verb=1.8)


def tension():
    tr = Track(108, 8)
    for b in range(8):
        root = [45, 45, 46, 44][b % 4]
        for k in range(16):
            tr.put(spic(root + (12 if k % 4 == 2 else 0), tr.s(0.22), 0.9 if k % 4 == 0 else 0.6, 1800), b * 4 + k * 0.25, -0.3, 0.8)
        tr.put(trem(root + 24, tr.s(4.1), 0.5 + 0.15 * (b % 4)), b * 4, 0.35)
        tr.put(subbass(root - 12, tr.s(3.9), 0.9), b * 4, 0.0, 0.85)
        tr.kick(b * 4, 0.8)
        tr.kick(b * 4 + 1.5, 0.55)
        tr.kick(b * 4 + 2, 0.7)
        tr.d(taiko(0.7), b * 4 + 3)
        if b % 4 == 3:
            for k in range(8):
                tr.d(tom(43 - (k % 3) * 2, 0.4 + 0.08 * k), b * 4 + 2 + k * 0.25, -0.2 + 0.05 * k)
            tr.d(riser_noise(tr.s(4), 0.7), b * 4)
    render(tr, 'tension', duck=0.3, mix=0.24)


def honour():
    tr = Track(96, 16)
    prog = [(43, [55, 59, 62, 67]), (40, [55, 59, 64, 67]), (36, [55, 60, 64, 67]), (38, [54, 57, 62, 66])]  # G Em C D
    for b in range(16):
        root, ch = prog[b % 4]
        tr.put(pad(ch, tr.s(4.3), 0.5, 0.8, 2400), b * 4, 0.0, 0.7)
        for k in range(8):
            tr.put(spic(ch[[0, 2, 1, 3][k % 4]], tr.s(0.45), 0.8 if k % 2 == 0 else 0.6), b * 4 + k * 0.5, 0.35 if k % 2 else -0.35, 0.65)
        for k in range(4):
            tr.put(piano(ch[k] + 12, 2.0, 0.55), b * 4 + k, -0.2, 0.6)
        tr.put(subbass(root - 12 + 12 if root < 40 else root - 12, tr.s(3.9), 0.85), b * 4, 0.0, 0.85)
        tr.kick(b * 4, 0.75)
        tr.kick(b * 4 + 2, 0.65)
        tr.d(snare(0.75), b * 4 + 1)
        tr.d(snare(0.85), b * 4 + 3)
        tr.d(tom(45, 0.6), b * 4 + 3.5, 0.2)
        if b >= 8:
            tr.put(brass([ch[0], ch[2], ch[0] + 12], tr.s(3.9), 0.85, att=0.35), b * 4, 0.1)
        if b % 8 == 7:
            for k, n in enumerate((45, 43, 41, 40, 38, 36)):
                tr.d(tom(n, 0.75), b * 4 + 2.5 + k * 0.25, -0.3 + 0.12 * k)
    render(tr, 'honour', duck=0.3, mix=0.26, verb=2.6)


def finale():
    tr = Track(128, 16)
    prog = [(50, [62, 66, 69]), (47, [62, 66, 71]), (43, [59, 62, 67]), (45, [61, 64, 69])]  # D Bm G A
    for b in range(16):
        root, ch = prog[b % 4]
        tr.put(pad(ch + [ch[0] + 12], tr.s(4.1), 0.2, 0.5, 3200), b * 4, 0.0, 0.6)
        for k in range(16):
            tr.put(spic(ch[[0, 1, 2, 1][k % 4]] + 12 * (k >= 8), tr.s(0.2), 1.0 if k % 4 == 0 else 0.7), b * 4 + k * 0.25, -0.4 if k % 2 else 0.4, 0.65)
        for k in range(4):
            tr.kick(b * 4 + k, 0.95)
            tr.put(subbass(root - 12, tr.s(0.45), 1.0), b * 4 + k + 0.5, 0.0, 0.85)
        tr.d(snare(1.0), b * 4 + 1)
        tr.d(snare(1.0), b * 4 + 3)
        tr.d(clap(0.8), b * 4 + 3)
        for k in range(16):
            tr.d(hat(0.4 + 0.35 * (k % 2)), b * 4 + k * 0.25, 0.3)
        if b % 4 == 0:
            tr.d(taiko(1.0), b * 4)
        # brass fanfare figures on alternate bars, full sustained horns in the second half
        if b % 2 == 0:
            for k, (n, d) in enumerate(((ch[0], 0.5), (ch[1], 0.5), (ch[2], 1.0))):
                tr.put(brass([n + 12, n], tr.s(d * 0.95), 1.0, att=0.02, bright=1.2), b * 4 + [0, 0.5, 1.0][k], 0.0, 0.9)
        if b >= 8:
            tr.put(brass([ch[0], ch[2], ch[0] + 12], tr.s(3.9), 0.85, att=0.25), b * 4, -0.1)
        if b % 4 == 3:
            tr.d(riser_noise(tr.s(4), 0.9), b * 4)
            for k, n in enumerate((45, 43, 41, 38)):
                tr.d(tom(n, 0.9), b * 4 + 3 + k * 0.25)
    render(tr, 'finale', duck=0.45, mix=0.2)


for w in sys.argv[2:] or ['prestige', 'legacy', 'momentum', 'luxury', 'opportunity', 'tension', 'honour', 'finale']:
    globals()[w]()
