import os

import filetype  # type: ignore
import pytest

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


def pytest_configure(config):
    # Register custom markers
    config.addinivalue_line(
        "markers", "watson: mark test as requiring Watson credentials"
    )


@pytest.fixture(scope="session", autouse=True)
def load_credentials():
    from .load_credentials import load_credentials as load_creds

    load_creds()


def pytest_runtest_setup(item):
    if "watson" in item.keywords and os.getenv("GITHUB_ACTIONS") == "true":
        pytest.skip("Skipping test: Watson tests are always skipped in CI")
