#!/usr/bin/env python3
import numpy as np
import wave
import struct
import os
import subprocess
from typing import Callable

class SoundTrainer:
    """
    Interactive SFX trainer - generates sound, asks questions, refines based on answers.
    """
    
    def __init__(self):
        self.sample_rate = 44100
        self.volume = 0.7
        self.attempts_dir = "attempts"
        os.makedirs(self.attempts_dir, exist_ok=True)
    
    def generate_sound(self, generator_func: Callable, params: dict, attempt_num: int) -> str:
        """Generate a single attempt WAV file."""
        t = np.linspace(0, params['duration'], int(self.sample_rate * params['duration']), False)
        
        signal = generator_func(t, params, self.sample_rate)
        
        # Normalize and apply volume
        signal = signal / np.max(np.abs(signal)) * self.volume
        
        # Low-pass filter for smoothness
        lp_filter_size = int(self.sample_rate / params.get('cutoff', 3000))
        signal = np.convolve(signal, np.ones(lp_filter_size)/lp_filter_size, mode='same')
        
        # Normalize after filtering
        signal = signal / np.max(np.abs(signal)) * self.volume
        
        # Convert to 16-bit PCM
        samples = (signal * 32767).astype(np.int16)
        
        # Create stereo
        output_file = os.path.join(self.attempts_dir, f"attempt_{attempt_num:02d}.wav")
        with wave.open(output_file, 'w') as wav_file:
            wav_file.setnchannels(2)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            for sample in samples:
                wav_file.writeframes(struct.pack('<hh', sample, sample))
        
        return output_file
    
    def play_audio(self, file_path: str, description: str):
        """Play an audio file and show description."""
        print(f"\n🔊 Playing: {description}")
        print(f"   File: {file_path}")
        print("   Listen carefully...")
        
        try:
            subprocess.run(['afplay', file_path], check=True)
        except FileNotFoundError:
            print("   Error: afplay not found (macOS). Install with: brew install sox")
        except Exception as e:
            print(f"   Error playing audio: {e}")
    
    def get_user_choice(self, attempt1_desc: str, attempt2_desc: str) -> int:
        """Get user feedback on which attempt is better."""
        print("\n" + "="*60)
        print("Which version sounds better?")
        print("="*60)
        print(f"[0] {attempt1_desc}")
        print(f"[1] {attempt2_desc}")
        print("[2] Keep trying - generate more variations")
        print("="*60)
        
        while True:
            choice = input("\nEnter choice (0, 1, or 2): ").strip()
            
            if choice in ['0', '1', '2']:
                return int(choice)
            print("Please enter 0, 1, or 2")
    
    def train_sound(self, sound_name: str, generator_func: Callable, 
                   base_params: dict):
        """
        Training loop for a single sound effect.
        """
        print(f"\n" + "="*60)
        print(f"🎯 Training: {sound_name}")
        print("="*60)
        
        # Track best iteration
        best_params = base_params.copy()
        iteration = 1
        
        while True:
            iteration += 1
            
            # Generate two attempts
            print(f"\n--- Generating attempt {iteration} ---")
            file1 = self.generate_sound(generator_func, best_params, iteration * 2 - 1)
            file2 = self.generate_sound(generator_func, best_params, iteration * 2)
            
            # Create descriptions
            desc1 = f"Attempt {iteration}A - Current best"
            desc2 = f"Attempt {iteration}B - Proposed improvement"
            
            # Play both attempts
            self.play_audio(file1, desc1)
            self.play_audio(file2, desc2)
            
            # Get user feedback
            choice = self.get_user_choice(desc1, desc2)
            
            if choice == 0:
                # User chose current best
                print(f"\n✅ Keeping current best: {desc1}")
                best_params = base_params.copy()
                # Save as final
                final_file = os.path.join(self.attempts_dir, f"{sound_name.replace(' ', '_')}_final.wav")
                os.rename(file1, final_file)
                print(f"💾 Saved final: {final_file}")
                break
            elif choice == 1:
                # User chose proposed improvement
                print(f"\n✅ Accepting improvement: {desc2}")
                best_params = best_params.copy()
                # Save as final
                final_file = os.path.join(self.attempts_dir, f"{sound_name.replace(' ', '_')}_final.wav")
                os.rename(file2, final_file)
                print(f"💾 Saved final: {final_file}")
                break
            else:
                # Keep trying - generate new parameters
                print(f"\n🔄 Keep trying - generating new variations...")
                # For now, randomly vary parameters between attempt1 and attempt2
                import random
                new_params = {}
                for key in best_params.keys():
                    if isinstance(best_params[key], (int, float)):
                        val1 = best_params[key]
                        val2 = best_params[key]
                        mid = (val1 + val2) / 2
                        # Add some randomness
                        variation = (mid - val1) * random.uniform(-0.3, 0.3)
                        new_params[key] = mid + variation
                    else:
                        new_params[key] = best_params[key]
                
                best_params = new_params
        
        print(f"\n✨ Training complete for: {sound_name}")
        return best_params


# Sound generator functions
def generate_door_creak(t, params, sample_rate):
    """Generate door creak sound."""
    base_freq = params['base_freq']
    
    # Slow, irregular pitch modulation
    slow_wobble1 = 0.7 * np.sin(2 * np.pi * 0.12 * t)
    slow_wobble2 = 0.5 * np.sin(2 * np.pi * 0.3 * t)
    slow_wobble3 = 0.4 * np.sin(2 * np.pi * 0.6 * t)
    
    freq_modulation = base_freq * (1 + 0.6 * (slow_wobble1 + slow_wobble2 + slow_wobble3))
    
    # Add sticking points
    num_sticks = int(params['duration'] * 1.5)
    for i in range(num_sticks):
        stick_pos = int(np.random.random() * len(t))
        stick_duration = int(sample_rate * 0.08)
        freq_change = np.random.uniform(-200, 200)
        stick_end = min(stick_pos + stick_duration, len(t))
        freq_modulation[stick_pos:stick_end] += freq_change
    
    # Generate oscillator
    phase = 2 * np.pi * np.cumsum(freq_modulation) / sample_rate
    oscillator = np.sin(phase) * 0.6
    
    # Add filtered noise
    noise = np.random.normal(0, 1, len(t))
    low_filter = int(sample_rate / 2000)
    high_filter = int(sample_rate / 800)
    noise_lp = np.convolve(noise, np.ones(low_filter)/low_filter, mode='same')
    noise_bp = noise_lp - np.convolve(noise_lp, np.ones(high_filter)/high_filter, mode='same')
    friction_mod = 0.5 + 0.3 * np.sin(2 * np.pi * 0.04 * t)
    noise_bp = noise_bp * friction_mod * 0.4
    
    # Sub-harmonic rumble
    rumble_freq = 100
    rumble_phase = 2 * np.pi * np.cumsum(freq_modulation * 0.15) / sample_rate
    rumble = np.sin(rumble_phase) * 0.25
    
    # Mix
    signal = oscillator + noise_bp + rumble
    
    # Envelope
    attack_time = 1.0
    attack_samples = int(attack_time * sample_rate)
    envelope = np.ones(len(t))
    if attack_samples > 0:
        envelope[:attack_samples] = (1 - np.cos(np.pi * t[:attack_samples] / attack_time)) / 2
    
    decay_start = attack_samples
    if len(t[decay_start:]) > 0:
        decay_curve = np.exp(-1.5 * t[decay_start:] / (params['duration'] - attack_time))
        envelope[decay_start:] = decay_curve
    
    amplitude_noise = 0.85 + 0.15 * np.random.normal(0, 1, len(t))
    amplitude_noise = np.convolve(amplitude_noise, np.ones(int(sample_rate/8))/int(sample_rate/8), mode='same')
    envelope = envelope * amplitude_noise
    
    return signal * envelope


def generate_siren_wail(t, params, sample_rate):
    """Generate US wail siren."""
    base_low = params['base_low']
    base_high = params['base_high']
    wail_speed = params['wail_speed']
    
    # Frequency sweep modulation
    modulation = 0.5 * (1 + np.sin(2 * np.pi * wail_speed * t))
    
    # Slight randomness
    sweep_noise = 1.0 + 0.1 * np.sin(2 * np.pi * 10 * t)
    
    freq = (base_low + (base_high - base_low) * modulation) * sweep_noise
    
    # Phase-locked oscillator
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    signal = np.sin(phase) * 0.5
    
    # Add harmonics for grit
    signal += 0.3 * np.sin(3 * phase)
    signal += 0.15 * np.sin(5 * phase)
    
    # Add slight noise
    noise = np.random.normal(0, 0.05, len(t))
    signal += noise
    
    # Tremolo
    tremolo = 1.0 + 0.2 * np.sin(2 * np.pi * 8 * t)
    signal = signal * tremolo
    
    # Quick attack
    attack_time = 0.02
    attack_samples = int(attack_time * sample_rate)
    envelope = np.ones(len(t))
    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
    
    return signal * envelope


def generate_gravel_footsteps(t, params, sample_rate):
    """Generate gravel footsteps."""
    total_samples = len(t)
    left_channel = np.zeros(total_samples)
    right_channel = np.zeros(total_samples)
    
    steps_per_second = params['steps_per_second']
    step_duration = params['step_duration']
    step_samples = int(sample_rate * step_duration)
    
    step_time = 0.5
    step_count = 0
    
    while step_time < params['duration']:
        step_start_sample = int(step_time * sample_rate)
        
        # Generate gravel step
        noise = np.random.normal(0, 1, step_samples)
        
        # Multiple frequency bands
        low_filter = int(sample_rate / 100)
        mid_filter = int(sample_rate / 500)
        noise_low = np.convolve(noise, np.ones(low_filter)/low_filter, mode='same') * 0.4
        noise_mid = np.convolve(noise, np.ones(mid_filter)/mid_filter, mode='same') * 0.3
        noise_high = noise * 0.3
        
        gravel = noise_low + noise_mid + noise_high
        
        # Add transients
        num_impacts = 8 + int(np.random.random() * 8)
        for _ in range(num_impacts):
            impact_pos = int(np.random.random() * step_samples)
            impact_duration = int(sample_rate * 0.002)
            impact_end = min(impact_pos + impact_duration, step_samples)
            impact = np.random.normal(0, 1, impact_end - impact_pos)
            impact_envelope = np.exp(-10 * np.linspace(0, 1, impact_end - impact_pos))
            gravel[impact_pos:impact_end] += impact * 0.8 * impact_envelope
        
        # Envelope for this step
        envelope = np.ones(step_samples)
        attack_samples = int(sample_rate * 0.002)
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Decay - create proper decay for step
        decay_samples = step_samples - attack_samples
        if decay_samples > 0:
            decay_curve = np.exp(-6 * t[attack_samples:] / (step_duration - attack_samples))
            envelope[attack_samples:] = decay_curve
        
        gravel = gravel * envelope
        
        # Intensity variation
        intensity = 0.5 + np.random.random() * 0.5
        
        # Distance attenuation
        distance_factor = 1.0 - (step_time / params['duration']) * 0.8
        
        # Pan position
        pan_position = step_time / params['duration']
        pan_angle = pan_position * (np.pi / 2)
        left_gain = np.cos(pan_angle) * distance_factor * intensity
        right_gain = np.sin(pan_angle) * distance_factor * intensity
        
        end_sample = min(step_start_sample + step_samples, total_samples)
        actual_samples = end_sample - step_start_sample
        left_channel[step_start_sample:end_sample] += gravel[:actual_samples] * left_gain
        right_channel[step_start_sample:end_sample] += gravel[:actual_samples] * right_gain
        
        # Random timing variation
        timing_variation = (np.random.random() - 0.5) * 0.3 * 0.3
        step_time += step_duration + timing_variation
        step_count += 1
    
    # Combine channels
    signal = np.column_stack((left_channel, right_channel))
    
    # Low-pass filter
    lp_filter_size = int(sample_rate / params.get('cutoff', 1500))
    signal = np.convolve(signal, np.ones(lp_filter_size)/lp_filter_size, mode='same')
    
    # Normalize per channel
    for i in range(2):
        signal[:, i] = signal[:, i] / np.max(np.abs(signal[:, i])) * 0.7
    
    return signal.flatten()


if __name__ == "__main__":
    trainer = SoundTrainer()
    
    # Example: Train door creak
    door_creak_params = {
        'duration': 3.0,
        'base_freq': 800,
        'cutoff': 2000
    }
    
    # Example: Train siren wail
    siren_params = {
        'duration': 5.0,
        'base_low': 500,
        'base_high': 900,
        'wail_speed': 2.5
    }
    
    # Example: Train gravel footsteps
    gravel_params = {
        'duration': 6.0,
        'steps_per_second': 2.0,
        'step_duration': 0.5,
        'cutoff': 1500
    }
    
    print("SFX Trainer - Interactive Sound Effect Training")
    print("=" * 60)
    print("Choose a sound to train:")
    print("[1] Door Creak")
    print("[2] Siren Wail")
    print("[3] Gravel Footsteps")
    print("[0] Exit")
    
    choice = input("\nEnter choice: ").strip()
    
    if choice == '1':
        trainer.train_sound("Door Creak", generate_door_creak, door_creak_params)
    elif choice == '2':
        trainer.train_sound("Siren Wail", generate_siren_wail, siren_params)
    elif choice == '3':
        trainer.train_sound("Gravel Footsteps", generate_gravel_footsteps, gravel_params)
    else:
        print("Exiting...")
