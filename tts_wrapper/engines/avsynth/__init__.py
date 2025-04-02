from .client import AVSynthClient
from .setup import build_swift_bridge
from .ssml import AVSynthSSML

# For backward compatibility
AVSynthTTS = AVSynthClient

__all__ = ["AVSynthClient", "AVSynthSSML", "AVSynthTTS", "build_swift_bridge"]
