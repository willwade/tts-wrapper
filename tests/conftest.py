import os

import filetype  # type: ignore
import pytest

from .load_credentials import load_credentials  # Import your load_credentials function

# Load credentials for the test session
load_credentials()

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_DATA_DIR = os.path.join(SCRIPT_DIR, "data")

def load_resp_wav():
    with open(os.path.join(TEST_DATA_DIR, "test.wav"), "rb") as f:
        return f.read()

class Helpers:
    @staticmethod
    def check_audio_file(path, format="wav") -> None:
        assert os.path.exists(path), f"{path} does not exist"
        assert os.path.getsize(path) > 1024
        assert filetype.guess_extension(path) == format

    @staticmethod
    def create_tmp_filename(tmp_dir, filename):
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        return os.path.join(tmp_dir, filename)

@pytest.fixture(scope="session")
def helpers():
    return Helpers
