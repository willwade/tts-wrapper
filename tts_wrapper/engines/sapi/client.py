import os
import platform
from typing import Any, Optional

import soundfile as sf

from tts_wrapper.engines.utils import create_temp_filename
from tts_wrapper.exceptions import ModuleNotInstalled

Credentials = tuple[str]

FORMATS = {"wav": "wav"}


class SAPIClient:
    def __init__(self, driver: Optional[str] = None) -> None:
        try:
            import pyttsx3  # type: ignore
        except ImportError:
            msg = "pyttsx3"
            raise ModuleNotInstalled(msg)
            pyttsx3 = None

        # Determine the default driver based on the platform
        if driver is None:
            self._system = platform.system()
            if self._system == "Windows":
                driver = "sapi5"
            elif self._system == "Darwin":
                driver = "nsss"
            elif self._system == "Linux":
                driver = "espeak"
            else:
                msg = "Unsupported operating system"
                raise ValueError(msg)

        try:
            self._client = pyttsx3.init(driver)
            if driver == "sapi5":
                default_voice = "David"
            elif driver == "nsss":
                default_voice = "com.apple.voice.compact.en-US.Samantha"
            elif driver == "espeak":
                default_voice = "English (America)"

            self.properties = {
                "rate": 100,
                "volume": 1.0,
                "pitch": "medium",
                "voice": default_voice,
            }
        except Exception as e:
            msg = f"Failed to initialize pyttsx3 with driver '{driver}': {e}"
            raise RuntimeError(
                msg,
            )

    def synth(self, text: str) -> bytes:
        temp_filename = create_temp_filename(".wav")
        # On a mac, it's actually an aiff file
        self._client.save_to_file(text, temp_filename)
        self._client.runAndWait()

        if self._system == "Darwin":
            # Use soundfile to read AIFF and write to WAV
            temp_aiff = temp_filename.replace(".wav", ".aiff")
            os.rename(
                temp_filename, temp_aiff,
            )  # Rename .wav to .aiff, as macOS uses AIFF internally

            data, samplerate = sf.read(temp_aiff)
            sf.write(temp_filename, data, samplerate, format="WAV")

            os.remove(temp_aiff)  # Clean up temporary AIFF file

        with open(temp_filename, "rb") as temp_f:
            content = temp_f.read()
        os.remove(temp_filename)
        return content

    def get_voices(self) -> list[dict[str, Any]]:
        """Fetches available voices and returns a standardized list of voice properties."""
        voices = self._client.getProperty("voices")
        standardized_voices = []
        for voice in voices:
            if voice.gender is None:
                voice.gender = "male"
            voice_data = {
                "id": voice.id,
                "name": voice.name,
                "languages": str(voice.languages).replace("_", "-"),
                "gender": self._standardize_gender(voice.gender),
                "age": voice.age,
                "voice_uri": voice.id,
            }
            standardized_voices.append(voice_data)

        return standardized_voices

    def _standardize_gender(self, gender: str) -> str:
        """Converts gender information to a standardized format."""
        gender = gender.lower()
        if "male" in gender:
            return "Male"
        if "female" in gender:
            return "Female"
        if "neutral" in gender or "unknown" in gender:
            return "Neutral"
        return "Unknown"

    def set_voice(self, voice_id: str) -> None:
        """Sets the voice based on the provided voice_id."""
        voices = self.get_voices()
        matching_voice = next(
            (voice for voice in voices if voice["id"] == voice_id), None,
        )

        if matching_voice:
            self._client.setProperty("voice", matching_voice["id"])
        else:
            msg = f"Voice with ID '{voice_id}' not found."
            raise ValueError(msg)

    def get_property(self, property_name):
        """Get the value of a TTS property."""
        return self.properties.get(property_name, None)

    def set_property(self, property_name, value) -> None:
        """Set the value of a TTS property."""
        self.properties[property_name] = value

        if property_name == "rate":
            self._client.setProperty("rate", self._map_rate(value))
        elif property_name == "volume":
            self._client.setProperty("volume", self._map_volume(value))
        elif property_name == "pitch":
            # Since pyttsx3 does not support pitch, we keep this for interface consistency.
            self.properties[property_name] = value
        elif property_name == "voice":
            self.set_voice(value)

    def _map_rate(self, rate: str) -> int:
        """Maps abstract rate settings to pyttsx3-compatible rate values."""
        rate_mapping = {
            "x-slow": 50,
            "slow": 100,
            "medium": 150,
            "fast": 200,
            "x-fast": 250,
        }
        return rate_mapping.get(rate, 150)

    def _map_volume(self, volume: str) -> float:
        """Maps volume from 0-100 scale to pyttsx3 0-1 scale."""
        return float(volume) / 100.0
