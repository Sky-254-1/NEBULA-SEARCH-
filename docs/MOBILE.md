# Nebula Search — Mobile App Roadmap (Phase 10)

## Recommendation: **Capacitor** (primary) with React Native as long-term option

### Why Capacitor first

| Factor | Capacitor | React Native | Flutter |
|--------|-----------|--------------|---------|
| Reuse web codebase | **Excellent** — wraps existing React PWA | Partial — new UI layer | None — full rewrite |
| Time to v1 mobile | **Weeks** | Months | Months |
| Offline/PWA alignment | **Native** — same storage patterns | Good | Good |
| Team skill fit | Matches current React + Vite stack | Requires RN ecosystem | Requires Dart |

Nebula already has a React frontend and PWA service worker. **Capacitor** ships the same UI in iOS/Android WebViews with native plugins for:

- Secure token storage (Keychain/Keystore)
- Background sync
- Share sheet
- File upload to `storage/uploads`

### Suggested path

1. **v1.1** — Add `@capacitor/core` + iOS/Android projects
2. **v1.2** — Native secure storage for JWT refresh tokens
3. **v1.3** — Voice search via Capacitor Speech Recognition plugin
4. **v2.0** — Evaluate React Native if performance-critical offline LLM inference is needed on-device

### When to choose React Native instead

- On-device GGUF inference becomes a core requirement
- Need 60fps custom animations beyond web capabilities
- App Store policies require fully native components

### When to choose Flutter

- Team standardizes on Dart
- Full greenfield mobile UI unrelated to web

## Conclusion

**Ship Capacitor for v1 mobile** to maximize reuse of Nebula's React frontend, PWA offline model, and FastAPI backend — then reassess React Native when local LLM features mature.
