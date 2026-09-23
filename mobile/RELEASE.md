# Nebula Mobile — Build & Release (v1.1)

Single codebase: **Web → Android → iOS**

## Prerequisites

- Node.js 20+
- Android Studio (Android SDK 34+)
- Xcode 15+ (macOS, for iOS)
- Java 17 (Android Gradle)

## Quick start

```bash
# 1. Build web assets
cd frontend && npm ci && npm run build

# 2. Sync to native projects
cd ../mobile && npm ci && npx cap sync

# 3. Open native IDE
npm run android   # Android Studio
npm run ios       # Xcode (macOS only)
```

## Configuration

`mobile/capacitor.config.ts`:

- `appId`: `com.nebula.search`
- `webDir`: `../frontend/dist`
- Plugins: Push, Splash, Camera, Filesystem, Network, Preferences, Share, Speech

## Debug APK

```bash
cd mobile
npm run build:web
npx cap sync android
cd android && ./gradlew assembleDebug
```

Output: `mobile/android/app/build/outputs/apk/debug/app-debug.apk`

## Release APK / AAB

1. Create keystore: `keytool -genkey -v -keystore nebula-release.keystore -alias nebula -keyalg RSA -keysize 2048 -validity 10000`
2. Configure signing in `android/app/build.gradle`
3. Run: `./gradlew bundleRelease` (Play Store) or `assembleRelease`

## iOS release

1. Open `mobile/ios/App/App.xcworkspace` in Xcode
2. Set team + bundle identifier
3. Product → Archive → Distribute App

## Native features

| Feature | Plugin |
|---------|--------|
| Persistent session | `@capacitor/preferences` |
| Offline sync queue | `mobile/sync/queue.ts` |
| Voice search | `@capacitor-community/speech-recognition` |
| Camera upload | `@capacitor/camera` |
| Share / clipboard | `@capacitor/share`, `@capacitor/clipboard` |
| Network status | `@capacitor/network` |
| Push notifications | `@capacitor/push-notifications` |

## Performance

- Lazy-loaded web bundle via Vite code splitting
- Capacitor WebView with `androidScheme: https`
- Sync queue flushes on app resume when online

## Mobile E2E

Playwright projects: `mobile-chrome` (Pixel 5), `tablet` (iPad)

```bash
npm run e2e -- --project=mobile-chrome
npm run e2e -- --project=tablet
```
