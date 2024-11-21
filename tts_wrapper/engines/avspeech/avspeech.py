from typing import Any, Generator, List, Dict, Tuple
from queue import Queue
import threading
import logging
from AVFoundation import (
    AVAudioEngine,
    AVAudioFormat,
    AVAudioFrameCount,
    AVSpeechSynthesizer,
    AVSpeechUtterance,
    AVSpeechUtteranceDefaultSpeechRate,
    AVSpeechSynthesisVoice,
)
from tts_wrapper.tts import AbstractTTS
from tts_wrapper.engines.avspeech.client import AVSpeechClient

class AVSpeechTTS(AbstractTTS):
    """High-level TTS interface for AVSpeech."""

    def __init__(self, client: AVSpeechClient):
        super().__init__()
        self._client = client
        self._tts = AVSpeechSynthesizer.alloc().init()
        self._tts.setDelegate_(self)
        self._voice = AVSpeechSynthesisVoice.voiceWithIdentifier_("com.apple.voice.compact.en-US.Samantha")
        self._rate = AVSpeechUtteranceDefaultSpeechRate
        self._volume = 1.0
        self._audio_queue = Queue()
        self._is_speaking = threading.Event()
        self.word_timings: List[Dict[str, Any]] = []  # Store word timing data
        logging.debug("AVSpeechTTS initialized")

    def synth_to_bytes(self, text: Any) -> bytes:
        """
        Synthesize text to audio bytes.

        This implementation intercepts audio output using AVAudioEngine
        to record the synthesized audio to a byte buffer.
        """
        logging.debug("Synthesizing text to bytes.")
        engine = AVAudioEngine()
        output_node = engine.outputNode
        pcm_buffer = bytearray()

        # Define a default AVAudioFormat (e.g., 44.1kHz, 2 channels, interleaved)
        audio_format = AVAudioFormat.alloc().initWithCommonFormat_sampleRate_channels_interleaved_(
            1, 44100.0, 2, True
        )

        def audio_capture_callback(_, buffer, when):
            """Capture audio data into the PCM buffer."""
            audio_data = buffer.audioBufferList().mBuffers[0].mData
            audio_length = buffer.audioBufferList().mBuffers[0].mDataByteSize
            pcm_buffer.extend(audio_data[:audio_length])

        # Install tap to capture audio from the output node
        output_node.installTapOnBus_bufferSize_format_block_(
            0, AVAudioFrameCount(1024), audio_format, audio_capture_callback
        )

        # Configure and speak text
        utterance = AVSpeechUtterance.speechUtteranceWithString_(text)
        utterance.setVoice_(self._voice)
        utterance.setRate_(self._rate)
        utterance.setVolume_(self._volume)

        # Start engine and speech synthesis
        engine.prepare()
        error = engine.startAndReturnError_(None)
        if error:
            raise RuntimeError(f"Failed to start AVAudioEngine: {error}")

        self._tts.speakUtterance_(utterance)

        # Wait for the utterance to finish
        while self._tts.isSpeaking():
            pass

        # Clean up
        engine.stop()
        output_node.removeTapOnBus_(0)

        return bytes(pcm_buffer)

    def synth_to_bytestream(
        self, text: Any, format: str | None = "wav"
    ) -> Generator[bytes, None, None]:
        logging.debug("Synthesizing text to bytestream.")
        self.generated_audio = bytearray()
        self.word_timings = []

        utterance = AVSpeechUtterance.speechUtteranceWithString_(text)
        utterance.setVoice_(self._voice)
        utterance.setRate_(self._rate)
        utterance.setVolume_(self._volume)

        self._is_speaking.set()
        threading.Thread(target=self._speak_async, args=(utterance,)).start()

        while self._is_speaking.is_set() or not self._audio_queue.empty():
            try:
                chunk = self._audio_queue.get(timeout=0.1)
                self.generated_audio.extend(chunk)
                yield chunk
            except:
                pass  # Wait for more chunks

        if self.on_end:
            self.on_end()
        self.set_timings(self._process_word_timings(self.word_timings, text))

    def _speak_async(self, utterance: AVSpeechUtterance) -> None:
        """Speak the utterance asynchronously."""
        self._tts.speakUtterance_(utterance)
        while self._tts.isSpeaking():
            pass
        self._is_speaking.clear()

    def _process_word_timings(
        self, word_timings: List[Dict[str, Any]], input_text: str
    ) -> List[Tuple[float, float, str]]:
        """Processes word timings into (start_time, end_time, word) format."""
        processed_timings = []
        for i, timing in enumerate(word_timings):
            start_time = timing["start_time"]
            end_time = (
                word_timings[i + 1]["start_time"] if i + 1 < len(word_timings) else None
            )
            word = timing["word"]
            processed_timings.append((start_time, end_time, word))
        return processed_timings

    # AVSpeechSynthesizer Delegate Methods
    def speechSynthesizer_willSpeakRangeOfSpeechString_(self, tts, range_info):
        """Capture word timings."""
        text = range_info["AVSpeechSynthesisSpeechString"]
        char_range = range_info["NSRange"]
        word = text[char_range.location : char_range.location + char_range.length]
        start_time = self.get_audio_duration()  # Simulate timing
        self.word_timings.append({"start_time": start_time, "word": word})

    def speechSynthesizer_didFinishSpeechUtterance_(self, tts, utterance):
        """Handle completion of an utterance."""
        logging.debug("Synthesis finished for utterance: %s", utterance.speechString())

    def get_voices(self) -> list[dict[str, str]]:
        """Retrieve available voices."""
        return self._client.get_voices()

    def set_voice(self, voice_id: str, lang: str = "en-US") -> None:
        """Set the voice for synthesis."""
        self._voice = AVSpeechSynthesisVoice.voiceWithIdentifier_(voice_id)