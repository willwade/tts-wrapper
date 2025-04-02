# __init__.py
from .client import SherpaOnnxClient
from .ssml import SherpaOnnxSSML

# For backward compatibility
SherpaOnnxTTS = SherpaOnnxClient
