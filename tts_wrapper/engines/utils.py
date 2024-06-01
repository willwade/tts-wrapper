import os
import random
import string
import tempfile
import wave
from io import BytesIO
import re
from typing import List, Dict, Tuple

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


def estimate_word_timings(text: str, wpm: int = 150) -> List[Tuple[float, str]]:
    #remove ssml
    text = re.sub('<[^<]+?>', '', text)
    words = re.findall(r'\b\w+\b', text)
    words_per_second = wpm / 60
    seconds_per_word = 1 / words_per_second
    timings = []
    current_time = 0
    for word in words:
        # Append a tuple instead of a dictionary
        timings.append((float(current_time), word))
        current_time += seconds_per_word
    return timings