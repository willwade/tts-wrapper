# Silent Audio Synthesis

The `synthesize()` method provides silent audio synthesis without playback, making it perfect for applications that need audio data without immediate playback.

## Overview

Unlike `speak()` which plays audio immediately, `synthesize()` returns raw audio data that you can process, save, or play later. This method is ideal for:

- **SAPI bridges and accessibility tools**
- **Audio processing pipelines**
- **Batch audio generation**
- **Real-time audio streaming applications**
- **Custom audio players**

## Basic Usage

### Complete Audio Data

By default, `synthesize()` returns complete audio data as bytes:

```python
from tts_wrapper import MicrosoftClient

# Initialize client
client = MicrosoftClient(credentials=('subscription_key', 'region'))

# Get complete audio data
audio_bytes = client.synthesize("Hello, this is a test of silent synthesis.")

# audio_bytes is now a bytes object containing WAV audio data
print(f"Generated {len(audio_bytes)} bytes of audio data")
```

### Streaming Audio Data

For real-time processing or large texts, use streaming mode:

```python
# Get streaming audio data
audio_stream = client.synthesize("This is a longer text that will be streamed.", streaming=True)

# Process chunks as they're generated
total_bytes = 0
for chunk in audio_stream:
    # Each chunk is a bytes object
    total_bytes += len(chunk)
    
    # Process the chunk (e.g., send to audio player, save to buffer, etc.)
    process_audio_chunk(chunk)

print(f"Processed {total_bytes} total bytes")
```

## Method Signature

```python
def synthesize(
    self,
    text: str | SSML,
    voice_id: str | None = None,
    streaming: bool = False,
) -> bytes | Generator[bytes, None, None]:
```

### Parameters

- **`text`**: The text to synthesize (can be plain text or SSML)
- **`voice_id`** (optional): The ID of the voice to use for synthesis
- **`streaming`** (optional): Controls data delivery method:
  - `False` (default): Return complete audio data as bytes
  - `True`: Return generator yielding audio chunks in real-time

### Return Value

- When `streaming=False`: Returns `bytes` containing complete audio data
- When `streaming=True`: Returns `Generator[bytes, None, None]` yielding audio chunks

## Voice Selection

You can specify a voice for synthesis without changing the client's default voice:

```python
# Use a specific voice for this synthesis only
audio_bytes = client.synthesize(
    "Hello in a different voice",
    voice_id="en-US-AriaNeural"
)

# Client's default voice remains unchanged
```

## SSML Support

The `synthesize()` method supports SSML markup:

```python
# Using SSML for advanced speech control
ssml_text = client.ssml.add('Hello, <break time="500ms"/> world!')
audio_bytes = client.synthesize(ssml_text)

# Or pass SSML directly as string
ssml_string = '<speak>Hello, <break time="1s"/> this is SSML.</speak>'
audio_bytes = client.synthesize(ssml_string)
```

## Practical Examples

### Example 1: Batch Audio Generation

```python
texts = [
    "Welcome to our service.",
    "Please hold while we connect you.",
    "Thank you for waiting.",
    "Your call is important to us."
]

audio_files = []
for i, text in enumerate(texts):
    audio_bytes = client.synthesize(text)
    
    # Save to file
    filename = f"message_{i+1}.wav"
    with open(filename, "wb") as f:
        f.write(audio_bytes)
    
    audio_files.append(filename)

print(f"Generated {len(audio_files)} audio files")
```

### Example 2: Real-time Audio Streaming

```python
import queue
import threading

# Audio buffer for streaming
audio_queue = queue.Queue()

def audio_producer(text):
    """Generate audio chunks and put them in queue"""
    audio_stream = client.synthesize(text, streaming=True)
    for chunk in audio_stream:
        audio_queue.put(chunk)
    audio_queue.put(None)  # Signal end of stream

def audio_consumer():
    """Consume audio chunks from queue and play them"""
    while True:
        chunk = audio_queue.get()
        if chunk is None:
            break
        # Play or process the audio chunk
        play_audio_chunk(chunk)

# Start producer and consumer
text = "This is a long text that will be streamed in real-time."
producer_thread = threading.Thread(target=audio_producer, args=(text,))
consumer_thread = threading.Thread(target=audio_consumer)

producer_thread.start()
consumer_thread.start()

producer_thread.join()
consumer_thread.join()
```

### Example 3: Audio Processing Pipeline

```python
from pydub import AudioSegment
import io

def process_audio_with_effects(text, voice_id=None):
    """Generate audio and apply effects"""
    # Generate audio
    audio_bytes = client.synthesize(text, voice_id=voice_id)
    
    # Convert to AudioSegment for processing
    audio = AudioSegment.from_wav(io.BytesIO(audio_bytes))
    
    # Apply effects
    audio = audio.speedup(playback_speed=1.1)  # Slightly faster
    audio = audio + 3  # Increase volume by 3dB
    audio = audio.fade_in(100).fade_out(100)  # Add fade effects
    
    # Export processed audio
    output_buffer = io.BytesIO()
    audio.export(output_buffer, format="wav")
    
    return output_buffer.getvalue()

# Use the processing pipeline
processed_audio = process_audio_with_effects(
    "This audio will be processed with effects",
    voice_id="en-US-JennyNeural"
)
```

## Engine Compatibility

The `synthesize()` method works consistently across all TTS engines:

- **Cloud engines** (Azure, Google, AWS, etc.): True streaming support
- **Local engines** (eSpeak, SAPI, etc.): Simulated streaming by chunking complete audio

## Performance Considerations

### Complete vs Streaming

- **Complete mode** (`streaming=False`):
  - Best for: Short texts, batch processing, simple use cases
  - Memory usage: Stores entire audio in memory
  - Latency: Higher initial latency, but all data available at once

- **Streaming mode** (`streaming=True`):
  - Best for: Long texts, real-time applications, memory-constrained environments
  - Memory usage: Lower memory footprint
  - Latency: Lower initial latency, data available as generated

### Memory Management

```python
# For large texts, prefer streaming to avoid memory issues
long_text = "..." * 10000  # Very long text

# This could use a lot of memory
# audio_bytes = client.synthesize(long_text)  # Not recommended for very long texts

# This uses less memory
audio_stream = client.synthesize(long_text, streaming=True)
for chunk in audio_stream:
    # Process chunk immediately and release memory
    process_chunk(chunk)
```

## Error Handling

```python
from tts_wrapper.exceptions import TTSError, SynthesisError

try:
    audio_bytes = client.synthesize("Hello world")
except SynthesisError as e:
    print(f"Synthesis failed: {e}")
except TTSError as e:
    print(f"TTS error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Next Steps

- Learn about [streaming capabilities](streaming) for advanced audio streaming
- Explore [audio control features](audio-control) for playback control
- Check out [callback functionality](callbacks) for word-level timing
- Understand [SSML support](ssml) for advanced speech markup
