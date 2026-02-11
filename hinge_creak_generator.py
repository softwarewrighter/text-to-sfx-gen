#!/usr/bin/env python3
"""
Hinge Creak Sound Effect Generator

Generates realistic hinge creak sounds using research-driven synthesis:
- Stick-slip friction exciter with bursty envelope
- Modal resonator bank (3 resonant modes)
- Tonal glide during friction events
- Micro-variation for natural irregularity

Based on acoustic research for metal-on-metal friction sounds.
"""

import numpy as np
import wave
import struct


def _generate_stick_slip_envelope(num_samples, sample_rate, burst_rate_hz, burst_duration_ms):
    """
    Generate bursty stick-slip friction envelope.

    Creates irregular bursts simulating friction events with:
    - Random walk on burst rate (±30% variation)
    - Variable burst duration with jitter
    - Asymmetric shape (fast attack 20%, slower decay 80%)
    """
    envelope = np.zeros(num_samples)

    # Convert burst duration to samples
    base_burst_samples = int((burst_duration_ms / 1000.0) * sample_rate)

    # Generate burst events with random timing
    current_sample = 0
    while current_sample < num_samples:
        # Jitter on burst rate (±30%)
        jitter = 1.0 + (np.random.random() - 0.5) * 0.6
        samples_between_bursts = int((sample_rate / burst_rate_hz) * jitter)

        # Jitter on burst duration (±40%)
        duration_jitter = 1.0 + (np.random.random() - 0.5) * 0.8
        burst_samples = int(base_burst_samples * duration_jitter)
        burst_samples = max(burst_samples, int(sample_rate * 0.01))  # Minimum 10ms

        # Create asymmetric burst shape (20% attack, 80% decay)
        attack_samples = int(burst_samples * 0.2)
        decay_samples = burst_samples - attack_samples

        # Attack: fast exponential rise
        attack = 1 - np.exp(-5 * np.linspace(0, 1, attack_samples))

        # Decay: slower exponential fall
        decay = np.exp(-3 * np.linspace(0, 1, decay_samples))

        # Combine into single burst
        burst = np.concatenate([attack, decay])

        # Random amplitude variation per burst (0.4 to 1.0)
        burst_amplitude = 0.4 + np.random.random() * 0.6
        burst = burst * burst_amplitude

        # Place burst in envelope
        end_sample = min(current_sample + len(burst), num_samples)
        actual_len = end_sample - current_sample
        envelope[current_sample:end_sample] = burst[:actual_len]

        # Move to next burst
        current_sample += samples_between_bursts

    return envelope


def _biquad_bandpass_coeffs(center_freq, Q, sample_rate):
    """
    Calculate biquad bandpass filter coefficients.

    Direct Form II Transposed implementation.
    Returns (b0, b1, b2, a1, a2) coefficients.
    """
    omega = 2 * np.pi * center_freq / sample_rate
    sin_omega = np.sin(omega)
    cos_omega = np.cos(omega)
    alpha = sin_omega / (2 * Q)

    # Bandpass filter (constant skirt gain, peak gain = Q)
    b0 = alpha
    b1 = 0.0
    b2 = -alpha
    a0 = 1 + alpha
    a1 = -2 * cos_omega
    a2 = 1 - alpha

    # Normalize by a0
    return b0/a0, b1/a0, b2/a0, a1/a0, a2/a0


def _apply_biquad(signal, b0, b1, b2, a1, a2):
    """
    Apply biquad filter to signal using Direct Form II Transposed.

    Sample-by-sample processing for maximum flexibility.
    """
    output = np.zeros(len(signal))
    z1 = 0.0
    z2 = 0.0

    for i in range(len(signal)):
        x = signal[i]
        y = b0 * x + z1
        z1 = b1 * x - a1 * y + z2
        z2 = b2 * x - a2 * y
        output[i] = y

    return output


def _apply_modal_bank(signal, sample_rate, mode_freqs, mode_Q, freq_variation=0.05):
    """
    Apply 3-mode resonator bank to input signal.

    Each mode gets slight random walk on center frequency for micro-variation.
    """
    num_samples = len(signal)
    output = np.zeros(num_samples)

    for base_freq in mode_freqs:
        # Add slow random walk to frequency (micro-variation)
        # Generate smooth random walk
        walk_rate = 0.5  # Changes per second
        num_changes = int(num_samples / sample_rate * walk_rate * 10)
        random_points = np.random.randn(max(num_changes, 2)) * freq_variation
        random_points = np.cumsum(random_points)
        random_points = random_points - np.mean(random_points)

        # Interpolate to full length and smooth
        freq_modulation = np.interp(
            np.linspace(0, 1, num_samples),
            np.linspace(0, 1, len(random_points)),
            random_points
        )
        # Smooth the modulation
        smooth_samples = int(sample_rate * 0.1)
        freq_modulation = np.convolve(
            freq_modulation,
            np.ones(smooth_samples) / smooth_samples,
            mode='same'
        )

        # Apply filter with slowly varying center frequency
        # For efficiency, use average frequency (micro-variation is subtle)
        avg_freq = base_freq * (1 + np.mean(freq_modulation))
        avg_freq = max(20, min(avg_freq, sample_rate / 2 - 100))

        b0, b1, b2, a1, a2 = _biquad_bandpass_coeffs(avg_freq, mode_Q, sample_rate)
        mode_output = _apply_biquad(signal, b0, b1, b2, a1, a2)

        # Scale by mode importance (lower modes are stronger)
        mode_scale = 1.0 / (1 + mode_freqs.index(base_freq) * 0.3)
        output += mode_output * mode_scale

    return output


def _generate_friction_noise(num_samples, sample_rate, low_hz, high_hz, envelope):
    """
    Generate band-limited friction noise shaped by envelope.
    """
    # White noise
    noise = np.random.randn(num_samples)

    # Low-pass filter at high_hz
    if high_hz < sample_rate / 2:
        lp_samples = max(1, int(sample_rate / high_hz / 2))
        noise = np.convolve(noise, np.ones(lp_samples) / lp_samples, mode='same')

    # High-pass filter at low_hz (subtract low-passed version)
    hp_samples = max(1, int(sample_rate / low_hz))
    noise_lp = np.convolve(noise, np.ones(hp_samples) / hp_samples, mode='same')
    noise = noise - noise_lp

    # Apply envelope
    return noise * envelope


def _generate_tonal_component(t, sample_rate, base_freq, glide_rate_oct, envelope):
    """
    Generate tonal component with pitch glide during friction events.

    Frequency glides upward during high-envelope moments (tension building),
    with slow random walk for natural variation.
    """
    num_samples = len(t)

    # Base frequency with slow random walk (±10%)
    walk_points = int(num_samples / sample_rate * 2) + 2
    freq_walk = np.cumsum(np.random.randn(walk_points) * 0.02)
    freq_walk = freq_walk - np.mean(freq_walk)
    freq_walk = np.clip(freq_walk, -0.1, 0.1)

    freq_modulation = np.interp(
        np.linspace(0, 1, num_samples),
        np.linspace(0, 1, len(freq_walk)),
        freq_walk
    )

    # Glide based on envelope derivative (pitch rises with friction)
    # Smooth envelope for derivative calculation
    smooth_env = np.convolve(envelope, np.ones(100) / 100, mode='same')
    env_derivative = np.gradient(smooth_env) * sample_rate
    env_derivative = np.clip(env_derivative, 0, None)  # Only upward movement

    # Convert derivative to frequency glide
    glide_amount = env_derivative * glide_rate_oct * 0.01
    glide_amount = np.clip(glide_amount, -0.5, 0.5)

    # Combine modulations
    freq = base_freq * (1 + freq_modulation + glide_amount)

    # Phase accumulation for clean oscillator
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate

    # Main tone with harmonics
    signal = np.sin(phase) * 0.6
    signal += np.sin(2 * phase) * 0.25  # 2nd harmonic
    signal += np.sin(3 * phase) * 0.15  # 3rd harmonic

    # Shape by envelope
    return signal * envelope


def generate_hinge_creak(t, params, sample_rate):
    """
    Generate hinge creak sound (trainer-compatible function).

    Args:
        t: Time array from np.linspace
        params: Dictionary with synthesis parameters
        sample_rate: Sample rate in Hz

    Returns:
        Numpy array of audio samples
    """
    num_samples = len(t)

    # Extract parameters with defaults
    burst_rate_hz = params.get('burst_rate_hz', 6.0)
    burst_duration_ms = params.get('burst_duration_ms', 60)
    noise_band_low_hz = params.get('noise_band_low_hz', 500)
    noise_band_high_hz = params.get('noise_band_high_hz', 6000)
    mode1_hz = params.get('mode1_hz', 950)
    mode2_hz = params.get('mode2_hz', 2200)
    mode3_hz = params.get('mode3_hz', 3800)
    mode_Q = params.get('mode_Q', 25)
    glide_rate_oct = params.get('glide_rate_oct', 0.5)
    noise_to_tone_db = params.get('noise_to_tone_db', 8)

    # Generate stick-slip envelope
    envelope = _generate_stick_slip_envelope(
        num_samples, sample_rate, burst_rate_hz, burst_duration_ms
    )

    # Generate friction noise (band-limited)
    friction_noise = _generate_friction_noise(
        num_samples, sample_rate,
        noise_band_low_hz, noise_band_high_hz,
        envelope
    )

    # Apply modal resonator bank to friction noise
    mode_freqs = [mode1_hz, mode2_hz, mode3_hz]
    resonated_noise = _apply_modal_bank(
        friction_noise, sample_rate, mode_freqs, mode_Q
    )

    # Generate tonal component
    tonal = _generate_tonal_component(
        t, sample_rate, mode1_hz * 0.5,  # Tonal at half first mode
        glide_rate_oct, envelope
    )

    # Mix noise and tonal components using dB ratio
    # noise_to_tone_db: positive means noise is louder
    tone_scale = 1.0
    noise_scale = 10 ** (noise_to_tone_db / 20)

    # Normalize components before mixing
    if np.max(np.abs(resonated_noise)) > 0:
        resonated_noise = resonated_noise / np.max(np.abs(resonated_noise))
    if np.max(np.abs(tonal)) > 0:
        tonal = tonal / np.max(np.abs(tonal))

    # Mix
    signal = resonated_noise * noise_scale + tonal * tone_scale

    # Overall envelope for natural attack/decay
    overall_attack = int(sample_rate * 0.3)
    overall_decay = int(sample_rate * 0.5)
    overall_env = np.ones(num_samples)

    if overall_attack > 0 and overall_attack < num_samples:
        overall_env[:overall_attack] = np.linspace(0, 1, overall_attack)

    if overall_decay > 0 and overall_decay < num_samples:
        decay_start = num_samples - overall_decay
        overall_env[decay_start:] = np.linspace(1, 0, overall_decay)

    signal = signal * overall_env

    return signal


def generate_hinge_creak_wav(
    output_file='hinge_creak.wav',
    duration=2.5,
    sample_rate=44100,
    volume=0.7,
    burst_rate_hz=6.0,
    burst_duration_ms=60,
    noise_band_low_hz=500,
    noise_band_high_hz=6000,
    mode1_hz=950,
    mode2_hz=2200,
    mode3_hz=3800,
    mode_Q=25,
    glide_rate_oct=0.5,
    noise_to_tone_db=8
):
    """
    Generate a hinge creak sound effect and save as WAV file.

    Args:
        output_file: Path to output WAV file
        duration: Duration in seconds (1.0-5.0)
        sample_rate: Sample rate in Hz
        volume: Amplitude scaling (0.0 to 1.0)
        burst_rate_hz: Stick-slip event rate (3-12 Hz)
        burst_duration_ms: Duration of each friction burst (20-120 ms)
        noise_band_low_hz: Friction noise lower bound (400-900 Hz)
        noise_band_high_hz: Friction noise upper bound (4000-8000 Hz)
        mode1_hz: First resonant mode (700-1200 Hz)
        mode2_hz: Second resonant mode (1800-2600 Hz)
        mode3_hz: Third resonant mode (3200-4500 Hz)
        mode_Q: Resonator quality factor (10-60)
        glide_rate_oct: Pitch glide rate (0.2-1.5 oct/sec)
        noise_to_tone_db: Noise vs tone ratio (3-15 dB, higher = rustier)
    """
    # Create time array
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # Build params dict
    params = {
        'duration': duration,
        'burst_rate_hz': burst_rate_hz,
        'burst_duration_ms': burst_duration_ms,
        'noise_band_low_hz': noise_band_low_hz,
        'noise_band_high_hz': noise_band_high_hz,
        'mode1_hz': mode1_hz,
        'mode2_hz': mode2_hz,
        'mode3_hz': mode3_hz,
        'mode_Q': mode_Q,
        'glide_rate_oct': glide_rate_oct,
        'noise_to_tone_db': noise_to_tone_db
    }

    # Generate sound
    signal = generate_hinge_creak(t, params, sample_rate)

    # Normalize and apply volume
    if np.max(np.abs(signal)) > 0:
        signal = signal / np.max(np.abs(signal)) * volume

    # Convert to 16-bit PCM
    samples = (signal * 32767).astype(np.int16)

    # Write stereo WAV file
    with wave.open(output_file, 'w') as wav_file:
        wav_file.setnchannels(2)  # Stereo
        wav_file.setsampwidth(2)  # 2 bytes (16-bit)
        wav_file.setframerate(sample_rate)

        # Create stereo by duplicating mono signal
        for sample in samples:
            wav_file.writeframes(struct.pack('<hh', sample, sample))

    print(f"Hinge creak saved to {output_file}")


if __name__ == "__main__":
    print("Generating hinge creak sound...")
    generate_hinge_creak_wav()
    print("Done!")
