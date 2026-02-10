import numpy as np
import wave
import struct

def generate_gravel_footsteps_wav(output_file='gravel_footsteps.wav', duration=6.0, sample_rate=44100, volume=0.7):
    """
    Generate gravel footsteps sound effect and save as WAV file.
    
    Gravel footsteps are created by:
    - Many small stone impacts and grinding
    - Irregular timing like human walking
    - Mix of frequency bands (small stones = high freq, large stones = low freq)
    - Varying intensity based on step pressure
    
    Args:
        output_file: Path to output WAV file
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        volume: Amplitude scaling (0.0 to 1.0)
    """
    total_samples = int(sample_rate * duration)
    left_channel = np.zeros(total_samples)
    right_channel = np.zeros(total_samples)
    
    # Walking parameters
    steps_per_second = 2.0
    step_interval = sample_rate / steps_per_second
    
    # Generate footsteps with 3D positioning
    step_time = 0.5  # Start with slight offset
    step_count = 0
    
    while step_time < duration:
        step_start_sample = int(step_time * sample_rate)
        
        # Vary step duration slightly (0.15 - 0.25 seconds)
        step_duration = 0.15 + np.random.random() * 0.1
        step_samples = int(step_duration * sample_rate)
        
        if step_start_sample + step_samples > total_samples:
            break
        
        # Generate gravel sound for this step
        gravel = generate_single_gravel_step(step_samples, sample_rate)
        
        # 3D positioning
        # Position from left (0.0) to right (1.0) across duration
        pan_position = step_time / duration
        
        # Distance from close (1.0) to far (0.1) across duration (more dramatic)
        distance_attenuation = 1.0 - (step_time / duration) * 0.9
        
        # Constant power panning for smooth stereo transitions
        # left_gain = cos(angle), right_gain = sin(angle) where angle goes 0 to pi/2
        pan_angle = pan_position * (np.pi / 2)
        left_gain = np.cos(pan_angle) * distance_attenuation
        right_gain = np.sin(pan_angle) * distance_attenuation
        
        # Vary intensity randomly (0.5 - 1.0)
        intensity = 0.5 + np.random.random() * 0.5
        
        # Apply to left and right channels with 3D positioning
        end_sample = min(step_start_sample + step_samples, total_samples)
        actual_samples = end_sample - step_start_sample
        left_channel[step_start_sample:end_sample] += gravel[:actual_samples] * intensity * left_gain
        right_channel[step_start_sample:end_sample] += gravel[:actual_samples] * intensity * right_gain
        
        # Random variation in step timing - larger range for more human-like irregularity
        timing_variation = (np.random.random() - 0.5) * 0.3
        step_time += 1.0 / steps_per_second + timing_variation
        step_count += 1
    
    # Normalize and apply volume
    left_channel = left_channel / np.max(np.abs(left_channel)) * volume
    right_channel = right_channel / np.max(np.abs(right_channel)) * volume
    
    # Apply low-pass filter to both channels (cutoff ~1500 Hz)
    lp_filter_size = int(sample_rate / 1500)  # Filters above ~1500 Hz
    left_channel = np.convolve(left_channel, np.ones(lp_filter_size)/lp_filter_size, mode='same')
    right_channel = np.convolve(right_channel, np.ones(lp_filter_size)/lp_filter_size, mode='same')
    
    # Normalize after filtering to compensate for amplitude loss
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
    
    print(f"Gravel footsteps saved to {output_file}")

def generate_single_gravel_step(num_samples, sample_rate):
    """
    Generate a single gravel footstep sound.
    
    Creates multiple frequency bands to simulate different sized stones:
    - High frequency: small stones (2000-5000 Hz)
    - Mid frequency: medium stones (500-2000 Hz)
    - Low frequency: large stones (100-500 Hz)
    """
    t = np.linspace(0, num_samples / sample_rate, num_samples, False)
    
    # Generate noise for different stone sizes
    noise = np.random.normal(0, 1, num_samples)
    
    # High frequency component (small stones) - minimal filtering
    high_freq = noise
    
    # Mid frequency component (medium stones) - light filtering
    mid_filter_size = int(sample_rate / 1000)  # ~1ms
    mid_freq = np.convolve(noise, np.ones(mid_filter_size)/mid_filter_size, mode='same')
    
    # Low frequency component (large stones) - heavy filtering
    low_filter_size = int(sample_rate / 200)  # ~5ms
    low_freq = np.convolve(noise, np.ones(low_filter_size)/low_filter_size, mode='same')
    
    # Mix frequency bands (less high freq to reduce hiss)
    gravel = high_freq * 0.2 + mid_freq * 0.4 + low_freq * 0.4
    
    # Add sharp transients (individual stone impacts)
    num_impacts = 8 + int(np.random.random() * 8)  # 8-16 impacts per step
    for _ in range(num_impacts):
        impact_pos = int(np.random.random() * num_samples)
        impact_duration = int(sample_rate * 0.002)  # 2ms
        impact_end = min(impact_pos + impact_duration, num_samples)
        
        if impact_pos < num_samples:
            impact = np.random.normal(0, 1, impact_end - impact_pos)
            impact_envelope = np.exp(-10 * np.linspace(0, 1, impact_end - impact_pos))
            gravel[impact_pos:impact_end] += impact * impact_envelope * 0.8
    
    # Amplitude envelope - very fast attack, fast decay
    attack_time = 0.002  # 2ms attack
    decay_time = (num_samples / sample_rate) - attack_time
    
    attack_samples = int(attack_time * sample_rate)
    envelope = np.ones(num_samples)
    
    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
    
    if len(t[attack_samples:]) > 0:
        decay_curve = np.exp(-6 * t[attack_samples:] / decay_time)
        envelope[attack_samples:] = decay_curve
    
    return gravel * envelope

if __name__ == "__main__":
    generate_gravel_footsteps_wav()
