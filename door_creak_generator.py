import numpy as np
import wave
import struct

def generate_door_creak_wav(output_file='door_creak.wav', duration=2.0, sample_rate=44100, volume=0.7):
    """
    Generate a door creak sound effect and save as WAV file.
    
    A door creak is created by:
    - Multiple oscillating frequencies around 300-800 Hz
    - Fluctuating pitch (wobble) simulating friction
    - Band-pass filtered noise for texture
    - Slow attack and decay envelope
    - Irregular amplitude modulation
    
    Args:
        output_file: Path to output WAV file
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        volume: Amplitude scaling (0.0 to 1.0)
    """
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Primary creak frequency (fluctuating)
    base_freq = 500  # Hz
    # Create wobble using sine wave modulation
    wobble_speed = 3  # Hz - how fast pitch wobbles
    wobble_depth = 200  # Hz - how much pitch varies
    freq_modulation = base_freq + wobble_depth * np.sin(2 * np.pi * wobble_speed * t)
    
    # Generate phase-locked oscillator for smooth pitch transitions
    phase = 2 * np.pi * np.cumsum(freq_modulation) / sample_rate
    oscillator = np.sin(phase) * 0.4
    
    # Add second harmonic for richness
    oscillator += 0.2 * np.sin(2 * phase)
    
    # Add third harmonic for metallic quality
    oscillator += 0.1 * np.sin(3 * phase)
    
    # Generate noise for texture
    noise = np.random.normal(0, 1, len(t))
    
    # Band-pass filter for noise (focus around 1-2 kHz)
    low_filter_size = int(sample_rate / 2000)  # Low cutoff ~2kHz
    high_filter_size = int(sample_rate / 1000)  # High cutoff ~1kHz
    
    # Low-pass filter
    noise_lp = np.convolve(noise, np.ones(low_filter_size)/low_filter_size, mode='same')
    # Subtract to create high-pass effect (simple band-pass)
    noise_bp = noise_lp - np.convolve(noise_lp, np.ones(high_filter_size)/high_filter_size, mode='same')
    
    # Mix oscillator and filtered noise
    signal = oscillator + noise_bp * 0.3
    
    # Amplitude envelope - slow attack, long decay
    attack_time = 0.3  # 300ms attack
    decay_time = duration - attack_time
    
    attack_samples = int(attack_time * sample_rate)
    envelope = np.ones(len(t))
    
    # Smooth attack using cosine curve
    if attack_samples > 0:
        envelope[:attack_samples] = (1 - np.cos(np.pi * t[:attack_samples] / attack_time)) / 2
    
    # Exponential decay with slight modulation
    decay_start = attack_samples
    decay_curve = np.exp(-2 * t[decay_start:] / decay_time)
    # Add slight amplitude wobble
    amplitude_wobble = 0.9 + 0.1 * np.sin(2 * np.pi * 5 * t[decay_start:])
    envelope[decay_start:] = decay_curve * amplitude_wobble
    
    # Apply envelope and volume
    signal = signal * envelope * volume
    
    # Normalize to prevent clipping
    signal = signal / np.max(np.abs(signal)) * volume
    
    # Low-pass filter to soften harsh frequencies (cutoff ~3000 Hz)
    lp_filter_size = int(sample_rate / 3000)
    signal = np.convolve(signal, np.ones(lp_filter_size)/lp_filter_size, mode='same')
    
    # Normalize after filtering
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
    
    print(f"Door creak saved to {output_file}")

if __name__ == "__main__":
    generate_door_creak_wav()
