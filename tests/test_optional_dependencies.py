# test_optional_dependencies.py
import importlib
import sys
import pytest

# List of optional dependencies and their corresponding TTS classes from tts_wrapper
optional_dependencies = {
    "boto3": ("tts_wrapper", "PollyTTS", "PollyClient"),
    "ibm_watson": ("tts_wrapper", "WatsonTTS", "WatsonClient"),
    "google_cloud_texttospeech": ("tts_wrapper", "GoogleTTS", "GoogleClient"),
    "pyttsx3": ("tts_wrapper", "SapiTTS", "SapiClient"),  
    "azure_cognitiveservices_speech": ("tts_wrapper", "MicrosoftTTS", "MicrosoftClient"),
    "requests": ("tts_wrapper", "ElevenLabsTTS", "ElevenLabsClient"),  # Used by ElevenLabs and WitAI
    "piper-tts": ("tts_wrapper", "PiperTTS", "PiperClient"),  # Assuming piper-tts needs to be added
    "py3-ttsmms": ("tts_wrapper", "MMSTTS", "MMSClient"), 
    "gTTS": ("tts_wrapper", "GoogleTransTTS", "GoogleTransClient"),
    "sherpa-onnx": ("tts_wrapper", "SherpaOnnxTTS", "SherpaOnnxClient"),
}

# Flatten the dictionary for pytest.mark.parametrize
flattened_dependencies = [
    (module_name, *details) for module_name, details in optional_dependencies.items()
]

@pytest.mark.parametrize("module_name, tts_wrapper, tts_class, client_class", flattened_dependencies)
def test_optional_dependencies(module_name, tts_wrapper, tts_class, client_class):
    # Temporarily remove the module from sys.modules
    original_module = sys.modules.pop(module_name, None)
    
    try:
        # Attempt to import the TTS and Client classes without the optional dependency
        tts_module = importlib.import_module(tts_wrapper)
        tts_cls = getattr(tts_module, tts_class)
        client_cls = getattr(tts_module, client_class)
    except (ModuleNotFoundError, AttributeError):
        # If the import fails, it should be due to the missing optional dependency
        assert module_name not in sys.modules
    else:
        # If the import succeeds, ensure the classes are indeed available
        assert tts_cls is not None
        assert client_cls is not None
    finally:
        # Restore the original module if it was removed
        if original_module:
            sys.modules[module_name] = original_module