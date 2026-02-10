import sounddevice as sd
import numpy as np

def play_3d_audio(filename):
    """
    Play a WAV file with 3D spatial positioning using headphones.
    
    The WAV file should already contain stereo channels with proper
    panning and distance attenuation baked in.
    
    Args:
        filename: Path to WAV file to play
    """
    import wave
    
    # Read the WAV file
    with wave.open(filename, 'r') as wav_file:
        num_channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        sample_rate = wav_file.getframerate()
        num_frames = wav_file.getnframes()
        
        # Read audio data
        frames = wav_file.readframes(num_frames)
        
    # Convert to numpy array
    if sample_width == 2:  # 16-bit
        dtype = np.int16
    elif sample_width == 4:  # 32-bit
        dtype = np.int32
    else:
        raise ValueError(f"Unsupported sample width: {sample_width}")
    
    # Convert bytes to numpy array
    audio_data = np.frombuffer(frames, dtype=dtype)
    
    # Normalize to float32 range [-1, 1]
    audio_data = audio_data.astype(np.float32) / np.iinfo(dtype).max
    
    # Reshape for stereo if needed
    if num_channels == 2:
        audio_data = audio_data.reshape(-1, 2)
    
    # Play the audio
    print(f"Playing {filename} (3D positioning encoded in stereo channels)")
    print("For best 3D effect, use headphones")
    sd.play(audio_data, sample_rate)
    sd.wait()
    print("Playback complete")

if __name__ == "__main__":
    play_3d_audio('gravel_footsteps.wav')
