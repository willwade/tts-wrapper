#!/usr/bin/env python3
"""
Test script to verify that MicrosoftClient can be imported and used
even when the Azure Speech SDK is not available.
"""

import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_import_without_speechsdk():
    """Test importing MicrosoftClient when Speech SDK is not available."""
    print("Testing MicrosoftClient import without Speech SDK...")
    
    # Temporarily hide the azure.cognitiveservices.speech module
    original_modules = sys.modules.copy()
    
    # Remove any existing azure speech modules
    modules_to_remove = [
        'azure.cognitiveservices.speech',
        'azure.cognitiveservices',
        'azure'
    ]
    
    for module in modules_to_remove:
        if module in sys.modules:
            del sys.modules[module]
    
    # Mock the import to fail
    import builtins
    original_import = builtins.__import__
    
    def mock_import(name, *args, **kwargs):
        if name == 'azure.cognitiveservices.speech':
            raise ImportError("Mocked: Azure Speech SDK not available")
        return original_import(name, *args, **kwargs)
    
    builtins.__import__ = mock_import
    
    try:
        # This should work now
        from tts_wrapper import MicrosoftClient
        print("✓ Successfully imported MicrosoftClient without Speech SDK")
        
        # Test creating a client (this should work with REST API fallback)
        try:
            client = MicrosoftClient(credentials=("dummy_key", "eastus"))
            print("✓ Successfully created MicrosoftClient instance")
            print(f"✓ Using Speech SDK: {client._use_speech_sdk}")
            
            # Test getting voices (this should work with REST API)
            # Note: This will fail with dummy credentials, but should not fail due to missing SDK
            try:
                voices = client.get_voices()
                print("✓ get_voices() method works")
            except Exception as e:
                if "azure.cognitiveservices.speech" in str(e):
                    print("✗ get_voices() still depends on Speech SDK")
                    return False
                else:
                    print(f"✓ get_voices() fails due to credentials (expected): {e}")
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to create MicrosoftClient: {e}")
            return False
            
    except ImportError as e:
        print(f"✗ Failed to import MicrosoftClient: {e}")
        return False
    finally:
        # Restore original import
        builtins.__import__ = original_import
        # Restore modules
        sys.modules.clear()
        sys.modules.update(original_modules)

def test_import_with_speechsdk():
    """Test importing MicrosoftClient when Speech SDK is available."""
    print("\nTesting MicrosoftClient import with Speech SDK...")
    
    try:
        from tts_wrapper import MicrosoftClient
        print("✓ Successfully imported MicrosoftClient")
        
        # Test creating a client
        try:
            client = MicrosoftClient(credentials=("dummy_key", "eastus"))
            print("✓ Successfully created MicrosoftClient instance")
            print(f"✓ Using Speech SDK: {client._use_speech_sdk}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to create MicrosoftClient: {e}")
            return False
            
    except ImportError as e:
        print(f"✗ Failed to import MicrosoftClient: {e}")
        return False

if __name__ == "__main__":
    print("Testing Microsoft Azure TTS client import behavior...\n")
    
    # Test without Speech SDK
    success1 = test_import_without_speechsdk()
    
    # Test with Speech SDK (if available)
    success2 = test_import_with_speechsdk()
    
    print(f"\nResults:")
    print(f"Import without Speech SDK: {'✓ PASS' if success1 else '✗ FAIL'}")
    print(f"Import with Speech SDK: {'✓ PASS' if success2 else '✗ FAIL'}")
    
    if success1:
        print("\n🎉 Issue #56 has been fixed! MicrosoftClient can now be imported and used without the Speech SDK.")
    else:
        print("\n❌ Issue #56 is not yet fixed. MicrosoftClient still requires the Speech SDK.")
