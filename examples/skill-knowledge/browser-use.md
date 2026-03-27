# browser-use — experience

> Hands-on experience accumulated while using the browser-use skill.
> Max 30 entries; oldest are dropped when the limit is reached. Last updated: 2026-03-27

## Entries

- [State before acting] Always run `browser-use state` before clicking or typing to get current element indices. Indices change after any page interaction — never reuse a stale index.
- [Daemon persists] The browser daemon stays open between commands (~50ms latency per call). Explicitly run `browser-use close` when done to free resources; don't rely on session end to clean up.
- [doctor first] Run `browser-use doctor` on a new machine before first use. It validates the installation and points to setup docs for missing dependencies.
- [Profile for auth] Use `--profile "Default"` (or a named Chrome profile) to access sites where you're already logged in. Headless Chromium has no saved cookies.
- [Headless vs headed] Headless mode (default) is faster but can't solve CAPTCHAs or interact with OS dialogs. Switch to `--headed` for sites that require visual interaction.
- [screenshot for verification] After form submissions or complex interactions, always run `browser-use screenshot` to verify the page state visually rather than trusting DOM state alone.
- [CDP connect] Use `--connect` or `--cdp-url` to attach to an already-running Chrome instance. Useful when the user has a browser open with an active session you should not disrupt.
