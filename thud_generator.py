#!/usr/bin/env python3
import numpy as np
import wave
import struct

def generate_thud_wav(output_file='thud.wav', duration=0.5, sample_rate=44100, volume=0.7, seed=0):
    """
    Generate a "thud" sound effect and save as WAV file.

    A heavy impact is three layers:
    - Click: a 3 ms burst of bright noise (the moment of contact)
    - Body: a sine whose pitch drops quickly from 200 Hz to 80 Hz (like a kick drum)
    - Knock: 200-600 Hz band noise with a short decay, so the thud is audible on
      laptop and phone speakers, which barely reproduce anything below ~150 Hz

    Args:
        output_file: Path to output WAV file
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        volume: Amplitude scaling (0.0 to 1.0)
        seed: Random seed (same seed = same sound)
    """
    rng = np.random.default_rng(seed)
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # Body: pitch drops exponentially from 200 Hz to 80 Hz over ~40 ms
    freq = 80 + 120 * np.exp(-t / 0.04)
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    body = np.sin(phase) * np.exp(-t / 0.08)
    # Soft saturation adds odd harmonics (240 Hz and up) that small speakers can play
    body = np.tanh(3 * body) / np.tanh(3)

    # Knock: band-limited noise (difference of two moving averages ~ 200-600 Hz)
    noise = rng.normal(0, 1, len(t))
    low = np.convolve(noise, np.ones(int(sample_rate / 600)) / int(sample_rate / 600), mode='same')
    lower = np.convolve(noise, np.ones(int(sample_rate / 200)) / int(sample_rate / 200), mode='same')
    knock = (low - lower) * np.exp(-t / 0.05)
    knock = knock / np.max(np.abs(knock))

    # Click: very short bright noise burst at the moment of impact
    click_samples = int(0.003 * sample_rate)
    click = np.zeros(len(t))
    click[:click_samples] = rng.normal(0, 1, click_samples) * np.linspace(1, 0, click_samples)

    # Mix layers
    signal = body * 0.6 + knock * 0.9 + click * 0.15

    # 2 ms fade-in to avoid a DC click at the start
    fade = int(0.002 * sample_rate)
    signal[:fade] *= np.linspace(0, 1, fade)

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
