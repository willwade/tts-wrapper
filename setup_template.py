from setuptools import setup, find_packages
import os

version = os.getenv("PACKAGE_VERSION", "0.0.0")

setup(
    name="py3-tts-wrapper",
    version=version,
    packages=find_packages(),
    install_requires=[
        # List your install_requires here, or leave it empty and let Poetry handle it
    ],
    # Add any additional options necessary for building platform-specific wheels
)
