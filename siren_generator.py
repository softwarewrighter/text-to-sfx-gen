import numpy as np
import wave
import struct

def generate_siren_wav(output_file='siren.wav', duration=2.0, sample_rate=44100, volume=0.7):
    """
    Generate a siren sound effect and save as WAV file.
    
    A siren is created by:
    - Two alternating frequencies (typical: 500-800 Hz and 600-900 Hz)
    - Regular pitch oscillation
    - Multiple harmonics for richness
    - Continuous amplitude
    
    Args:
        output_file: Path to output WAV file
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        volume: Amplitude scaling (0.0 to 1.0)
    """
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Two-tone siren (alternating frequencies)
    low_freq = 500  # Hz
    high_freq = 800  # Hz
    
    # Alternating modulation (typical siren speed: 2-3 Hz)
    siren_speed = 2.5  # Hz
    modulation = 0.5 * (1 + np.sin(2 * np.pi * siren_speed * t))
    
    # Interpolate between frequencies
    freq_modulation = low_freq + (high_freq - low_freq) * modulation
    
    # Generate phase-locked oscillator for smooth transitions
    phase = 2 * np.pi * np.cumsum(freq_modulation) / sample_rate
    oscillator = np.sin(phase) * 0.5
    
    # Add harmonics for fullness
    oscillator += 0.3 * np.sin(2 * phase)
    oscillator += 0.15 * np.sin(3 * phase)
    
    signal = oscillator
    
    # Siren has continuous amplitude (no attack/decay)
    signal = signal * volume
    
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
    
    print(f"Siren saved to {output_file}")

if __name__ == "__main__":
    generate_siren_wav()
