import os
import sys
import subprocess
from setuptools import setup, find_packages
from setuptools.command.install import install

class CustomInstallCommand(install):
    """Customized setuptools install command - installs system dependencies on Linux."""
    
    def run(self):
        if os.name == 'posix' and sys.platform.startswith('linux'):
            print("Installing system dependencies...")
            commands = [
                ["sudo", "apt-get", "update"],
                ["sudo", "apt-get", "install", "-y", "portaudio19-dev"],
                # Add other system dependencies here
            ]
            for command in commands:
                subprocess.run(command, check=True)
        install.run(self)

setup(
    name='tts-wrapper',
    version='0.9.0',
    description='TTS-Wrapper makes it easier to use text-to-speech APIs by providing a unified and easy-to-use interface.',
    author='Giulio Bottari',
    author_email='giuliobottari@gmail.com',
    url='https://github.com/mediatechlab/tts-wrapper',
    packages=find_packages(),
    install_requires=[
        'pyaudio>=0.2.11'
    ],
    extras_require={
        'google': ['google-cloud-texttospeech>=2.11.1'],
        'watson': ['ibm-watson>=6.0.0'],
        'polly': ['boto3>=1.24.34'],
        'microsoft': ['azure-cognitiveservices-speech>=1.15.0'],
        'elevenlabs': ['requests>=2.28.0'],
        'witai': ['requests>=2.28.0'],
        'sapi': ['pyttsx3>=2.90'],
        'uwp': ['pythonnet>=3.0.1'],
        'piper': ['piper_tts>=1.2.0'],
        'mms': ['ttsmms>=0.7']
    },
    cmdclass={
        'install': CustomInstallCommand,
    },
)
