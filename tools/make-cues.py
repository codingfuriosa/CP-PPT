"""Show cues v2 — built around the client's shortlisted cinematic library + original orchestral layers. NO bells/chimes.

Usage:  python tools/make-cues.py <library_wav_dir> <out_dir>
  library_wav_dir holds the client's files decoded to 48 kHz WAV (see LIBRARY below).

Library files used (client's Google Drive "sound library" folder):
  bz-epic-reveal-logo-201065        breakzstudios (Pixabay)   Ananta grand reveal — build, built-in breath, impact @4.816 s, epic sustain
  bz-epic-logo-reveal-333643        breakzstudios (Pixabay)   Reward 3 reveal — impact @2.292 s + sustain
  uf-logo-reveal-intro-352299       universfield (Pixabay)    Reward 1 — swoosh-reveal peak @0.594 s
  ai-quick-impact-swoosh-578002     artificiallyinspired (Pixabay)  Reward 2 impact layer @0.574 s · chapter whoosh
  es-stinger-complex-18             Epidemic Sound            Opening title + Reward 3 depth — deep impact @1.586 s
  es-riser-fast-short-clean-01      Epidemic Sound            Reward 2 build — riser ends @4.17 s
  es-airy-noisy-surge-02            Epidemic Sound            flight-path transition — surge @1.38 s
  enfield-350cc-firing              rsn267 via Pixabay ("350cc bike firing", Pixabay Content License)  Reward 3 — real Royal Enfield 350
                                    start, revs and rev-down; decoded from the Pixabay MP3 to 48 kHz WAV
Rejected after analysis: universfield-clean-logo-reveal-139678 (sustained pure partials to 12 kHz = shimmer/bell),
  ES Magic Oscillating Chimes 04 + ES Magic Mystic Thrill 03 (chimes, 10–12 kHz tonal), ES Rocket Launch Ring Out 02
  (metallic ring-out; the deck already has a synced takeoff sound).
"""
import importlib.util
import os
import sys
import wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('sfx', os.path.join(HERE, 'make-sfx.py'))
_argv = sys.argv
sys.argv = [_argv[0], _argv[2]]  # make-sfx writes into OUT
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)
sys.argv = _argv
LIB, OUT = _argv[1], _argv[2]
SR = S.SR


def tame(x, keep=0.10, fc=1800, xf=0.06):
    """Keep the full-band impact transient, then low-pass the tail to remove metallic shimmer / ringing."""
    lpx = np.array([S.lp(c, fc, 5) for c in x])
    k, n = int(keep * SR), int(xf * SR)
    w = np.concatenate([np.ones(k), np.linspace(1, 0, n), np.zeros(max(0, x.shape[1] - k - n))])[: x.shape[1]]
    return x * w + lpx * (1 - w)


def lib(name, start=0.0, end=None, gain=1.0, fade_in=0.0, fade_out=0.0, lowpass=None, tamed=False):
    w = wave.open(os.path.join(LIB, name + '.wav'))
    x = np.frombuffer(w.readframes(w.getnframes()), '<i2').reshape(-1, 2).T.astype(float) / 32768
    i, j = int(start * SR), (x.shape[1] if end is None else int(end * SR))
    x = x[:, i:j] * gain
    if fade_in:
        n = int(fade_in * SR)
        x[:, :n] *= np.linspace(0, 1, n)
    if fade_out:
        n = int(fade_out * SR)
        x[:, -n:] *= np.linspace(1, 0, n) ** 2
    if lowpass:
        x = np.array([S.lp(c, lowpass, 2) for c in x])
    if tamed:
        x = tame(x)
    return x


def put(buf, st, at):
    i = int(at * SR)
    j = min(buf.shape[1], i + st.shape[1])
    if j > i:
        buf[:, i:j] += st[:, : j - i]


def mono(buf, sig, at, pan=0.0, gain=1.0):
    S.place(buf, sig, at, pan, gain)


def master(buf, name, target=-1.0, tail=1.5):
    """True-peak-safe: soft-knee limiter then normalise; trim + fade the tail. No reverb added on top of library audio."""
    peak = np.max(np.abs(buf))
    buf = buf / peak
    knee = 0.7
    a = np.abs(buf)
    buf = np.sign(buf) * np.where(a < knee, a, knee + (1 - knee) * np.tanh((a - knee) / (1 - knee)))
    buf *= 10 ** (target / 20) / np.max(np.abs(buf))
    e = np.max(np.abs(buf), axis=0)
    last = np.nonzero(e > 10 ** (-62 / 20))[0]
    buf = buf[:, : (last[-1] if len(last) else buf.shape[1]) + int(0.05 * SR)]
    n = int(tail * SR)
    buf[:, -n:] *= np.linspace(1, 0, n) ** 2
    pcm = (np.clip(buf.T, -1, 1) * 32767).astype('<i2')
    with wave.open(os.path.join(OUT, name + '.wav'), 'wb') as w:
        w.setnchannels(2), w.setsampwidth(2), w.setframerate(SR), w.writeframes(pcm.tobytes())
    print(f'{name:15s} {buf.shape[1] / SR:5.2f}s  peak {target} dBFS')


def orch_swell(root, dur, gain=1.0, major=True):
    """Uplifting orchestral swell (strings + brass + timpani), stereo, no metallic layers."""
    b = S.new(dur + 1)
    iv = [0, 7, 12, 16, 19] if major else [0, 7, 12, 15, 19]
    for k, n in enumerate(iv):
        mono(b, S.strings(S.note(root + n), dur, att=0.5), 0.0, -0.4 + 0.2 * k, 1.1)
    mono(b, S.chord_brass(root, [0, 7, 12, 16], dur * 0.9, swell=0.35, bright=1.0, gain=1.0), 0.15)
    return S.reverb(b, 2.6, 0.3)[:, : b.shape[1]] * gain


def fanfare(root, at, buf, gain=1.0):
    """Triumphant brass fanfare + strings + timpani (original)."""
    line = [(0, 0.0, 0.22), (4, 0.22, 0.22), (7, 0.44, 0.22), (12, 0.66, 0.5), (11, 1.16, 0.22), (12, 1.38, 2.6)]
    b = S.new(5.5)
    for n, off, d in line:
        mono(b, S.brass(S.note(root + 12 + n), d + 0.25, 0.03, 1.2), off, -0.15, 1.0)
        mono(b, S.brass(S.note(root + 5 + n), d + 0.25, 0.03, 1.0), off, 0.2, 0.6)
    for n, pan in ((root - 12, 0.0), (root, -0.3), (root + 7, 0.3), (root + 12, -0.1), (root + 16, 0.1)):
        mono(b, S.strings(S.note(n), 4.4, att=0.25), -0.05 if False else 0.0, pan, 1.3)
    for off in (0.0, 0.66, 1.38):
        mono(b, S.timpani(46, 2.2, 0.9), off)
    put(buf, S.reverb(b, 3.0, 0.3)[:, : b.shape[1]] * gain, at)


# ================= ANANTA GRAND REVEAL (impact at 3.50 s) =================
def ananta():
    HIT = 3.5
    b = S.new(14)
    # 1-2. Build + breath: bz-201065 from 1.316 s so its 4.816 s impact lands exactly on HIT (its own pre-impact dip = the breath)
    put(b, lib('bz-epic-reveal-logo-201065', start=4.816 - HIT, fade_in=0.6), 0.0)
    # sub-rumble under the build, gated before the impact
    r = S.rumble(HIT - 0.25, 0.5)
    mono(b, r, 0.0)
    # 3. impact reinforcement: deep cinematic boom + timpani on the exact frame
    mono(b, S.boom(4.0, 62, 26, 1.2), HIT)
    mono(b, S.timpani(41, 3.0, 1.0), HIT)
    # 4. uplifting orchestral swell sustaining the excitement (D major), entering under the library sustain
    put(b, orch_swell(50, 6.5, 0.55), HIT + 1.0)
    master(b, 'ananta-reveal', target=-1.0, tail=3.0)


# ================= BONUS 1 — short riser + clean reveal impact (hit 0.60 s) =================
def reward1():
    b = S.new(3.0)
    put(b, lib('uf-logo-reveal-intro-352299', start=0.0), 0.0)
    master(b, 'reward-1', target=-6.0, tail=0.6)


# ================= BONUS 2 — stronger build, deeper impact, celebratory flourish (hit 1.60 s) =================
def reward2():
    HIT = 1.6
    b = S.new(8.0)
    # riser: last 1.6 s of the clean riser, ending on the hit
    put(b, lib('es-riser-fast-short-clean-01', start=4.17 - HIT, end=4.17, fade_in=0.2), 0.0)
    for k, st in enumerate(np.arange(0.2, HIT - 0.05, 0.1)):
        mono(b, S.snare(0.2, 0.2 + 0.6 * st / HIT), st, 0.12 if k % 2 else -0.12)
    # deeper impact: library swoosh-impact aligned + synthesized sub hit
    put(b, lib('ai-quick-impact-swoosh-578002', start=0.574 - 0.25, gain=0.9), HIT - 0.25)
    mono(b, S.boom(2.6, 64, 30, 1.1), HIT)
    mono(b, S.timpani(45, 2.4, 1.0), HIT)
    # celebratory brass flourish (G major)
    flo = S.new(4.0)
    for n, off, d in ((67, 0.0, 0.18), (71, 0.18, 0.18), (74, 0.36, 0.18), (79, 0.54, 1.6)):
        mono(flo, S.brass(S.note(n), d + 0.25, 0.03, 1.1), off, -0.1, 1.0)
        mono(flo, S.brass(S.note(n - 12), d + 0.25, 0.03, 0.9), off, 0.15, 0.6)
    for n, pan in ((43, 0.0), (55, -0.3), (62, 0.3), (67, 0.0)):
        mono(flo, S.strings(S.note(n), 2.6, att=0.2), 0.5, pan, 1.0)
    put(b, S.reverb(flo, 2.4, 0.3)[:, : flo.shape[1]] * 0.8, HIT + 0.15)
    master(b, 'reward-2', target=-3.0, tail=1.5)


# ================= BONUS 3 — escalating suspense, silence, grand climax (hit 3.40 s) =================
def reward3_orchestral():  # previous v2 cue, kept for reference
    RISE, HIT = 2.95, 3.4
    b = S.new(14.0)
    pre = S.new(RISE + 0.1)
    # escalating build: airy surge (twice, rising) + accelerating timpani / snare roll + rising strings
    put(pre, lib('es-airy-noisy-surge-02', start=0.0, end=1.38, fade_in=0.3) * 0.8, 0.0)
    put(pre, lib('es-airy-noisy-surge-02', start=0.0, end=1.38) * 1.2, RISE - 1.38)
    t = S.t_axis(RISE)
    for base, pan in ((48, -0.4), (55, 0.4), (60, 0.0), (64, -0.2)):
        f = S.note(base) * 2 ** (t / RISE)
        x = sum(S.saw(f * (1 + d), t, S.rng.random()) for d in (-0.005, 0.0, 0.005))
        mono(pre, S.lp(x, 3000, 2) * (t / RISE) ** 1.6 * 0.09, 0.0, pan)
    hits, gap, tt = [], 0.45, 0.15
    while tt < RISE - 0.05:
        hits.append(tt)
        tt += gap
        gap = max(0.06, gap * 0.8)
    for k, h in enumerate(hits):
        v = 0.3 + 0.7 * h / RISE
        mono(pre, S.timpani(52 + (k % 2) * 7, 0.9, v), h, -0.15 if k % 2 else 0.15)
        mono(pre, S.snare(0.25, v * 0.7), h + 0.02, 0.25)
    g0 = int((RISE - 0.04) * SR)
    pre[:, g0:] *= np.linspace(1, 0, pre.shape[1] - g0)  # hard stop -> 0.45 s of true silence
    put(b, pre, 0.0)
    # GRAND CLIMAX: library reveal impact aligned to HIT + epidemic deep impact + sub + triumphant fanfare
    put(b, lib('bz-epic-logo-reveal-333643', start=2.292 - 0.02, tamed=True), HIT - 0.02)
    put(b, lib('es-stinger-complex-18', start=1.586 - 0.01, gain=0.8, tamed=True), HIT - 0.01)
    mono(b, S.boom(4.5, 70, 26, 1.3), HIT)
    fanfare(53, HIT + 1.2, b, 0.75)
    master(b, 'reward-3-orchestral', target=-0.5, tail=3.0)


# ================= BONUS 3 — Royal Enfield: the bike fires up as the sun fades, revs harder, slams in on the reveal (hit 3.40 s) =================
# Built from a real recording (enfield-350cc-firing). No orchestral build / fanfare: the engine IS the music here.
def reward3():
    HIT = 3.4
    b = S.new(10.5)
    rec = lambda a, z, **k: lib('enfield-350cc-firing', start=a, end=z, **k)
    # 0.00 – 1.20  starter + catch (the bike fires up while the sun fades)
    put(b, rec(0.0, 1.25, fade_out=0.05) * 1.0, 0.0)
    # 1.15 – 3.28  climbing revs, crescendo into the reveal
    climb = rec(2.0, 4.15, fade_in=0.08, fade_out=0.06)
    climb *= np.linspace(0.75, 1.35, climb.shape[1])
    put(b, climb, 1.15)
    # a breath (gear-shift gap) then the hardest rev slams in exactly on the reveal frame
    put(b, rec(5.4, 8.35, fade_in=0.01) * 1.45, HIT - 0.01)
    put(b, rec(8.35, 11.2, fade_out=1.6) * 1.2, HIT - 0.01 + 2.95)  # rev-down, settling
    # punch: library reveal impact + sub boom on the hit (keeps the moment cinematic)
    put(b, lib('bz-epic-logo-reveal-333643', start=2.292 - 0.02, end=2.292 + 1.6, gain=0.7, fade_out=0.9, tamed=True), HIT - 0.02)
    mono(b, S.boom(2.2, 80, 30, 1.1), HIT)
    # energetic driving beat under the revs for two bars after the hit (128 bpm), fading out
    beat = 60 / 128
    for k in range(8):
        v = 1.0 - k / 10
        mono(b, S.boom(0.32, 125, 45, 0.9 * v), HIT + k * beat)
        k % 2 and mono(b, S.snare(0.22, 0.75 * v), HIT + k * beat, 0.15)
    master(b, 'reward-3', target=-0.5, tail=2.2)


# ================= OPENING TITLE — powerful arrival at 4.40 s =================
def opening():
    HIT = 4.4
    b = S.new(10.0)
    mono(b, S.rumble(HIT, 0.6), 0.0)
    for k, ht in enumerate(np.arange(0.4, HIT - 1.4, 0.75)):
        mono(b, S.timpani(41, 1.4, 0.3 + 0.08 * k), ht)
    # es-stinger: its rise + deep impact, impact aligned to the title
    put(b, lib('es-stinger-complex-18', start=0.0, end=1.586), HIT - 1.586)
    put(b, lib('es-stinger-complex-18', start=1.586, tamed=True), HIT)
    mono(b, S.chord_brass(50, [0, 7, 12, 15], 2.8, swell=0.06, bright=0.8, gain=0.6), HIT)
    master(b, 'opening', target=-3.0, tail=2.5)


# ================= TRANSITION WHOOSH (chapter openers) — no tonal content =================
def whoosh():
    b = S.new(3.0)
    put(b, lib('ai-quick-impact-swoosh-578002', start=0.0), 0.0)
    master(b, 'whoosh', target=-12.0, tail=0.8)


def surge():
    b = S.new(3.0)
    put(b, lib('es-airy-noisy-surge-02'), 0.0)
    master(b, 'surge', target=-12.0, tail=0.6)


# ================= BRIEF CELEBRATORY STINGER for earning figures (refined brass, hit 0.15 s) =================
def stinger():
    b = S.new(3.0)
    mono(b, S.chord_brass(52, [0, 7, 12, 16], 0.7, swell=0.02, bright=1.0, gain=1.0), 0.15)
    mono(b, S.timpani(40, 1.6, 0.7), 0.15)
    mono(b, S.boom(1.6, 70, 40, 0.4), 0.15)
    master(b, 'stinger', target=-10.0, tail=0.8)


# ================= FINALE (hit 1.20 s) — controlled orchestral close, no bells =================
def finale():
    HIT = 1.2
    b = S.new(10.0)
    for n, pan in ((48, -0.3), (55, 0.3), (60, 0.0), (64, 0.15)):
        t = S.t_axis(HIT)
        f = S.note(n - 5) * 2 ** (5 / 12 * t / HIT)
        x = sum(S.saw(f * (1 + d), t, S.rng.random()) for d in (-0.004, 0.0, 0.004))
        mono(b, S.lp(x, 2600, 2) * (t / HIT) ** 1.5 * 0.08, 0.0, pan)
    put(b, lib('es-stinger-complex-18', start=1.586 - 0.01, gain=0.6, tamed=True), HIT - 0.01)
    put(b, orch_swell(48, 6.5, 0.9), HIT)
    mono(b, S.timpani(36, 3.0, 1.0), HIT)
    master(b, 'finale', target=-3.0, tail=2.5)


ALL = dict(ananta=ananta, r1=reward1, r2=reward2, r3=reward3, opening=opening, whoosh=whoosh, surge=surge, stinger=stinger, finale=finale)
for k in _argv[3:] or list(ALL):
    ALL[k]()
