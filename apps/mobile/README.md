# Maya mobile shell

A small iOS/Android shell built with Expo, React Native, and TypeScript. The same source tree provides Home, Chat, and Projects; Expo builds platform-specific JavaScript/native-module bundles for both platforms. This keeps the first UI slice lean while leaving room for native capabilities later.

## Run and verify

```bash
npm install
npm test
npm run typecheck
npm run build:all
```

The iOS and Android export commands validate the cross-platform app bundles. They do not create signed IPA/APK store binaries; those require native build infrastructure and signing configuration.

## Chat and local API

Chat is a thin client of the existing `MayaTurnService` through `POST /v1/chat/completions`; there is no model SDK, alternate inference path, persona prompt, or model secret in the mobile bundle. Each turn sends the ordered user/assistant history with a stable in-memory session ID and request ID. The server-owned system prompt remains implicit. History/session continuity is only in the running app process and is not restored after app restart.

Set `EXPO_PUBLIC_MAYA_API_BASE_URL` to the API origin at build/start time, for example `http://127.0.0.1:5000` for a local simulator path, then start the existing API with `python loaders/maya_loader.py --api --backend ollama`. Expo public variables are client-visible configuration; put only a non-secret URL there. Do not place provider keys, bearer tokens, or private prompts in this app.

The existing API is unauthenticated and deliberately binds only to loopback. Do not widen it to a LAN/public interface. A physical-phone or production connection needs an authenticated HTTPS gateway; that deployment is not part of this shell.

## Read-only tools and reports

Search is called only by the `Search the web` button and reads public DuckDuckGo results. Weather is called only by `Get weather for this city`, after a manually typed city passes validation; it uses Open-Meteo geocoding and current weather, and shows the source and service update time. Results are plain text and are never fed back as model instructions. Neither tool performs an action beyond a public lookup.

Each completed assistant reply has a **Report reply** button. A tap submits only that assistant reply (no user transcript or account identity) to `POST /v1/reports`; the request includes a stable report ID so retrying does not create duplicate reports. The local API stores opted-in reports in `maya_reports.db` on the machine running the server. That file can contain the reported assistant text and is ignored by Git. This is a local development inbox, not an operational moderation queue; a deployed app needs a private authenticated reporting destination, retention rules, and a support/review process.

This phase intentionally has no sign-in, project sync, social feed, GPS/location access, voice, attachments, background checks, outbound calls, checkout, X posting, Telegram, Team Bots, or commerce.
