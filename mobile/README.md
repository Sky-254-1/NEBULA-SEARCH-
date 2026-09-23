# Nebula Search - Flutter Mobile App

Cross-platform mobile client for Nebula Search built with Flutter and Dart.

## Tech Stack

- **Flutter SDK** >=3.0.0
- **Riverpod** for state management
- **HTTP** client for API communication

## Project Structure

```
mobile/
├── lib/
│   ├── main.dart                 # App entry point
│   ├── screens/
│   │   └── home_screen.dart      # Search home screen
│   └── providers/
│       └── search_provider.dart  # Riverpod search state
├── pubspec.yaml                  # Dependencies
└── analysis_options.yaml         # Lint rules
```

## Getting Started

1. Install Flutter SDK: https://flutter.dev/docs/get-started/install
2. Run `flutter pub get`
3. Run `flutter run`

## Features

- Search via backend API
- Material 3 UI
- State management with Riverpod
- Offline-capable architecture

## Platforms

- Android
- iOS
- Web (experimental)
- Desktop (experimental)