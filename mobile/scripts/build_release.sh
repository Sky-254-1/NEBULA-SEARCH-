#!/bin/bash
set -e

echo "Building Nebula Search for Play Store..."

# Flutter build
flutter clean
flutter pub get
flutter build appbundle --release \
  --obfuscate \
  --split-debug-info=build/debug-info \
  --build-name=1.0.0 \
  --build-number=1

echo "Build complete: build/app/outputs/bundle/release/app-release.aab"