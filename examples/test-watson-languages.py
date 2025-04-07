from tts_wrapper import WatsonClient
import json
import os


def main():
    # Check if credentials are available
    api_key = os.environ.get("WATSON_API_KEY")
    region = os.environ.get("WATSON_REGION", "us-south")
    instance_id = os.environ.get("WATSON_INSTANCE_ID")

    if not api_key or not instance_id:
        print("Watson credentials not found in environment variables.")
        print(
            "Please set WATSON_API_KEY, WATSON_REGION, and WATSON_INSTANCE_ID environment variables to test Watson TTS."
        )
        return

    # Initialize the client
    client = WatsonClient(credentials=(api_key, region, instance_id))

    # Test different language code formats
    print("Testing Watson language code formats:")

    # 1. BCP-47 format (default)
    voices_bcp47 = client.get_voices()
    print("\n1. BCP-47 format (default):")
    # Just print a few examples to keep output manageable
    print(json.dumps(voices_bcp47[:3], indent=2))

    # 2. ISO 639-3 format
    voices_iso = client.get_voices(langcodes="iso639_3")
    print("\n2. ISO 639-3 format:")
    print(json.dumps(voices_iso[:3], indent=2))

    # 3. Human-readable display names
    voices_display = client.get_voices(langcodes="display")
    print("\n3. Human-readable display names:")
    print(json.dumps(voices_display[:3], indent=2))

    # 4. All formats in a dictionary
    voices_all = client.get_voices(langcodes="all")
    print("\n4. All formats in a dictionary:")
    print(json.dumps(voices_all[:3], indent=2))

    # 5. Find English voices
    print("\n5. English voices (BCP-47 format):")
    english_voices = [v for v in voices_bcp47 if "en" in str(v["language_codes"])]
    print(json.dumps(english_voices[:3], indent=2))


if __name__ == "__main__":
    main()
