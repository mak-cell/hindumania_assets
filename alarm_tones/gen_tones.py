"""Synthesises HinduMania's devotional alarm / alert tones (all original, CC0).

Each deity gets a full alarm tone (~20-25 s, loops on the alarm stream) and a
short alert variant (~5-6 s) for event / reminder notifications.

usage: python gen_tones.py <out_dir>
"""
import hashlib
import json
import os
import subprocess
import sys

import numpy as np

SR = 44100
rng = np.random.default_rng(108)


# ---------------------------------------------------------------- helpers ---
def silence(sec):
    return np.zeros(int(sec * SR))


def tvec(sec):
    return np.arange(int(sec * SR)) / SR


def place(buf, sig, at):
    i = int(at * SR)
    end = min(len(buf), i + len(sig))
    buf[i:end] += sig[: end - i]
    return buf


def fade(x, fin=0.02, fout=0.5):
    n_in, n_out = int(fin * SR), int(fout * SR)
    if n_in:
        x[:n_in] *= np.linspace(0, 1, n_in)
    if n_out:
        x[-n_out:] *= np.linspace(1, 0, n_out) ** 1.5
    return x


def lowpass(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / np.sqrt(1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x))


def highpass(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / np.sqrt(1 + (cutoff / np.maximum(f, 1e-3)) ** 4)
    return np.fft.irfft(X, len(x))


def bandpass(x, lo, hi):
    return lowpass(highpass(x, lo), hi)


def reverb(x, t60=2.4, mix=0.3, tail=None):
    """Temple-hall reverb: convolution with decaying, darkening noise."""
    tail = tail or t60
    n = int(tail * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-6.9 * t / t60)
    ir = lowpass(ir, 5000) + 0.5 * lowpass(ir, 1200)
    ir[: int(0.012 * SR)] = 0  # pre-delay
    ir /= np.sqrt(np.sum(ir**2))
    size = len(x) + n
    nfft = 1 << (size - 1).bit_length()
    wet = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)[:size]
    dry = np.concatenate([x, np.zeros(n)])
    return (1 - mix) * dry + mix * wet * 3.0


def master(x, rms_db=-17.0, fade_out=1.2):
    x = x - np.mean(x)
    x = fade(x, 0.01, fade_out)
    rms = np.sqrt(np.mean(x**2)) + 1e-12
    x = x * (10 ** (rms_db / 20) / rms)
    x = np.tanh(x * 1.2) / 1.2  # gentle limiter
    return x * (0.89 / max(np.max(np.abs(x)), 1e-9))


# ------------------------------------------------------------ instruments ---
BELL_RATIOS = [0.5, 1.0, 1.19, 1.56, 2.0, 2.51, 2.66, 3.01, 4.1, 5.42]
BELL_AMPS = [0.35, 1.0, 0.6, 0.5, 0.45, 0.3, 0.25, 0.2, 0.12, 0.08]
BELL_DECAY = [1.6, 1.0, 0.8, 0.65, 0.55, 0.42, 0.36, 0.3, 0.2, 0.14]


def bell(f, length=6.0, decay=3.0, amp=1.0):
    t = tvec(length)
    out = np.zeros_like(t)
    for r, a, d in zip(BELL_RATIOS, BELL_AMPS, BELL_DECAY):
        fr = f * r
        if fr > 16000:
            continue
        beat = rng.uniform(0.4, 2.2)
        env = np.exp(-t / (decay * d))
        out += a * env * (np.sin(2 * np.pi * fr * t + rng.uniform(0, 6.3))
                          + 0.6 * np.sin(2 * np.pi * (fr + beat) * t))
    strike = highpass(rng.standard_normal(len(t)), 2500) * np.exp(-t / 0.004)
    return amp * (out / 3.0 + 0.25 * strike)


def bowl(f, length=12.0, decay=6.0, amp=1.0):
    """Himalayan singing bowl: few inharmonic modes, long beating decay."""
    t = tvec(length)
    out = np.zeros_like(t)
    for r, a, d in [(1, 1.0, 1.0), (2.76, 0.55, 0.7), (5.4, 0.25, 0.45),
                    (8.93, 0.1, 0.3)]:
        beat = rng.uniform(0.5, 1.4)
        env = np.exp(-t / (decay * d)) * (1 - np.exp(-t / 0.01))
        out += a * env * (np.sin(2 * np.pi * f * r * t)
                          + 0.8 * np.sin(2 * np.pi * (f * r + beat) * t + 1.0))
    strike = bandpass(rng.standard_normal(len(t)), 800, 6000) * np.exp(-t / 0.006)
    return amp * (out / 2.0 + 0.15 * strike)


def hand_bell(f=1450, length=1.6, amp=1.0):
    """Small aarti ghanti: bright, quick decay."""
    return bell(f, length, decay=0.6, amp=amp)


def lorentz(freq, centre, width):
    return 1.0 / (1.0 + ((freq - centre) / (width / 2)) ** 2)


# vowel formants (Hz) and relative gains for A -> O -> U -> M
VOWELS = {
    "A": ([730, 1090, 2440], [90, 110, 170], [1.0, 0.5, 0.18]),
    "O": ([570, 840, 2410], [80, 100, 160], [1.0, 0.35, 0.10]),
    "U": ([320, 870, 2240], [70, 100, 160], [1.0, 0.18, 0.06]),
    "M": ([250, 1000, 2200], [60, 200, 300], [1.0, 0.03, 0.02]),
}


def om(f0=110.0, length=5.2, amp=1.0):
    """One sustained "Om" by a small group of chanters (additive formants)."""
    t = tvec(length)
    u = t / length
    # vowel trajectory: A (0-.12) -> O (.25) -> U (.45) -> M (.62-1)
    keys = [(0.0, "A"), (0.12, "A"), (0.25, "O"), (0.45, "U"), (0.62, "M"),
            (1.0, "M")]
    xs = [k[0] for k in keys]
    F = np.array([[np.interp(u, xs, [VOWELS[v][0][i] for _, v in keys])
                   for i in range(3)]])[0]
    B = np.array([[np.interp(u, xs, [VOWELS[v][1][i] for _, v in keys])
                   for i in range(3)]])[0]
    G = np.array([[np.interp(u, xs, [VOWELS[v][2][i] for _, v in keys])
                   for i in range(3)]])[0]
    # breath-in swell, sustain, hum fades out
    env = np.minimum(1, t / 0.35) * np.where(u < 0.8, 1, np.cos((u - 0.8) / 0.2 * np.pi / 2) ** 2 * 0.9 + 0.1)
    env *= np.where(u > 0.6, 1 - 0.35 * (u - 0.6) / 0.4, 1)
    out = np.zeros_like(t)
    voices = [(1.0, 1.0), (1.004, 0.8), (0.996, 0.8), (0.5, 0.55), (1.002, 0.6)]
    for detune, vamp in voices:
        vib = 1 + 0.004 * np.sin(2 * np.pi * rng.uniform(4.6, 5.6) * t
                                 + rng.uniform(0, 6)) * np.minimum(1, t / 1.5)
        drift = 1 + 0.002 * np.sin(2 * np.pi * 0.3 * t + rng.uniform(0, 6))
        f = f0 * detune * vib * drift
        phase = 2 * np.pi * np.cumsum(f) / SR
        for k in range(1, 48):
            fk = k * f
            if fk[0] > 5000:
                break
            spec = sum(G[i] * lorentz(fk, F[i], B[i]) for i in range(3))
            spec = spec + 0.015  # keep some buzz between formants
            out += vamp * (1 / k**0.7) * spec * np.sin(k * phase + rng.uniform(0, 6))
    breath = bandpass(rng.standard_normal(len(t)), 400, 3000) * 0.01 * np.exp(-t / 0.4)
    return amp * env * out / 6 + breath


def shankh(f0=311.0, length=3.6, amp=1.0):
    """Conch blow: pitch scoops up, brightens with breath, falls off at end."""
    t = tvec(length)
    u = t / length
    env = np.minimum(1, (t / 0.35) ** 1.5) * np.where(u < 0.85, 1, (1 - (u - 0.85) / 0.15)) ** 1.2
    scoop = 2 ** (-1.2 * np.exp(-t / 0.18) / 12)
    fall = 2 ** (-2.0 * np.clip((u - 0.88) / 0.12, 0, 1) ** 2 / 12)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.clip((t - 1.2) / 1.0, 0, 1)
    f = f0 * scoop * fall * vib
    phase = 2 * np.pi * np.cumsum(f) / SR
    out = np.zeros_like(t)
    for k in range(1, 30):
        fk = k * f0
        if fk > 9000:
            break
        bright = env ** (0.15 * k)  # louder -> brighter, like brass
        res = 0.4 + lorentz(fk, 1150, 900) + 0.5 * lorentz(fk, 2600, 1200)
        out += (k ** -0.9) * res * bright * np.sin(k * phase)
    breath = bandpass(rng.standard_normal(len(t)), 900, 4500) * 0.03 * env
    return amp * env * out / 3 + breath


def drum(f=95.0, length=0.6, amp=1.0, ring=0.0):
    """Bass stroke (dha/dhol) with optional harmonic treble ring (na)."""
    t = tvec(length)
    pitch = f * (1 + 0.5 * np.exp(-t / 0.03))
    body = np.sin(2 * np.pi * np.cumsum(pitch) / SR) * np.exp(-t / 0.18)
    click = bandpass(rng.standard_normal(len(t)), 1200, 7000) * np.exp(-t / 0.005)
    out = body + 0.3 * click
    if ring:
        rf = ring
        for k, a in [(1, 1.0), (2, 0.6), (3, 0.45), (4, 0.3), (5, 0.18)]:
            out += 0.5 * a * np.sin(2 * np.pi * rf * k * t) * np.exp(-t / (0.35 / k**0.4))
    return amp * out


def damru_hit(amp=1.0):
    t = tvec(0.18)
    pitch = 420 * (1 + 0.25 * np.exp(-t / 0.015))
    body = np.sin(2 * np.pi * np.cumsum(pitch) / SR) * np.exp(-t / 0.05)
    snap = highpass(rng.standard_normal(len(t)), 2000) * np.exp(-t / 0.008)
    return amp * (body + 0.5 * snap)


def ghungroo(length=0.5, amp=1.0):
    """A shake of ankle bells: cluster of tiny, very high bells."""
    out = np.zeros(int(length * SR))
    for _ in range(14):
        at = abs(rng.normal(0.05, 0.05))
        b = bell(rng.uniform(3800, 6200), 0.45, decay=0.12, amp=rng.uniform(0.2, 0.5))
        place(out, b, min(at, length - 0.01))
    return amp * highpass(out, 2500)


def tanpura(sa=146.83, length=20.0, amp=1.0, cycle=4.8):
    """Pa - Sa - Sa - Sa(low) drone with jawari shimmer."""
    out = np.zeros(int(length * SR))
    pattern = [sa * 0.75, sa, sa, sa * 0.5]
    step = cycle / 4
    n = 0
    at = 0.0
    while at < length:
        f = pattern[n % 4]
        t = tvec(min(5.0, length - at + 0.01))
        s = np.zeros_like(t)
        for k in range(1, 26):
            if f * k > 7000:
                break
            jawari = 1 + 2.5 * (k / 25) * np.exp(-((t - 0.6) / 0.5) ** 2)
            s += (k ** -1.1) * jawari * np.exp(-t / (3.2 / k**0.25)) * np.sin(
                2 * np.pi * f * k * t + rng.uniform(0, 6))
        s *= 1 - np.exp(-t / 0.004)
        place(out, s, at)
        at += step
        n += 1
    return amp * out / 3


def flute(notes, sa=293.66, amp=1.0, glide=0.07):
    """Bansuri phrase. notes = [(ratio, seconds), ...]; ratio None = rest."""
    total = sum(d for _, d in notes)
    t = tvec(total)
    f = np.zeros_like(t)
    gate = np.zeros_like(t)
    pos = 0
    last = notes[0][0] or 1.0
    for ratio, dur in notes:
        n = int(dur * SR)
        if ratio is None:
            f[pos:pos + n] = sa * last
        else:
            target = sa * ratio
            g = np.minimum(1, np.arange(n) / (glide * SR))
            f[pos:pos + n] = sa * last + (target - sa * last) * g
            seg = np.ones(n)
            a, r = int(0.06 * SR), int(0.12 * SR)
            seg[:a] = np.linspace(0, 1, a)
            seg[-r:] *= np.linspace(1, 0.6, r)
            gate[pos:pos + n] = seg
            last = ratio
        pos += n
    gate = lowpass(gate, 30)
    vib = 1 + 0.008 * np.sin(2 * np.pi * 5.0 * t)
    phase = 2 * np.pi * np.cumsum(f * vib) / SR
    tone = np.sin(phase) + 0.12 * np.sin(2 * phase) + 0.06 * np.sin(3 * phase)
    breath = bandpass(rng.standard_normal(len(t)), 1500, 6000) * 0.05
    return amp * gate * (tone * (1 + 0.1 * np.sin(2 * np.pi * 3.1 * t)) + breath)


# just-intonation swaras
S, r, R, g, G, m, M, P, d, D, n, N = (1, 16 / 15, 9 / 8, 6 / 5, 5 / 4, 4 / 3,
                                      45 / 32, 3 / 2, 8 / 5, 5 / 3, 9 / 5, 15 / 8)


# ------------------------------------------------------------------ tones ---
def shiva(short):
    if short:
        buf = silence(6.5)
        place(buf, om(110, 5.2), 0.1)
        place(buf, bowl(220, 6.0, 3.0, 0.35), 0.0)
        return master(reverb(buf, 2.6, 0.32), fade_out=1.0)
    buf = silence(24)
    at = 0.0
    for i in range(22):  # damru roll, accelerating then settling
        place(buf, damru_hit(0.5 + 0.02 * i), at)
        at += 0.14 if i % 2 else 0.09
    place(buf, bowl(220, 10.0, 4.0, 0.4), 2.6)
    for k in range(3):
        place(buf, om(110, 5.6), 3.0 + k * 6.2)
    place(buf, bowl(220, 6.0, 3.5, 0.45), 21.0)
    return master(reverb(buf, 3.0, 0.34))


def hanuman(short):
    length = 6.0 if short else 22.0
    buf = silence(length)
    beat = 0.5
    t = 0.0
    i = 0
    while t < length - 1.5:
        place(buf, drum(85, 0.7, 0.9 if i % 4 == 0 else 0.6), t)
        if i % 2:
            place(buf, drum(110, 0.5, 0.4, ring=392), t + beat / 2)
        for j in range(3):  # aarti ghanti clangs
            place(buf, hand_bell(1450 + 30 * (j % 2), 1.2, 0.45), t + j * beat / 3)
        t += beat
        i += 1
    if not short:
        place(buf, shankh(311, 2.4, 0.7), 0.0)
    place(buf, bell(392, 6.0, 2.5, 0.9), length - 4.0)
    return master(reverb(buf, 2.2, 0.28))


def ganesha(short):
    length = 6.5 if short else 22.0
    sa = 261.63
    buf = silence(length)
    place(buf, tanpura(sa / 2, length, 0.5), 0)
    motif = [S, G, P, D, P, G, R, S]
    beat = 0.36
    reps = 1 if short else 5
    at = 0.4
    for rep in range(reps):
        for k, ratio in enumerate(motif):
            place(buf, bell(sa * 2 * ratio, 2.2, 0.9, 0.5), at + k * beat)
            if k % 2 == 0:
                place(buf, drum(100, 0.5, 0.45, ring=sa), at + k * beat)
            else:
                place(buf, drum(130, 0.3, 0.2, ring=sa * 1.5), at + k * beat)
        at += len(motif) * beat + (0.3 if short else 0.9)
    place(buf, bell(sa, 5.0, 2.5, 0.6), min(at, length - 4))
    return master(reverb(buf, 2.4, 0.3))


def vishnu(short):
    if short:
        buf = silence(6.0)
        place(buf, shankh(311, 3.8), 0.1)
        place(buf, bell(466, 4.0, 2.0, 0.5), 3.6)
        return master(reverb(buf, 2.8, 0.32))
    buf = silence(23)
    place(buf, tanpura(155.56, 23, 0.35), 0)
    for k, ln in enumerate([3.4, 3.4, 5.6]):  # the traditional three blows
        place(buf, shankh(311, ln), 0.3 + k * 4.4)
    for k in range(6):
        place(buf, bell(466, 5.0, 2.4, 0.55), 14.0 + k * 1.4)
    return master(reverb(buf, 3.0, 0.32))


def lakshmi(short):
    sa = 293.66
    # Raga Bhupali — gentle, auspicious pentatonic
    phrase = [(S, .6), (R, .4), (G, .9), (P, .5), (G, .4), (R, .5), (G, 1.0),
              (P, .5), (D, .5), (2 * S, 1.2), (D, .4), (P, .5), (G, .6),
              (R, .4), (S, 1.6)]
    if short:
        phrase = [(G, .5), (P, .4), (D, .5), (2 * S, 1.4), (D, .4), (P, 1.4)]
    length = sum(dd for _, dd in phrase) + 2.5
    buf = silence(length)
    place(buf, tanpura(sa / 2, length, 0.4), 0)
    place(buf, flute(phrase, sa, 0.55), 0.8)
    for at in np.arange(0.0, length - 2, 1.9 if not short else 2.2):
        place(buf, ghungroo(0.5, 0.35), at)
    place(buf, bell(sa * 2, 4.0, 1.8, 0.35), length - 3.2)
    return master(reverb(buf, 2.6, 0.33))


def shani(short):
    if short:
        buf = silence(6.5)
        place(buf, bowl(110, 6.5, 4.5, 1.0), 0.05)
        place(buf, bowl(165, 5.0, 3.0, 0.4), 1.6)
        return master(reverb(buf, 3.2, 0.3), fade_out=1.6)
    buf = silence(25)
    for at, f, a in [(0.0, 110, 1.0), (4.0, 165, 0.6), (8.5, 110, 0.9),
                     (12.5, 146.8, 0.6), (17.0, 110, 1.0)]:
        place(buf, bowl(f, 9.0, 5.0, a), at)
    place(buf, om(98, 6.0, 0.35), 9.0)
    return master(reverb(buf, 3.4, 0.32), fade_out=2.5)


def surya(short):
    sa = 293.66
    # Raga Bhairav, the classic dawn raga — a rising, brightening phrase
    phrase = [(S, .8), (r, .5), (G, .7), (m, .6), (P, 1.0), (d, .5), (P, .5),
              (m, .4), (P, .6), (d, .5), (N, .5), (2 * S, 1.8), (N, .4),
              (d, .5), (P, 1.4)]
    if short:
        phrase = [(S, .5), (G, .5), (m, .4), (P, .6), (d, .4), (N, .4), (2 * S, 1.6)]
    length = sum(dd for _, dd in phrase) + 2.8
    buf = silence(length)
    tp = tanpura(sa / 2, length, 0.5)
    tp *= np.linspace(0.4, 1.0, len(tp))  # sunrise swell
    place(buf, tp, 0)
    place(buf, flute(phrase, sa, 0.6), 1.0 if not short else 0.4)
    place(buf, bell(sa * 2, 5.0, 2.2, 0.5), length - 3.6)
    if not short:
        place(buf, bell(sa, 5.0, 2.6, 0.4), 0.0)
    return master(reverb(buf, 2.6, 0.3))


TONES = [
    ("shiva_om", "Om chant · Shiva", shiva),
    ("hanuman_ghanta", "Aarti ghanta · Hanuman", hanuman),
    ("ganesha_mangal", "Mangal bells · Ganesha", ganesha),
    ("vishnu_shankh", "Shankh naad · Vishnu", vishnu),
    ("lakshmi_bhupali", "Bansuri & ghungroo · Lakshmi", lakshmi),
    ("shani_bowl", "Singing bowl · Shani Dev", shani),
    ("surya_bhairav", "Dawn raga · Surya", surya),
]


def encode(x, path):
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(SR),
         "-ac", "1", "-i", "pipe:0", "-c:a", "libvorbis", "-q:a", "4", path],
        input=pcm, check=True)


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    manifest = []
    for tone_id, name, fn in TONES:
        for short in (False, True):
            fname = f"{tone_id}{'_short' if short else ''}_v1.ogg"
            path = os.path.join(out_dir, fname)
            encode(fn(short), path)
            data = open(path, "rb").read()
            manifest.append({"id": tone_id, "name": name, "short": short,
                             "file": fname, "bytes": len(data),
                             "sha256": hashlib.sha256(data).hexdigest()})
            print(f"{fname:34s} {len(data) / 1024:7.1f} KB")
    with open(os.path.join(out_dir, "tones.json"), "w") as f:
        json.dump({"version": 1, "license": "CC0-1.0", "tones": manifest}, f,
                  indent=2)


if __name__ == "__main__":
    main(sys.argv[1])
