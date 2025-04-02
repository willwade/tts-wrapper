from tts_wrapper import PlayHTClient
import json
import os

def main():
    # Check if credentials are available
    api_key = os.environ.get("PLAYHT_API_KEY")
    user_id = os.environ.get("PLAYHT_USER_ID")
    
    if not api_key or not user_id:
        print("PlayHT credentials not found in environment variables.")
        print("Please set PLAYHT_API_KEY and PLAYHT_USER_ID environment variables to test PlayHT TTS.")
        return
    
    # Initialize the client
    client = PlayHTClient(api_key=api_key, user_id=user_id)
    
    # Test different language code formats
    print("Testing PlayHT language code formats:")
    
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
