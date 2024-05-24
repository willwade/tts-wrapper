import os
import random
import string
import tempfile
import wave
from io import BytesIO
import re


def process_wav(raw: bytes) -> bytes:
    bio = BytesIO()
    with wave.open(bio, "wb") as wav:
        wav.setparams((1, 2, 16000, 0, "NONE", "NONE"))  # type: ignore
        wav.writeframes(raw)
    return bio.getvalue()


def create_temp_filename(suffix="") -> str:
    random_seq = "".join(random.choice(string.ascii_letters) for _ in range(10))
    return os.path.join(
        tempfile.gettempdir(), f"{tempfile.gettempprefix()}_{random_seq}{suffix}"
    )


def estimate_word_timings(self, text: str, wpm: int = 150) -> List[Dict[str, float]]:
    words = re.findall(r'\b\w+\b', text)
    words_per_second = wpm / 60
    seconds_per_word = 1 / words_per_second
    timings = []
    current_time = 0
    for word in words:
        timings.append({
            'word': word,
            'start_time': current_time
        })
        current_time += seconds_per_word
    return timings