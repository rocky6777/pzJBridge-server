# pzJBridge binary releases

## 0.7.2 / Levels 0.4.6

- Sample the busy-poll render-ready probe once per 4,096 invocations per thread, including detailed mode. Unsampled calls avoid clock reads, series lookup, shared counters and recording locks. Reports identify selected-call counts and do not extrapolate them into total polling cost; rare stalls may be missed.
- Separate animal update packet parsing/writing, animal loading/world insertion, synchronization requests, chunk save work, decompression/buffer growth and chunk construction. Report aggregate successful decompression input/output bytes without retaining buffers or payloads. Additional hooks require debug launch and detailed profiling.
- Preserve gameplay and optimizer policies. Normal launches remain silent with no detailed hooks/MCP reporter. Levels 0.4.6 updates its embedded Bridge footer; Performance Boost 0.2.1 and Zombie Types 0.1.4 binaries are unchanged. Workshop discovery declarations follow Bridge 0.7.2.
- Detect Steam/native Windows `-debug` even when Java command properties are absent, using one startup-only native command-line read under the existing native-access permission. Verify positive and negative launch arguments.
- Profiling preparation for matched play tests; no new engine speedup or FPS gain claimed.

## 0.7.1 / Performance Boost 0.2.1 / Levels 0.4.5

- Fix a native profiler capacity blind spot: retain 128 engine series and report dropped engine/packet series. Add detailed bounded per-packet timing and payload-size aggregates, render-state waits, chunk/decompression and FBO preparation/tree phases. All collection remains debug-launch-only.
- Extend optional precipitation reduction to native ground rain splashes, preserving climate, wetness, fog, sound and fish splashes. Disabled-mod restoration is checked against both installed B42 JARs; no new FPS gain is claimed.
- Reuse empty callback argument arrays, avoid unchanged zombie speed writes, and prune noncontributing heatmap epicentres with exact output regression coverage. Add detailed Levels profile/sync sections for investigating isolated callback spikes.
- Include empty Bridge animation/action-group folders to prevent native Workshop folder-scan errors. Update installers, branding and binary distribution references. Zombie Types remains 0.1.4.

## 0.7.0 / Performance Boost 0.2.0

- Require an explicit native debug launch for bridge logging, MCP endpoint creation, profiler reporting and detailed engine transformations. Saved debug preferences alone cannot enable them. Normal launches retain gameplay, extension lifecycle, frame-scoped shared work and cached optimization policies.
- Add read-only engine_diagnostics: renderer batches/state runs/vertices, sampled pending client queues, anonymous server transport/connected counts and reported ping, Lua callback registrations and MCP request totals. Native zombie update/state/postupdate, pathfinding and selected Lua event timings subdivide the previous broad phases; HTTP only reads detached data.
- Add optional decorative rain/snow particle render suppression, covering RainParticle's override and SnowParticle's inherited base method. Fog, climate updates, sound and native drawer cleanup remain active. Disabled mod restoration is tested; no FPS gain claimed yet.
- Levels 0.4.4 and Zombie Types 0.1.4 follow debug-only diagnostics/logging. Startup uses Byte Buddy safe injection selection to avoid its Java 25 Unsafe initialization warning; no global stdout/stderr redirection or vanilla logging suppression.

## 0.6.4

- Fix duplicate native render/network timers and optimizer frame callbacks caused by cumulative Byte Buddy transformations. Each native method now receives its ordinary timer once.
- Performance Boost 0.1.2 suppresses B42.21 FBO ground-shadow submissions before pooled allocation and omits their cosmetic render queue. Pool cleanup remains native; disabling the mod restores behavior. The 0.1.1 legacy shadow hook did not reduce work in the tested FBO session.
- Add detailed upload-buffer phase timings and detached shadow-submission/buffer-capacity counters. Preserve 250% maximum zoom, gameplay and packet processing. Native client/server fixtures pass; matched live FPS validation remains pending.

## 0.6.3

- Performance Boost 0.1.1 adds a configurable cosmetic ground-shadow pass reduction while preserving maximum camera view and simulation. FPS gains require a matched test.
- Detailed profiling separates world/UI draw-buffer submission, state/world updates, shadow/rain/snow rendering and client maintenance. MCP retains detached render command counts and skipped shadow passes.
- Keep normal sampled probes when adding detailed hooks to the same class; disabled native mods immediately remove all optimizer budgets.

## 0.6.2

- Add lifecycle-gated, cached optimization contributions for optional Performance Boost 0.1.0. Native game-loop pacing call sites use a cached policy without changing saved display settings; disabled Workshop mods immediately clear their shared budgets.
- One Performance Boost JAR covers client/SP pacing and water/puddle rendering plus SP/server hot-reload polling and cooperating diagnostic budgets. Gameplay and packet scheduling are preserved.
- Matching Levels 0.4.3 and Zombie Types 0.1.3 metadata and optional nonessential diagnostic cooperation.

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
