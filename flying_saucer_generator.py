import numpy as np
import wave
import struct

def calculate_doppler_shift(base_freq, velocity_radial, speed_of_sound=343):
    """
    Calculate Doppler-shifted frequency based on radial velocity.
    
    Args:
        base_freq: Base frequency in Hz
        velocity_radial: Radial velocity in m/s (positive = approaching, negative = receding)
        speed_of_sound: Speed of sound in m/s (default 343 m/s)
    
    Returns:
        Shifted frequency in Hz
    """
    return base_freq * (speed_of_sound + velocity_radial) / speed_of_sound

def generate_flying_saucer_wav(output_file='flying_saucer.wav', duration=5.0, sample_rate=44100, volume=0.7,
                                 apply_doppler=False, doppler_velocity=30.0):
    """
    Generate a sci-fi flying saucer (UFO) sound effect.
    
    Flying saucer sound characteristics:
    - Continuous rising and falling frequency sweep (not wailing)
    - Frequency range: 200-800 Hz
    - Smooth, cyclical sweep pattern
    - Metallic/electronic texture
    - Often has a slight "wub-wub-wub" quality
    
    Args:
        output_file: Path to output WAV file
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        volume: Amplitude scaling (0.0 to 1.0)
        apply_doppler: Whether to apply Doppler effect
        doppler_velocity: Vehicle velocity in m/s for Doppler effect
    """
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # 3D positioning parameters
    # Saucer moves from left/close to right/far over duration
    pan_position = t / duration  # 0.0 (left) → 1.0 (right)
    distance_factor = 1.0 - (t / duration) * 0.8  # 1.0 (close) → 0.2 (far)
    
    # Calculate radial velocity for Doppler effect
    # At start: approaching (positive), at middle: perpendicular (0), at end: receding (negative)
    if apply_doppler:
        # Smooth transition from approaching to receding
        radial_velocity = doppler_velocity * np.cos(np.pi * t / duration)
    else:
        radial_velocity = np.zeros_like(t)
    
    # Flying saucer frequency sweep - rise and fall
    # Cyclical pattern: rises then falls smoothly
    # Base frequency range: 200-800 Hz
    base_freq_low = 200  # Hz
    base_freq_high = 800  # Hz
    
    # Create smooth rise-and-fall modulation
    # Two overlapping sine waves at different rates for organic feel
    sweep1 = 0.5 * (1 + np.sin(2 * np.pi * 0.5 * t))  # 0.5 Hz cycle
    sweep2 = 0.3 * (1 + np.sin(2 * np.pi * 0.7 * t))  # 0.7 Hz cycle
    sweep3 = 0.2 * (1 + np.sin(2 * np.pi * 1.2 * t))  # 1.2 Hz cycle
    
    # Combine for complex, smooth sweep
    sweep_modulation = sweep1 + sweep2 + sweep3
    
    # Apply Doppler shift to frequencies
    freq_low_shifted = calculate_doppler_shift(base_freq_low, radial_velocity)
    freq_high_shifted = calculate_doppler_shift(base_freq_high, radial_velocity)
    
    # Interpolate between frequencies with sweep modulation
    freq = freq_low_shifted + (freq_high_shifted - freq_low_shifted) * sweep_modulation
    
    # Generate phase-locked oscillator
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    signal = np.sin(phase) * 0.5
    
    # Add second harmonic for richness (gives metallic quality)
    signal += 0.25 * np.sin(2 * phase)
    
    # Add third harmonic for "electronic" feel
    signal += 0.1 * np.sin(3 * phase)
    
    # Add subtle high-frequency "electronic" texture
    # Light noise for electronic buzz
    noise = np.random.normal(0, 1, len(t))
    # High-pass filter around 3-5 kHz
    high_filter = int(sample_rate / 3000)
    noise_hp = noise - np.convolve(noise, np.ones(high_filter)/high_filter, mode='same')
    signal += noise_hp * 0.05
    
    # Add slight amplitude modulation (pulsing quality)
    pulse = 1.0 + 0.1 * np.sin(2 * np.pi * 2 * t)
    signal = signal * pulse
    
    # Envelope - smooth attack, continuous
    attack_time = 0.2  # 200ms smooth attack
    attack_samples = int(attack_time * sample_rate)
    envelope = np.ones_like(t)
    
    if attack_samples > 0:
        # Very smooth attack using cosine
        envelope[:attack_samples] = (1 - np.cos(np.pi * t[:attack_samples] / attack_time)) / 2
    
    # No decay - continuous sound
    
    # Apply envelope and volume
    signal = signal * envelope * volume
    
    # 3D spatialization
    # Pan left→right
    pan_angle = pan_position * (np.pi / 2)
    left_gain = np.cos(pan_angle) * distance_factor
    right_gain = np.sin(pan_angle) * distance_factor
    
    left_channel = signal * left_gain
    right_channel = signal * right_gain
    
    # Light low-pass filter for smoothness
    lp_filter_size = int(sample_rate / 8000)  # Cutoff ~8kHz
    left_channel = np.convolve(left_channel, np.ones(lp_filter_size)/lp_filter_size, mode='same')
    right_channel = np.convolve(right_channel, np.ones(lp_filter_size)/lp_filter_size, mode='same')
    
    # Normalize to prevent clipping
    left_channel = left_channel / np.max(np.abs(left_channel)) * volume
    right_channel = right_channel / np.max(np.abs(right_channel)) * volume
    
    # Convert to 16-bit PCM
    left_samples = (left_channel * 32767).astype(np.int16)
    right_samples = (right_channel * 32767).astype(np.int16)
    
    # Write stereo WAV file
    with wave.open(output_file, 'w') as wav_file:
        wav_file.setnchannels(2)  # Stereo
        wav_file.setsampwidth(2)  # 2 bytes (16-bit)
        wav_file.setframerate(sample_rate)
        
        # Interleave left and right channels
        for left, right in zip(left_samples, right_samples):
            wav_file.writeframes(struct.pack('<hh', left, right))
    
    doppler_info = f" (Doppler: {doppler_velocity} m/s)" if apply_doppler else ""
    print(f"Flying saucer saved to {output_file}{doppler_info}")

if __name__ == "__main__":
    # Example: Flying saucer with Doppler effect
    print("Generating sci-fi flying saucer with Doppler effect (left/close → right/far)...")
    generate_flying_saucer_wav('flying_saucer_doppler.wav',
                                 apply_doppler=True,
                                 doppler_velocity=40.0)
    
    # Example: Stationary flying saucer (no Doppler)
    print("\nGenerating stationary flying saucer (no Doppler)...")
    generate_flying_saucer_wav('flying_saucer_stationary.wav',
                                 apply_doppler=False)
