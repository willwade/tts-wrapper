---
sidebar_position: 4
---

# Streaming

TTS Wrapper provides powerful streaming capabilities that allow you to process and play audio in real-time, making it ideal for applications requiring immediate audio feedback or handling large amounts of text.

## Understanding Streaming

Streaming in TTS Wrapper works by:
1. Breaking down text into manageable chunks
2. Converting these chunks to audio in real-time
3. Playing the audio while continuing to process remaining chunks
4. Managing memory efficiently by processing only what's needed

## Basic Streaming

### Simple Streaming

```python
from tts_wrapper import PollyClient, PollyTTS

# Initialize TTS
client = PollyClient(credentials=('region', 'key_id', 'access_key'))
tts = PollyTTS(client)

# Stream text
tts.speak_streamed("This text will be processed and played in real-time.")
```

### Streaming with Callbacks

```python
def on_chunk_processed(chunk_info):
    print(f"Processed chunk: {chunk_info['text']}")
    print(f"Duration: {chunk_info['duration']}s")

# Stream with callback
tts.speak_streamed(
    "This text will trigger callbacks for each chunk.",
    on_chunk_processed=on_chunk_processed
)
```

## Advanced Streaming

### Custom Stream Configuration

```python
# Configure stream parameters
tts.setup_stream(
    chunk_size=1024,        # Size of audio chunks
    buffer_size=4096,       # Audio buffer size
    samplerate=44100,       # Sample rate
    channels=1,             # Mono audio
    dtype="int16"           # Audio data type
)
```

### Stream Control

```python
# Start a stream
stream = tts.create_stream()

# Feed text in chunks
stream.feed("First part of the text. ")
stream.feed("Second part of the text. ")

# Indicate no more text
stream.done()

# Wait for completion
stream.wait_until_done()
```

### Async Streaming

```python
import asyncio

async def stream_text():
    # Create async stream
    stream = await tts.create_async_stream()
    
    # Feed text asynchronously
    await stream.feed("First part. ")
    await stream.feed("Second part. ")
    
    # Complete stream
    await stream.done()
    
    # Wait for completion
    await stream.wait_until_done()

# Run async stream
asyncio.run(stream_text())
```

## Memory Management

### Efficient Chunking

```python
# Configure chunk settings
tts.set_stream_config({
    "chunk_size": 1024,          # Audio chunk size
    "max_text_chunk": 100,       # Maximum text characters per chunk
    "buffer_threshold": 0.75      # Buffer fullness threshold
})
```

### Memory-Efficient Processing

```python
# Process large text efficiently
with open("large_text.txt", "r") as f:
    # Stream text line by line
    for line in f:
        tts.speak_streamed(line.strip(), wait=False)
        # Optional: Add delay between lines
        time.sleep(0.1)
```

## Real-Time Applications

### Interactive Chat Bot

```python
class ChatBot:
    def __init__(self):
        self.tts = PollyTTS(PollyClient(...))
        self.stream = self.tts.create_stream()
    
    def respond(self, text):
        # Stream response immediately
        self.stream.feed(text)
    
    def finish_response(self):
        self.stream.done()
        self.stream = self.tts.create_stream()
```

### Live Text Processing

```python
def process_live_text(text_generator):
    stream = tts.create_stream()
    
    for text in text_generator:
        # Process and stream in real-time
        stream.feed(text)
        
        # Check if we should pause
        if stream.buffer_full():
            time.sleep(0.1)
    
    stream.done()
```

## Error Handling

### Stream Error Management

```python
try:
    stream = tts.create_stream()
    stream.feed("Text to stream")
except StreamError as e:
    print(f"Streaming error: {e}")
except BufferError as e:
    print(f"Buffer error: {e}")
finally:
    stream.close()
```

### Recovery Strategies

```python
def robust_streaming(text):
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            return tts.speak_streamed(text)
        except StreamError:
            retry_count += 1
            time.sleep(1)  # Wait before retry
    
    raise Exception("Failed to stream after multiple attempts")
```

## Best Practices

1. **Buffer Management**
   - Monitor buffer levels
   - Adjust chunk sizes based on performance
   - Implement backpressure when needed

2. **Resource Cleanup**
   ```python
   # Always clean up streams
   stream = tts.create_stream()
   try:
       stream.feed("Text")
       stream.done()
   finally:
       stream.close()
   ```

3. **Performance Optimization**
   - Use appropriate chunk sizes
   - Implement proper error handling
   - Monitor memory usage
   - Clean up resources promptly

## Example: Complete Streaming Application

```python
from tts_wrapper import PollyClient, PollyTTS
import time
import threading

class StreamManager:
    def __init__(self):
        self.client = PollyClient(credentials=('region', 'key_id', 'access_key'))
        self.tts = PollyTTS(self.client)
        self.stream = None
        self.is_active = False
        
    def start_stream(self):
        self.stream = self.tts.create_stream()
        self.is_active = True
        
        # Start monitoring thread
        threading.Thread(target=self._monitor_stream).start()
    
    def _monitor_stream(self):
        while self.is_active:
            if self.stream.buffer_full():
                print("Buffer full, waiting...")
                time.sleep(0.1)
            time.sleep(0.01)
    
    def feed_text(self, text):
        if not self.stream:
            self.start_stream()
        self.stream.feed(text)
    
    def stop_stream(self):
        if self.stream:
            self.stream.done()
            self.stream.wait_until_done()
            self.stream.close()
            self.is_active = False
            self.stream = None
    
    def cleanup(self):
        self.stop_stream()
        self.tts.cleanup()

# Usage example
manager = StreamManager()
try:
    manager.start_stream()
    
    # Feed text in chunks
    manager.feed_text("First part of the speech. ")
    time.sleep(1)
    manager.feed_text("Second part of the speech. ")
    time.sleep(1)
    manager.feed_text("Final part of the speech.")
    
    # Stop streaming
    manager.stop_stream()
finally:
    manager.cleanup()
```

## Next Steps

- Learn about [audio control features](audio-control) for fine-tuned playback
- Explore [callback functionality](callbacks) for stream events
- Check out [SSML support](ssml) for enhanced speech control 