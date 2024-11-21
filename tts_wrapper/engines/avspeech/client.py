import logging
from tts_wrapper.engines.avspeech.ssml import AVSpeechSSML


class AVSpeechClient:
    """Client interface for the AVSpeech TTS engine."""

    def __init__(self) -> None:
        """Initialize the AVSpeech library client."""
        self.ssml = AVSpeechSSML()
        logging.debug("AVSpeechClient initialized")

    def get_voices(self) -> list[dict[str, str]]:
        """Retrieve available voices from the AVSpeech engine."""
        from AVFoundation import AVSpeechSynthesisVoice
        voices = AVSpeechSynthesisVoice.speechVoices()
        return [
            {"id": voice.identifier(), "name": voice.name(), "language": voice.language()}
            for voice in voices
        ]