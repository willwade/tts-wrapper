"""Example usage of the UpliftAI engine."""

import os

from tts_wrapper import UpliftAIClient


def main() -> None:
    api_key = os.getenv("UPLIFTAI_KEY")
    if not api_key:
        raise RuntimeError("UPLIFTAI_KEY environment variable is not set")

    client = UpliftAIClient(api_key=api_key)
    text = "Testing the UpliftAI text to speech engine"
    client.speak_streamed(text)


if __name__ == "__main__":
    main()
