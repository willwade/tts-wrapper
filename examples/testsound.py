import numpy as np
import sounddevice as sd

def play_sine_wave(frequency=440, duration=2, sample_rate=16000):
    """Play a sine wave with the given frequency and duration."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    sine_wave = 0.5 * np.sin(2 * np.pi * frequency * t).astype(np.float32)

    print(f"Playing {frequency}Hz sine wave for {duration} seconds...")
    sd.play(sine_wave, samplerate=sample_rate)
    sd.wait()  # Wait until the sound has finished playing
    print("Playback finished.")

if __name__ == "__main__":
    # Test playback with a 440Hz sine wave (A4 note) for 2 seconds
    play_sine_wave(frequency=440, duration=2, sample_rate=16000)