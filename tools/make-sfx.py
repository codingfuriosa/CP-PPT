"""Original cinematic sound cues for the Limitless Success deck (synthesised; no third-party samples).

Cues (48 kHz stereo):
  ananta-reveal : 3.5 s anticipation (sub rumble, string tremolo crescendo, rising whoosh) -> impact at 3.50 s
                  (bass hit, brass chord stab, metallic shimmer) -> 2.8 s majestic flourish -> natural fade -> silence
  reward-1      : rising whoosh -> bright chime + light musical hit at 0.55 s (~1.4 s)
  reward-2      : percussion build + rising sweep -> deeper hit at 1.20 s with brass (~2.4 s)
  reward-3      : 3 s cinematic riser with accelerating timpani/snare -> 0.40 s silence -> triumphant hit at 3.40 s
                  (bass + full brass + cymbal + bells) -> flourish -> fade
Hit times are mirrored in app.js so visuals land on the impact frame.
"""
import os
import sys
import wave
import numpy as np

SR = 48000
rng = np.random.default_rng(11)
OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
os.makedirs(OUT, exist_ok=True)


def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def env_adsr(n, a, d, s, r, sus_len=None):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    sus = n - a - d - r if sus_len is None else int(sus_len * SR)
    sus = max(sus, 0)
    e = np.concatenate([np.linspace(0, 1, max(a, 1)), np.linspace(1, s, max(d, 1)), np.full(sus, s), np.linspace(s, 0, max(r, 1))])
    return np.pad(e, (0, max(0, n - len(e))))[:n]


from scipy.signal import lfilter


def onepole_lp(x, fc):
    """One-pole low-pass. fc may be scalar or per-sample array (Hz); arrays are applied in 256-sample blocks."""
    fc = np.asarray(fc, float)
    if fc.ndim == 0:
        a = np.exp(-2 * np.pi * fc / SR)
        return lfilter([1 - a], [1, -a], x)
    fc = np.broadcast_to(fc, x.shape)
    y = np.empty_like(x)
    zi = np.zeros(1)
    B = 256
    for i in range(0, len(x), B):
        a = np.exp(-2 * np.pi * float(fc[i:i + B].mean()) / SR)
        y[i:i + B], zi = lfilter([1 - a], [1, -a], x[i:i + B], zi=zi)
    return y


def lp(x, fc, order=2):
    for _ in range(order):
        x = onepole_lp(x, fc)
    return x


def hp(x, fc, order=2):
    return x - lp(x, fc, order)


def bp(x, fc, width=0.5):
    return lp(hp(x, np.asarray(fc) * (1 - width / 2)), np.asarray(fc) * (1 + width / 2))


def saw(f, t, phase=0.0):
    ph = np.cumsum(np.broadcast_to(f, t.shape) / SR) + phase
    return 2 * (ph % 1.0) - 1


def noise(n):
    return rng.standard_normal(n)


def reverb(stereo, seconds=2.6, mix=0.3, predelay=0.02):
    n = int(seconds * SR)
    tt = np.arange(n) / SR
    out = []
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-tt * 6.9 / seconds)
        ir = lp(ir, 6000, 1)
        ir[: int(predelay * SR)] = 0
        ir /= np.sqrt(np.sum(ir ** 2))
        L = len(stereo[ch]) + n
        F = 1 << (L - 1).bit_length()
        wet = np.fft.irfft(np.fft.rfft(stereo[ch], F) * np.fft.rfft(ir, F), F)[:L]
        dry = np.pad(stereo[ch], (0, n))
        out.append(dry * (1 - mix) + wet * mix * 1.6)
    return np.array(out)


def place(buf, sig, at, pan=0.0, gain=1.0):
    """Mix mono sig into stereo buf at time `at` with constant-power pan (-1..1)."""
    i = int(at * SR)
    j = min(buf.shape[1], i + len(sig))
    if j <= i:
        return
    l = np.cos((pan + 1) * np.pi / 4) * gain
    r = np.sin((pan + 1) * np.pi / 4) * gain
    buf[0, i:j] += sig[: j - i] * l
    buf[1, i:j] += sig[: j - i] * r


def note(n):  # MIDI -> Hz
    return 440.0 * 2 ** ((n - 69) / 12)


# ---------------- instruments ----------------
def brass(freq, dur, swell=0.05, bright=1.0, vib=True):
    t = t_axis(dur)
    f = freq * (1 + (0.004 * np.sin(2 * np.pi * 5.2 * t) * np.clip(t / 0.4, 0, 1) if vib else 0))
    x = sum(saw(f * d, t, rng.random()) for d in (1.0, 1.003, 0.997))
    e = env_adsr(len(t), swell, 0.25, 0.75, min(0.6, dur * 0.5))
    cutoff = 400 + 3800 * bright * (0.35 + 0.65 * np.clip(e * 1.2, 0, 1))
    return lp(x, cutoff, 2) * e * 0.35


def strings(freq, dur, att=0.6, trem=0.0):
    t = t_axis(dur)
    x = sum(saw(freq * (1 + d), t, rng.random()) for d in (-0.006, -0.002, 0.0, 0.003, 0.007))
    e = env_adsr(len(t), att, 0.3, 0.9, min(1.0, dur * 0.4))
    if trem:
        e = e * (0.65 + 0.35 * np.sin(2 * np.pi * trem * t) ** 2)
    return lp(x, 2600, 2) * e * 0.12


def timpani(freq=65, dur=2.2, vel=1.0):
    t = t_axis(dur)
    f = freq * (1 + 0.25 * np.exp(-t * 18))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR) * np.exp(-t * 4)
    thump = lp(noise(len(t)), 900, 2) * np.exp(-t * 40) * 1.4
    return (x * np.exp(-t * 2.4) + thump) * 0.7 * vel


def snare(dur=0.35, vel=1.0):
    t = t_axis(dur)
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30)
    rattle = bp(noise(len(t)), 3500, 1.2) * np.exp(-t * 14)
    return (0.5 * body + rattle) * 0.6 * vel


def boom(dur=3.0, f0=62, f1=30, vel=1.0):
    t = t_axis(dur)
    f = f1 + (f0 - f1) * np.exp(-t * 3.5)
    x = np.tanh(1.8 * np.sin(2 * np.pi * np.cumsum(f) / SR))
    click = lp(noise(len(t)), 2500, 2) * np.exp(-t * 60)
    return (x * np.exp(-t * 1.5) + 0.8 * click) * vel


def cymbal(dur=3.0, swell=False, vel=1.0):
    t = t_axis(dur)
    x = hp(noise(len(t)), 5500, 2) + 0.4 * bp(noise(len(t)), 9000, 0.5)
    e = (t / dur) ** 2.2 if swell else np.exp(-t * 1.6) * np.clip(t / 0.004, 0, 1)
    return x * e * 0.35 * vel


def bell(freq, dur=3.0, vel=1.0):
    t = t_axis(dur)
    partials = [(1, 1.0, 1.2), (2.01, 0.55, 1.8), (2.76, 0.4, 2.4), (5.4, 0.25, 4.0), (8.93, 0.12, 6.0)]
    x = sum(a * np.sin(2 * np.pi * freq * r * t + rng.random() * 6) * np.exp(-t * d) for r, a, d in partials)
    tail = np.clip((dur - t) / (dur * 0.25), 0, 1)
    return x * np.clip(t / 0.002, 0, 1) * tail * 0.25 * vel


def whoosh(dur, f0=250, f1=6000, vel=1.0, curve=2.2):
    t = t_axis(dur)
    k = (t / dur) ** curve
    fc = f0 * (f1 / f0) ** k
    x = bp(noise(len(t)), fc, 0.9)
    return x * k * 0.9 * vel


def rumble(dur, vel=1.0):
    t = t_axis(dur)
    x = lp(noise(len(t)), 70, 3) * 6 + 0.5 * np.sin(2 * np.pi * 36 * t)
    return x * (t / dur) ** 1.4 * vel


def chord_brass(root, intervals, dur, swell=0.04, bright=1.0, gain=1.0):
    return sum(brass(note(root + i), dur, swell, bright) for i in intervals) * gain / len(intervals) * 2.2


def finish(buf, name, verb_mix=0.28, verb_len=2.8, target=-1.5, tail_fade=1.2, verb=True):
    if verb:
        buf = reverb(buf, verb_len, verb_mix)
    # trim trailing silence, fade tail
    peak = np.max(np.abs(buf))
    buf = buf / peak * (10 ** (target / 20))
    energy = np.max(np.abs(buf), axis=0)
    last = np.nonzero(energy > 10 ** (-60 / 20))[0]
    end = (last[-1] if len(last) else buf.shape[1]) + int(0.05 * SR)
    buf = buf[:, :end]
    n = int(tail_fade * SR)
    if buf.shape[1] > n:
        buf[:, -n:] *= np.linspace(1, 0, n) ** 2
    pcm = (np.clip(buf.T, -1, 1) * 32767).astype('<i2')
    path = os.path.join(OUT, name + '.wav')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(name, round(buf.shape[1] / SR, 2), 's')


def new(dur):
    return np.zeros((2, int(dur * SR)))


# =============== ANANTA REVEAL (impact at 3.50 s) ===============
def ananta():
    HIT = 3.5
    b = new(10.5)
    place(b, rumble(HIT, 0.6), 0.0)
    # string tremolo crescendo on a suspended chord (D sus)
    for n_, pan in ((50, -0.4), (57, 0.0), (62, 0.4), (64, 0.2), (69, -0.2)):
        s = strings(note(n_), HIT + 0.05, att=HIT * 0.9, trem=11)
        place(b, s, 0.0, pan, 0.55)
    place(b, whoosh(HIT - 0.08, 180, 7000, 0.75, 2.6), 0.0, 0.0)
    place(b, cymbal(HIT - 0.08, swell=True, vel=0.6), 0.0, 0.2)
    # timpani pulse, accelerating into the hit
    hits = [0.6, 1.4, 2.0, 2.45, 2.8, 3.05, 3.22]
    for k, ht in enumerate(hits):
        place(b, timpani(55, 1.2, 0.25 + 0.06 * k), ht, -0.1)
    g0, g1 = int((HIT - 0.12) * SR), int((HIT - 0.04) * SR)
    b[:, g0:g1] *= np.linspace(1, 0.08, g1 - g0)
    b[:, g1:int(HIT * SR)] *= 0.08
    # IMPACT
    place(b, boom(4.0, 70, 28, 1.9), HIT)
    place(b, timpani(49, 3.0, 1.3), HIT, 0.0)
    place(b, cymbal(4.0, vel=1.1), HIT, 0.1)
    place(b, chord_brass(50, [0, 7, 12, 16, 19], 1.3, swell=0.02, bright=1.2, gain=1.3), HIT, 0.0)
    for f_, pan in ((note(86), -0.5), (note(90), 0.5), (note(93), 0.0), (note(98), 0.3)):
        place(b, bell(f_, 4.0, 0.9), HIT + 0.02, pan)
    # majestic flourish: ascending brass line into a sustained major chord (D major), strings underneath
    line = [(62, 0.0, 0.32), (66, 0.32, 0.32), (69, 0.64, 0.32), (74, 0.96, 1.9)]
    for n_, off, d in line:
        place(b, brass(note(n_), d + 0.2, 0.04, 1.0), HIT + 1.25 + off, -0.15, 0.9)
        place(b, brass(note(n_ - 12), d + 0.2, 0.04, 0.8), HIT + 1.25 + off, 0.15, 0.6)
    for n_, pan in ((50, -0.3), (57, 0.3), (62, -0.1), (66, 0.1), (69, 0.0)):
        place(b, strings(note(n_), 3.6, att=0.5), HIT + 1.2, pan, 1.2)
    place(b, timpani(55, 2.5, 0.8), HIT + 2.21, 0.0)
    place(b, cymbal(3.5, vel=0.6), HIT + 2.21, -0.2)
    finish(b, 'ananta-reveal', verb_mix=0.3, verb_len=3.2, tail_fade=2.0, target=-1.0)


# =============== REWARD 1 (hit at 0.55 s) — pleasant surprise ===============
def reward1():
    HIT = 0.55
    b = new(3.0)
    place(b, whoosh(HIT, 600, 9000, 0.7, 2.0), 0.0, -0.2)
    # light pizzicato-ish pickup
    for k, n_ in enumerate((79, 83, 86)):
        place(b, bell(note(n_), 0.6, 0.5), 0.12 + k * 0.12, -0.3 + 0.3 * k)
    place(b, boom(1.2, 90, 45, 0.45), HIT)
    for f_, pan in ((note(84), -0.3), (note(88), 0.3), (note(91), 0.0), (note(96), 0.15)):
        place(b, bell(f_, 2.2, 0.9), HIT, pan)
    place(b, chord_brass(60, [0, 4, 7], 0.55, swell=0.015, bright=0.8, gain=0.6), HIT, 0.0)
    place(b, cymbal(1.6, vel=0.35), HIT, 0.2)
    finish(b, 'reward-1', verb_mix=0.3, verb_len=2.0, tail_fade=0.8, target=-7.0)


# =============== REWARD 2 (hit at 1.20 s) — escalating ===============
def reward2():
    HIT = 1.2
    b = new(4.0)
    place(b, whoosh(HIT, 200, 8000, 0.9, 2.3), 0.0)
    # snare build (16ths, accelerating velocity) + toms
    steps = np.arange(0, HIT - 0.05, 0.075)
    for k, st in enumerate(steps):
        place(b, snare(0.25, 0.25 + 0.75 * k / len(steps)), st, 0.15 if k % 2 else -0.15)
    for k, st in enumerate((0.0, 0.3, 0.6, 0.9)):
        place(b, timpani(62 + k * 5, 0.8, 0.5 + 0.12 * k), st, -0.2)
    # rising string line
    for n_, pan in ((55, -0.3), (62, 0.3), (67, 0.0)):
        t = t_axis(HIT)
        s = strings(note(n_), HIT, att=HIT * 0.8) * (1 + 0 * t)
        place(b, s, 0.0, pan, 1.1)
    # impact: deeper + brass
    place(b, boom(2.4, 66, 32, 1.0), HIT)
    place(b, timpani(55, 2.0, 1.0), HIT)
    place(b, chord_brass(55, [0, 7, 12, 16], 1.1, swell=0.02, bright=1.0, gain=1.0), HIT, 0.0)
    for f_, pan in ((note(86), -0.4), (note(91), 0.4), (note(95), 0.0)):
        place(b, bell(f_, 2.6, 0.8), HIT, pan)
    place(b, cymbal(2.5, vel=0.8), HIT, 0.1)
    finish(b, 'reward-2', verb_mix=0.3, verb_len=2.4, tail_fade=1.0, target=-3.5)


# =============== REWARD 3 (riser 0-3.0 s, silence 3.0-3.4 s, hit at 3.40 s) — spectacular ===============
def reward3():
    RISE, HIT = 3.0, 3.4
    b = new(10.0)
    post = new(10.0)
    place(b, rumble(RISE, 1.0), 0.0)
    place(b, whoosh(RISE, 150, 9000, 1.0, 2.8), 0.0)
    place(b, cymbal(RISE, swell=True, vel=1.0), 0.0, -0.15)
    # Shepard-like rising string cluster
    t = t_axis(RISE)
    for base, pan in ((48, -0.4), (55, 0.4), (60, 0.0), (64, -0.2), (67, 0.2)):
        f = note(base) * 2 ** (t / RISE * 1.0)
        x = sum(saw(f * (1 + d), t, rng.random()) for d in (-0.005, 0.0, 0.005))
        e = (t / RISE) ** 1.6 * (0.7 + 0.3 * np.sin(2 * np.pi * 13 * t) ** 2)
        place(b, lp(x, 3000, 2) * e * 0.1, 0.0, pan)
    # accelerating timpani + snare roll
    hits, gap, tt = [], 0.5, 0.2
    while tt < RISE - 0.05:
        hits.append(tt)
        tt += gap
        gap = max(0.06, gap * 0.8)
    for k, h_ in enumerate(hits):
        v_ = 0.3 + 0.7 * h_ / RISE
        place(b, timpani(52 + (k % 2) * 7, 0.9, v_), h_, -0.15 if k % 2 else 0.15)
        place(b, snare(0.3, v_ * 0.8), h_ + 0.02, 0.25)
    # hard stop -> 0.4 s silence (nothing placed between RISE and HIT)
    # TRIUMPHANT HIT
    place(post, boom(4.5, 72, 26, 1.6), HIT)
    place(post, timpani(46, 3.5, 1.5), HIT, -0.1)
    place(post, timpani(58, 3.0, 1.0), HIT + 0.01, 0.1)
    place(post, cymbal(5.0, vel=1.3), HIT, -0.2)
    place(post, cymbal(5.0, vel=1.0), HIT + 0.012, 0.25)
    place(post, chord_brass(53, [0, 7, 12, 16, 19, 24], 1.6, swell=0.015, bright=1.4, gain=1.6), HIT, 0.0)
    for f_, pan in ((note(89), -0.6), (note(93), 0.6), (note(96), 0.0), (note(101), 0.3), (note(105), -0.3)):
        place(post, bell(f_, 4.5, 1.0), HIT + 0.01, pan)
    # celebratory brass fanfare (F major) + strings, with timpani punctuation
    fan = [(65, 0.0, 0.22), (69, 0.22, 0.22), (72, 0.44, 0.22), (77, 0.66, 0.5), (76, 1.16, 0.22), (77, 1.38, 2.4)]
    for n_, off, d in fan:
        place(post, brass(note(n_), d + 0.25, 0.03, 1.2), HIT + 1.5 + off, -0.15, 1.0)
        place(post, brass(note(n_ - 7), d + 0.25, 0.03, 1.0), HIT + 1.5 + off, 0.2, 0.6)
    for n_, pan in ((41, 0.0), (53, -0.3), (60, 0.3), (65, -0.1), (69, 0.1), (72, 0.0)):
        place(post, strings(note(n_), 4.6, att=0.4), HIT + 1.4, pan, 1.3)
    for off in (1.5, 2.16, 2.88):
        place(post, timpani(46, 2.2, 0.9), HIT + off, 0.0)
    place(post, cymbal(4.0, vel=0.9), HIT + 2.88, 0.0)
    pre = reverb(b, 1.6, 0.25)[:, : b.shape[1]]
    g0, g1 = int((RISE - 0.04) * SR), int(RISE * SR)
    pre[:, g0:g1] *= np.linspace(1, 0, g1 - g0)
    pre[:, g1:] = 0
    post = reverb(post, 3.4, 0.32)[:, : post.shape[1]]
    out = pre + post
    out = np.pad(out, ((0, 0), (0, int(2.0 * SR))))
    finish(out, 'reward-3', tail_fade=2.2, target=-0.5, verb=False)



# =============== SHOW ACCENTS (restrained; hit times mirrored in app.js) ===============
def opening():  # low pulse + atmospheric rise -> grand but soft arrival at 4.4 s as LIMITLESS SUCCESS appears
    HIT = 4.4
    b = new(10.0)
    place(b, rumble(HIT, 0.5), 0.0)
    for k, ht in enumerate(np.arange(0.3, HIT - 0.2, 0.9)):
        place(b, timpani(41, 1.4, 0.2 + 0.05 * k), ht)
    for n_, pan in ((50, -0.3), (57, 0.3), (62, 0.0)):
        place(b, strings(note(n_), HIT, att=HIT * 0.9), 0.0, pan, 0.5)
    place(b, whoosh(HIT - 0.05, 150, 5000, 0.5, 2.6), 0.0)
    place(b, boom(3.5, 60, 30, 0.8), HIT)
    place(b, chord_brass(50, [0, 7, 12, 16], 2.4, swell=0.08, bright=0.7, gain=0.7), HIT, 0.0)
    for f_, pan in ((note(86), -0.4), (note(90), 0.4), (note(93), 0.0)):
        place(b, bell(f_, 4.0, 0.6), HIT + 0.02, pan)
    finish(b, 'opening', verb_mix=0.35, verb_len=3.4, tail_fade=2.0, target=-5.0)


def accent_soft():  # warm shimmer for factual milestones / chapter titles (hit 0.40 s)
    HIT = 0.4
    b = new(4.0)
    place(b, whoosh(HIT, 800, 6000, 0.35, 2.0), 0.0)
    place(b, boom(2.0, 70, 45, 0.35), HIT)
    for f_, pan in ((note(79), -0.3), (note(83), 0.3), (note(86), 0.0)):
        place(b, bell(f_, 2.8, 0.55), HIT, pan)
    finish(b, 'accent-soft', verb_mix=0.35, verb_len=2.6, tail_fade=1.0, target=-12.0)


def accent_rise():  # forward-looking lift (hit 0.90 s)
    HIT = 0.9
    b = new(4.0)
    place(b, whoosh(HIT, 300, 8000, 0.6, 2.4), 0.0)
    place(b, cymbal(HIT, swell=True, vel=0.4), 0.0)
    for f_, pan in ((note(81), -0.3), (note(85), 0.3), (note(88), 0.0), (note(93), 0.1)):
        place(b, bell(f_, 2.8, 0.6), HIT, pan)
    place(b, boom(1.8, 75, 45, 0.35), HIT)
    finish(b, 'accent-rise', verb_mix=0.32, verb_len=2.4, tail_fade=1.0, target=-10.0)


def accent_bright():  # brief celebratory sting for earning figures (hit 0.15 s)
    HIT = 0.15
    b = new(3.0)
    place(b, whoosh(HIT, 1500, 9000, 0.4, 1.6), 0.0)
    place(b, chord_brass(64, [0, 4, 7, 12], 0.5, swell=0.01, bright=1.1, gain=0.8), HIT)
    for f_, pan in ((note(88), -0.3), (note(91), 0.3), (note(96), 0.0)):
        place(b, bell(f_, 2.0, 0.7), HIT, pan)
    place(b, cymbal(1.5, vel=0.3), HIT, 0.2)
    finish(b, 'accent-bright', verb_mix=0.3, verb_len=2.0, tail_fade=0.8, target=-9.0)


def accent_dark():  # the landscape darkens: low hit + descending air (hit 0.05 s)
    b = new(5.0)
    place(b, boom(3.5, 55, 26, 0.9), 0.05)
    t = t_axis(3.5)
    fc = 4000 * (0.05 / 1.0) ** (t / 3.5) + 200
    place(b, bp(noise(len(t)), fc, 0.9) * (1 - t / 3.5) * 0.35, 0.05)
    for n_, pan in ((45, -0.3), (52, 0.3), (48, 0.0)):
        place(b, strings(note(n_), 3.8, att=0.3), 0.05, pan, 0.6)
    finish(b, 'accent-dark', verb_mix=0.35, verb_len=3.0, tail_fade=1.5, target=-8.0)


def cta():  # decisive: snare roll -> unison brass + timpani at 0.60 s
    HIT = 0.6
    b = new(4.5)
    for k, st in enumerate(np.arange(0, HIT - 0.04, 0.05)):
        place(b, snare(0.2, 0.25 + 0.6 * st / HIT), st, 0.1)
    place(b, timpani(45, 2.5, 1.2), HIT)
    place(b, boom(2.5, 66, 32, 1.0), HIT)
    place(b, chord_brass(48, [0, 12, 19, 24], 1.6, swell=0.01, bright=1.3, gain=1.3), HIT)
    place(b, cymbal(3.0, vel=0.8), HIT, 0.1)
    finish(b, 'cta', verb_mix=0.3, verb_len=2.8, tail_fade=1.2, target=-2.5)


def finale_sting():  # controlled finale: rising strings into a sustained C major (hit 1.20 s)
    HIT = 1.2
    b = new(9.0)
    for n_, pan in ((48, -0.3), (55, 0.3), (60, 0.0), (64, 0.15)):
        t = t_axis(HIT)
        f = note(n_ - 5) * 2 ** (5 / 12 * t / HIT)
        x = sum(saw(f * (1 + d), t, rng.random()) for d in (-0.004, 0.0, 0.004))
        place(b, lp(x, 2600, 2) * (t / HIT) ** 1.5 * 0.08, 0.0, pan)
    place(b, timpani(36, 3.0, 1.0), HIT)
    place(b, boom(3.0, 60, 30, 0.8), HIT)
    place(b, chord_brass(48, [0, 7, 12, 16, 19], 4.5, swell=0.15, bright=1.0, gain=1.1), HIT)
    for n_, pan in ((36, 0.0), (48, -0.3), (55, 0.3), (60, -0.1), (64, 0.1), (67, 0.0)):
        place(b, strings(note(n_), 6.0, att=0.3), HIT, pan, 1.0)
    for f_, pan in ((note(84), -0.4), (note(88), 0.4), (note(91), 0.0)):
        place(b, bell(f_, 4.5, 0.7), HIT + 0.02, pan)
    place(b, cymbal(4.0, vel=0.7), HIT)
    finish(b, 'finale', verb_mix=0.34, verb_len=3.4, tail_fade=2.5, target=-3.0)


ALL = {'ananta': ananta, 'r1': reward1, 'r2': reward2, 'r3': reward3, 'opening': opening, 'soft': accent_soft,
       'rise': accent_rise, 'bright': accent_bright, 'dark': accent_dark, 'cta': cta, 'finale': finale_sting}
if __name__ == '__main__':
    for w_ in sys.argv[2:] or list(ALL):
        ALL[w_]()
