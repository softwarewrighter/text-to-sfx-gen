# Audio Synthesis Research Findings

## Overview

This document summarizes research conducted using online resources to understand procedural audio synthesis techniques for generating sound effects without AI models.

## Research Methods

Research was conducted using Playwright browser automation to gather information from:
- Wikipedia (synthesis techniques, sound design, envelopes, filtering)
- Musicradar.com (game audio techniques)
- FreeSound.org (sound effect library)
- Stanford CCRMA (audio programming resources)
- Animations Physics UNSW (frequency ranges)

---

## 1. Audio Synthesis Techniques

### Additive Synthesis
- **Definition**: Building complex sounds by summing simple waveforms (sine, square, sawtooth, triangle)
- **Key technique**: Amplitude envelopes applied to individual oscillators
- **Use cases**: 
  - Creating harmonically rich sounds
  - Layering multiple frequency components
  - Building complex timbres from simple building blocks
- **Advantages**: Simple to implement, predictable results
- **Limitations**: Can sound artificial if not carefully designed

### Subtractive Synthesis
- **Definition**: Creating sounds by filtering noise through frequency-dependent filters
- **Key technique**: White/pink noise filtered through bandpass/notch filters
- **Use cases**:
  - Wind, water, ambient sounds
  - Drum sounds (filtered noise bursts)
  - Breath/wind instruments
- **Advantages**: More natural, organic textures
- **Limitations**: Requires careful filter design

### Frequency Modulation (FM/PM)
- **FM Synthesis**: Varying frequency of one oscillator with another
  - Carrier signal frequency modulated by modulator
  - Creates rich, complex timbres
- **PM Synthesis**: Phase modulation
  - Varying phase of oscillator
  - Creates different timbre characteristics
- **Use cases**:
  - Bells, metallic sounds, vocal-like tones
  - Percussive sounds, textures
- **Advantages**: Extremely flexible, computationally efficient
- **Implementation**: Single sine wave modulating another

### Granular Synthesis
- **Definition**: Decomposing sound into tiny "grains" and reassembling
- **Key technique**:
  - Grain duration: 10-100ms
  - Grain spacing: sparse to dense
  - Grain playback: forward, backward, random
- **Use cases**:
  - Ambient textures
  - Complex, evolving sounds
  - Textures that evolve over time
- **Advantages**: Extremely flexible, organic results
- **Limitations**: Computationally intensive

---

## 2. Sound Design Principles

### Core Elements

#### Envelopes (ADSR)
- **Attack**: Initial sound onset
  - Percussive: 1-10ms (immediate)
  - Melodic: 100-500ms (smooth)
  - Ambient: 200-1000ms (very gradual)
- **Decay**: Volume decrease after sound ends
  - Linear: Simple, predictable
  - Exponential: More natural, "dying" sound
  - Logarithmic: Extended decay
- **Sustain**: Maintained volume level during main portion
- **Release**: Final fade-out (especially important for looped sounds)
  - Fade-out to prevent clicking in loops
  - Duration: 100-500ms typical

#### Frequency Ranges (by sound type)

| Sound Type | Low Range | Mid Range | High Range |
|-------------|-----------|-----------|-------------|
| **Impacts** | 20-80 Hz | 100-500 Hz | 500-2000 Hz |
| **Doors/Wood** | 100-400 Hz | 400-1000 Hz | 1000-3000 Hz |
| **UI Sounds** | 500-1500 Hz | 1500-4000 Hz | 4000-8000 Hz |
| **Ambience** | 50-200 Hz | 200-800 Hz | 800-4000 Hz |
| **Voices** | 80-300 Hz | 300-1500 Hz | 1500-5000 Hz |

#### Harmonics
- Odd harmonics (3rd, 5th, 7th) create "woody" or "brassy" timbres
- Even harmonics (2nd, 4th, 6th) can create "hollow" or "nasal" sounds
- Fundamental + 2nd harmonic = rich, full tone
- Adding higher harmonics increases brightness
- Inharmonic partials create metallic or percussive sounds
- Balance: Too many harmonics = harsh, too few = thin

#### Filtering

##### Low-Pass Filters
- **Purpose**: Remove high frequencies
- **Application**: Sub-bass, removing harshness
- **Characteristics**: Smooth, warm sound
- **Implementation**: Moving average, FIR/IIR filters
- **Cutoff**: Typically 200-500 Hz for low-pass

##### High-Pass Filters
- **Purpose**: Remove low frequencies
- **Application**: Hi-hat, cymbals, brightness
- **Characteristics**: Thin, crisp sound
- **Implementation**: Moving average, FIR/IIR filters
- **Cutoff**: Typically 2000-5000 Hz for high-pass

##### Band-Pass Filters
- **Purpose**: Isolate specific frequency range
- **Application**: Formants in voices, telephone sounds
- **Characteristics**: Focused, "radio" quality
- **Implementation**: Cascaded low-pass and high-pass
- **Bandwidth**: Narrow formants, wide for ambient

---

## 3. Game Audio Techniques

### One-Shot vs Looped Sounds

#### One-Shot
- **Definition**: Single playthrough, no repetition
- **Use cases**: 
  - Button clicks
  - Menu selections
  - Explosions
  - Impacts
- **Design considerations**:
  - Clean fade-out (no tail)
  - Short duration (50-500ms)
  - Immediate attack
  - No phase discontinuities at end

#### Looped
- **Definition**: Repeating seamlessly
- **Use cases**:
  - Ambience
  - Engine sounds
  - Footsteps
  - Wind
- **Design considerations**:
  - Smooth fade-in at loop point
  - Consistent energy level
  - No phase artifacts at loop boundary
  - Crossfade between start and end
  - Loop length: typically 2-8 seconds

### Procedural vs Recorded

#### Procedural Advantages
- **Infinite variety**: Parameters can be tweaked endlessly
- **Small file size**: Code instead of audio samples
- **Dynamic**: Can change pitch/timbre in real-time
- **Memory-efficient**: No need to load large samples
- **Commercial-friendly**: No licensing restrictions on generated sounds
- **Reproducible**: Same inputs = same outputs
- **Portable**: Runs on any platform with Python

#### Procedural Limitations
- **Time-consuming**: Designing high-quality sounds takes effort
- **Can sound artificial**: If not carefully tuned
- **Requires expertise**: Understanding of audio programming
- **Lower quality**: Than recorded samples for complex sounds

---

## 4. Specific Sound Effect Techniques

### Impact Sounds (Thud, Explosion)

#### Thud
- **Components**:
  - Low-frequency oscillator (60-80 Hz)
  - Filtered noise (bandpass 100-500 Hz for body)
  - Sharp attack envelope (1-10ms)
  - Exponential decay (fast)
  - Single harmonic or slight second
- **Enhancement**: Transient spikes for crack/impact feel
- **Example frequencies**: 80 Hz fundamental, 160 Hz harmonic
- **Attack**: Very fast (1-5ms)
- **Decay**: Quick (200-300ms)

#### Explosion
- **Components**:
  - Low-frequency rumble (20-50 Hz)
  - Broadband noise (100-5000 Hz)
  - Sharp attack (1-10ms)
  - Long decay (1-2 seconds)
  - Multiple frequency layers
- **Design**:
  - Layer 1: Sub-bass (sine + harmonics)
  - Layer 2: Low-mid noise (body of explosion)
  - Layer 3: High-freq noise (crack, debris)
  - Envelope: Punchy attack, long exponential tail
- **Enhancements**: 
  - Transient spikes for crack/snap
  - Slight frequency modulation during decay
  - Reverb simulation (echo tail)

### Button/UI Sounds

#### Button Click
- **Components**:
  - High-frequency sine wave (2000-4000 Hz)
  - Light filtering (keep brightness)
  - Very fast attack (1-5ms)
  - Immediate decay
- **Enhancement**: Second harmonic for richness
- **Example frequencies**: 3000 Hz fundamental, 6000 Hz harmonic
- **Duration**: 30-100ms
- **Characteristics**: Crisp, UI-appropriate

#### Menu Select
- **Components**:
  - Two-tone sequence
  - Short silence between
  - Clean waveforms
- **Implementation**: Multiple sine generators with slight frequency difference
- **Frequencies**: 800 Hz and 880 Hz (common UI tones)

### Door Sounds

#### Creak
- **Characteristics**:
  - Very slow, irregular pitch variations
  - Friction-based sound with filtered noise
  - Random frequency jumps simulating sticking points
  - Gritty texture, not smooth oscillator-like sound
  - Sub-harmonic rumble for creepiness
  - Slow attack, long decay
- **Frequency range**: 200-800 Hz
- **Implementation**:
  - Multiple slow modulation waves (0.1-0.6 Hz)
  - Random sticking points every 0.5-1.0 seconds
  - Bandpass filtered noise (500-2000 Hz)
  - Sub-harmonic rumble (80-120 Hz)
  - Very slow attack (500-1000ms)
  - Long exponential decay
- **Enhancements**: 
  - More dramatic pitch jumps
  - Varying friction modulation
  - Low-pass filtering (1.5-2 kHz)

#### Close
- **Components**:
  - High-energy impact
  - Multiple resonance layers
  - Reverb tail
  - Thud + slam
- **Frequency range**: 50-2000 Hz
- **Implementation**:
  - Low-frequency thud (80-120 Hz)
  - Mid-frequency slam (200-500 Hz)
  - High-frequency rattle (500-2000 Hz)
  - Separate envelopes for each layer

### Footsteps (Gravel, Wood)

#### Gravel Footsteps
- **Characteristics**:
  - Many small stone impacts
  - Irregular timing
  - Mix of frequency bands (small=high, large=low)
  - Texture from filtered noise
- **Implementation**:
  - Individual stone transients (2-5ms duration)
  - 8-16 impacts per step
  - Bandpass noise (800-2000 Hz)
  - Subtle rumble layer
  - Frequency bands:
    - Small stones: 2000-5000 Hz
    - Medium stones: 500-1000 Hz
    - Large stones: 100-500 Hz
- **Enhancements**:
  - 3D spatialization (pan left→right)
  - Distance attenuation (close→far)
  - Low-pass filtering to reduce hiss

#### Wood Footsteps
- **Differences** from gravel:
  - Fewer, softer impacts
  - More consistent timing
  - Lower frequency content
  - More resonant, less noisy
- **Implementation**:
  - Softer transients (5-10ms attack)
  - Wooden tap frequencies (300-600 Hz)
  - Less noise content
  - More resonant, less noisy
  - Slightly longer step interval (0.4-0.5s)

### Sirens

#### US Wail
- **Characteristics**: Continuous frequency sweep
- **Frequency range**: 500-1200 Hz (improved)
- **Sweep rate**: 2-4 Hz cycle
- **Waveform**: Odd harmonics (1st, 3rd, 5th, 7th)
- **Implementation**:
  - Phase-locked oscillator with varying frequency
  - Slight randomness in sweep
  - Tremolo (amplitude modulation) for realism
- **Enhancements**:
  - More odd harmonic content for grit
  - Less regular sweep (slight randomness)
  - Light filtering (keep high frequencies)
  - Higher frequency range (not too low)

#### European Hi-Lo
- **Characteristics**: Two alternating tones
- **Frequencies**: 450 Hz (low), 900 Hz (high)
- **Switch rate**: 2-4 Hz
- **Waveform**: Square-like transitions between tones
- **Implementation**:
  - Two separate oscillators
  - Modulated blending (smooth switching)
  - Slightly different frequencies create "minor third" interval
- **Enhancements**:
  - Harmonics for realism
  - Smoother switching transitions
  - Slight noise component

#### US Yelp
- **Characteristics**: Rapid alternating
- **Frequency**: 700 Hz
- **Switch rate**: 8-10 Hz (twice as fast as normal)
- **Waveform**: Square modulation
- **Implementation**:
  - Fast square wave modulation
  - Sharper transitions
  - More urgent feel
- **Enhancements**:
  - Harmonics
  - Noise for texture

### Wind/Ambience Sounds

#### Wind
- **Types**:
  - **Breeze**: Gentle, sustained (white/pink noise)
  - **Gust**: Modulated noise bursts
  - **Whistling**: Narrow-band sine wave
- **Whistling characteristics**:
  - Regular, smooth pitch variations (not erratic)
  - Sustained tone with gentle modulation
  - Higher frequency than door creak (500-900 Hz range)
  - Pure sine wave with light harmonics
  - Smooth, flowing quality
- **Implementation**:
  - Base frequency: 600-900 Hz
  - Regular modulation (0.8-2.3 Hz cycles)
  - Gentle sine with 2nd harmonic
  - Light noise for air texture
  - Moderate attack, gradual decay
  - No frequency jumps (unlike door creak)

#### Ambience
- **Layers**: Multiple frequency bands
- **Components**:
  - Low rumble (50-100 Hz)
  - Mid texture (200-500 Hz)
  - High air (1000-4000 Hz)
  - Subtle movement
- **Implementation**:
  - Separate oscillators per band
  - Independent modulation per layer
  - Slow crossfading between layers
  - Long duration (10-60 seconds)
  - Subtle amplitude variations

### UFO/Flying Saucer
- **Characteristics**: Smooth rise-and-fall
- **Frequency range**: 200-800 Hz
- **Waveform**: Cyclical, smooth sweep
- **Texture**: Metallic/electronic quality
- **Implementation**:
  - Multiple overlapping sine waves at different rates
  - Second harmonic for richness
  - Slight high-frequency "electronic" texture
  - Pulsing amplitude modulation
  - No decay (continuous)

---

## 5. Spatial Audio (3D Positioning)

### Doppler Effect
- **Formula**: `f_observed = f_source * (v_sound ± v_radial) / v_sound`
- **Approaching**: Higher frequency (blue shift)
- **Receding**: Lower frequency (red shift)
- **Application**: Moving vehicles, flying objects
- **Implementation**:
  - Calculate radial velocity over time
  - Apply frequency shift to base frequency
  - Smooth transition at passing moment
  - Use with siren, flying saucer sounds
- **Example**: 40 m/s vehicle = ~12% frequency shift

### Stereo Panning
- **Linear panning**: Simple L/R volume control
- **Constant power panning**: `L = cos(θ)`, `R = sin(θ)`
  - Maintains perceived loudness across pan positions
- **Application**: Positioning sounds in 2D/3D space
- **Implementation**:
  - Pan angle from 0 (left) to π/2 (right)
  - Apply gains to both channels

### Distance Attenuation
- **Inverse square law**: Volume ∝ 1/distance²
- **Implementation**:
  - Distance factor from 1.0 (close) to 0.2 (far)
  - Volume scaling: 1.0 → 0.2 over time
  - Combined with Doppler for realistic movement

### Binaural Audio
- **Purpose**: Create realistic 3D audio through headphones
- **Technique**: Slight frequency/phase differences between ears
- **Implementation**:
  - Left/right channels with subtle timing differences
  - HRTF filtering (complex frequency-dependent filtering)
  - Requires headphones for full effect

---

## 6. Python Audio Libraries

### NumPy
- **Purpose**: Numerical computing, signal processing
- **Key functions**:
  - `sin()`, `cos()`: Wave generation
  - `convolve()`: Filtering
  - `cumsum()`: Phase-locked oscillators
  - `linspace()`: Time vectors
  - `random.normal()`: White noise generation
- **Advantages**: Fast, efficient array operations
- **Usage**: Core of all audio synthesis code

### Wave Module (stdlib)
- **Purpose**: WAV file I/O
- **Functions**:
  - Wave file reading/writing
  - 16-bit PCM encoding
  - Stereo support
  - Sample rate control
- **Advantages**: Native Python, no dependencies
- **Usage**: Simple sound file export

### Third-Party Libraries

#### PyAudio
- **Purpose**: Real-time audio I/O
- **Features**:
  - Microphone input
  - Speaker output
  - Low latency
- **Use case**: Real-time sound generation/playback
- **Advantages**: Cross-platform, simple API

#### SoundDevice
- **Purpose**: Audio playback
- **Features**:
  - Cross-platform
  - Simple API
  - Good for playing generated sounds
- **Use case**: Testing and playback of generated effects
- **Advantages**: Easy to install, minimal dependencies

---

## 7. Best Practices for Procedural SFX

### Envelope Design
- **Attack time**: Match to physical sound
  - Fast for percussive (1-10ms)
  - Slow for ambient (200-1000ms)
- **Decay shape**: 
  - Exponential for natural, "dying" sound
  - Logarithmic for extended tail
- **Sustain**: For sustained sounds, add slight noise for realism
- **Release**: Fade-out to prevent clicking in looped sounds (100-500ms)

### Layering
- **Frequency separation**: Use non-overlapping frequency bands
- **Dynamics**: Independent volume envelopes per layer
- **Balancing**: Adjust relative volumes carefully
- **Panning**: Spatialize layers for width

### Realism Enhancements
- **Micro-structure**: Add small variations at millisecond scale
- **Imperfections**: Slight pitch wobble, timing jitter
- **Texture**: Subtle noise, light filtering
- **Movement**: Doppler, panning, distance attenuation for spatial effects

### Performance Considerations
- **Pre-computation**: Generate envelopes once, reuse
- **Vectorization**: Use NumPy array operations instead of loops
- **Filter efficiency**: Use convolution for filtering
- **Normalization**: Normalize to prevent clipping

### Audio Quality
- **Sample rate**: 44.1 kHz minimum for high quality
- **Bit depth**: 16-bit minimum, 24-bit for professional
- **Dynamic range**: Aim for -1 dBFS peak
- **Clipping**: Avoid at all costs, use limiting instead

---

## 8. Common Issues and Solutions

### Aliasing
- **Cause**: Frequencies above Nyquist limit (sample_rate / 2)
- **Symptoms**: Metallic, harsh sounds at high frequencies
- **Solution**: Band-limiting, oversampling

### Clipping
- **Cause**: Samples exceed ±32767 (16-bit limit)
- **Symptoms**: Distortion, loss of detail
- **Solution**: 
  - Hard limit to ±32767
  - Soft clipping (smooth saturation)
  - Dynamic range compression
  - Normalize before final output

### Clicks/Artifacts
- **Cause**: Discontinuous signals at loop boundaries
- **Symptoms**: Popping, clicking in looped sounds
- **Solution**: 
  - Crossfade between loop start/end
  - Zero-crossing at loop points
  - Ensure DC offset removal

---

## 9. Implementation Insights

### Current Project Sounds

| Sound | Techniques Used | Frequency Range | Status | Notes |
|--------|------------------|------------------|--------|-------|
| **Thud** | Low-freq oscillator + filtered noise | 60-80 Hz | ✅ Works well, clean impact |
| **Button Click** | High-freq sine + light filtering | 3000-4000 Hz | ✅ Crisp, UI-appropriate |
| **Door Creak** (Wind Whistling) | Sustained sine with modulation | 600-900 Hz | ⚠️ Sounds like wind whistling, not creaky |
| **Explosion** | Rumble + broadband noise | 20-500 Hz | ✅ Good impact, long decay |
| **Gravel Footsteps** | Multi-band transients + noise | 100-5000 Hz | ✅ Realistic 3D effect |
| **Siren (US Wail)** | Frequency sweep + harmonics | 500-1200 Hz | ⚠️ Too low pitched, sounds like flying saucer |
| **Siren (EU Hi-Lo)** | Alternating tones | 450/900 Hz | ✅ Two-tone pattern |
| **Siren (US Yelp)** | Square modulation | 700 Hz | ✅ Urgent, fast |
| **Flying Saucer** | Rise-fall sweep | 200-800 Hz | ✅ Sci-fi quality |
| **Wind Whistling** | Regular, smooth pitch | 600-900 Hz | ⚠️ Misnamed - actually wind whistling |

### Improvements Needed

#### Door Creak → Actual Door Creak
- **Current**: Sounds like wind whistling (intended misnomer)
- **Needed**: Actually generate door creak sound
- **Characteristics**:
  - Very slow, irregular pitch variations
  - Friction-based sound with filtered noise
  - Random frequency jumps simulating sticking points
  - Sub-harmonic rumble for creepiness
  - Frequency range: 200-800 Hz
  - Slow attack (500-1000ms)
  - Long exponential decay
- **Key difference**: More erratic, less regular than wind whistling

#### Siren (Wail) → More Realistic
- **Current**: Basic frequency sweep (sounds too low)
- **Needed**: Higher frequency range (500-1200 Hz)
- **Enhancements**:
  - More odd harmonics (1st, 3rd, 5th, 7th)
  - Tremolo for realism
  - Less regular sweep (slight randomness)
  - Light filtering (keep high frequencies for grit)

#### Wind Whistling
- **Status**: Actually implemented correctly (file misnamed)
- **Characteristics**:
  - Regular, smooth pitch variations (not erratic)
  - Sustained tone (600-900 Hz)
  - Gentle modulation
  - Smooth, flowing quality
- **Improvements**: 
  - Add slight breathiness
  - Very subtle wind noise
  - Natural vibrato

---

## 10. Future Sound Effects to Implement

### Natural Sounds
- **Rain** (white noise through bandpass filters)
- **Thunder** (low rumble + impulse + delay)
- **Fire** (noise bursts + crackling + rumble)
- **Water** (filtered noise + modulation)
- **Birdsong** (sine waves + irregular timing)
- **Crickets** (high-freq pulses + timing variations)
- **Frogs** (multiple frequency chirps with amplitude envelope)
- **Waves** (filtered pink noise + modulation)
- **Insects** (high-freq buzzing with irregular patterns)

### Mechanical Sounds
- **Engine idle** (low rumble + harmonics)
- **Engine rev** (rising pitch + noise bursts)
- **Gear shift** (pitch jumps + whoosh)
- **Brake squeal** (high-freq sine + amplitude modulation)
- **Hydraulic** (low hiss + pressure release)
- **Clock tick** (short high-freq transients)
- **Typewriter** (mechanical key sounds + carriage return)
- **Cash register** (cha-ching sounds with frequency variation)

### Impact Sounds
- **Punch** (transient + low-mid impact)
- **Kick drum** (sine sweep + click)
- **Slap** (sharp attack + body + decay)
- **Drop** (impact + bounce resonance)
- **Body slam** (thud + rattle + reverb)
- **Glass break** (high-freq transients + shatter)
- **Wood knock** (mid-freq resonance + fast decay)

### UI/Feedback Sounds
- **Power up** (rising sine + harmony)
- **Level up** (sequence of tones)
- **Error** (dissonant chord + decay)
- **Achievement** (major chord + sparkle)
- **Typing** (filtered noise bursts)
- **Menu selection** (soft sine with decay)

### Weapon Sounds
- **Gunshot** (transient + noise tail + echo)
- **Laser** (high-freq sine + sweep)
- **Explosion** (refine existing)
- **Rocket launch** (rising hiss + rumble + high-freq thrust)

### Movement Sounds
- **Footsteps** (different surfaces):
  - Wood (softer, resonant)
  - Metal (higher freq, more metallic)
  - Water (splashes, gurgles)
  - Snow (crunchy, irregular)
  - Grass (soft, light)
- **Vehicle movement** (Doppler + engine sounds):
  - Car (idle + rev + shift)
  - Truck (deeper, heavier)
  - Motorcycle (higher pitch, faster)
  - Train (rumble + click-clack + whistle)
- **Flying**:
  - Propeller plane (rhythmic throb + wind)
  - Jet engine (sweep + afterburner)
  - Helicopter (throb + blade chop)
  - UFO (various patterns)

### Ambient/Atmospheric
- **Forest** (birds + wind + leaves)
- **City** (traffic + distant sirens + urban ambience)
- **Space** (hum + high-freq textures + reverb)
- **Underwater** (filtered noise + muted high freq)
- **Dungeon** (drips + echoes + distant sounds)
- **Haunted house** (creaks + footsteps + wind + distant noises)
- **Marketplace** (crowd babble + distant music + environmental)
- **War zone** (gunfire + explosions + distant impacts + rubble)

---

## 11. Resources

### Documentation
- Wikipedia: Audio synthesis, sound design, envelopes, filtering
- Stanford CCRMA: Audio programming resources
- FreeSound.org: Sound effect library
- Musicradar.com: Game audio techniques

### Tools
- Playwright: Web browser automation for research
- NumPy: Signal processing
- Wave: Audio file I/O
- Python: Implementation language

### Next Research Targets
- **More sophisticated filtering**: FIR/IIR filter design
- **Spatial audio**: Binaural rendering, HRTF
- **Advanced synthesis**: Granular, wavetable, physical modeling
- **Real-time generation**: Continuous procedural sound generation
- **Sound mixing**: Combining multiple layers effectively

---

## Conclusion

Procedural audio synthesis offers a powerful, license-friendly alternative to AI-generated sounds. While quality may be lower than recorded samples or AI models, the ability to infinitely vary parameters and generate unique sounds without external dependencies makes it valuable for:

- Indie game development
- Open-source projects with restrictive licensing
- Educational applications (understanding sound)
- Prototyping and rapid iteration
- Customizable sound design

### Key Success Factors

1. **Understanding fundamentals**: Frequency, amplitude, timbre, envelope
2. **Layering complexity**: Multiple simple elements create rich sounds
3. **Realism through imperfections**: Natural sounds aren't perfect
4. **Spatial positioning**: Doppler, panning, distance add immersion
5. **Iterative refinement**: Test, tweak, improve constantly
6. **Technical quality**: Proper filtering, avoiding clipping, good envelopes

This research provides a solid foundation for generating a wide variety of sound effects using pure mathematical synthesis without relying on AI models or external samples.
