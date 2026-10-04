# pzJBridge binary releases

## 0.6.1

- Retain up to 64 timestamped slow calls in detailed performance mode for MCP diagnostics. Slow native phases (16 ms), mod callbacks (5 ms), and packet handlers (16 ms) retain completion time, duration and thread ID; no packet payloads are collected.
- Add detailed-only native scene update/render, UI, collision-state, sound, voice, Steam and lighting probes; name slow client/server packet handlers by their native packet enum. No gameplay scheduling or packet delivery changes.
- Refresh matching Workshop metadata and footer for Levels 0.4.2 and Zombie Types 0.1.2.

## 0.6.0

Add read-only detailed/sampled MCP profiling, frame/stutter history, JVM/GC metrics and explicit mod relationship/override reports. Configurable 60 FPS target controls cooperating mods' cosmetic budgets; simulation and multiplayer rules remain unchanged. Include updated API, SDK documentation and client installer ZIP. This is a prerelease for live performance measurement, with no measured FPS guarantee and no engine chunk/render reductions yet. Detailed profiling adds overhead. Gameplay module source/binaries remain separate from the public bridge distribution.

## 0.5.2

Optional game-thread extension dispatch supports independent Zombie Types and Levels modules. Update the shared agent/API, server installer and embedded client ZIP. Gameplay modules remain separate installations; private Levels source and binaries remain excluded from the public bridge package.

## 0.5.1

Make extension Java hooks follow B42’s enabled save/server mods. Disabling restores native methods and removes the extension from the server’s required client list. Workshop mod.info binds installed JARs to native enablement; manual development JARs expose workshopModId. MCP reports activeMods alongside discovered binaries. The companion menu shows green ● Connected when Java integration is present. Client and server must both update. Automated native enable/disable cycles, method restoration, MCP, Lua/settings and package checks passed; live save/server toggle testing remains for the player. Workshop publishing stays on hold.

## 0.5.0

Add the shared Bridge Options tab and native Bridge sandbox page for extension settings. Expose a declarative settings API and active settings through read-only MCP status. Client preferences save locally; sandbox rules persist with the world and are server controlled. Debug is off by default, keeping current diagnostics/error reporting while skipping verbose histories. Client and server startup agents must both update. Private gameplay extensions are excluded from this distribution.

Validated against installed 42.21 classes, native sandbox serialization and Lua compilation, settings persistence/validation, packaged startup and installer checks. Final page layout and live multiplayer options behavior await user verification.

## 0.4.2 launcher follow-up — Steam server identity

Launch the dedicated server with SteamAppId/SteamGameId 108600, scoped to the child process and restored afterwards. A live server advertising the dedicated tool identity 380870 answered A2S queries but client P2P connections timed out. After restarting with 108600, Steam authentication succeeded and the player confirmed joining works. Agent 0.4.2 and Levels 0.2.2 are unchanged; Workshop uploads remain on hold.

## 0.4.2

Fix a launch failure caused by connection files left behind after an interrupted client/server shutdown. MCP endpoints hold an exclusive sidecar file lock, record process identity and safely recover stale legacy loopback files. Live or unknown owners are preserved. Shutdown removes only the connection file this process published. Optional MCP failures now warn and allow game instrumentation to finish; required game/login hooks still fail closed. Both client and server must use bridge 0.4.2. Levels gameplay remains 0.2.2.

Regression checks cover stale-file recovery, active owners, PID reuse, duplicate endpoints, owned-file cleanup, forced JVM termination/relaunch and game startup when MCP is unavailable.

## 0.4.1

Correct stale menu version labels. Join rejection now lists all missing or incompatible Java components and explains manual agent installation, Workshop extension downloads and restarting. A version-specific client ZIP link is included. The stock missing-mod translation preserves the explanation even on a vanilla client. Both sides must update to 0.4.1. Private gameplay extensions remain excluded.

Automated tests cover the handshake, stale branding, client/server hook installation, MCP and installer behavior. Native translations preserve the reason; live join-screen layout still needs player validation.

## 0.4.0

Client and dedicated-server startup agents, API JAR, installers, client ZIP and optional authenticated local MCP companion. In-game display branding now includes the bridge version; the engine version used by networking and saves is preserved. MCP class inspection adds concise signatures alongside Java and bytecode views. Includes the extension callback API, startup instrumentation audit, bounded mod diagnostics, hook reports, debug events, history, runtime health and optional fixed game logs.

Install/update the startup agent on both client and server and restart both. This package does not include private gameplay extensions. Workshop publishing remains on hold. Build/source provenance and hashes are recorded in BUILD_INFO.json and SHA256SUMS.txt.
