# Phase 1: AI-written procedural generators (2026-02)

![Phase 1 demo page](../images/screenshot.png)

[opencode](https://opencode.ai) with GLM-4.7 ([Z.ai Coding Plan](https://z.ai/subscribe)) wrote
a Python script per sound effect. Each script uses pure mathematical synthesis (sine waves,
noise, filters, envelopes) and writes a WAV file. The [session transcript](../session-ses_3ba5.md)
shows the interactive development.

Simple sounds (impacts, clicks, sweeps, sirens) worked well. Door sounds did not: the "door
creak" sounded like wind, and the first hinge generator didn't sound like a hinge. That led to
[Phase 2](../README.md). Status and remaining work are in [phases.md](phases.md).

## Sound effects

| Sound | Generator | Features |
|-------|-----------|----------|
| **Thud** | `thud_generator.py` | Click, 200→80 Hz pitch-drop body, 200–600 Hz knock (revised 2026-10; the original was inaudible on laptop speakers) |
| **Button Click** | `button_click_generator.py` | High frequency (2–4 kHz), sharp attack, immediate decay |
| **Wind Whistling** | `wind_whistling_generator.py` | Pitch variations (600–900 Hz), smooth flow. The original demo page labels this "door creak" (an early door creak attempt that sounded like wind) |
| **Explosion** | `explosion_generator.py` | Low rumble (20–50 Hz), broadband noise, long decay |
| **Gravel Footsteps** | `gravel_footsteps_generator.py` | 6-second sequence, irregular timing, 3D spatialization, multi-band filtering |
| **Siren (Basic)** | `siren_generator.py` | 500/800 Hz alternating, 2.5 Hz cycle |
| **Siren (US Wail, EU Hi-Lo, US Yelp)** | `siren_3d_generator.py` | Sweeps and alternating tones with Doppler and radial velocity |
| **Siren (Realistic US Wail)** | `siren_realistic_generator.py` | Odd harmonics, tremolo, smoother sweep. Removed from the demo in 2026-10: it doesn't sound realistic yet |
| **Flying Saucer** | `flying_saucer_generator.py` | 200–800 Hz rise-fall sweep, metallic texture, Doppler |
| **Hinge Creak** | `hinge_creak_generator.py` | First stick-slip attempt (superseded by Phase 2) |

```bash
.venv/bin/python thud_generator.py
afplay thud.wav                                          # macOS
.venv/bin/python play_3d_audio.py gravel_footsteps.wav   # use headphones for 3D
```

WAV files are written to the project root (gitignored). The original demo page is
`demos/index.html`; its `*.wav` entries are symlinks to the root files.

Note: except for the revised Thud, these generators don't seed their randomness, so noise-based
parts differ slightly on each run.

## Interactive trainer

`sfx_trainer.py` generates 4 variations, plays them, and lets you pick the best (0–3), regenerate
(r), or tweak parameters first. It saves the winner as `{sound_name}_final.wav`.

```bash
.venv/bin/python sfx_trainer.py
```

## How the generators work

1. **Research** (AI-assisted): natural acoustics of the target sound, foley techniques, key
   frequency components, envelope shape
2. **Implementation** (AI-generated code): waveforms (sine, square, noise), filters (low-, high-,
   band-pass), envelopes (attack, decay, sustain), mixing, effects
3. **3D spatialization** (optional): left/right panning, distance attenuation

Audio format: 44.1 kHz, 16-bit PCM WAV; mono, or stereo for spatialized sounds.

## Phase 1 docs

- [research-findings.md](research-findings.md): audio synthesis research
- [3D_AUDIO_README.md](../3D_AUDIO_README.md): 3D spatial audio techniques
- [session-ses_3ba5.md](../session-ses_3ba5.md): development transcript
