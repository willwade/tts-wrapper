import re
import tempfile
import wave
from io import BytesIO


def process_wav(raw: bytes) -> bytes:
    bio = BytesIO()
    with wave.open(bio, "wb") as wav:
        wav.setparams((1, 2, 16000, 0, "NONE", "NONE"))  # type: ignore
        wav.writeframes(raw)
    return bio.getvalue()


def create_temp_filename(suffix="") -> str:
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
        return temp_file.name


def estimate_word_timings(text: str, wpm: int = 150) -> list[tuple[float, float, str]]:
    # Remove SSML tags
    text = re.sub("<[^<]+?>", " ", text)

    # Split text into words, keeping punctuation
    words = re.findall(r"\b[\w\']+\b|[.,!?;]", text)

    words_per_second = wpm / 60
    base_seconds_per_word = 1 / words_per_second

    timings = []
    current_time = 0.0

    for i, word in enumerate(words):
        # Adjust timing based on word length and type
        if len(word) <= 3:
            duration = base_seconds_per_word * 0.8
        elif len(word) >= 8:
            duration = base_seconds_per_word * 1.2
        else:
            duration = base_seconds_per_word

        # Adjust for punctuation
        if word in ".,!?;":
            duration = base_seconds_per_word * 0.5
            if i > 0:
                # Add a pause after the previous word
                prev_start, prev_end, prev_word = timings[-1]
                timings[-1] = (prev_start, prev_end + 0.2, prev_word)
                current_time += 0.2

        # Add natural variations
        variation = (hash(word) % 20 - 10) / 100  # -10% to +10% variation
        duration *= 1 + variation

        end_time = current_time + duration
        timings.append((current_time, end_time, word))
        current_time = end_time

    return timings
