# Hinge Lab

Slider UI and CLI for the squeaky-hinge friction synthesizer described in
`../docs/domain-expertise.md` (elasto-plastic stick-slip friction driving hinge and
door-leaf modes, radiated through a wood panel, door frame and room).

## Run the UI

```bash
cd hinge-lab
cargo run --release
```

- Pick a **preset**, then drag sliders; the sound re-renders when you release the mouse
  and auto-plays (toggle with "Auto-play on change"). Hover a slider for what it does.
- **Seed**: same parameters + same seed = identical sound. `+1` or `Random` gives a new
  variation with the same parameters.
- **Save WAV + JSON…** writes `name.wav` and `name.json` (every parameter including seed).
  **Load JSON…** restores it exactly.
- Plots: waveform, squeak pitch track (dots only where the sound is periodic), and pin
  sliding speed against `stribeck_speed` (the squeak window sits near that line).

## CLI

```bash
cargo run --release -- render --preset squeaky --out squeaky.wav
cargo run --release -- render --preset rusty_groan --set load=3 --seed 7 --out x.wav
cargo run --release -- render --params x.json --out x_again.wav   # bit-identical to x.wav
```

## Tests

```bash
cargo test --release   # determinism, seed variation, oiled much quieter than dry
```
