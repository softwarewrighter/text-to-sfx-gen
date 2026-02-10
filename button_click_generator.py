import numpy as np
import wave
import struct

def generate_button_click_wav(output_file='button_click.wav', duration=0.05, sample_rate=44100, volume=0.7):
    """
    Generate a button click sound effect and save as WAV file.
    
    A button click is created by:
    - Very short duration
    - High-frequency components (2-5 kHz)
    - Sharp attack, immediate decay
    - Mix of sine wave and filtered noise
    - Quick envelope
    
    Args:
        output_file: Path to output WAV file
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        volume: Amplitude scaling (0.0 to 1.0)
    """
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # High-frequency sine wave for the "click"
    freq = 3000  # Hz
    sine = np.sin(2 * np.pi * freq * t) * 0.6
    
    # Add higher harmonic for brightness
    sine += 0.3 * np.sin(2 * np.pi * freq * 2 * t)
    
    # Add high-frequency noise for texture
    noise = np.random.normal(0, 1, len(t))
    
    # Light low-pass filtering to soften slightly
    filter_size = int(sample_rate / 8000)  # Cutoff ~8kHz
    noise_filtered = np.convolve(noise, np.ones(filter_size)/filter_size, mode='same')
    
    # Mix sine and noise
    signal = sine + noise_filtered * 0.2
    
    # Envelope - instant attack, very fast decay
    attack_time = 0.001  # 1ms attack
    decay_time = duration - attack_time
    
    attack_samples = int(attack_time * sample_rate)
    envelope = np.ones(len(t))
    
    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
    
    decay_curve = np.exp(-10 * t[attack_samples:] / decay_time)
    envelope[attack_samples:] = decay_curve
    
    # Apply envelope and volume
    signal = signal * envelope * volume
    
    # Normalize to prevent clipping
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
    
    print(f"Button click saved to {output_file}")

if __name__ == "__main__":
    generate_button_click_wav()
