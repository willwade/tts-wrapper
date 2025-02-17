---
sidebar_position: 1
---

# TTS Engines Overview

TTS Wrapper supports multiple text-to-speech engines, each with its own features, capabilities, and authentication requirements. This section provides detailed documentation for each supported engine.

## Quick Feature Comparison

| Engine | SSML Support | Streaming | Word Timing | Platform | Type |
|--------|--------------|-----------|-------------|-----------|------|
| AWS Polly | ✅ Full | ✅ | ✅ | Cloud | Commercial |
| Google Cloud | ✅ Full | ✅ | ✅ | Cloud | Commercial |
| Microsoft Azure | ✅ Full | ✅ | ✅ | Cloud | Commercial |
| IBM Watson | ✅ Full | ✅ | ✅ | Cloud | Commercial |
| ElevenLabs | ❌ | ✅ | ❌ | Cloud | Commercial |
| Play.HT | ❌ | ✅ | ❌ | Cloud | Commercial |
| Wit.ai | ❌ | ❌ | ❌ | Cloud | Commercial |
| eSpeak | ✅ Basic | ❌ | ❌ | Local | Open Source |
| SAPI | ✅ Limited | ❌ | ❌ | Local (Windows) | System |
| AVSynth | ✅ Limited | ✅ | ✅ | Local (macOS) | System |
| GoogleTrans | ❌ | ❌ | ❌ | Cloud | Free |
| Sherpa-ONNX | ❌ | ✅ | ❌ | Local | Open Source |

## Choosing an Engine

Consider the following factors when choosing a TTS engine:

1. **Platform Requirements**
   - Cloud engines require internet connectivity and API keys
   - Local engines need specific operating systems or dependencies

2. **Feature Requirements**
   - SSML support for speech control
   - Streaming capabilities for real-time synthesis
   - Word timing for synchronization

3. **Cost Considerations**
   - Commercial cloud services charge per character/request
   - Local engines are typically free but may have quality tradeoffs

4. **Quality and Voice Options**
   - Cloud services often offer higher quality and more voices
   - Local engines may have limited voice selection

## Engine Documentation

Each engine's documentation page includes:

- Authentication setup
- Available features
- Code examples
- Platform-specific notes
- Known limitations
- Best practices

Select an engine from the sidebar to view its detailed documentation. 