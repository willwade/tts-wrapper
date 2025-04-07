from .client import WatsonClient
from .ssml import WatsonSSML

# For backward compatibility
WatsonTTS = WatsonClient

__all__ = ["WatsonClient", "WatsonSSML", "WatsonTTS"]
