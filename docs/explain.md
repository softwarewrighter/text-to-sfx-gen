# What each file does (explained simply)

Think of this project as a kitchen that cooks sounds instead of food.

- **Recipes** are code that *creates* audio: math that turns numbers into a wiggly line
  (a waveform). A speaker moves back and forth following that line, and you hear it.
- **Jars** are WAV files: the waveform *saved to disk* so you can keep it.
- **Taste testers** *play* audio through your speakers.
- **Photos of the food** are graphs: pictures that show what a sound looks like (how loud it
  is over time, what pitch it has).

There are two kitchens: the **first attempt** (Python, 2026-02) and the **second attempt**
(Rust app + Python analysis, 2026-10). The second one cooks only one dish, the squeaky door
hinge, but cooks it much better.

## Cheat sheet

| File | Creates audio | Saves to file | Plays audio | Graphs / visualizes |
|---|:---:|:---:|:---:|:---:|
| `*_generator.py` (first attempt) | ✅ | ✅ WAV | | |
| `sfx_trainer.py` | ✅ | ✅ WAV | ✅ (`afplay`) | |
| `play_3d_audio.py` | | | ✅ (`sounddevice`) | |
| `hinge-lab/src/synth.rs` | ✅ | ✅ WAV + JSON | | |
| `hinge-lab/src/analysis.rs` | | | | ✅ (computes the plot data) |
| `hinge-lab/src/main.rs` | (calls synth) | ✅ (Save button, CLI) | ✅ (`rodio`) | ✅ (draws plots, `egui_plot`) |
| `tools/squeak_analysis.py` | ✅ (resyntheses) | ✅ WAV, PNG, JSON, HTML | | ✅ (`matplotlib`) |
| `tools/build_page.py` | | ✅ HTML | ✅ (via browser `<audio>` players) | |
| `demos/index.html`, `index.html` | | | ✅ (browser players) | |

## First attempt: the Python recipe cards

Each generator is one recipe for one sound. Run it and a WAV file appears next to it.
They all work the same way: `numpy` builds the waveform (sine waves, random noise, filters,
volume envelopes), then Python's built-in `wave` module writes it as a 16-bit, 44.1 kHz WAV.
None of them play sound; they only make and save it.

| File | Sound it makes | Output file(s) |
|---|---|---|
| `thud_generator.py` | A heavy knock: a low boom, a mid "knock", a tiny click | `thud.wav` |
| `button_click_generator.py` | A short high UI click | `button_click.wav` |
| `explosion_generator.py` | Low rumble plus a burst of noise | `explosion.wav` |
| `flying_saucer_generator.py` | Sci-fi UFO wobble that rises and falls | `flying_saucer_*.wav` |
| `gravel_footsteps_generator.py` | Footsteps on gravel walking left to right | `gravel_footsteps.wav` |
| `siren_generator.py` | Simple two-tone siren | `siren.wav` |
| `siren_3d_generator.py` | US wail, European hi-lo and US yelp sirens driving past (Doppler) | `siren_*_doppler.wav`, ... |
| `siren_realistic_generator.py` | An attempt at a more realistic wail (not convincing; removed from the demo) | `siren_us_wail_realistic.wav` |
| `wind_whistling_generator.py` | Whistling tone. Started life as the first "door creak" | `wind_whistling.wav` |
| `hinge_creak_generator.py` | Second try at a door creak (pulses through filters) | `hinge_creak.wav` |

Helpers from the first attempt:

- **`sfx_trainer.py`**: a "taste test" loop. It cooks 4 versions of a sound, *plays* each one
  with macOS `afplay`, and asks you to pick the best (or tweak and retry). It *saves*
  `attempts/attempt_NN.wav` and your pick as `attempts/<sound>_final.wav`. It has its own
  copies of a few recipes inside it (door creak, siren wail, gravel footsteps).
- **`play_3d_audio.py`**: the simplest taste tester. Give it a WAV file and it *plays* it
  through your speakers with the `sounddevice` library. Works for mono and stereo.
  `.venv/bin/python play_3d_audio.py thud.wav`
- **`research_audio.py`**: an early script that used a browser (Playwright) to read Wikipedia
  about synthesis. No audio.

First-attempt pages: `demos/index.html` (and an older copy, `index.html`, at the top level)
are web pages with an `<audio>` player per sound. Your browser does the playing; the WAVs in
`demos/` are copies of generator output.

## Second attempt: Hinge Lab (Rust)

`hinge-lab/` is a desktop app with sliders. Move a slider and you hear the new squeak about a
tenth of a second later. It is three files:

- **`src/synth.rs`** *creates and saves* the sound. It simulates the physics of a hinge: the
  pin sticks, force builds up, it slips, and the cycle repeats hundreds of times a second
  (stick-slip friction). Those slips shake the metal, which rings at its own pitches, then the
  door panel and the room color the sound. It holds the list of sliders (`Params`) and the
  presets (`squeaky`, `oiled`, `horror_slow`, ...). `render()` turns sliders into samples;
  `save()` writes a WAV (via `hound`) plus a JSON file of the exact slider values, so
  `load_json()` can rebuild the identical sound later. Same sliders + same seed = same sound,
  every time.
- **`src/analysis.rs`** *measures* the sound for the graphs: how loud it is over time
  (envelope), what pitch it has over time (pitch track), and how fast the door is swinging
  (speed curve). It makes numbers, not pictures.
- **`src/main.rs`** is the app and the command line. It draws the window (`eframe`/`egui`),
  the sliders, and *draws the three graphs* (`egui_plot`) from `analysis.rs`'s numbers. It
  *plays* audio with `rodio` (Play/Stop, or auto-play after each change). It *saves* through
  the Save WAV+JSON button, loads with Load JSON, and has two commands:
  - `hinge-lab render --preset squeaky --out s.wav` (make and save, no window)
  - `hinge-lab screenshot out.png squeaky` (open the app in the background, save a picture of
    it, quit; used to make `images/hinge-lab-ui.png`)

`demos/hinge/*.json` are saved slider settings for each preset.

## Second attempt: measuring real squeaks (Python)

**`tools/squeak_analysis.py`** is the "listen carefully and take notes" tool. Give it a
recording of real squeaks (the reference from YouTube lives only on your machine, in the
gitignored `references/` folder). It:

1. **Finds** each squeak in the recording (where it gets loud and quiet again).
2. **Measures** each one: pitch over time (the YIN method), how smooth vs. rough it is, where
   the pitch jumps, how many clicks per second when it turns into a creak.
3. **Sorts** each squeak into one of 5 kinds (stepped, gliding, squeak-to-creak, creak, groan).
4. **Creates audio**: rebuilds each squeak from those measurements as a train of slip pulses
   pushed through the squeak's measured tone color. These *resyntheses* are our own sound,
   not the recording, and they are the second-attempt sounds on the demo.
5. **Graphs** it with `matplotlib`: one picture per squeak (spectrogram of the original with
   the pitch line and squeak/creak parts marked, spectrogram of our rebuild below it for
   comparison, then loudness and roughness over time) and an overview picture of all squeaks.
6. **Saves** `ev{n}_resynth.wav`, `ev{n}.png`, `overview.png`, `analysis.json` and an
   `index.html` report. Only in local mode (no `--no-reference-audio`) does it also save
   `ev{n}_ref.wav` clips of the original recording; those never leave your machine. Note
   that the published spectrogram pictures do show the original recording; only its audio
   is withheld.

## Building and publishing the demo website

- **`tools/build_site.sh`** is the head chef. It runs everything into `site/`: re-cooks the
  first-attempt sounds, renders the Hinge Lab presets, takes the Hinge Lab screenshot, runs
  `squeak_analysis.py` in publish mode (no reference audio), builds the pages, and takes
  screenshots of the pages with headless Chrome. It refuses to finish if any `*_ref.wav`
  slipped into `site/`.
- **`tools/build_page.py`** *writes the web pages*: `site/index.html` (Part 1 players, Part 2
  players, Details) and `site/hinge-lab.html`, and adds the GitHub corner and footer. The
  pages contain `<audio>` players; the browser plays the sounds.
- **`tools/publish_site.sh`** copies `site/` to the `gh-pages` branch and pushes it, which
  updates the live demo. It also refuses if any reference audio is present.
- **`site-src/style.css`**: the look of the demo pages.

## Everything else

| Path | What it is |
|---|---|
| `README.md` | Front page: what the project is, summary, quick start |
| `docs/phase1.md` | First attempt in detail |
| `docs/phases.md` | Status and what remains, per attempt |
| `docs/domain-expertise.md` | The research on why hinges squeak and how to model it |
| `docs/blog-outline.md` | Outline for a blog post about the project |
| `docs/research-findings.md`, `3D_AUDIO_README.md` | First-attempt research notes |
| `docs/process.md`, `docs/tools.md`, `docs/ai_agent_instructions.md` | General agent/process guidelines copied from a template |
| `session-ses_3ba5.md` | Transcript of the first-attempt coding session |
| `AGENTS.md` | Notes for AI coding agents |
| `.claude/skills/domain-expert/` | The research skill used for the second attempt |
| `images/` | Screenshots and figures used in the README and docs |
| `references/` (gitignored) | Local copy of the YouTube reference audio; never committed or published |
| `site/` (gitignored) | Built demo website |
| `LICENSE`, `COPYRIGHT` | MIT license and copyright notice |

## The path a sound takes

```
First attempt:   thud_generator.py ──creates──▶ thud.wav ──▶ play_3d_audio.py / browser player

Hinge Lab:       sliders ──▶ synth.rs render() ──▶ samples ──▶ rodio plays them
                                                      ├──▶ analysis.rs ──▶ main.rs graphs
                                                      └──▶ save(): .wav + .json

Analysis:        reference recording ──▶ squeak_analysis.py ──▶ measurements ──▶ resynth .wav
                                                                       └──▶ .png graphs + report

Website:         build_site.sh ──▶ site/ ──▶ publish_site.sh ──▶ gh-pages (browser plays)
```
