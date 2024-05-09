from abc import ABC, abstractmethod
from typing import Any, List, Literal, Optional, Union, Dict
import pyaudio
import threading
from threading import Event
import logging
import time

FileFormat = Union[Literal["wav"], Literal["mp3"]]

class AbstractTTS(ABC):
    """Abstract class (ABC) for text-to-speech functionalities, including synthesis and playback."""

    def __init__(self):
        self.voice_id = None
        self.audio_object = None
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.audio_rate = 22050
        self.audio_bytes = None
        self.playing = Event()
        self.playing.clear()  # Not playing by default
        self.position = 0  # Position in the byte stream
        self.timings = []
        self.timers = []

    @abstractmethod
    def get_voices(self) -> List[Dict[str, Any]]:
        """Retrieves a list of available voices from the TTS service."""
        pass

    def set_voice(self, voice_id: str, lang: str = "en-US"):
        """
        Sets the voice by its ID and language for synthesis.

        @param voice_id: The ID of the voice to be used for synthesis.
        @param lang: The language code to be used.
        """
        self.voice_id = voice_id
        self.lang = lang

        
    @classmethod
    @abstractmethod
    def supported_formats(cls) -> List[FileFormat]:
        """Returns list of supported audio types in concrete text-to-speech classes."""
        pass

    @abstractmethod
    def synth_to_bytes(self, text: Any, format: Optional[FileFormat] = "wav") -> bytes:

        """
        Transforms written text to audio bytes on supported formats.

        @param text: Text to be transformed into audio bytes
        @param format: File format to be used when transforming to audio bytes, defaults to 'wav'
        @returns: audio bytes created
        @raises UnsupportedFileFormat: if file format is not supported
        """
        pass

    def synth_to_file(self, text: Any, filename: str, format: Optional[FileFormat] = None) -> None:
        """
        Transforms written text to an audio file and saves on disk.

        @param text: Text to be transformed to audio file
        @param filename: Name of the file to be saved on disk
        @param format: File format to be used when transforming to audio file. Defaults to None.
        """
        audio_content = self.synth_to_bytes(text, format=format or "wav")
        with open(filename, "wb") as file:
            file.write(audio_content)

    def synth(self, text: str, filename: str, format: Optional[FileFormat] = "wav"):
        """
        Synthesizes text to speech and directly saves it to a file. Alias
        """
        self.synth_to_file(text,filename,format)

    def speak(self, text: Any, format: Optional[FileFormat] = "wav") -> bytes:
        """
        Directly plays audio data without using streaming.
        """
        try:
            audio_bytes = self.synth_to_bytes(text,format)
            #lets fade in
            audio_bytes = self.apply_fade_in(audio_bytes)
            # Initialize PyAudio and open a stream
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=self.audio_rate, output=True)
            # Play the entire byte array
            stream.write(audio_bytes)
            # Cleanup
            stream.stop_stream()
            stream.close()
            p.terminate()
        except Exception as e:
            logging(f"Error playing audio: {e}")
            
            
    def setup_stream(self, format=pyaudio.paInt16, channels=1):
        """
        Configures and opens an audio stream with specified format settings.
        
        @param format: The sample format (default is 16-bit PCM).
        @param channels: Number of audio channels (default is 1 for mono).
        @param rate: Sampling rate in Hz (default is 22050 Hz).
        """
        try:
            if self.p is None:
                self.p = pyaudio.PyAudio()
            if self.stream is not None:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            self.stream = self.p.open(format=format,
                                      channels=channels,
                                      rate=self.audio_rate,
                                      output=True,
                                      stream_callback=self.callback)
        except Exception as e:
            logging(f"Failed to setup audio stream: {e}")
            raise



    def callback(self, in_data, frame_count, time_info, status):
        """
        Callback function for PyAudio stream to handle audio playback.

        @param in_data: Input data for the stream, not used in output-only mode.
        @param frame_count: Number of frames per buffer.
        @param time_info: Dictionary with timing information.
        @param status: Status flags.
        @return: A tuple containing the chunk of data to be played and a flag indicating whether to continue.
        """
        if self.playing:
            end_position = self.position + frame_count * 2  # *2 because each frame for 16-bit audio is 2 bytes
            data = self.audio_bytes[self.position:end_position]
            self.position = end_position
            if self.position >= len(self.audio_bytes):
                return (data, pyaudio.paComplete)  # Signal end of buffer
            return (data, pyaudio.paContinue)
        else:
            return (None, pyaudio.paContinue)
    
    
    def speak_streamed(self, text: Any, format: Optional[FileFormat] = "wav"):
        """
        Starts playback of audio data.
        """
        try:
            audio_bytes = self.synth_to_bytes(text, format)
        except Exception as e:
            logging.error(f"Error synthesizing speech: {e}")
        self.audio_bytes = self.apply_fade_in(audio_bytes)
        self.position = 0
        self.playing.set()
        if not self.stream:
            self.setup_stream()
        try:
            # Use a thread to handle playback
            self.play_thread = threading.Thread(target=self._start_stream)
            self.play_thread.start()
        except Exception as e:
            logging(f"Failed to play audio: {e}")
            raise  # Correct placement of raise within the except block

    def apply_fade_in(self, audio_bytes, fade_duration_ms=50, sample_rate=22050):
        """
        Applies a fade-in effect to the start of the audio bytes.
        `fade_duration_ms` in milliseconds, `sample_rate` in Hz.
        """
        num_fade_samples = int(fade_duration_ms * sample_rate / 1000)
        fade_in = [i / num_fade_samples for i in range(num_fade_samples)]
    
        # Convert byte data to a list of samples (16-bit signed integers)
        audio_samples = list(int.from_bytes(audio_bytes[2 * i:2 * i + 2], 'little', signed=True)
                             for i in range(len(audio_bytes) // 2))
    
        # Apply fade-in by multiplying samples by corresponding fade-in factor
        for i in range(min(len(audio_samples), num_fade_samples)):
            audio_samples[i] = int(audio_samples[i] * fade_in[i])
    
        # Convert samples back to byte data
        faded_audio_bytes = b''.join((sample.to_bytes(2, 'little', signed=True) for sample in audio_samples))
        return faded_audio_bytes

        
    def _start_stream(self):
        """
        Starts the stream and waits for it to finish in a thread.
        """
        if self.stream:
            self.stream.start_stream()
        while self.stream.is_active() and self.playing.is_set():
            time.sleep(0.1)
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def pause_audio(self):
        """Pauses the audio playback."""
        self.playing.clear()

    def resume_audio(self):
        """Resumes the paused audio playback."""
        self.playing.set()  # Set the playing event to resume
        if not self.stream:
            self.setup_stream()
        if self.stream and not self.stream.is_active():
            self.stream.start_stream()

    def stop_audio(self):
        """
        Explicitly stops the audio playback and ensures all resources are released.
        """
        self.playing.clear()  # Signal to stop playback
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join()  # Wait for the playback thread to finish
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        for timer in self.timers:
            timer.cancel()
        self.timers.clear()

    def set_timings(self, timing_data):
        """
        Sets the timing data for triggering callbacks during audio playback.

        @param timing_data: List of timing information for words or sounds in the audio.
        """
        self.timings = timing_data

    def on_word_callback(self, word):
        """
        Callback function that is called when a word is spoken.

        @param word: The word that was spoken.
        """        
        logging(f"Word spoken: {word}")

    def start_playback_with_callbacks(self, audio_data: bytes):
        """
        Plays back audio with callbacks triggered based on predefined timings.

        @param audio_data: Byte array containing audio data.
        """        
        self.speak_streamed(audio_data)
        start_time = time.time()
        for word, timing in self.timings:
            delay = timing - (time.time() - start_time)
            if delay > 0:
                timer = threading.Timer(delay, self.on_word_callback, args=(word,))
                timer.start()
                self.timers.append(timer)
                
    def finish(self):
        try:
            if self.stream and not self.stream.is_stopped():
                self.stream.stop_stream()
            if self.stream:
                self.stream.close()
            if self.p:
                self.p.terminate()
        except Exception as e:
            logging(f"Failed to clean up audio resources: {e}")
        finally:
            self.stream = None
            self.p = None
            

    def __del__(self):
        """Cleans up resources upon deletion of the instance."""
        # Safely check and close the stream
        self.finish()

