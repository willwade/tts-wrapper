#!/bin/bash

LIB_NAME="SpeechBridge"
SOURCE="SpeechBridge.swift"
TARGET_VERSION="macos14"

# Build for ARM64
swiftc -emit-library -target arm64-apple-$TARGET_VERSION -o $LIB_NAME-arm64.dylib $SOURCE

# Build for x86_64
swiftc -emit-library -target x86_64-apple-$TARGET_VERSION -o $LIB_NAME-x86_64.dylib $SOURCE

# Create Universal Binary
lipo -create -output $LIB_NAME.dylib $LIB_NAME-arm64.dylib $LIB_NAME-x86_64.dylib

# Verify
lipo -info $LIB_NAME.dylib