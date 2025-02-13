import sys

from .elevenlabs import *
from .google import *
from .googletrans import *
from .microsoft import *
from .pico import *
from .polly import *
from .systemtts import *
from .sherpaonnx import *
from .watson import *
from .witai import *
from .espeak import *
from .playht import *

# Windows-only imports
if sys.platform == "win32":
    try:
        from .sapi import *
        from .uwp import *
    except ImportError:
        # Avoid hard failure if these modules aren't installed or not supported
        pass

#deprecated
# from .mms import *
# from .piper import *
