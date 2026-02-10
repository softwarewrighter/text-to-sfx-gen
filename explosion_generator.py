import numpy as np
import wave
import struct

def generate_explosion_wav(output_file='explosion.wav', duration=2.0, sample_rate=44100, volume=0.7):
    """
    Generate an explosion sound effect and save as WAV file.
    
    An explosion is created by:
    - Very loud, sudden onset
    - Low-frequency rumble (20-100 Hz)
    - Broadband noise for shockwave
    - Slow attack (50-100ms) with sustain
    - Long decay with reverberation
    - Multiple frequency layers
    
    Args:
        output_file: Path to output WAV file
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        volume: Amplitude scaling (0.0 to 1.0)
    """
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Low-frequency oscillator for rumble
    rumble_freq = 50  # Hz
    rumble = np.sin(2 * np.pi * rumble_freq * t) * 0.8
    rumble += 0.4 * np.sin(2 * np.pi * rumble_freq * 1.5 * t)
    
    # Add sub-bass (20 Hz)
    sub_bass = np.sin(2 * np.pi * 20 * t) * 0.6
    
    # Generate white noise for shockwave
    noise = np.random.normal(0, 1, len(t))
    
    # Split noise into frequency layers
    # Low-frequency noise (rumble texture)
    low_filter = int(sample_rate / 100)  # Cutoff ~100 Hz
    noise_low = np.convolve(noise, np.ones(low_filter)/low_filter, mode='same') * 0.5
    
    # Mid-frequency noise (crunch)
    mid_filter = int(sample_rate / 500)  # Cutoff ~500 Hz
    noise_mid = np.convolve(noise, np.ones(mid_filter)/mid_filter, mode='same') * 0.3
    
    # High-frequency noise (crack)
    noise_high = noise * 0.2
    
    # Mix all components
    signal = rumble + sub_bass + noise_low + noise_mid + noise_high
    
    # Envelope - fast attack, long decay with tail
    attack_time = 0.05  # 50ms attack
    sustain_time = 0.2  # 200ms sustain
    decay_time = duration - attack_time - sustain_time
    
    attack_samples = int(attack_time * sample_rate)
    sustain_samples = int(sustain_time * sample_rate)
    envelope = np.ones(len(t))
    
    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
    
    sustain_end = attack_samples + sustain_samples
    if sustain_end < len(t):
        envelope[sustain_end:] = np.exp(-3 * t[sustain_end:] / decay_time)
    
    # Apply envelope
    signal = signal * envelope
    
    # Add random variations for realism
    # Fluctuate the amplitude slightly
    amplitude_mod = 0.9 + 0.1 * np.sin(2 * np.pi * 10 * t)
    signal = signal * amplitude_mod
    
    # Normalize to prevent clipping
    signal = signal / np.max(np.abs(signal)) * volume
    
    # Soft clipping for natural limiting
    signal = np.tanh(signal * 1.5) / np.tanh(1.5)
    
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
    
    print(f"Explosion saved to {output_file}")

if __name__ == "__main__":
    generate_explosion_wav()
