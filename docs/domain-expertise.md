# Domain briefing — friction-induced sound (squeaky hinges, creaks) and procedural SFX pipelines

(compiled 2026-10-29, for task: synthesize parameterized squeaky-hinge sounds; generalize to an
exciter → interaction → resonator → modifier pipeline that an LLM can author; propose experiments)

**Confidence & ceiling:** High on the physics of friction sound and the elasto-plastic model:
these come from Akay's JASA tutorial and the Avanzini/Serafin/Rocchesso DAFx-02 paper, both read
in full here. High on Farnell's phenomenological creaking-door recipe (code read verbatim). Medium on
LLM-authored procedural audio: the 2025–2026 papers were read, but the field is young and has no
agreed evaluation protocol. Parameter values in the "presets" table are reasoned starting points.
They were **not** measured from recordings. The physical claims were checked with a toy simulation
(see "Sanity simulation"), not against real hinges.
Not covered: HRTF/spatialization, recorded-sample analysis, neural text-to-audio models.
Recheck frontier after 2027-06.

---

## 1. What physically makes a hinge squeak (the short answer)

1. **Two surfaces slide under a normal load.** In a hinge, the pin rubs the knuckle bore. The door's
   weight and any misalignment set the normal force F_N. Opening speed sets the sliding velocity v.
2. **Friction falls as sliding speed rises** (static > kinetic, plus the *Stribeck* dip at low speed).
   That negative slope of friction vs. velocity feeds energy into vibration. It is the energy source.
   Akay lists "instabilities due to decreasing friction with increasing velocity" as the mechanism
   where friction plays an *active* role (Akay 2002, §III.A).
3. The result is **stick-slip**: the contact sticks, elastic force builds, it breaks away and slips,
   then it re-sticks. Each slip is an impulse into the structure.
4. **Two regimes decide what you hear:**
   - **Squeak/squeal = mode lock-in.** Under "strong contact" the friction pair and the structure
     become one coupled system, and "the coupled system responds at one of its fundamental
     frequencies and its harmonics. … the selection of the mode … depends on the normal load,
     sliding velocity, and the contact geometry" (Akay 2002, §I). The stick-slip cycles once per
     period of a structural mode, so the **slip rate IS the pitch** (hundreds of Hz to a few kHz),
     with harmonics. A bowed string (Helmholtz motion) and a rubbed wineglass work the same way.
   - **Creak/groan = relaxation stick-slip.** When the vibrating part is compliant and well damped,
     the slips are discrete events at a rate set by force build-up (∝ speed, stiffness, load). That
     rate runs from a few Hz to tens of Hz and is heard as a ratchety, grainy creak. Each slip
     *rings* the door panel and frame, which supply the timbre. This is Farnell's model: "slip events
     are generated … with frequency proportional to force" (Farnell, Designing Sound, Practical 9,
     SC port).
   - Weak contact on rough surfaces gives **roughness (surface) noise**: random impulses that ring
     each component's own modes independently (Akay §I). Think dry rust grind, or sandpaper.
5. **The radiator matters.** A pin is a poor radiator. The sound you hear is the door leaf and frame
   (wood panel modes, plus frame/room-like delays in Farnell's model) driven by the hinge.
6. **Brake-noise vocabulary carries over directly.** "squeak describes a short-lived squeal, wire
   brush describes a randomly modulated squeal, and squelch describes an amplitude-modulated version
   of squeak noise" (Akay §IV.D). Akay names door hinges as a low-energy member of the same family
   (§IV.D).
7. **Beyond a critical normal load, friction stops slipping and acts as a constraint.** The system
   then rings at its clamped (constrained) frequencies. Between the two extremes, both boundary
   conditions coexist within each cycle, and that is stick-slip (Akay §IV, beam experiment, Fig. 16).
   ⇒ There is a **window** of (F_N, v) in which a hinge squeaks. Below it you get silence or smooth
   sliding. Above it, the hinge sticks or groans. Bowed-string players know this window as the
   *Schelleng diagram*.

**Why the oiled hinge goes silent:** lubrication flattens or reverses the friction–velocity slope
(no negative-slope energy source) and lowers μ_s − μ_d (less force build-up per slip). Model it as
μ_s → μ_d and a flatter Stribeck curve.

---

## 2. Vocabulary — terms of art

- **Stick-slip** — alternating adhesion and sliding of a contact. Each break-away releases stored
  elastic energy as an impulse. [Akay 2002; Farnell P9]
- **Stribeck effect / Stribeck velocity v_s** — the dip of friction force at low sliding speed. v_s
  sets where the dip happens. [DAFx-02 §1, eq. 6]
- **Static / Coulomb (kinetic) force f_s, f_c** — f_s = μ_s F_N and f_c = μ_d F_N. Violin rosin:
  μ_s ≈ 0.4–0.5, μ_d ≈ 0.2. [DAFx-02 §5.1]
- **Mode lock-in** — a self-excited oscillation locks to one natural mode (plus harmonics) of the
  coupled system. This is the squeal/squeak mechanism. [Akay §I, §III]
- **Roughness / surface noise** — light-contact noise from asperity impacts. Broadband, and
  components ring independently. [Akay §I]
- **Corrugation frequency** — impulse rate = sliding speed / surface feature spacing. Relevant to
  ratchety textures. [Akay §I]
- **Presliding displacement, break-away displacement z_ba** — the elastic micro-motion before true
  sliding. Elasto-plastic models make it purely elastic below z_ba (no drift). [DAFx-02 §2.1]
- **Bristle model / LuGre / elasto-plastic (Dupont et al. 2002)** — dynamic friction models with an
  internal state z, the mean bristle deflection. [DAFx-02 §2]
- **Exciter / resonator** — the nonlinear contact model that injects force, and the linear modal
  system that colors it. [DAFx-02 §2.2; SDT API]
- **Modal synthesis / modal resonator** — a bank of parallel 2nd-order mass–spring–dampers. Per mode:
  frequency, decay, gain at each pickup point. A 0 Hz mode with infinite decay = an inertial point
  mass. [SDT resonator API]
- **Pickup / interaction point** — the position on an object where force is applied or motion is
  read. It weights each mode's participation. [SDT API; DAFx-02 §4.1]
- **K-method / delay-free loop** — the implicit coupling between the nonlinear force and the linear
  resonators. It is solved per sample (Newton–Raphson, typically < 7 iterations). [DAFx-02 §3]
- **Helmholtz motion** — the canonical regular stick-slip of a bowed string (one stick + one slip per
  period). [DAFx-02 §5.1; McIntyre, Schumacher & Woodhouse 1983]
- **Squeak / squeal / squelch / wire-brush / groan / chatter** — perceptual labels for friction-noise
  types. Groan and chatter are low-frequency; the squeal family is high. [Akay §IV.D, Fig. 8]
- **Basic-level vs. complex events (ecological acoustics)** — sound events classed by material
  (solid / liquid / gas) and interaction (impact, scraping, …). Complex events are temporal patterns,
  compounds, or hybrids of basic ones. [Gaver 1993]

---

## 3. Canon — the load-bearing sources

- **Akay, A. "Acoustics of friction." JASA 111(4):1525–1548, 2002.** doi:10.1121/1.1456514. The
  standard tutorial review: regimes, mode lock-in, brake noise taxonomy, door hinges as an example.
  Read here via https://www.imperial.ac.uk/media/imperial-college/research-centres-and-groups/dynamics/Akay-Acoustics-of-friction.pdf
- **Avanzini, Serafin, Rocchesso. "Modeling interactions between rubbed dry surfaces using an
  elasto-plastic friction model." DAFx-02, pp. 111–116.** Gives the equations used below, the
  discretization, and states that the same model covers "squeaking doors and chalks."
  https://avanzini.di.unimi.it/downloads/publications/avanzini_dafx02.pdf
- **Avanzini, Serafin, Rocchesso. "Interactive simulation of rigid body interaction with
  friction-induced sound generation." IEEE TSAP 13(5):1073–1081, 2005.** doi:10.1109/TSA.2005.852984.
  Its abstract reports squeaky doors, braking, and rubbed wineglass as successful cases.
  *Full text not obtained (repository blocked); parameter values for the door example are unknown.*
- **Dupont, Hayward, Armstrong, Altpeter. "Single state elastoplastic friction models." IEEE TAC
  47(5):787–792, 2002.** doi:10.1109/TAC.2002.1000274. The origin of the α(v,z) adhesion map.
  Cited through DAFx-02; not read directly.
- **Farnell, A. *Designing Sound*, MIT Press 2010, Practical 9 "Creaking door".** A phenomenological
  stick-slip + wood-panel + frame model. Pd patch:
  https://mitp-content-server.mit.edu/books/content/sectbyfn/books_pres_0/8375/designing_sound.zip/practical09.html
  SuperCollider port (code read verbatim): https://en.wikibooks.org/wiki/Designing_Sound_in_SuperCollider/Creaking_door
- **Sound Design Toolkit (SDT), Baldan / Delle Monache / Rocchesso (GPLv3).** A reference
  implementation of elasto-plastic friction + modal resonators with real parameter names.
  https://sdt.lim.di.unimi.it/docs/API/v2.2-078/group__friction.html ·
  https://sdt.lim.di.unimi.it/docs/API/v2.2-078/group__resonators.html
  (The SoftwareX 2017 paper describing its taxonomy could not be fetched.)
- **Rocchesso & Fontana (eds.), *The Sounding Object*, 2003.** The book behind the SDT lineage
  (ch. 8, low-level models). Not read here.
- **Gaver, W. "What in the world do we hear?" and "How do we hear in the world?", Ecological
  Psychology 5(1) and 5(4), 1993.** A taxonomy of sound-producing events and synthesis algorithms
  for impact/scrape/drip and their compounds. The conceptual basis for a stage-graph DSL.
  Abstracts only were read.
- **Schelleng, J. "The bowed string and the player." JASA 53(1), 1973.** The force/speed playability
  window (Schelleng diagram). Cited from domain knowledge, not re-read here.

---

## 4. Pitfalls — what outsiders get wrong

1. **Treating a squeak as "noise bursts plus a sine."** The pitch of a squeak *comes from* the
   stick-slip repetition locking to a mode. It is not a separate oscillator added on top. An
   independent sine tone sounds like a synth over a rattle. ⇒ The existing `hinge_creak_generator.py`
   does exactly this (see §9).
2. **Slip rate in the 3–12 Hz range for a squeak.** That rate is a *creak/ratchet*. Squeaks need
   slip rates at audio pitch. Farnell's patch spans 1 Hz → ~333 Hz (`force.linlin(0.1,1,1,1/0.003)`).
   Lock-in squeals go higher still.
3. **Using `Dust` (Poisson) for slip events.** Farnell's port notes that Dust "lacks the slight
   'pitched' sound of the creaky door". Use a jittered *periodic* impulse train instead.
4. **Slip amplitude independent of interval.** Each slip releases the force that built up since the
   last one. Long gaps should give louder, longer events. Farnell latches √(build-up) as the amplitude
   and uses √amp as the decay scale.
5. **Static pitch.** In a real swing, F_N and v change over the motion, so the locked mode can *hop*
   (mode selection depends on load and speed, Akay §I). The squeak can also break into creak and
   back. Drive the model from a door-motion trajectory, not a fixed tone.
6. **LuGre drift.** Plain LuGre creeps under tiny forces. The elasto-plastic α(z,v) with z_ba fixes
   this. Also enforce z_ba < min z_ss = f_c/σ0 (DAFx-02 eq. 14: z_ba = c·f_c/σ0, c < 1).
7. **Naive explicit integration of the friction ODE.** The contact is stiff, and DAFx-02 needs
   K-method + Newton–Raphson. Explicit Euler only works with heavy oversampling (8× worked in the
   toy test) and moderate σ0. Expect blow-ups or wrong regimes if you skimp.
8. **Resonating the pin instead of the door.** Timbre lives in the radiator (panel + frame). Farnell
   uses wood-panel bandpasses at 62.5/125/250/395/560/790 Hz (Q 1,1,2,2,3,3) plus 8 frame delays of
   4.5–16 ms. A 1–4 kHz "metal" modal bank on its own sounds like a small metal object, not a door.
9. **Too many parameters exposed to the user or LLM.** DAFx-02 conclusion: "Due to the large number
   of control parameters, controlling the sound module is not a trivial task." Expose a few
   *physical/perceptual macros* (load, speed, lubrication, rust, door size/material) and map them to
   the low-level parameters.
10. **Trusting CLAP alone to evaluate.** CLAP is a weak, circular proxy when it also selected the
    training data (Gupta 2026). Every frontier system keeps a human listening step.
11. **Letting the LLM write raw DSP.** SonicRAG: "LLMs are prone to producing code that fails to
    execute reliably." The Faust LLM guide relies on the compiler as an oracle. Constrain output to
    a typed schema or DSL and validate it before rendering.

---

## 5. The model, precisely

### 5.1 Elasto-plastic friction (DAFx-02 eqs. 2, 4–8; Dupont et al. 2002)

State: z = mean bristle deflection. v = relative sliding velocity.

```
dz/dt = v · [ 1 − α(z,v) · z / z_ss(v) ]
f_fr  = σ0·z + σ1·dz/dt + σ2·v (+ σ3·w, a noise term for surface roughness in SDT)

z_ss(v) = sgn(v)/σ0 · [ f_c + (f_s − f_c)·exp(−(v/v_s)²) ]      (Stribeck curve)
f_s = μ_s·F_N,  f_c = μ_d·F_N
z_ba = c·f_c/σ0, c < 1                                           (break-away grows with load)

α(z,v) = 0                                  if |z| < z_ba             (purely elastic)
       = ½[1 + sin(π·(z − ½(z_ss+z_ba)) / (z_ss − z_ba))]  if z_ba < |z| < z_ss
       = 1                                  if |z| > z_ss
       (for sgn(v) = sgn(z); α = 0 when the signs differ)
```

σ0 = bristle stiffness (sets presliding compliance), σ1 = bristle damping, σ2 = viscous friction.
The exponent in the Stribeck term was garbled in the PDF text extraction. The squared form is the
standard LuGre parametrization (Canudas de Wit et al. 1995, the paper DAFx-02 cites).

### 5.2 Coupling to modal objects (DAFx-02 §2.2, §3; SDT)

Two modal objects: the "bow" (the sliding exciter, e.g., the pin/leaf) and the "resonator" (the
knuckle, door panel, or frame). Each is a set of 2nd-order oscillators `m x'' + r x' + k x = f`, with
v = Σ x'_b − Σ x'_r. The paper discretizes with the bilinear transform and solves the delay-free
loop with the K-method + Newton–Raphson. SDT discretizes the resonator with the impulse-invariant
method instead. SDT's exposed parameters are a good LLM-facing vocabulary: `normalForce (N)`,
`stiffness`, `dissipation`, `viscosity`, `noisiness`, `staticCoefficient`, `dynamicCoefficient`,
`breakAway`, `stribeckVelocity (m/s)`, and per-mode `frequency`, `decay`, `weight`, pickup `gain`.

### 5.3 Phenomenological alternative (Farnell P9) — cheap, vectorizable, good for creaks

```
force(t) ∈ [0,1]  →  lag 0.1 s
inMotion = force > 0.1                      (static friction threshold)
slipRate = lin(force: 0.1→1  ⇒  1 Hz→333 Hz) × jitter (LFDNoise 50 Hz, ×~0.5–2)
buildup  = ramp reset at each slip, +10/s, clipped to 1
amp      = sqrt(buildup at slip);   decay = 0.01 s × sqrt(amp)
event    = perc(1 ms attack, decay) × amp
→ wood panel: Σ BPF(62.5,125,250,395,560,790 Hz; Q 1,1,2,2,3,3) + 0.2·dry
→ frame: mean of 8 delays (4.52,5.06,6.27,8,5.48,7.14,10.12,16 ms), HPF 125 Hz
```

**Use 5.3 for creaks** (wooden door, ship timbers, floorboards). Use 5.1–5.2, or a mode-locked
version of 5.3 (see §6), **for squeaks** (metal hinge, chalk, sneaker, wineglass).

---

## 6. Parameterizing hinge variations

### 6.1 Control layer (what an LLM or user sets) → physical layer

| Macro (0–1 unless noted) | Physical meaning | Maps to |
|---|---|---|
| `door_motion` (curve: angle vs. t) | how the door is swung | v(t) = r_pin·dθ/dt |
| `load` | door weight, sag, misalignment | F_N(t), plus a cyclic term per revolution if bent |
| `lubrication` | oil vs. dry | μ_s − μ_d → 0, flatter Stribeck, smaller σ3 |
| `rust` / `grit` | roughness, debris | σ3 noise ↑, corrugation-rate impulses, more roughness noise |
| `hinge_size` / `material` | pin and knuckle stiffness | squeal mode frequencies (k/m), decay |
| `door_size` / `material` | panel radiator | panel mode set (scale Farnell's ratios), decay, frame delays |
| `space` | room | short reverb / frame-delay feedback |

### 6.2 Starting presets (reasoned, **not measured**: tune by ear, then fit to recordings)

| Variant | Regime | Slip/pitch | Notes |
|---|---|---|---|
| Oiled, smooth | below window | — | faint roughness noise only |
| Classic squeaky hinge | lock-in | 600–2000 Hz, with harmonics; pitch hops between 2–3 modes as v changes | moderate load |
| Horror slow creak | relaxation | 5–60 Hz slips that rise with speed | wood panel resonances dominate |
| Rusty groan | mixed | creak events + broadband grit | high σ3, low-frequency panel |
| Fast swing | lock-in, short | squeal chirps (squelch-like AM) | v sweeps through the window quickly |
| Heavy gate | relaxation → lock-in | low rate, accelerating into a squeal | large F_N, large panel |

The **window** is the key behavior to reproduce: sweep v(t) through it and the sound should go
silence → creak → squeak → (smooth) as speed changes.

---

## 7. Generalizing: a stage pipeline an LLM can author

### 7.1 Stage taxonomy (after Gaver 1993 and the SDT exciter/interactor/resonator split)

```
CONTROL      → EXCITATION/INTERACTION → RESONATOR(S)       → RADIATION/MODIFIERS → SPACE → MIX
(trajectories)  (friction, impact,       (modal bank, panel,   (EQ, saturation,      (early refl.,
 v(t), F_N(t),   rolling, scrape,         string/waveguide,     AM/FM, Doppler, pan)  reverb)
 density(t))     bubble, turbulence)      tube, noise band)
```

Many familiar sounds are **the same friction exciter with different resonators and controls**:

| Sound | Exciter regime | Resonator | Key control |
|---|---|---|---|
| Squeaky hinge | lock-in | small metal modes → door panel | swing speed, load |
| Creaking door / ship / floorboard | relaxation stick-slip | wood panel + frame | force/speed |
| Chalk on blackboard | lock-in (chatter) | chalk stick + board | pressure, angle |
| Sneaker on court | lock-in, short | sole + floor | slide speed (squelch envelope) |
| Wineglass rim | lock-in | glass bending modes (Akay §III.B.1) | finger speed, wetness |
| Brake squeal / groan | lock-in / low-freq. | disk/drum modes (Akay §IV.D) | pressure, speed |
| Bowed string / saw | Helmholtz | string waveguide | bow force, speed, position |
| Nail pull, cork twist, rope on post | stick-slip (Akay lists nail pull) | object modes | pull force |
| Dry rubbing / sanding | roughness noise | each surface's modes | speed, grit |

The same stage graph also covers *non-friction* exciters (impact, rolling, scraping, bubbles,
turbulence) already in this repo (thud, explosion, gravel, wind). They share resonator, modifier,
and space stages.

### 7.2 What the LLM should emit

Do not have the LLM write Python DSP. Have it emit a **typed JSON stage graph** with closed
vocabularies and bounded numeric ranges. This follows SonicRAG's Mixer-Script DSL, the enumerated
schema in Gupta 2026, and the named-recipe library in `procedural-sfx`:

```json
{
  "name": "haunted_door_slow_open",
  "duration_s": 4.0,
  "seed": 17,
  "controls": {
    "angle_deg": {"type": "curve", "points": [[0, 0], [3.5, 70]], "shape": "ease_in_out"},
    "load":      {"type": "const", "value": 0.6}
  },
  "stages": [
    {"id": "fric", "op": "friction.stick_slip",
     "params": {"speed": "d(angle_deg)/dt * 0.004", "load": "load",
                "mu_s": 0.55, "mu_d": 0.30, "stribeck_v": 0.02, "roughness": 0.3}},
    {"id": "hinge", "op": "resonator.modal",
     "in": "fric", "params": {"preset": "small_steel_hinge", "freq_scale": 1.0}},
    {"id": "panel", "op": "resonator.modal",
     "in": "hinge", "params": {"preset": "wood_door_panel", "size": 1.0}},
    {"id": "frame", "op": "modifier.delay_bank", "in": "panel", "params": {"preset": "door_frame"}},
    {"id": "room",  "op": "space.small_room", "in": "frame", "params": {"wet": 0.15}}
  ]
}
```

Pipeline:
`text → LLM → JSON → schema validation (ranges, graph acyclic, known ops) → render (numpy) →
automatic audio checks → best-of-N with descriptor/CLAP ranking → human A/B → saved preset`

- **Validation oracle first** (Faust LLM guide pattern): reject unknown ops, out-of-range values,
  and cycles. Then check the audio for NaN, silence, clipping, runaway energy, DC offset.
- **Descriptor targets** per sound class (procedural-sfx `analyze.py` pattern): f0/periodicity,
  spectral centroid, onset rate, RMS envelope, band energies.
- **Offline cache:** run the LLM offline to build a library of text → preset pairs; runtime needs no
  LLM (Gupta 2026 retrieval backend). This fits the repo's "no AI at runtime" rule.
- **Human in the loop:** extend `sfx_trainer.py` so the user picks among N renders of LLM-proposed
  graphs; record choices as preference data.

---

## 8. Experiments and demos to prove the approach

Each experiment has a pass criterion so it can be judged objectively.

1. **Regime map (Schelleng-style) for one hinge.** Sweep F_N × v on the elasto-plastic model,
   classify each cell as silent / creak / squeak / stuck (periodicity, f0 vs. mode f, RMS). Render a
   heat-map PNG and a WAV per region.
   *Pass:* a bounded squeak window appears, and squeak f0 sits at a mode (±3%) inside it.
2. **Pitch-locks-to-mode test.** Change only the resonator's mode frequency (400/800/1600 Hz).
   *Pass:* squeak f0 follows the mode; slip-rate-driven creak rate does not.
3. **Creak rate tracks speed.** In the relaxation regime, ramp v. *Pass:* slip events/s increase
   monotonically with v (Farnell's linear map is the phenomenological reference).
4. **Swing trajectory demo.** Drive v(t), F_N(t) from a door angle curve (open slow → fast → stop).
   *Pass, by ear:* audible creak → squeak transitions and pitch hops; listeners prefer it over
   fixed-pitch versions.
5. **Lubrication ablation.** Same swing, lubrication 0 → 1. *Pass:* squeal energy falls
   monotonically and disappears at μ_s ≈ μ_d.
6. **Old vs. new hinge blind A/B.** Current `hinge_creak_generator.py` vs. the new model, 5+ listeners,
   forced choice "which sounds more like a squeaky door hinge?" *Pass:* the new model is preferred
   at ≥ 70%.
7. **Recording match.** Take 3–5 CC0 recordings of squeaky doors (e.g., from Freesound, filtered by
   CC0 license). Measure f0 track, harmonicity, slip rate, centroid. Fit the macros by grid or random
   search. *Pass:* descriptor error within tolerances, and listeners can't reliably pick out the
   synthetic one in an ABX test.
8. **Transfer demo: one exciter, many sounds.** Using only resonator and control changes (no code
   changes), produce chalk, sneaker squeak, wineglass, brake squeal, and creaky floorboard.
   *Pass:* blind labeling accuracy by listeners well above chance (5-way > 50%).
9. **LLM → graph → audio.** Give an LLM 20 text prompts ("rusty gate in wind", "tiny squeak of a
   cabinet"). *Pass:* ≥ 95% schema-valid JSON after one repair pass. Prompt-matching preferred over a
   random-valid-graph baseline (the baseline Gupta 2026 found surprisingly hard to beat on CLAP:
   0.139 random vs. 0.137–0.163). Use human ratings, with CLAP only as a secondary metric.
10. **Demo page.** Add to `demos/`: a regime-map image with clickable cells, a swing slider demo
    (pre-rendered grid), and a "same exciter, many sounds" gallery.

---

## 9. Applying this to the current repo

**Verdict: extend, not restart.** The repo already has the right top-level structure (exciter →
modal bank → mix, trainer integration). What's wrong is the *exciter model*.

`hinge_creak_generator.py` as of commit 69a0e09:

| Part | Keep / change | Why |
|---|---|---|
| `_generate_stick_slip_envelope` (3–12 Hz bursts, random amplitude) | **Replace** | Slip rate is creak-range at best; amplitude is random instead of ∝ √(build-up); no link to force/speed (Pitfalls 2, 4) |
| `_generate_tonal_component` (sine at mode1/2 + harmonics) | **Remove** | Pitch must emerge from slip rate locking to a mode, not a separate oscillator (Pitfall 1) |
| `_apply_modal_bank` | **Fix** | The random-walk frequency modulation is averaged away (`avg_freq`), so micro-variation is a no-op; it should modulate per block |
| `_biquad_bandpass_coeffs` / `_apply_biquad` | Keep | Correct RBJ bandpass; reuse for the Farnell panel bank |
| Fixed 0.3 s / 0.5 s overall envelope | **Replace** | Envelope should come from the door-motion trajectory |
| Per-sample `struct.pack` stereo WAV write | Optimize | Use `np.column_stack(...).astype('<i2').tobytes()` |
| Params `mode1..3_hz` (950/2200/3800), `mode_Q` | Keep as the *hinge* resonator | Add a *panel* resonator and frame delays after it |

Suggested new modules (numpy-only, per AGENTS.md):

- `friction.py` — `stick_slip_events(force, speed, ...)` (Farnell, vectorized) and
  `elastoplastic(v, F_N, resonator, ...)` (per-sample, oversampled; numba optional).
- `resonators.py` — modal bank (block-varying frequencies), wood panel preset, frame delay bank.
- `controls.py` — door-angle curve → v(t), F_N(t).
- `graph.py` — the JSON stage-graph schema, validator, and renderer (§7.2).
- An updated `docs/research-findings.md` "Door Sounds → Creak" section. It currently says 200–800 Hz
  with "random sticking points every 0.5–1.0 s", which describes neither regime correctly.

### 9.1 Implemented: `hinge-lab/` (Rust, 2026-10-29)

The model in §5.1–5.3 is implemented in Rust (`hinge-lab/src/synth.rs`): an egui slider UI,
a CLI (`render --preset/--params/--set/--seed`), seeded determinism (SplitMix64; same JSON →
bit-identical WAV, verified by hash), and sidecar JSON per render. A 3 s sound renders in
about 0.1 s. Demo renders are in `demos/hinge/` (`*.wav` + reproducible `*.json`).

Tuning finding: pure elasto-plastic lock-in holds the pitch at the hinge mode almost
regardless of speed, load, or contact stiffness (tested 2e4–2e5). Real squeaks glide, so a
**phenomenological** `pitch_bend` makes the hinge mode stiffen with the instantaneous load
(f ∝ load^pitch_bend; Akay notes that normal force changes the system's dynamic response).
With the defaults, the squeak glides from ~710 to 900 Hz over a swing. Validate this against
recordings (Experiment 7).

---

## 10. Sanity simulation (run during this research)

Script: elasto-plastic friction (§5.1, μ_s 0.6, μ_d 0.3, v_s 0.02 m/s, σ0 2e4, z_ba = 0.7 f_c/σ0)
driving one mass-spring mode, explicit integration at 8× oversampling (352.8 kHz). A toy model; one
run per cell.

**A. Stiff, lightly damped 600 Hz mode (ζ = 0.002), RMS of resonator velocity:**

| F_N (N) | v = 0.005 | v = 0.03 | v = 0.15 m/s |
|---|---|---|---|
| 0.05 | 1.1e-3 | 7.2e-4 | 6.7e-5 |
| 0.3 | 3.7e-4 | **2.6e-2** | 3.1e-4 |
| 1.0 | 1.7e-4 | **2.7e-2** | 9.6e-4 |
| 3.0 | 2.5e-5 | **2.6e-2** | 2.6e-3 |

f0 was 596–604 Hz in every cell (periodicity ≥ 0.98): the pitch is the mode's. Near the Stribeck
velocity the oscillation is self-sustained and ~10–1000× louder than elsewhere. ⇒ This supports
"squeak = lock-in to a mode, inside a speed/force window."

**B. Compliant, heavily damped 40 Hz mode (ζ = 0.3), slip events/s:**

| F_N (N) | v = 0.002 | 0.005 | 0.01 | 0.02 m/s |
|---|---|---|---|---|
| 0.5 | 0 | 1.3 | 2.7 | 4.0 |
| 2.0 | 0 | 1.3 | 29.3 | 34.7 |

At low load the slip rate rises with speed and sits far below the mode frequency (creak regime). At
higher load it jumps toward the mode (~30–35/s vs. 40 Hz), which is onset of lock-in. ⇒ This
supports "creak rate tracks speed; regime depends on load." Counts are coarse (1 s runs, threshold
detector).

---

## 11. Open gaps — what search couldn't establish

- **Measured door-hinge squeak spectra** (typical f0 ranges, harmonic counts, mode hopping). No
  primary measurement paper was found. *Close by* analyzing CC0 recordings (Experiment 7).
- **Avanzini et al. 2005 door parameters.** The full text was blocked. *Close by* getting the PDF
  through IEEE Xplore or the authors.
- **The SDT taxonomy paper (SoftwareX 2017).** Fetch was blocked (403). The SDT source code on
  GitHub (`SkAT-VG/SDT`) likely has door/friction presets and could be inspected.
- **Dupont et al. 2002 original.** α(z,v) was taken from its DAFx-02 restatement.
- **Perceptual thresholds** (how much jitter or pitch-hop makes it "real"). *Close by* listening tests.
- **LLM authoring reliability for stage graphs specifically.** There is no published benchmark.
  Experiment 9 would be a first data point.

---

## 12. Frontier — LLM-driven procedural audio (2024–2026)

- **CTAG** (Cherep, Singh, Shand, ICML 2024; arXiv 2406.00294): optimizes 78 parameters of a modular
  synth (SynthAX) against LAION-CLAP text similarity with gradient-free LES. Results are deliberately
  "sketch-like". LLM-generated prompt captions did not reliably help.
- **SonicRAG** (Guo & Tai, arXiv 2505.03244, May 2025): an LLM writes a small method-chaining DSL
  ("Mixer Script": Volume, Compressor, Reverb, Peak/LP/HP filters, StartAt/StopAt) over *retrieved
  recordings*. It avoids raw code because generated scripts "fail to execute reliably." Evaluated
  with FAD / CLAP / SNR.
- **Text-steerable procedural soundscapes** (Gupta, NIME 2026; arXiv 2607.00309): the LLM emits a
  34-field enumerated JSON config for a CPU procedural synth. Best-of-5 CLAP selection builds a
  retrieval map. Embedding lookup (0.163 CLAP) beat direct LLM calls, and a random-valid baseline
  scored 0.139. No formal human study.
- **Faust LLM guide** (faustdoc.grame.fr/manual/llm/): "prompt → generated Faust → compile → inspect
  JSON/SVG → listen/measure → targeted correction → repeat". The compiler is the symbolic oracle;
  audio metrics are the perceptual one.
- **bianbianzhu/procedural-sfx** (MIT, GitHub): an agent skill with a numpy/scipy recipe library,
  event JSON, deterministic seeding, and `analyze.py` descriptors. Human audition table for anything
  not ear-tuned.

Takeaway for this repo: closed op vocabulary + typed parameters + automatic checks + best-of-N +
human choice in `sfx_trainer.py`. No LLM at runtime.

---

## 13. Expert-enough gate

- **Vocabulary:** §§1, 5, 7 use Stribeck, mode lock-in, presliding/break-away, K-method, pickup,
  roughness noise, and squeal/squelch taxonomy in their source senses (Akay; DAFx-02; SDT).
- **Canon:** every physics claim traces to Akay 2002 or DAFx-02, both read in full. The synthesis
  recipe traces to Farnell P9 code. Frontier claims trace to arXiv full texts. Unread items (TSAP
  2005, Dupont 2002, Schelleng 1973, Sounding Object) are labeled as such.
- **Pitfalls:** §4 lists 11, each with its source, including the specific defects in the current
  generator.
- **Transfer:** §5 gives the equations and Farnell's constants, §6 the parameter mapping, §7.2 the
  schema, §8 experiments with pass criteria, and §9 a file-level plan. Another instance can implement
  from this document without redoing the search.
