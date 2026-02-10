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

def generate_siren_wav(output_file='siren.wav', duration=5.0, sample_rate=44100, volume=0.7,
                   siren_type='wail', siren_speed=40.0, apply_doppler=False,
                   doppler_velocity=30.0):
    """
    Generate a siren sound effect with optional Doppler effect and 3D positioning.
    
    Siren types:
    - 'wail': US-style continuous frequency sweep
    - 'hi_lo': European-style alternating high/low tones
    - 'yelp': US-style rapid alternating tones
    
    Args:
        output_file: Path to output WAV file
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        volume: Amplitude scaling (0.0 to 1.0)
        siren_type: Type of siren ('wail', 'hi_lo', 'yelp')
        siren_speed: Speed of siren cycles (wail = Hz, hi_lo/yelp = cycles per second)
        apply_doppler: Whether to apply Doppler effect
        doppler_velocity: Vehicle velocity in m/s for Doppler effect
    """
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # 3D positioning parameters
    # Vehicle moves from left/close to right/far over duration
    pan_position = t / duration  # 0.0 (left) → 1.0 (right)
    distance_factor = 1.0 - (t / duration) * 0.8  # 1.0 (close) → 0.2 (far)
    
    # Calculate radial velocity for Doppler effect
    # At start: approaching (positive), at middle: perpendicular (0), at end: receding (negative)
    if apply_doppler:
        # Smooth transition from approaching to receding
        radial_velocity = doppler_velocity * np.cos(np.pi * t / duration)
    else:
        radial_velocity = np.zeros_like(t)
    
    left_channel = np.zeros_like(t)
    right_channel = np.zeros_like(t)
    
    if siren_type == 'wail':
        # US-style wailing siren (continuous frequency sweep)
        # Higher frequencies for "wah wah" sound
        base_low_freq = 800  # Hz
        base_high_freq = 1200  # Hz
        
        # Frequency sweep modulation
        modulation = 0.5 * (1 + np.sin(2 * np.pi * siren_speed * t))
        
        # Apply Doppler shift to both frequencies
        freq_low = calculate_doppler_shift(base_low_freq, radial_velocity)
        freq_high = calculate_doppler_shift(base_high_freq, radial_velocity)
        
        # Interpolate between frequencies
        freq = freq_low + (freq_high - freq_low) * modulation
        
        # Generate phase-locked oscillator
        phase = 2 * np.pi * np.cumsum(freq) / sample_rate
        signal = np.sin(phase) * 0.4
        signal += 0.2 * np.sin(2 * phase)  # Add harmonic
        signal += 0.1 * np.sin(3 * phase)  # Add another harmonic
        
    elif siren_type == 'hi_lo':
        # European-style hi-lo siren (alternating two tones)
        hi_freq = 800  # Hz
        lo_freq = 400  # Hz
        
        # Square wave-like switching between tones
        switch_modulation = np.sign(np.sin(2 * np.pi * siren_speed * t))
        # Smooth the switching slightly
        switch_modulation = np.convolve(switch_modulation, np.ones(int(sample_rate/100))/int(sample_rate/100), mode='same')
        
        # Apply Doppler shift to both tones
        hi_freq_shifted = calculate_doppler_shift(hi_freq, radial_velocity)
        lo_freq_shifted = calculate_doppler_shift(lo_freq, radial_velocity)
        
        # Generate both tones
        phase_hi = 2 * np.pi * np.cumsum(np.full_like(t, hi_freq_shifted)) / sample_rate
        phase_lo = 2 * np.pi * np.cumsum(np.full_like(t, lo_freq_shifted)) / sample_rate
        
        signal_hi = np.sin(phase_hi) * 0.4
        signal_lo = np.sin(phase_lo) * 0.4
        
        # Blend between tones
        blend = (switch_modulation + 1) / 2  # 0 to 1
        signal = signal_hi * blend + signal_lo * (1 - blend)
        
    elif siren_type == 'yelp':
        # US-style yelp (rapid alternating)
        yelp_freq = 600  # Hz
        yelp_speed = siren_speed * 2  # Twice as fast as normal
        
        # Square wave modulation for yelp
        yelp_modulation = np.sign(np.sin(2 * np.pi * yelp_speed * t))
        
        # Apply Doppler shift
        yelp_freq_shifted = calculate_doppler_shift(yelp_freq, radial_velocity)
        
        # Generate tone
        phase = 2 * np.pi * np.cumsum(np.full_like(t, yelp_freq_shifted)) / sample_rate
        signal = np.sin(phase) * 0.5 * yelp_modulation
        
    else:
        raise ValueError(f"Unknown siren type: {siren_type}")
    
    # Apply envelope - quick attack at start
    attack_time = 0.1  # 100ms attack
    attack_samples = int(attack_time * sample_rate)
    envelope = np.ones_like(t)
    
    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
    
    # Apply envelope
    signal = signal * envelope * volume
    
    # 3D spatialization
    # Pan left→right
    pan_angle = pan_position * (np.pi / 2)
    left_gain = np.cos(pan_angle) * distance_factor
    right_gain = np.sin(pan_angle) * distance_factor
    
    left_channel = signal * left_gain
    right_channel = signal * right_gain
    
    # Low-pass filter for realism
    lp_filter_size = int(sample_rate / 4000)  # Cutoff ~4kHz
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
    print(f"Siren ({siren_type}) saved to {output_file}{doppler_info}")

if __name__ == "__main__":
    # Example: US wail siren with Doppler effect
    print("Generating US wail siren with Doppler effect (left/close → right/far)...")
    generate_siren_wav('siren_us_wail_doppler.wav', 
                       siren_type='wail', 
                       apply_doppler=True,
                       doppler_velocity=40.0)
    
    # Example: European hi-lo siren with Doppler effect
    print("\nGenerating European hi-lo siren with Doppler effect...")
    generate_siren_wav('siren_eu_hilo_doppler.wav',
                       siren_type='hi_lo',
                       apply_doppler=True,
                       doppler_velocity=35.0)
    
    # Example: US yelp siren with Doppler effect
    print("\nGenerating US yelp siren with Doppler effect...")
    generate_siren_wav('siren_us_yelp_doppler.wav',
                       siren_type='yelp',
                       apply_doppler=True,
                       doppler_velocity=40.0)
    
    # Example: Without Doppler (stationary siren)
    print("\nGenerating stationary US wail siren (no Doppler)...")
    generate_siren_wav('siren_us_wail_stationary.wav',
                       siren_type='wail',
                       apply_doppler=False)
