# Blog post outline (draft)

**Working title:** "Why my procedural door squeak sounded like a beep, and how measuring real
squeaks fixed it"

Alternative: "From AI-written sound effects to physics and back: teaching code to squeak"

## 1. Where we started (hook + context)
- The thesis: AI writes the *code* for sound effects; no AI at runtime; MIT output vs.
  CC-BY-NC "open" audio models.
- Phase 1 (2026-02, opencode + GLM-4.7): 10 generators, a trainer, a demo page.
  Image: `images/screenshot.png`.
- What worked (thud, click, sirens, saucer) and what didn't: the "door creak" that sounded like
  wind, and a hinge generator that didn't sound like a hinge.
- Repo state on return: WAVs never committed, a generator with a broken `__main__`,
  unseeded randomness, no venv.

## 2. Setting up properly (short, practical)
- `uv venv`, `uv pip install numpy sounddevice matplotlib`; never system Python.
- Rust toolchain for the UI (eframe/egui, rodio, hound).
- `ffmpeg` and `uvx yt-dlp` for reference audio, kept in a gitignored `references/` folder.
- Lesson: write the environment rules down (CLAUDE.md, agent memory) so the agent follows them.

## 3. Research before code (the domain-expert step)
- Primary sources: Akay (JASA 2002), Avanzini/Serafin/Rocchesso (DAFx-02), Farnell (*Designing
  Sound*).
- The physics in four bullets: stick-slip, lock-in = pitch, creak = irregular slips, the
  load/speed window. Why oil works.
- What the old generator got wrong: 3–12 Hz "bursts" plus an added sine tone.
- Sanity simulation: squeak only inside the window; creak rate tracks speed.

## 4. Building Hinge Lab
- Elasto-plastic friction + modal resonators in Rust; why Rust (0.1 s renders, live sliders).
- Reproducibility: seed + JSON sidecar = bit-identical WAV (shown with hashes).
- Image: `images/hinge-lab-ui.png`.
- Honest result: physically correct, perceptually wrong. One smooth, slowly gliding tone.
- Side quest: the pure model held one pitch; `pitch_bend` (load-dependent stiffness) was a
  labeled phenomenological fix.

## 5. Listening wasn't enough: measuring real squeaks
- Pulling audio from a reference video; why it stays local (provenance).
- `tools/squeak_analysis.py`: events → pitch (YIN) + roughness → parts → categories →
  resynthesis.
- Debugging the analyzer in public: octave errors (the "every jump is exactly 12 semitones"
  clue), outlier frames at transitions, noise-wash creaks → pulse-timed creaks.
- Images: `images/analysis-stepped.png`, `images/analysis-overview.png`,
  `images/analysis-page.png`.

## 6. What the measurements showed
- Five categories: stepped squeak, gliding squeak, squeak → creak, creak/ratchet, low groan.
- Three things the model lacked: multiple parts with pitch jumps, bright pulse spectra,
  smooth/rough alternation with slowing clicks.
- Resynthesis from slip pulses + measured contours reproduces them (listen on the demo site).

## 7. Publishing without redistributing
- gh-pages site, one main page: first-attempt players, second-attempt players, then a short
  Details section linking to the full analysis (spectrograms, no reference audio, timestamped
  links to the source) and the physics model. Image: `images/demo-page.png`.
- Fixing what the old demo hid: a thud that was inaudible on laptop speakers, a "realistic"
  siren that wasn't (removed), WAVs never kept, a generator that crashed on run.
- Build script guard: refuses to build if reference clips appear in the output.

## 8. What's next
- Segment-score synthesis in Hinge Lab ("load from analysis").
- Parameter fitting, then text → segment score via an LLM, with listening tests.
- Same exciter for chalk, sneakers, wineglass, brakes.
- Own CC0 recordings so references can be shared.

## 9. Takeaways
- Research first, but **measure** before trusting the model or your ears.
- A physically correct model can be perceptually wrong. Measurement shows which part is missing.
- Make outputs reproducible early (seeds, sidecars): it turns "sounds wrong" into a diff.
- Keep provenance clean from day one.

## Assets checklist
- [ ] Before/after audio: Phase 1 "door creak", Hinge Lab `squeaky`, a resynthesized stepped squeak
- [ ] Screenshots: Phase 1 page, Hinge Lab UI, analysis page
- [ ] One annotated spectrogram (reference vs. resynthesis)
- [ ] Link to the live demo and repo
