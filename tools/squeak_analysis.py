#!/usr/bin/env python3
"""
Squeak analysis: split a recording into events, extract a segment score per event,
categorize events, resynthesize them, and write an HTML report with plots and audio.

Usage (run with the project venv):
    .venv/bin/python tools/squeak_analysis.py references/squeak_yt_mono.wav references/analysis
    # For publishing: no reference clips, link each event to the source instead
    .venv/bin/python tools/squeak_analysis.py in.wav site/analysis \
        --no-reference-audio --source-url https://www.youtube.com/watch?v=...

Requires: numpy, matplotlib (uv pip install numpy matplotlib)

Per 5 ms frame: YIN pitch, aperiodicity (YIN dip depth: 0 = perfectly periodic), RMS.
Segments split where pitch jumps abruptly (> JUMP_SEMITONES) or voicing flips.
Resynthesis: stick-slip pulse train following the measured pitch contour (jitter from
aperiodicity), colored by the event's average spectral envelope (LPC). See
docs/domain-expertise.md for why squeaks are pulse trains locked to a hinge mode.
"""

import argparse
import html
import json
import sys
import wave
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt

SR = 44100
HOP = 220             # 5 ms analysis hop
WIN = 1024
FMIN, FMAX = 120, 3000
VOICED_APER = 0.25    # YIN dip below this = periodic (squeak)
JUMP_SEMITONES = 1.5  # pitch change within one hop that counts as a jump
MIN_SEG_FRAMES = 8    # 40 ms
EVENT_MIN_PEAK_DB = -32
EVENT_MIN_DUR_S = 0.4

CATEGORY_COLORS = {
    'stepped squeak': '#d62728',
    'gliding squeak': '#1f77b4',
    'squeak → creak': '#9467bd',
    'creak / ratchet': '#8c564b',
    'low groan': '#2ca02c',
}
CATEGORY_HELP = {
    'stepped squeak': 'Several steady pitch plateaus with abrupt jumps between them (mode hopping)',
    'gliding squeak': 'Mostly one continuous pitched glide, few or no jumps',
    'squeak → creak': 'Pitched squeak that breaks up into irregular stick-slip pulses',
    'creak / ratchet': 'Mostly aperiodic: separate slip pulses, heard as a creak or ratchet',
    'low groan': 'Pitched but low (under ~600 Hz), often wobbly',
}


def load(path):
    w = wave.open(str(path))
    if w.getnchannels() != 1 or w.getframerate() != SR:
        sys.exit(f"{path}: convert to mono {SR} Hz first, e.g. "
                 f"ffmpeg -i in.wav -ac 1 -ar {SR} out.wav")
    return np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(float) / 32768


def save(path, y):
    y = y / (np.max(np.abs(y)) + 1e-9) * 0.8
    with wave.open(str(path), 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((y * 32767).astype('<i2').tobytes())


def find_events(y):
    """Events = regions more than 15 dB above the noise floor, gaps < 150 ms closed."""
    hop = 441
    frames = len(y) // hop
    rms = np.sqrt(np.mean(y[:frames * hop].reshape(frames, hop) ** 2, axis=1))
    db = 20 * np.log10(rms + 1e-9)
    active = db > np.percentile(db, 20) + 15
    events, start, gap = [], None, 0
    for i, a in enumerate(active):
        if a:
            start = i if start is None else start
            gap = 0
        elif start is not None:
            gap += 1
            if gap > 15:
                end = i - gap + 1  # one past the last active frame
                events.append((start * hop, end * hop, db[start:end].max()))
                start, gap = None, 0
    if start is not None:
        events.append((start * hop, frames * hop, db[start:].max()))
    return [(a, b) for a, b, peak in events
            if peak > EVENT_MIN_PEAK_DB and (b - a) / SR > EVENT_MIN_DUR_S]


def yin_frame(x):
    max_lag, min_lag = SR // FMIN, SR // FMAX
    frame = x[:WIN]
    d = np.array([np.sum((frame - x[lag:lag + WIN]) ** 2) for lag in range(max_lag + 1)])
    cmnd = np.ones_like(d)
    cmnd[1:] = d[1:] * np.arange(1, max_lag + 1) / np.maximum(np.cumsum(d[1:]), 1e-12)
    below = np.flatnonzero(cmnd[min_lag:] < 0.2)
    if len(below):
        lag = min_lag + below[0]
        while lag + 1 <= max_lag and cmnd[lag + 1] < cmnd[lag]:
            lag += 1
    else:
        lag = min_lag + np.argmin(cmnd[min_lag:])
    shift = 0.0
    if 0 < lag < max_lag:
        a, b, c = cmnd[lag - 1], cmnd[lag], cmnd[lag + 1]
        shift = 0.5 * (a - c) / (a - 2 * b + c + 1e-12)
    return SR / (lag + shift), cmnd[lag]


def fix_octave(x, f0):
    """YIN can lock onto the 2nd harmonic. If odd multiples of f0/2 carry real energy,
    the true pitch is f0/2."""
    n = 4096
    spec = np.abs(np.fft.rfft(x[:n] * np.hanning(min(len(x), n)), n))
    bin_hz = SR / n

    def peak(f):
        k = int(round(f / bin_hz))
        return spec[max(k - 2, 0):k + 3].max() if k + 3 < len(spec) else 0.0

    half = f0 / 2
    if half < FMIN:
        return f0
    odd = sum(peak(half * k) for k in (1, 3, 5))
    even = sum(peak(f0 * k) for k in (1, 2, 3))
    return half if odd > 0.3 * even else f0


def track(y):
    max_lag = SR // FMIN
    n = max((len(y) - WIN - max_lag) // HOP, 0)
    f0, aper, rms = np.zeros(n), np.ones(n), np.zeros(n)
    for i in range(n):
        x = y[i * HOP:i * HOP + WIN + max_lag]
        rms[i] = np.sqrt(np.mean(x[:WIN] ** 2))
        if rms[i] > 1e-3:
            f0[i], aper[i] = yin_frame(x)
            f0[i] = fix_octave(x, f0[i])
    # Windows straddling a pitch jump look aperiodic; smooth those brief spikes out
    aper = np.array([np.median(aper[max(i - 4, 0):i + 5]) for i in range(n)])
    voiced = (aper < VOICED_APER) & (rms > 1e-3)
    # Single-frame pitch outliers at transitions: 5-frame median over voiced neighbors
    smoothed = f0.copy()
    for i in np.flatnonzero(voiced):
        neighbors = f0[max(i - 2, 0):i + 3][voiced[max(i - 2, 0):i + 3]]
        smoothed[i] = np.exp(np.median(np.log(neighbors)))
    return smoothed, aper, rms, voiced


def segment(f0, aper, rms, voiced):
    bounds, jumps = [0], []
    for i in range(1, len(f0)):
        flip = voiced[i] != voiced[i - 1]
        jump = (voiced[i] and voiced[i - 1]
                and abs(12 * np.log2(f0[i] / f0[i - 1])) > JUMP_SEMITONES)
        if (flip or jump) and i - bounds[-1] >= MIN_SEG_FRAMES:
            bounds.append(i)
            if jump:
                jumps.append(12 * np.log2(f0[i] / f0[i - 1]))
    bounds.append(len(f0))
    segs = []
    for a, b in zip(bounds[:-1], bounds[1:]):
        v = voiced[a:b]
        fv = f0[a:b][v]
        seg = {
            'start_s': round(a * HOP / SR, 3),
            'dur_s': round((b - a) * HOP / SR, 3),
            'type': 'squeak' if v.mean() > 0.5 else 'creak',
            'roughness': round(float(np.median(aper[a:b])), 3),
            'level_db': round(float(20 * np.log10(np.mean(rms[a:b]) + 1e-9)), 1),
        }
        if len(fv) >= 3:
            seg.update(f0_start=round(float(np.median(fv[:3])), 1),
                       f0_end=round(float(np.median(fv[-3:])), 1),
                       f0_median=round(float(np.median(fv)), 1))
        segs.append(seg)
    return segs, jumps


def brightness(y, f0_median):
    """Effective harmonic count: spectral centroid divided by the median pitch."""
    spec = np.abs(np.fft.rfft(y * np.hanning(len(y))))
    freqs = np.fft.rfftfreq(len(y), 1 / SR)
    centroid = np.sum(freqs * spec) / np.sum(spec)
    return centroid, centroid / f0_median if f0_median else None


def features(y, f0, aper, rms, voiced, segs, jumps):
    loud = rms > 0.1 * rms.max()
    fv = f0[voiced & loud]
    f0_median = float(np.median(fv)) if len(fv) else None
    centroid, harmonics = brightness(y, f0_median)
    squeak_segs = [s for s in segs if s['type'] == 'squeak' and 'f0_start' in s]
    glides = [12 * np.log2(s['f0_end'] / s['f0_start']) for s in squeak_segs if s['dur_s'] > 0.08]
    wobble = []
    for s in squeak_segs:
        a = int(s['start_s'] * SR / HOP)
        b = a + int(s['dur_s'] * SR / HOP)
        seg_f = f0[a:b][voiced[a:b]]
        if len(seg_f) > 10:
            st = 12 * np.log2(seg_f / np.median(seg_f))
            wobble.append(np.std(st - np.convolve(st, np.ones(9) / 9, 'same')))
    creak = creak_mask(voiced)
    pulse_times = slip_pulses(y, creak, rms)
    gaps = np.diff(pulse_times) / SR
    gaps = gaps[gaps < 0.15]  # pulses within one creak stretch
    return {
        'duration_s': round(len(y) / SR, 2),
        'creak_rate_hz': round(float(np.median(1 / gaps)), 0) if len(gaps) > 3 else 0,
        'squeak_pct': round(100 * float(voiced[loud].mean()), 0) if loud.any() else 0,
        'n_segments': len(segs),
        'n_jumps': len(jumps),
        'median_jump_st': round(float(np.median(np.abs(jumps))), 1) if jumps else 0,
        'f0_median_hz': round(f0_median, 0) if f0_median else None,
        'f0_range_st': round(float(12 * np.log2(np.percentile(fv, 95) / np.percentile(fv, 5))), 1)
        if len(fv) > 5 else 0,
        'mean_glide_st': round(float(np.mean(glides)), 1) if glides else 0,
        'wobble_st': round(float(np.mean(wobble)), 2) if wobble else 0,
        'centroid_hz': round(float(centroid), 0),
        'harmonic_count': round(float(harmonics), 1) if harmonics else None,
    }


def categorize(f):
    creak_pct = 100 - f['squeak_pct']
    if creak_pct > 60:
        return 'creak / ratchet'
    if creak_pct > 25:
        return 'squeak → creak'
    if f['f0_median_hz'] and f['f0_median_hz'] < 600:
        return 'low groan'
    if f['n_jumps'] >= 3:
        return 'stepped squeak'
    return 'gliding squeak'


def lpc(x, order=24):
    x = x * np.hanning(len(x))
    r = np.correlate(x, x, 'full')[len(x) - 1:len(x) + order].copy()
    r[0] *= 1.0001
    a = np.zeros(order + 1)
    a[0] = 1
    err = r[0]
    for i in range(1, order + 1):
        k = -(r[i] + np.dot(a[1:i], r[i - 1:0:-1])) / err
        a[1:i + 1] = a[1:i + 1] + k * np.concatenate([a[i - 1:0:-1], [1]])
        err *= 1 - k * k
    return a


def all_pole(a, x):
    y = np.zeros(len(x))
    for n in range(len(x)):
        acc = x[n]
        for k in range(1, min(len(a) - 1, n) + 1):
            acc -= a[k] * y[n - k]
        y[n] = acc
    return y


def creak_mask(voiced):
    """Frames inside an unvoiced run longer than MIN_SEG_FRAMES (short gaps are glitches)."""
    mask = np.zeros(len(voiced), bool)
    i = 0
    while i < len(voiced):
        if voiced[i]:
            i += 1
            continue
        j = i
        while j < len(voiced) and not voiced[j]:
            j += 1
        if j - i > MIN_SEG_FRAMES:
            mask[i:j] = True
        i = j
    return mask


def slip_pulses(y, mask, rms):
    """Times (samples) of individual slip pulses in creak frames: peaks of the
    high-passed envelope, at least 2 ms apart, standing out from the local level."""
    hp = np.abs(np.diff(y, prepend=0.0))
    env = np.convolve(hp, np.ones(44) / 44, 'same')        # 1 ms smoothing
    local = np.convolve(env, np.ones(882) / 882, 'same')   # 20 ms local level
    min_gap = int(0.002 * SR)
    times = []
    i = 1
    while i < len(env) - 1:
        frame = min(i // HOP, len(mask) - 1)
        if (mask[frame] and env[i] > 1.8 * local[i] and env[i] >= env[i - 1]
                and env[i] >= env[i + 1] and rms[frame] > 1e-3):
            times.append(i)
            i += min_gap
        else:
            i += 1
    return np.array(times, int)


def resynthesize(y, f0, aper, rms, voiced, seed=0):
    rng = np.random.default_rng(seed)
    n = len(f0) * HOP
    frames_t = np.arange(len(f0)) * HOP
    creak = creak_mask(voiced)
    held = f0.copy()
    last = 300.0
    for i in range(len(held)):
        if voiced[i]:
            last = held[i]
        else:
            held[i] = last  # short glitch: hold the pitch; creak frames are skipped below
    rate = np.interp(np.arange(n), frames_t, held)
    amp = np.interp(np.arange(n), frames_t, rms)
    rough = np.interp(np.arange(n), frames_t, np.clip(aper, 0, 1))
    in_creak = np.repeat(creak, HOP)[:n]
    pulses = np.zeros(n)
    phase = 0.0
    for i in range(n):
        if in_creak[i]:
            continue
        phase += rate[i] / SR * (1 + 0.2 * rough[i] * rng.standard_normal())
        if phase >= 1.0:
            phase -= 1.0
            pulses[i] = amp[i] * (1 + rough[i] * rng.standard_normal())
    # Creak: individual slip impulses at the measured times, scaled to the frame level
    for t in slip_pulses(y, creak, rms):
        if t < n:
            pulses[t] += amp[t] * 3 * (1 + 0.2 * rng.standard_normal())
    return all_pole(lpc(y), pulses)


def plot_event(path, title, y, resynth, f0, aper, rms, voiced, segs):
    t = np.arange(len(f0)) * HOP / SR
    fig, axes = plt.subplots(3, 1, figsize=(11, 7.5), sharex=True,
                             gridspec_kw={'height_ratios': [3, 3, 1.4]})
    for ax, sig, label in [(axes[0], y, 'reference'), (axes[1], resynth, 'resynthesis')]:
        ax.specgram(sig, NFFT=1024, Fs=SR, noverlap=896, cmap='magma', vmin=-125)
        ax.set_ylim(0, 10000)
        ax.set_ylabel(f'{label}\nHz')
    for s in segs:
        color = '#ffffff' if s['type'] == 'squeak' else '#00e5ff'
        axes[0].axvspan(s['start_s'], s['start_s'] + s['dur_s'], ymin=0.97, ymax=1.0,
                        color=color, alpha=0.9)
        axes[0].axvline(s['start_s'], color='#00ff88', lw=0.8, alpha=0.7)
    fv = np.where(voiced, f0, np.nan)
    axes[0].plot(t, fv, '.', color='#00ff88', ms=2.5, label='pitch (periodic frames)')
    axes[0].legend(loc='upper right', fontsize=8)
    axes[0].set_title(title, fontsize=10)
    axes[2].plot(t, 20 * np.log10(rms + 1e-9), color='#444', lw=1, label='level dB')
    axes[2].set_ylabel('dB')
    ax2 = axes[2].twinx()
    ax2.plot(t, np.clip(aper, 0, 1), color='#00a6c8', lw=1, label='roughness')
    ax2.axhline(VOICED_APER, color='#00a6c8', ls=':', lw=0.8)
    ax2.set_ylabel('roughness', color='#00a6c8')
    axes[2].set_xlabel('seconds  (top bar: white = squeak segment, cyan = creak segment)')
    plt.tight_layout()
    plt.savefig(path, dpi=72)
    plt.close(fig)


def plot_overview(path, rows):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    pairs = [('n_jumps', 'squeak_pct', 'pitch jumps', 'squeak (periodic) %'),
             ('f0_median_hz', 'harmonic_count', 'median pitch Hz', 'brightness (harmonics)'),
             ('mean_glide_st', 'f0_range_st', 'mean glide per segment (semitones)', 'pitch range (semitones)')]
    for ax, (x, yk, xl, yl) in zip(axes, pairs):
        for r in rows:
            f = r['features']
            if f[x] is None or f[yk] is None:
                continue
            ax.scatter(f[x], f[yk], s=60, color=CATEGORY_COLORS[r['category']],
                       edgecolor='k', lw=0.5)
            ax.annotate(f"#{r['id']}", (f[x], f[yk]), fontsize=8, xytext=(4, 3),
                        textcoords='offset points')
        ax.set_xlabel(xl)
        ax.set_ylabel(yl)
        ax.grid(alpha=0.3)
    handles = [plt.Line2D([], [], marker='o', ls='', color=c, label=k)
               for k, c in CATEGORY_COLORS.items()]
    fig.legend(handles=handles, loc='upper center', ncol=len(handles), fontsize=9)
    plt.tight_layout(rect=(0, 0, 1, 0.9))
    plt.savefig(path, dpi=72)
    plt.close(fig)


def source_link(source_url, seconds=None):
    """Link into the source; YouTube URLs get a timestamp."""
    if seconds is None or 'youtube.com/watch' not in source_url:
        return source_url
    return f"{source_url}&t={int(seconds)}s"


def write_html(path, source, rows, source_url=None, reference_audio=True):
    cats = {}
    for r in rows:
        cats.setdefault(r['category'], []).append(r)
    feature_keys = list(rows[0]['features'].keys())
    if source_url:
        url = html.escape(source_url)
        source_html = f"<a href='{url}'>{url}</a>"
    else:
        source_html = f"<code>{html.escape(source)}</code>"
    audio_note = '' if reference_audio else (
        "<p><b>Reference audio is not included.</b> Its provenance is unclear, so this page "
        "shows only analysis of it (spectrograms, pitch tracks, measurements). Each event "
        "links to its moment in the source. Every player on this page plays our own "
        "resynthesis, rebuilt from the measured pitch contour, slip-pulse timing and "
        "average spectral envelope.</p>")
    parts = [f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Squeak analysis</title>
<style>body{{font-family:system-ui,sans-serif;max-width:1180px;margin:24px auto;padding:0 16px;color:#222}}
table{{border-collapse:collapse;font-size:13px}}td,th{{border:1px solid #ccc;padding:3px 7px;text-align:right}}
th{{background:#f3f3f3}}td.l{{text-align:left}}.chip{{display:inline-block;padding:1px 8px;border-radius:9px;color:#fff;font-size:12px}}
.ev{{border-top:1px solid #ddd;margin-top:28px;padding-top:8px}}audio{{height:32px;vertical-align:middle}}
img{{max-width:100%}}code{{background:#f3f3f3;padding:1px 4px}}</style></head><body>
<h1>Squeak analysis</h1><p>Source: {source_html} — {len(rows)} events
(peak &gt; {EVENT_MIN_PEAK_DB} dBFS, longer than {EVENT_MIN_DUR_S} s).</p>{audio_note}
<h2>Categories</h2><ul>"""]
    for name, color in CATEGORY_COLORS.items():
        members = ', '.join(f"<a href='#ev{r['id']}'>#{r['id']}</a>" for r in cats.get(name, []))
        parts.append(f"<li><span class='chip' style='background:{color}'>{name}</span> "
                     f"{CATEGORY_HELP[name]} — {members or 'none'}</li>")
    parts.append("</ul><h2>How they differ</h2><img src='overview.png'>")
    parts.append("<h2>Features</h2><table><tr><th>#</th><th>category</th>"
                 + ''.join(f"<th>{k}</th>" for k in feature_keys) + "</tr>")
    for r in rows:
        parts.append(f"<tr><td><a href='#ev{r['id']}'>{r['id']}</a></td>"
                     f"<td class='l'><span class='chip' style='background:{CATEGORY_COLORS[r['category']]}'>"
                     f"{r['category']}</span></td>"
                     + ''.join(f"<td>{r['features'][k]}</td>" for k in feature_keys) + "</tr>")
    parts.append("</table><p>squeak_pct = share of loud frames that are periodic. "
                 "harmonic_count = spectral centroid / median pitch (higher = brighter). "
                 "wobble_st = pitch jitter within segments. glide = pitch change within a "
                 "segment (positive = rising).</p>")
    for r in rows:
        if reference_audio:
            reference = f"reference <audio controls src='ev{r['id']}_ref.wav'></audio> &nbsp; "
        elif source_url:
            link = html.escape(source_link(source_url, r['start_s']))
            reference = f"reference: <a href='{link}'>listen in the source at {r['start_s']:.0f} s</a> &nbsp; "
        else:
            reference = ''
        seg_rows = ''.join(
            f"<tr><td>{s['start_s']}</td><td>{s['dur_s']}</td><td class='l'>{s['type']}</td>"
            f"<td>{s.get('f0_start', '')}</td><td>{s.get('f0_end', '')}</td>"
            f"<td>{s['roughness']}</td><td>{s['level_db']}</td></tr>" for s in r['segments'])
        parts.append(f"""<div class='ev' id='ev{r['id']}'><h3>#{r['id']} at {r['start_s']} s
<span class='chip' style='background:{CATEGORY_COLORS[r['category']]}'>{r['category']}</span></h3>
<p>{reference}resynthesis <audio controls src='ev{r['id']}_resynth.wav'></audio></p>
<img src='ev{r['id']}.png'>
<details><summary>{len(r['segments'])} segments</summary><table>
<tr><th>start s</th><th>dur s</th><th>type</th><th>f0 start</th><th>f0 end</th><th>roughness</th><th>level dB</th></tr>
{seg_rows}</table></details></div>""")
    parts.append("</body></html>")
    Path(path).write_text('\n'.join(parts))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('source', type=Path, help='mono 44.1 kHz WAV')
    parser.add_argument('outdir', type=Path)
    parser.add_argument('--source-url', help='where the recording came from (shown and linked)')
    parser.add_argument('--no-reference-audio', action='store_true',
                        help='do not write or link reference clips (for publishing)')
    args = parser.parse_args()
    source, outdir = args.source, args.outdir
    outdir.mkdir(parents=True, exist_ok=True)
    y = load(source)
    rows = []
    for idx, (a, b) in enumerate(find_events(y)):
        a = max(a - int(0.03 * SR), 0)
        b = min(b + int(0.05 * SR), len(y))
        clip = y[a:b]
        f0, aper, rms, voiced = track(clip)
        segs, jumps = segment(f0, aper, rms, voiced)
        feats = features(clip, f0, aper, rms, voiced, segs, jumps)
        category = categorize(feats)
        resynth = resynthesize(clip, f0, aper, rms, voiced)
        if not args.no_reference_audio:
            save(outdir / f'ev{idx}_ref.wav', clip)
        save(outdir / f'ev{idx}_resynth.wav', resynth)
        title = f"#{idx} at {a / SR:.2f}s — {category}"
        plot_event(outdir / f'ev{idx}.png', title, clip, resynth, f0, aper, rms, voiced, segs)
        rows.append({'id': idx, 'start_s': round(a / SR, 2), 'category': category,
                     'features': feats, 'segments': segs})
        print(f"#{idx:2d} {a / SR:6.2f}s  {category:16s} {feats}")
    plot_overview(outdir / 'overview.png', rows)
    (outdir / 'analysis.json').write_text(json.dumps(rows, indent=1))
    write_html(outdir / 'index.html', str(source), rows, args.source_url,
               reference_audio=not args.no_reference_audio)
    print(f"Report: {outdir / 'index.html'}")


if __name__ == '__main__':
    main()
