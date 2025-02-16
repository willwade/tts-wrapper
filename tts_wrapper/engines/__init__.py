import sys
from contextlib import suppress

from .elevenlabs import *
from .google import *
from .googletrans import *
from .microsoft import *
from .pico import *
from .polly import *
from .sherpaonnx import *
from .watson import *
from .witai import *
from .espeak import *
from .playht import *

# Windows-only imports
if sys.platform == "win32":
    with suppress(ImportError):
        from .sapi import *
        from .uwp import *

if sys.platform == "darwin":
    with suppress(ImportError):
        from .avsynth import *

#deprecated
# from .mms import *
# from .piper import *
