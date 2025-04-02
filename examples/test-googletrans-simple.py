from tts_wrapper import GoogleTransClient


def main():
    # Initialize the client
    client = GoogleTransClient()

    # Test the get_voices method
    print("\nTesting get_voices method:")
    voices = client.get_voices(langcodes="bcp47")
    print(f"Found {len(voices)} voices")
    if voices:
        print(f"First voice: {voices[0]}")


if __name__ == "__main__":
    main()
