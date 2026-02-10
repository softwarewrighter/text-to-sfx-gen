# AGENTS.md

This file documents agents, tools, and dependencies for this project.

## Project Overview

**Text-to-SFX Generation (Procedural Audio)**

AI-assisted code generation for sound effects using only mathematical algorithms.
MIT-licensed alternative to CC-BY-NC restricted AI models.

## AI Agent

### OpenCode
- **URL**: https://opencode.ai
- **Description**: AI-powered coding agent for software development
- **Model**: GLM-4.7
- **Usage**: Generates Python scripts that create WAV files using procedural audio synthesis

### Z.ai
- **URL**: https://z.ai/subscribe
- **Description**: AI coding plan for agent workflows
- **Purpose**: Structured approach to AI-assisted development
- **Usage**: Provides coding plans and workflow management

## Core Dependencies

### Python Dependencies
```bash
# Required for all audio generators
numpy >= 2.0.0
```

**Usage in generators:**
- Wave generation (`sin()`, `cos()`, phase-locked oscillators)
- Signal processing (`convolve()`, filtering)
- Envelope generation
- Random noise generation
- Array operations

### Runtime Dependencies
```bash
# Optional - for audio playback only
sounddevice  # For playing generated sounds
```

## Sound Effect Generators

All generators use `numpy` for procedural audio synthesis:

### Primary Generators
1. **thud_generator.py** - Heavy impact sound
   - Low-frequency oscillator (60-80 Hz)
   - Filtered noise for body
   - Fast attack, exponential decay

2. **button_click_generator.py** - UI interaction sound
   - High-frequency sine wave (2000-4000 Hz)
   - Sharp attack, immediate decay
   - Short duration (50ms)

3. **explosion_generator.py** - Blast effect
   - Low-frequency rumble (20-50 Hz)
   - Broadband noise for shockwave
   - Long decay with reverberation

4. **flying_saucer_generator.py** - Sci-fi UFO sound
   - Smooth rise-and-fall sweep (200-800 Hz)
   - Cyclical modulation
   - Metallic/electronic texture
   - Optional Doppler effect

5. **gravel_footsteps_generator.py** - Walking on gravel
   - 6-second sequence
   - Multiple stone impacts per step
   - 3D spatialization (pan left→right, distance attenuation)
   - Multi-band filtering (small/large stones)
   - Irregular step timing

6. **siren_generator.py** - Basic two-tone siren
   - Alternating frequencies (500/800 Hz)
   - Regular sinusoidal modulation (2.5 Hz cycle)
   - Pure oscillator synthesis

7. **siren_3d_generator.py** - Advanced siren with 3D positioning
   - US wail (800-1200 Hz) with Doppler
   - European hi-lo (450/900 Hz) with Doppler
   - US yelp (700 Hz) with Doppler
   - Radial velocity simulation

8. **siren_realistic_generator.py** - Improved US wail
   - Higher frequencies (500-900 Hz range)
   - Odd harmonic content for grit
   - Tremolo for realism
   - Smother sweep with slight randomness

9. **wind_whistling_generator.py** - Atmospheric wind
   - Regular, smooth pitch variations (600-900 Hz)
   - Sustained tone with gentle modulation
   - Smooth, flowing quality

### Training Tool
10. **sfx_trainer.py** - Interactive SFX trainer
    - Batch generation of 4 attempts upfront
    - Auto-playback of all versions
    - User selects best (0-3) or regenerate (r)
    - Optional parameter tweaks before regeneration
    - Saves final as `{sound_name}_final.wav`
    - Human-in-the-loop training workflow

### Utility Scripts
11. **play_3d_audio.py** - Audio playback helper
    - Supports mono and stereo WAV files
    - Uses sounddevice library
    - Command-line interface

## Technical Approach

### Synthesis Techniques Used
- **Additive synthesis**: Summing multiple waveforms
- **Subtractive synthesis**: Filtering noise through frequency-dependent filters
- **Frequency modulation (FM)**: Varying oscillator frequency
- **Phase-locked oscillators**: Smooth frequency transitions
- **Envelope shaping**: ADSR (Attack, Decay, Sustain, Release)

### Sound Design Elements
- **Envelopes**: Vary amplitude over time (attack, decay, sustain)
- **Filtering**: Low-pass, high-pass, band-pass
- **Harmonics**: Add multiples of fundamental frequency
- **Doppler effect**: Pitch shift based on radial velocity
- **Spatial audio**: Panning (left→right), distance attenuation
- **Modulation**: Frequency (vibrato) and amplitude (tremolo)

### Audio Parameters
- Sample Rate: 44.1 kHz
- Bit Depth: 16-bit PCM
- Channels: Mono (single source) or Stereo (spatialized)
- Output Format: WAV

## Project Structure

```
text-to-sfx-gen/
├── .venv/                    # Virtual environment
├── attempts/                   # Training attempts (created by sfx_trainer.py)
├── demos/                      # Demo page with audio players
│   └── *.wav               # Symlinks to parent directory WAV files
├── docs/                        # Documentation
│   ├── research-findings.md   # Comprehensive audio synthesis research
│   └── 3D_AUDIO_README.md   # 3D spatial audio docs
├── images/                      # Screenshots and visuals
│   └── screenshot.png          # Demo page screenshot
├── *.py                        # Audio generator scripts
├── session-ses_3ba5.md          # Development transcript
└── README.md                    # Project documentation
```

## Key Concepts

### Procedural vs Sample-Based Audio
- **Procedural**: Generated mathematically at runtime
  - Pros: Small file size, infinitely variable, customizable
  - Cons: Requires more effort, can sound artificial
- **Sample-based**: Pre-recorded audio files
  - Pros: High quality, realistic
  - Cons: Large files, limited variability

### Training Workflow
1. **Batch generation**: Create multiple variations upfront
2. **Comparison**: Play all versions for user to compare
3. **Selection**: User picks best version
4. **Iteration**: Refine based on feedback or regenerate with tweaks
5. **Finalization**: Save as `{sound_name}_final.wav`

### Why This Approach?
- **MIT License**: Fully open source, commercial-friendly
- **No AI at Runtime**: Pure mathematical synthesis
- **AI-Assisted Development**: Use opencode with GLM-4.7 to write code
- **Infinite Variability**: Parameters can be tweaked endlessly
- **Reproducible**: Same inputs = same outputs

## Files to Track

### Core Project Files
- All `*_generator.py` files
- `sfx_trainer.py` - Interactive training tool
- `play_3d_audio.py` - Playback utility
- `README.md` - Main documentation
- `.gitignore` - Ignores binary WAV files and dev artifacts

### Documentation
- `docs/research-findings.md` - Audio synthesis research
- `docs/3D_AUDIO_README.md` - Spatial audio techniques
- `session-ses_3ba5.md` - Development history

### Build/Dev Files
- `.playwright-cli/` - Playwright workspace (gitignored)

### Generated Files (not tracked)
- `attempts/*.wav` - Training attempts (not committed)
- `{sound_name}_final.wav` - Final versions in project root

## Development Status

### Working Sounds
- ✅ Thud
- ✅ Button Click
- ✅ Explosion
- ✅ Flying Saucer
- ✅ Gravel Footsteps (with 3D spatialization)
- ✅ Siren (Basic, 3D with Doppler, Realistic)
- ✅ Wind Whistling

### Needs Refinement
- ⚠️ Door creak - Generator exists but needs rework
- ⚠️ Sirens - Require further tuning for realism
  - US wail currently too low-pitched
  - Need more harmonic content
  - Better tremolo characteristics

### Future Enhancements
- [ ] More sound effects (rain, thunder, fire, water, birdsong)
- [ ] More procedural techniques (granular, wavetable synthesis)
- [ ] Better filtering (IIR/FIR filters)
- [ ] Reverb simulation
- [ ] HRTF for better 3D audio
- [ ] Real-time parameter tweaking GUI
- [ ] Batch generation for game audio asset pipelines

## Getting Started

### Install Dependencies
```bash
# Install opencode (AI coding agent)
# See: https://opencode.ai/docs for installation options
curl -fsSL https://opencode.ai/install | bash

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv pip install numpy sounddevice
```

### Generate Sound Effects

#### Using Individual Generators
```bash
python3 thud_generator.py
python3 siren_3d_generator.py
```

#### Using Interactive Trainer
```bash
python3 sfx_trainer.py
# Follow prompts to select sound effect and train
```

### Testing Sound Effects

#### Using Playback Utility
```bash
python3 play_3d_audio.py thud.wav
```

#### Using Demo Page
```bash
# Start local server
python3 -m http.server 8080

# Open in browser
open http://localhost:8080/demos/
```

## Notes

### AI-Assisted Development
- opencode generates Python scripts
- GLM-4.7 provides coding intelligence
- Scripts use pure mathematical synthesis
- No AI/ML required at runtime
- Only development phase uses AI

### Procedural Audio Quality
- Can sound artificial if not carefully tuned
- Requires understanding of acoustics
- Iterative refinement through user feedback
- Trade-off: Quality vs. File size vs. Customizability

### Licensing
- All generated sounds are MIT-licensed
- Can be used in commercial projects
- No attribution required (but appreciated)
- Fully open source

### Future Directions
This is a proof-of-concept project. Future work could include:
- More sophisticated synthesis algorithms
- Better parameter presets
- GUI for real-time parameter tweaking
- Integration with game engines
- Real-time audio generation for dynamic sound effects
- Multi-threaded batch generation
- Integration with AI voice assistants for natural language parameter control
