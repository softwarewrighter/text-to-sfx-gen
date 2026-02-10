import numpy as np
import wave
import struct
import math

def generate_thud_wav(output_file='thud.wav', duration=0.3, sample_rate=44100, volume=0.7):
    """
    Generate a thud sound effect and save as WAV file.
    
    A thud is a dull, heavy impact sound created by combining:
    - Low frequency oscillator (around 60-100 Hz)
    - Low-pass filtered noise for body
    - Fast attack amplitude envelope
    - Medium decay
    
    Args:
        output_file: Path to output WAV file
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        volume: Amplitude scaling (0.0 to 1.0)
    """
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Low frequency oscillator for the "thud" fundamental
    freq = 80  # Hz - low frequency for heavy impact feel
    oscillator = np.sin(2 * np.pi * freq * t) * 0.5
    
    # Add some low-frequency noise for body/texture
    noise = np.random.normal(0, 1, len(t))
    
    # Simple low-pass filter for noise (moving average)
    filter_window = int(sample_rate / 50)  # Filters above ~50 Hz
    noise_filtered = np.convolve(noise, np.ones(filter_window)/filter_window, mode='same')
    
    # Mix oscillator and noise
    signal = oscillator * 0.6 + noise_filtered * 0.4
    
    # Amplitude envelope - fast attack, medium decay
    attack_time = 0.005  # 5ms attack
    decay_time = duration - attack_time
    
    attack_samples = int(attack_time * sample_rate)
    envelope = np.ones(len(t))
    
    # Linear attack
    envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
    
    # Exponential decay
    decay_start = attack_samples
    decay_curve = np.exp(-4 * t[decay_start:] / decay_time)
    envelope[decay_start:] = decay_curve
    
    # Apply envelope and volume
    signal = signal * envelope * volume
    
    # Normalize to prevent clipping
    signal = signal / np.max(np.abs(signal)) * volume
    
    # Convert to 16-bit PCM
    samples = (signal * 32767).astype(np.int16)
    
    # Write WAV file
    with wave.open(output_file, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes (16-bit)
        wav_file.setframerate(sample_rate)
        
        for sample in samples:
            wav_file.writeframes(struct.pack('<h', sample))
    
    print(f"Thud sound saved to {output_file}")

if __name__ == "__main__":
    generate_thud_wav()
