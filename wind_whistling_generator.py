import numpy as np
import wave
import struct

def generate_wind_whistling_wav(output_file='wind_whistling.wav', duration=5.0, sample_rate=44100, volume=0.7):
    """
    Generate a wind whistling sound effect and save as WAV file.
    
    A realistic wind whistling is created by:
    - Regular, smooth pitch variations (not erratic)
    - Sustained tone with gentle modulation
    - Higher frequency (600-900 Hz range)
    - Pure sine wave with light harmonics
    - Smooth, flowing quality
    - Moderate attack, gradual decay
    
    Args:
        output_file: Path to output WAV file
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        volume: Amplitude scaling (0.0 to 1.0)
    """
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Higher frequency for wind whistling (600-900 Hz range)
    base_freq = 700  # Hz
    
    # Regular, smooth pitch modulation (gentle oscillation)
    # Much faster modulation than door creak
    wobble1 = 0.3 * np.sin(2 * np.pi * 0.8 * t)  # 0.8 Hz cycle
    wobble2 = 0.2 * np.sin(2 * np.pi * 1.5 * t)  # 1.5 Hz cycle
    wobble3 = 0.1 * np.sin(2 * np.pi * 2.3 * t)  # 2.3 Hz cycle
    
    # Combine for regular, smooth pitch
    freq_modulation = base_freq * (1 + 0.15 * (wobble1 + wobble2 + wobble3))
    
    # Add random frequency jumps (sticking points) - more dramatic
    num_sticks = int(duration * 1.5)  # About 1.5 sticking points per second (less frequent)
    for i in range(num_sticks):
        stick_pos = int(np.random.random() * len(t))
        stick_duration = int(sample_rate * 0.08)  # 80ms stick (longer)
        freq_change = np.random.uniform(-200, 200)  # Random jump (larger)
        stick_end = min(stick_pos + stick_duration, len(t))
        freq_modulation[stick_pos:stick_end] += freq_change
    
    # Generate phase-locked oscillator with irregular pitch
    phase = 2 * np.pi * np.cumsum(freq_modulation) / sample_rate
    oscillator = np.sin(phase) * 0.6  # Increase oscillator volume
    
    # Add gritty texture using LESS filtered noise (to reduce wind-like sound)
    noise = np.random.normal(0, 1, len(t))
    
    # Band-pass filter for noise (narrower band, more focused)
    low_filter = int(sample_rate / 1500)  # Cutoff ~1.5kHz (lower)
    high_filter = int(sample_rate / 600)   # Cutoff ~600Hz (higher)
    
    noise_lp = np.convolve(noise, np.ones(low_filter)/low_filter, mode='same')
    noise_bp = noise_lp - np.convolve(noise_lp, np.ones(high_filter)/high_filter, mode='same')
    
    # Less aggressive friction modulation on noise
    friction_mod = 0.5 + 0.3 * np.sin(2 * np.pi * 0.3 * t)
    noise_bp = noise_bp * friction_mod * 0.35  # Reduce noise volume
    
    # Sub-harmonic rumble for creepiness (around 80-120 Hz)
    rumble_freq = 100
    rumble_phase = 2 * np.pi * np.cumsum(freq_modulation * 0.15) / sample_rate
    rumble = np.sin(rumble_phase) * 0.25  # Reduce rumble volume
    
    # Mix all components (oscillator dominant)
    signal = oscillator + noise_bp + rumble
    
    # Envelope - very slow attack, very long decay
    attack_time = 1.0  # 1 second attack (slower)
    decay_time = duration - attack_time
    
    attack_samples = int(attack_time * sample_rate)
    envelope = np.ones(len(t))
    
    # Very smooth, gradual attack
    if attack_samples > 0:
        envelope[:attack_samples] = (1 - np.cos(np.pi * t[:attack_samples] / attack_time)) / 2
    
    # Very long exponential decay
    decay_start = attack_samples
    if len(t[decay_start:]) > 0:
        decay_curve = np.exp(-0.8 * t[decay_start:] / decay_time)
        envelope[decay_start:] = decay_curve
    
    # Add more dramatic random amplitude fluctuations (unsteady pressure)
    amplitude_noise = 0.85 + 0.15 * np.random.normal(0, 1, len(t))
    amplitude_noise = np.convolve(amplitude_noise, np.ones(int(sample_rate/8))/int(sample_rate/8), mode='same')
    envelope = envelope * amplitude_noise
    
    # Apply envelope and volume
    signal = signal * envelope * volume
    
    # Normalize to prevent clipping
    signal = signal / np.max(np.abs(signal)) * volume
    
    # Low-pass filter to soften (cutoff ~2000 Hz) for that "creepy" dullness
    lp_filter_size = int(sample_rate / 2000)
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
