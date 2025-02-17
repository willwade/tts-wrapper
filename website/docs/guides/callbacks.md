---
sidebar_position: 5
---

# Callbacks

TTS Wrapper provides a simple callback system to handle speech events. There are three main callbacks available:

- `onStart`: Triggered when speech playback begins
- `onEnd`: Triggered when speech playback ends
- `started-word`: Triggered when a word starts being spoken

## Using Callbacks

You can connect callback functions to these events using the `connect()` method:

```python
from tts_wrapper import PollyClient, PollyTTS

# Initialize TTS
client = PollyClient(credentials=('region', 'key_id', 'access_key'))
tts = PollyTTS(client)

# Define callback functions
def on_start():
    print("Speech started")

def on_end():
    print("Speech ended")

def on_word(word: str):
    print(f"Speaking word: {word}")

# Connect callbacks
tts.connect("onStart", on_start)
tts.connect("onEnd", on_end)
tts.connect("started-word", on_word)

# Speak text with callbacks
tts.speak("Hello, this is a test of the callback system.")
```

## Callback Timing

- The `onStart` callback is triggered when audio playback actually begins
- The `onEnd` callback is triggered when the entire text has been spoken
- The `started-word` callback is triggered at the start of each word

## Example: Progress Tracking

Here's an example of using callbacks to track speech progress:

```python
def on_start():
    print("Starting speech...")

def on_end():
    print("Speech complete!")

def on_word(word: str):
    print(f"Currently speaking: {word}")

# Connect all callbacks
tts.connect("onStart", on_start)
tts.connect("onEnd", on_end)
tts.connect("started-word", on_word)

# Speak with progress tracking
text = "This is a test of progress tracking."
tts.speak(text)
```

## Best Practices

1. **Keep Callbacks Light**: Callback functions should be quick and not block execution
2. **Handle Exceptions**: Always include error handling in your callbacks
3. **Cleanup**: Clear callbacks when no longer needed by setting them to None
4. **Thread Safety**: Remember that callbacks may be called from different threads

## Next Steps

- Learn about [SSML support](ssml) for controlling speech synthesis
- Explore [audio control features](audio-control) for playback manipulation
- Check out [streaming capabilities](streaming) for real-time synthesis 