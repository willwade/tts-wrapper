from abc import ABC, abstractmethod
from typing import Any, List, Literal, Optional, Union, Dict
import pyaudio
import threading
import time

FileFormat = Union[Literal["wav"], Literal["mp3"]]

class AbstractTTS(ABC):
    """Abstract class (ABC) for text-to-speech functionalities, including synthesis and playback."""

    def __init__(self):
        self.voice_id = None
        self.audio_object = None
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.audio_bytes = None
        self.playing = False
        self.position = 0  # Position in the byte stream
        self.timings = []
        self.timers = []

    @abstractmethod
    def get_voices(self) -> List[Dict[str, Any]]:
        """Retrieves a list of available voices from the TTS service."""
        pass

    def set_voice(self, voice_id: str):
        """
        Sets the voice by its ID.

        @param voice_id: The ID of the voice to be used for synthesis.
        """
        self.voice_id = voice_id
        
    @classmethod
    @abstractmethod
    def supported_formats(cls) -> List[FileFormat]:
        """Returns list of supported audio types in concrete text-to-speech classes."""
        pass

    @abstractmethod
    def synth_to_bytes(self, text: Any, format: FileFormat) -> bytes:
        """
        Transforms written text to audio bytes on supported formats.

        @param text: Text to be transformed into audio bytes
        @param format: File format to be used when transforming to audio bytes, if supported
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

    def setup_stream(self, format=pyaudio.paInt16, channels=1, rate=22050):
        """
        Configures and opens an audio stream with specified format settings.
        
        @param format: The sample format (default is 16-bit PCM).
        @param channels: Number of audio channels (default is 1 for mono).
        @param rate: Sampling rate in Hz (default is 22050 Hz).
        """
        self.stream = self.p.open(format=format,
                                  channels=channels,
                                  rate=rate,
                                  output=True,
                                  stream_callback=self.callback)

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
            data = self.audio_bytes[self.position:self.position + frame_count]
            self.position += len(data)
            return (data, pyaudio.paContinue)
        else:
            return (None, pyaudio.paContinue)

    def play_audio(self, audio_bytes: bytes):
        """
        Starts playback of audio data.

        @param audio_bytes: Byte array containing audio data to be played.
        """
        self.audio_bytes = audio_bytes
        self.position = 0
        self.playing = True
        if not self.stream:
            self.setup_stream()
        self.stream.start_stream()

    def pause_audio(self):
        """Pauses the audio playback."""
        self.playing = False

    def resume_audio(self):
        """Resumes the paused audio playback."""
        self.playing = True

    def stop_audio(self):
        """Stops the audio stream and cleans up any active timers."""
        if self.stream:
            self.stream.stop_stream()
        self.playing = False
        for timer in self.timers:
            timer.cancel()
        self.timers = []

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
        print(f"Word spoken: {word}")

    def start_playback_with_callbacks(self, audio_data: bytes):
        """
        Plays back audio with callbacks triggered based on predefined timings.

        @param audio_data: Byte array containing audio data.
        """        
        self.play_audio(audio_data)
        start_time = time.time()
        for word, timing in self.timings:
            delay = timing - (time.time() - start_time)
            if delay > 0:
                timer = threading.Timer(delay, self.on_word_callback, args=(word,))
                timer.start()
                self.timers.append(timer)

    def __del__(self):
        """Cleans up resources upon deletion of the instance."""
        if self.stream:
            self.stream.close()
        self.p.terminate()