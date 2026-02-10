# Text-to-SFX Generation (Procedural Audio)

## Overview

This project demonstrates how to use an AI agent (opencode with GLM-4.7) to generate code that procedurally creates sound effects. This is an MIT-licensed approach that avoids using CC-BY-NC restrictive licensed "open" model weights, albeit with lower quality outputs. This serves as a Proof of Concept for an alternative way to generate sound effects.

## Why This Approach?

### The Problem
Many "open" audio models use CC-BY-NC (Creative Commons Attribution-NonCommercial) licenses, which restrict commercial use. This limits their practical application in real-world products and services.

### Our Solution
Instead of using AI models to generate audio directly, we use AI to:
1. Research and understand sound acoustics
2. Analyze how foley artists create specific sounds
3. Generate Python code that procedurally synthesizes those sounds
4. The generated code uses pure mathematical algorithms - no AI/ML required at runtime

### Trade-offs
**Advantages:**
- ✅ MIT License - fully open source, commercial-friendly
- ✅ No model downloads - lightweight and fast
- ✅ Fully customizable - parameters can be tweaked
- ✅ Reproducible - same inputs = same outputs
- ✅ No GPU required - runs on any CPU
- ✅ No runtime dependencies - just numpy

**Limitations:**
- ⚠️ Lower audio quality compared to AI-generated audio
- ⚠️ More effort required per sound effect
- ⚠️ Limited to sounds that can be procedurally modeled

## Project Goal

To prove that AI-assisted procedural audio generation is a viable alternative to ML-based audio generation for creating simple sound effects, especially when open licensing is important.

## Getting Started

### Prerequisites
- Python 3.x
- Virtual environment (using `uv` recommended)

### Installation
```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install numpy sounddevice
```

### Generate Sound Effects

#### Thud (Heavy Impact)
```bash
python3 thud_generator.py
afplay thud.wav  # macOS
# or
python3 play_3d_audio.py thud.wav
```

#### Gravel Footsteps (3D Spatial Audio)
```bash
python3 gravel_footsteps_generator.py
afplay gravel_footsteps.wav  # macOS
# or
python3 play_3d_audio.py gravel_footsteps.wav
```

**Note:** For best 3D spatial effect, use headphones.

## Documentation

- **[3D Audio Documentation](3D_AUDIO_README.md)** - Detailed explanation of 3D audio implementation and techniques

## Session Transcript

- **[Session Transcript](session-ses_3ba5.md)** - Full conversation log showing how this project was developed interactively with opencode

## How It Works

### Procedural Audio Generation Process

1. **Research Phase** (AI-assisted)
   - Analyze natural acoustics of target sound
   - Study foley artist techniques
   - Identify key frequency components
   - Determine envelope characteristics

2. **Implementation Phase** (AI-generated code)
   - Generate waveforms (sine, square, noise)
   - Apply filters (low-pass, high-pass, band-pass)
   - Create envelopes (attack, decay, sustain)
   - Mix multiple audio sources
   - Apply effects (reverb, delay, distortion)

3. **3D Spatialization** (optional)
   - Pan left/right
   - Simulate distance attenuation
   - Apply HRTF (Head-Related Transfer Functions)

### Example: Thud Sound
- 80 Hz sine wave oscillator
- Low-pass filtered noise for body
- 5ms attack, exponential decay
- All synthesized mathematically

### Example: Gravel Footsteps
- Multiple frequency bands (small/large stones)
- Irregular step timing
- Sharp transients for stone impacts
- 3D positioning (left→right, close→far)
- Distance attenuation

## Current Sound Effects

| Sound | Description | Features |
|-------|-------------|----------|
| **Thud** | Heavy impact sound | Low-frequency oscillator, filtered noise, fast attack |
| **Button Click** | UI interaction sound | High-frequency (2-4 kHz), sharp attack, immediate decay |
| **Wind Whistling** | Atmospheric wind | Regular pitch variations (600-900 Hz), smooth flow |
| **Explosion** | Blast effect | Low rumble (20-50 Hz), broadband noise, long decay |
| **Gravel Footsteps** | Walking on gravel | 6-second sequence, irregular timing, 3D spatialization, multi-band filtering |
| **Siren (Basic)** | Simple two-tone | 500/800 Hz alternating, 2.5 Hz cycle |
| **Siren (US Wail)** | US-style siren with Doppler | 500-1200 Hz sweep, 3D positioning, radial velocity |
| **Siren (EU Hi-Lo)** | European siren | 450/900 Hz alternating, Doppler effect |
| **Siren (US Yelp)** | Fast alternating | 700 Hz, 8-10 Hz cycle, urgent feel |
| **Flying Saucer** | Sci-fi UFO | 200-800 Hz rise-fall sweep, metallic texture, Doppler |

### Notes
- WAV files are generated in the project root directory by running generator scripts
- The `demos/` directory contains symlinks to these WAV files for serving
- Use headphones for best 3D spatialization effect
- All sounds use pure mathematical synthesis (no AI models or recorded samples)

## Technical Details

### Audio Parameters
- Sample Rate: 44.1 kHz
- Bit Depth: 16-bit PCM
- Channels: Mono (thud), Stereo (footsteps with 3D)
- Output Format: WAV

### Dependencies
- `numpy` - Array operations and signal processing
- `sounddevice` - Audio playback (optional, for playback)
- `wave`, `struct` - WAV file encoding (Python stdlib)

## Extending the Project

To generate new sound effects:

1. Research the sound's acoustic properties
2. Identify key components (waveforms, filters, envelopes)
3. Use the existing generators as templates
4. Experiment with parameters to refine the sound
5. Consider adding 3D spatialization for immersion

## License

MIT License - See LICENSE file for details

This means you are free to:
- Use in commercial projects
- Modify and redistribute
- Sublicense
- No attribution required (but appreciated!)

## Acknowledgments

- **opencode** - AI agent used for code generation
- **GLM-4.7** - AI model powering opencode
- **Foley Artists** - Whose techniques inform our procedural approaches

## Future Improvements

- [ ] Add more sound effects (door creak, button click, explosion, etc.)
- [ ] Implement reverb/delay effects
- [ ] Add Web Audio API port for browser use
- [ ] Create GUI for parameter tweaking
- [ ] Add batch generation for multiple variations
- [ ] Implement HRTF for better 3D positioning

## Contributing

Contributions welcome! Feel free to:
- Add new sound effect generators
- Improve existing ones
- Fix bugs
- Add documentation
- Suggest improvements

## Contact

This is a proof-of-concept project. For questions or suggestions, please refer to the session transcript or open an issue.
