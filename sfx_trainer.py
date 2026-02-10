#!/usr/bin/env python3
import numpy as np
import wave
import struct
import os
import subprocess
import shutil
from typing import Callable

class SoundTrainer:
    """
    Interactive SFX trainer - generates batch of 4 attempts upfront.
    User picks best from pre-generated options.
    Analogous to human training: iterate with feedback until satisfied.
    """
    
    def __init__(self):
        self.sample_rate = 44100
        self.volume = 0.7
        self.attempts_dir = "attempts"
        os.makedirs(self.attempts_dir, exist_ok=True)
    
    def generate_batch(self, generator_func: Callable, num_attempts: int = 4, base_params: dict = None) -> list:
        """
        Generate a batch of sound attempts at once.
        
        Returns list of file paths for generated attempts.
        """
        t = np.linspace(0, base_params['duration'], int(self.sample_rate * base_params['duration']), False)
        files = []
        
        # Generate dramatic variations for each attempt
        for attempt_num in range(1, num_attempts + 1):
            # Create diverse parameters for each attempt
            params = base_params.copy()
            
            if attempt_num == 1:
                # Base parameters - unchanged
                pass
            elif attempt_num == 2:
                # Attempt 2: Shorter duration, higher frequency
                params['duration'] = max(1.0, base_params['duration'] * 0.7)
                for key, value in params.items():
                    if isinstance(value, (int, float)) and 'freq' in key:
                        params[key] = value * 1.3  # +30% higher
            elif attempt_num == 3:
                # Attempt 3: Longer duration, lower frequency
                params['duration'] = base_params['duration'] * 1.3
                for key, value in params.items():
                    if isinstance(value, (int, float)) and 'freq' in key:
                        params[key] = value * 0.7  # -30% lower
            elif attempt_num == 4:
                # Attempt 4: Mixed dramatic changes
                params['duration'] = max(1.0, base_params['duration'] * 0.8)  # Different duration
                for key, value in params.items():
                    if isinstance(value, (int, float)) and 'freq' in key:
                        params[key] = value * (0.5 + np.random.random() * 1.0)  # ±50% random
            
            # Generate sound
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
            
            files.append(output_file)
        
        return files
    
    def play_batch(self, files: list, descriptions: list):
        """
        Play all audio files in the batch.
        """
        print(f"\n{'='*60}")
        print("🎧 Playing all {len(files)} attempts...")
        print(f"{'='*60}")
        
        for i, (file_path, desc) in enumerate(zip(files, descriptions)):
            print(f"\n[{i+1}/{len(files)}] {desc}")
            print(f"   File: {file_path}")
            print("   Playing now...\n")
            
            try:
                subprocess.run(['afplay', file_path], check=True)
            except FileNotFoundError:
                print("   Error: afplay not found (macOS). Install with: brew install sox")
            except Exception as e:
                print(f"   Error playing audio: {e}")
    
    def get_user_choice(self, files: list, descriptions: list) -> int:
        """
        Get user's choice from a batch.
        """
        print("\n" + "="*60)
        print("Which version sounds best?")
        print("="*60)
        
        for i, desc in enumerate(descriptions):
            print(f"[{i}] {desc}")
        
        print("[r] Regenerate batch with parameter tweaks")
        print("[q] Quit\n")
        
        while True:
            choice = input("Enter choice (0-{}, r, or q): ".format(len(files)-1)).strip().lower()
            
            if choice == 'q':
                return -1  # Quit signal
            
            if choice == 'r':
                return 0  # Regenerate signal
            
            try:
                return int(choice)
            except ValueError:
                print("Please enter a valid number")
    
    def apply_tweaks(self, base_params: dict) -> dict:
        """
        Ask user for parameter tweaks.
        """
        print("\n" + "-"*60)
        print("🔧 Parameter Tweaks")
        print("-"*60)
        print("\nAdjust parameters (leave blank to keep current value):")
        
        tweaked_params = base_params.copy()
        
        for key, value in base_params.items():
            if isinstance(value, (int, float)):
                if 'freq' in key:
                    prompt = f"{key} (Hz, current: {value:.1f}): "
                elif 'duration' in key:
                    prompt = f"{key} (seconds, current: {value:.1f}): "
                elif 'cutoff' in key:
                    prompt = f"{key} (Hz, current: {value:.1f}): "
                else:
                    continue  # Skip non-numeric params
                
                user_input = input(prompt).strip()
                if user_input:
                    try:
                        new_value = float(user_input)
                        if new_value > 0:
                            tweaked_params[key] = new_value
                            print(f"  ✓ Set {key} to {new_value:.1f}")
                    except ValueError:
                        print(f"   Invalid value, keeping {value}")
        
        return tweaked_params
    
    def train_sound(self, sound_name: str, generator_func: Callable, 
                   base_params: dict):
        """
        Training loop for a single sound effect.
        
        Args:
            sound_name: Name of sound effect (e.g., "Door creak")
            generator_func: Function that generates audio from parameters
            base_params: Starting parameters for generation
        """
        print(f"\n{'='*60}")
        print(f"🎯 Training: {sound_name}")
        print(f"{'='*60}")
        
        # Descriptions for 4 systematic attempts
        descriptions = [
            "Base parameters",
            "Higher frequency & cutoff",
            "Lower frequency & cutoff",
            "Mixed variation"
        ]
        
        while True:
            # Generate batch of 4 attempts
            print("\n📦 Generating batch of 4 attempts...")
            files = self.generate_batch(generator_func, 4, base_params)
            
            # Play all attempts
            descriptions = [
                "Base parameters",
                "Higher frequency & cutoff",
                "Lower frequency & cutoff",
                "Mixed variation"
            ]
            self.play_batch(files, descriptions)
            
            # Get user's choice
            print(f"\n{'='*60}")
            choice = self.get_user_choice(files, descriptions)
            print(f"{'='*60}")
            
            if choice == -1:
                # User wants to quit
                print("\n👋 Training stopped")
                break
            
            elif choice == 0:
                # User selected an attempt
                selected_file = files[choice]
                selected_desc = descriptions[choice]
                
                print(f"\n✅ Selected: {selected_desc}")
                print(f"💾 Saving final version...")
                
                # Save as final
                final_file = os.path.join(self.attempts_dir, f"{sound_name.replace(' ', '_')}_final.wav")
                shutil.copy2(selected_file, final_file)
                
                print(f"✅ Saved final: {final_file}")
                
                # Copy to project root
                project_root_final = os.path.join("..", f"{sound_name.replace(' ', '_')}_final.wav")
                shutil.copy2(selected_file, project_root_final)
                
                print(f"✅ Also saved to: {project_root_final}")
                
                # Show what parameters were used
                print(f"\n📊 Final parameters used:")
                for key, value in base_params.items():
                    if isinstance(value, (int, float)):
                        print(f"   {key}: {value}")
                
                break
            
            else:
                # User wants to regenerate with parameter tweaks
                print("\n🔄 Regenerating with your tweaks...")
                base_params = self.apply_tweaks(base_params)
        
        print(f"\n✨ Training complete for: {sound_name}")
        return base_params


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
    friction_mod = 0.5 + 0.3 * np.sin(2 * np.pi * 0.4 * t)
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
    sweep_noise = 1.0 + 0.1 * np.sin(2 * np.pi * 15 * t)
    
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
        timing_variation = (np.random.random() - 0.5) * 0.3
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


def main():
    """Main training loop."""
    trainer = SoundTrainer()
    
    print("="*60)
    print("🎵 Interactive SFX Trainer")
    print("="*60)
    print("This app generates 4 attempts upfront,")
    print("then lets you pick the best version. Analogous to human training.")
    print("\nAvailable sound effects:")
    print(" [1] Door creak")
    print(" [2] Siren (US wail)")
    print(" [3] Gravel footsteps")
    print(" [q] Quit")
    print("="*60)
    
    while True:
        choice = input("\nSelect sound effect to train (1-3, or q): ").strip().lower()
        
        if choice == 'q':
            print("\n👋 Goodbye!")
            break
        
        if choice == '1':
            # Door creak training
            base_params = {
                'duration': 5.0,
                'base_freq': 400,
                'cutoff': 2500
            }
            
            trainer.train_sound(
                "Door creak",
                generate_door_creak,
                base_params
            )
        
        elif choice == '2':
            # Siren training
            base_params = {
                'duration': 5.0,
                'base_low': 800,
                'base_high': 1200,
                'wail_speed': 2.5,
                'cutoff': 4000
            }
            
            trainer.train_sound(
                "Siren (US wail)",
                generate_siren_wail,
                base_params
            )
        
        elif choice == '3':
            # Gravel footsteps training
            base_params = {
                'duration': 6.0,
                'steps_per_second': 2.0,
                'step_duration': 0.2,
                'cutoff': 1500
            }
            
            trainer.train_sound(
                "Gravel footsteps",
                generate_gravel_footsteps,
                base_params
            )
        
        else:
            print("Please enter 1, 2, 3, or q")


if __name__ == "__main__":
    main()
