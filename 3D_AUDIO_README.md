# 3D Audio for SFX Generation

## Overview

This project demonstrates procedural generation of sound effects (SFX) using only mathematical algorithms - no external models, weights, or AI libraries.

## Audio Libraries for 3D Sound

### Libraries Available
1. **sounddevice** - Simple cross-platform audio I/O (recommended for basic use)
2. **pyopenal** - OpenAL 3D audio API (more advanced, game-focused)
3. **pyaudio** - PortAudio bindings (lower level)
4. **pygame** - Game library with basic spatial audio

### Implementation Used
We use **procedural 3D encoding** directly in the stereo WAV file:
- **Left-to-right panning**: Steps move from left speaker to right speaker over time
- **Distance attenuation**: Volume decreases as steps move further away
- **Constant power panning**: Smooth transitions using cos/sin angles

## How the 3D Effect Works

### Panning (Left ↔ Right)
```python
pan_position = step_time / duration  # 0.0 (left) → 1.0 (right)
pan_angle = pan_position * (np.pi / 2)
left_gain = np.cos(pan_angle)
right_gain = np.sin(pan_angle)
```

### Distance Attenuation (Close ↔ Far)
```python
distance_attenuation = 1.0 - (step_time / duration) * 0.8
# Starts at 1.0 (close), ends at 0.2 (far)
```

### Noise Reduction
1. **Removed ambient noise** - Eliminates hiss between steps
2. **Low-pass filter** - Cuts frequencies above ~1500 Hz
3. **Reduced high-frequency content** - Less high-frequency mix in gravel

## Usage

### Generate SFX with 3D positioning:
```bash
python3 gravel_footsteps_generator.py
```

### Play with 3D effect (use headphones for best effect):
```bash
python3 play_3d_audio.py
```

### Or play directly:
```bash
afplay gravel_footsteps.wav
```

## Current Features

1. **Thud generator** - Heavy impact sound with low frequency oscillator
2. **Gravel footsteps** - 6-second walk with:
   - Irregular step timing
   - 3D positioning (left→right, close→far)
   - Distance attenuation
   - Multi-frequency stone simulation
   - Low-pass filtering to reduce hiss

## Procedural Generation Approach

### Research Phase
Before generating code, we analyze:
- Natural acoustics of the sound
- How foley artists create it
- Key frequency components
- Envelope characteristics (attack, decay, sustain)

### Implementation
- No AI/ML models
- Pure mathematical synthesis
- Waveforms, filters, noise generators
- Amplitude/delay/pitch envelopes

### Benefits
- No external dependencies
- No download times
- Fully customizable parameters
- Lightweight and fast
- Perfectly reproducible
