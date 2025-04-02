---
sidebar_position: 1
---

# Introduction

Welcome to TTS Wrapper, a powerful and flexible **python** library that simplifies text-to-speech integration across multiple services. Whether you're building an application that needs speech synthesis capabilities or just want to experiment with different TTS engines, TTS Wrapper provides a unified interface that makes it easy to work with various text-to-speech services.

## What is TTS Wrapper?

TTS Wrapper is a Python library that abstracts away the complexities of working with different text-to-speech APIs by providing:

- A unified interface for multiple TTS services
- Consistent handling of voice selection and audio properties
- Streamlined audio playback controls
- Cross-platform support
- Comprehensive SSML support where available

## Supported Engines

TTS Wrapper supports a wide range of both cloud-based and local TTS engines:

### Cloud Services
- AWS Polly
- Google Cloud TTS
- Microsoft Azure TTS
- IBM Watson
- ElevenLabs
- Wit.Ai
- Play.HT

### Local Engines
- eSpeak-NG (Linux/macOS/Windows)
- AVSynth (macOS only)
- SAPI (Windows only)
- Sherpa-ONNX (All platforms)

### Experimental Support
- PicoTTS
- UWP (Windows 10+)

For a detailed comparison of features across all engines, see our [Engines Overview](engines/overview).

## Key Features

### Core Functionality
- Text-to-speech conversion with multiple output options
- SSML (Speech Synthesis Markup Language) support
- Voice and language selection
- Streaming and direct playback
- Audio file output in various formats

### Advanced Features
- Real-time playback controls (pause, resume, stop)
- Word-level timing and callbacks
- Volume, pitch, and rate control
- Unified voice handling across engines
- Audio device selection
- Streaming capabilities

### Developer-Friendly
- Simple, unified architecture where engine clients directly implement the TTS interface
- Consistent API across all engines
- Type hints for better IDE support
- Comprehensive documentation
- Rich example collection (see [examples](https://github.com/willwade/py3-tts-wrapper/tree/main/examples))
- Active community support

## Getting Started

Ready to get started? Check out our [Installation Guide](installation) to set up TTS Wrapper in your project, then move on to the [Basic Usage](guides/basic-usage) guide to learn how to use the library.