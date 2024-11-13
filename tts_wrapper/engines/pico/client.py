import subprocess
import tempfile
from typing import Optional

from tts_wrapper.engines.utils import process_wav
from tts_wrapper.exceptions import ModuleNotInstalled


class PicoClient:
    def __init__(self) -> None:
        bin_name = self._get_bin_name()
        if bin_name is None:
            msg = "pico-tts"
            raise ModuleNotInstalled(msg)
        self._bin_name = bin_name

    @classmethod
    def _check_bin_exists(cls, bin_name: str) -> bool:
        proc = subprocess.run(
            f"command -v {bin_name}", shell=True, stdout=subprocess.DEVNULL, check=False,
        )
        return proc.returncode == 0

    def _get_bin_name(self) -> Optional[str]:
        for name in ("pico2wave", "pico-tts"):
            if self._check_bin_exists(name):
                return name
        return None

    def _synth_pico2wave(self, text: str, voice: str) -> bytes:
        with tempfile.NamedTemporaryFile("w+b", suffix=".wav") as temp:
            subprocess.run([self._bin_name, "-l", voice, "-w", temp.name, text], check=False)
            temp.seek(0)
            return temp.read()

    def _synth_picotts(self, text: str, voice: str) -> bytes:
        proc = subprocess.run(
            [self._bin_name, "-l", voice],
            input=text.encode("utf-8"),
            capture_output=True, check=False,
        )
        raw = proc.stdout
        return process_wav(raw)

    def synth(self, text: str, voice: str) -> bytes:
        if self._bin_name == "pico2wave":
            return self._synth_pico2wave(text, voice)
        return self._synth_picotts(text, voice)
