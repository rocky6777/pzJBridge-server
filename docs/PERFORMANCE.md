# Performance analytics and cooperative optimization

Bridge 0.7.2 adds a configurable 60 FPS target and diagnostics for B42.21. It does not guarantee 60 FPS or alter the engine's chunk radius, combat, collision, physics, XP or multiplayer rules. Levels 0.4.6 and Zombie Types 0.1.4 cooperate with cosmetic budgets. Gameplay still works when adaptive quality or analytics are disabled.

**Diagnosis requires an explicit `-debug` launch in 0.7.2.** Normal gameplay does not collect these metrics or open MCP.

Bridge 0.7.2 expands the bounded native profiler from 32 to 128 series. The previous limit could silently omit zombie/pathfinding probes after other phases registered. `droppedEngineSeries` and `droppedPacketSeries` expose capacity loss. Detailed mode retains per-packet-type timing totals and payload byte counts at handler entry (up to 256 types), without reading or retaining payload contents. These bytes exclude transport overhead and are not measured network throughput. Render-state waits distinguish pipeline backpressure from active submission work. Chunk loading, received-chunk decompression, FBO scene/cache preparation and tree rendering have separate inclusive timings.

Performance Boost 0.2.1 extends the existing optional rain/snow reduction to both native ground rain-splash render methods. Climate, wetness, fish splashes, fog and sound stay native; splash animation is cosmetic. `engineDiagnostics.render.skippedRainSplashCalls` counts bypassed method calls, not visible droplets. Disable the option or mod to restore native rendering. Maximum camera view remains unchanged.

Levels 0.4.6 avoids unchanged zombie speed writes and prunes heatmap epicentres outside the contributing radius before calculating distance. Tests compare exact output to the original radial calculation over 10,000 positions. Detailed `zombie.profile` and `zombie.sync` sections separate initialization/profile lookup from server synchronization. The bridge also reuses an empty argument array for no-argument extension callbacks.

Detailed extension Lua timing uses cached labels for key tick, render, command and lifecycle events. Other events aggregate as `event:other`, preventing startup event names from filling the per-mod table and avoiding a new label allocation for every callback. Listener registration counts still retain their individual event names.

Full `performance_status` retains all bounded native and packet series. The sixty-sample history selects the 32 most costly native phases and 16 packet types per interval; omission counts distinguish this summary from missing probes. JVM metrics also expose process-wide allocation bytes per second when the VM already supports/enables its allocation counter; `-1` means unavailable or no baseline. The bridge never enables additional VM tracking for this counter. GC collection duration is not a measurement of stop-the-world pause time.

The 0.7.0 enabled-mod capture retained 56 focused gameplay samples at 250% zoom, speeds up to 93 tiles/second and up to 131 zombies. Median rolling frame p95 was 31.3 ms; native rendering/network stalls and GC activity remained. Its workload differs from the disabled-mod capture, so it does not establish an optimization gain or regression. The new probes and rain-splash policy are fixture-tested; their gameplay impact needs a fresh comparison.

## Player controls

Open **Options > Bridge > Performance**:

- **Performance analytics** collects frame cadence and sampled timings. Disable it for an overhead comparison; the small background JVM reporter and shared-work lifecycle still run.
- **Detailed performance profiler** times every bridge callback and native probe. It is separate from verbose mod logging. Keep it off outside diagnosis. Adaptive quality freezes at its current tier while detailed profiling is enabled.
- **Target FPS** defaults to 60 and accepts 15–144. A lower native game FPS cap lowers the effective target; the bridge does not override that cap.
- **Adaptive cosmetic budgets** reduces cooperating mods' label counts, cloud polygon detail and cosmetic refresh frequency after sustained pressure. There are four tiers, with slower recovery to avoid oscillation. Paused, unfocused and menu sessions do not trigger reductions. Settings are local to this computer.

Sandbox **Bridge > Performance** contains server analytics and detailed server profiling options. They do not reduce server simulation frequency. In single-player, the client Performance controls collect the combined simulation/render diagnostics.

## Read-only MCP tools

The existing authenticated loopback connection also serves `performance_status`, `performance_history` and `mod_plan`. Updating the bundled MCP Python companion and reconnecting/restarting Codex refreshes the tool list. `agent_status` also contains the current performance report and mod plan, so older tool discovery can still inspect them.

`performance_status` returns the latest report. History also retains its bounded timing breakdowns, so a paused game does not erase the work measured during the test. Server reports have no client FPS target/budget; their phase cadence is labelled explicitly.

Detailed mode additionally retains up to 64 timestamped slow calls in `slowCalls` on status/history. Native phases and client/server packet handlers qualify at 16 ms; mod callbacks qualify at 5 ms. Packet records contain the native packet enum name, never payloads or account data. Records retain completion time, inclusive duration and thread ID until replaced or a new world/session resets profiling. They survive the shorter aggregate timing sample ring. Nested records overlap and must not be added together. GC collection-time counters are not stop-the-world pause durations.

Extra scene update/render, UI, collision-state, sound, voice, Steam-loop and lighting probes run only in detailed mode. These subdivide broad native phases without changing their behavior. A normal sampled-mode/off comparison remains necessary to measure profiler overhead before claiming a performance improvement.

Reports contain:

- Rolling ten-second game-frame and render-submission cadence, p95/p99/worst intervals and over-budget counts.
- Game logic, rendering preparation, draw submission, chunk-map update and streaming update wall timings. Dedicated servers measure ServerMap.postupdate and streaming; **postupdate is a server phase, not a complete server tick**. The render-thread polling loop is deliberately uninstrumented because it can run hundreds of thousands of times per second while idle.
- Per-extension callback counts and sampled durations; detailed mode separates named Lua events. Optional named sections identify work inside a mod.
- Heap use, GC collection time, process CPU core equivalents, focus/pause state, zoom, player travel speed, camera shift and cell zombie count.
- Current cosmetic tier, shared-work hits and cautious recommendations tied to observed evidence.

Normal mode samples one in 64 mod callbacks and one in eight native probes. Full mode samples every invocation. Each timing series retains at most 128 durations, with 64 event names per mod, 64 mod namespaces and 32 native series. Reports show the 32 largest callback cost estimates. Overflow is reported. The history retains 60 one-second snapshots and 32 stutters; no player/game objects enter HTTP snapshots. A world-session reset increments `generation`; sequence numbers remain monotonic. Read with `afterSequence` and `limit` for incremental pages.

These are **inclusive wall times**: nested callbacks overlap and must not be added as exclusive CPU cost. Draw submission measures CPU/driver work, not GPU execution or idle render-thread waiting. Sampled cost estimates can miss rare expensive calls. Travel/camera/GC correlations suggest a hypothesis, not a cause. Detailed profiling adds overhead. External Lua mods are only included in whole engine-phase timings unless they publish explicit sections through a bridge integration.

## Reproducible play test

For multiplayer, use the same agent JAR on client and server and profile both endpoints. Additional probes time `GameClient.update` and `GameClient/GameServer.mainLoopDealWithNetData`. The server probe covers that named ZomboidNetData dispatch path, not every modern packet implementation or the entire server loop. It measures processing wall time, not ping, packet loss or throughput. Enable server detailed profiling through the world's Performance sandbox setting; client profiling remains a local option. Do not infer network latency from callback durations.

Use the same save, route, zoom, resolution, native cap and enabled mods for comparisons. Begin with adaptive cosmetics disabled to isolate measurements. Warm the world first, then perform roughly 30 seconds each of stationary play, repeated camera panning, running/driving over the same route and moving near a crowd. Record sampled mode, repeat briefly with full profiling to attribute hot callbacks, then compare analytics off. Re-enable adaptive cosmetics and repeat with each setting recorded. MCP can read both processes while you control the game; it cannot change live settings or execute arbitrary game code.

Only after repeatable evidence should engine reductions be added. Candidate ideas reviewed in [ZBBetterFPS](https://github.com/zed-0xff/ZBBetterFPS) include rendering distance, state changes, batching and background work. This release uses our own probes and cooperative budgets; no BetterFPS source has been copied.

## Mod relationship plan and shared work

`BridgeMod.dependencies()` declares required or optional peers, with an exact version or `*`. Configuration is topologically ordered with stable ID order for otherwise unrelated mods. Required dependencies must be enabled together; cycles and incompatible active versions fail clearly. Zombie Types declares optional Levels integration.

`hookClaims()` declares native class, method and JVM descriptor plus `CALLBACK`, `MODIFY_ARGUMENT`, `MODIFY_RETURN` or `REPLACE`. `mod_plan` classifies overlaps as cooperative callbacks, order-sensitive modifications or override risks. Our gameplay modules conservatively claim overloads by method name; some reported signatures may be broader than their actual advice matcher. Undeclared legacy hooks are explicitly unverified. These declarations cannot detect every external Java/Lua patch or prove semantic compatibility.

`sharedContracts()` documents agreed function/data contracts. `SharedWork.frameValue(key, type, supplier)` reuses one calculation on the same engine thread within a bridge frame scope. Use immutable results, stable versioned keys and an agreed meaning; never use actor IDs as keys or mutate another consumer's result. Results expire at the frame boundary, type collisions and recursion fail, and the cache holds at most 128 values. Outside a frame scope, the supplier runs normally. This is explicit reuse, not automatic semantic deduplication or merging compiled JARs.

The [example extension](../examples/example-mod/src/main/java/example/ExampleMod.java) demonstrates `PerformanceProfiler.section`, cosmetic hints and a shared immutable summary. Invoke its `cosmetic.summary` callback from an engine-thread UI hook; the example does not attach gameplay hooks on its own. Keep critical simulation independent of cosmetic hints. Current login metadata permits at most 32 Java extensions; this does not limit ordinary Lua-only Workshop mods.

## Optional Performance Boost 0.2.1

[Performance Boost](../mods/pzjbridge-performance/README.md) is a separate native-enabled Java extension; its one JAR selects client or dedicated-server policies. Client defaults apply a temporary 60 FPS upper cap, reduce water/puddle shaders and use tier 1 for cooperating cosmetic work. The cap substitutes only game-loop call sites, preserving saved display settings and lower native limits. SP hot-reload polling is limited to four checks per second; dedicated-server polling to two. File events remain queued, and native debug mode bypasses this limit. Server diagnostic intervals can be multiplied for cooperating extensions, with detailed profiling retaining the usual frequency.

These settings cut specific rendering/maintenance work. They do not skip zombie AI, world simulation, combat, XP or packet processing. Disable the native companion mod to restore its original methods and remove its cached shared budget. MCP performance status reports both `nativeFpsCap` and `effectiveFpsCap`; `extension_status` for `pzjbridge.optimizer` exposes watcher counters and policy. Changes are polled on the engine thread once per second. Compare warmed matching routes before claiming a measured FPS gain.

Performance Boost 0.2.1 optionally omits the native cosmetic ground-shadow pass for characters, vehicles and corpses. It preserves maximum zoom and world simulation. `renderWork` exposes skipped passes and detailed-only queued draw-command counts; nested renderer timings are inclusive and cannot be added together. The earlier Fast Move test was heavier than the walking baseline and recorded 50–141 ms stalls; it does not establish a gain. Compare the same fast route and crowd with shadow reduction off/on before attributing an improvement.

Bridge 0.7.2 fixes cumulative-transform duplication so ordinary render and network timers run once per invocation. Performance Boost 0.2.1 covers the current `FBORenderShadows` path as well as the legacy cell renderer: it suppresses shadow submissions before pooled allocation, then omits their render queue while preserving native cleanup. `skippedShadowSubmissions` counts suppressed requests, not visible shadows. `uploadBufferBytes` and `uploadBufferCount` describe native allocation capacity; they do not measure GPU memory pressure. Detailed RingBuffer begin/render/next timings identify upload/flush phases. The 0.6.3 off/on capture had zero skipped shadows and duplicated cadence events, so it cannot support an FPS improvement claim.

## Debug launch and quiet gameplay

Steam client Launch Options: add `-debug` when diagnosing. Dedicated server: use `Start-Server.ps1 -Debug` (its common PowerShell debug switch passes native `-debug`). MCP installation/configuration alone does not start a connection in normal gameplay. Remove the launch flag for quiet operation; saved Bridge Debug/Collect choices cannot enable diagnostic infrastructure without an explicit debug launch. Native `-Ddebug` is also a debug launch recognized by Zomboid and the bridge.

Normal launches produce no bridge/bundled-extension stdout/stderr messages, no MCP HTTP listener and no profiler reporter thread. Only the frame-scope hooks required for cooperative shared work remain; detailed timing transforms are not installed. Optimizer policies and gameplay still run. This does not mute Zomboid, the JVM, or unrelated third-party mods. Extension authors should use `BridgeDebug.log/error/trace` rather than raw printing and guard expensive diagnostic snapshot construction with `BridgeDebug.enabled()`.

Debug-only `engine_diagnostics` returns detached renderer batch/state-run/vertex totals, client pending main/loading/coop queues, server connection counts and maximum reported ping, Lua event callback registration counts, and MCP request totals. It contains no account names, addresses, packet payloads, tokens or Lua closures. Counts are cumulative; timestamps identify snapshot freshness. Client queues and server connections are sampled once per second; listener registration lists every five seconds, bounded to 512 events. Full profiling adds native zombie update/state/postupdate, `PathFindBehavior2.update(float)` and selected Lua event timings. Native pathfinding timing is an inclusive behavior phase, not all worker-thread search cost. Server postupdate is not a whole server tick. Full profiling remains an extra opt-in within a debug launch.

Optional Performance Boost “Reduce rain/snow particles” suppresses decorative precipitation draw calls on both old and FBO rendering paths. Weather update methods, fog, ground snow, climate, sound and caller drawer cleanup remain native. It defaults off and restores immediately when the native mod is disabled. Test wet/snowy scenes before claiming an improvement.

## Focused streaming and animal diagnosis (0.7.2)

The render-ready busy-poll method is sampled once per 4,096 calls per thread even in detailed mode. Unsampled calls do not read the clock, look up a timing series, increment a shared counter or lock the recorder. Its rows expose `invocationSampleStride=4096`; `calls`/`totalCalls` count selected invocations only, and costs are not extrapolated to all polls. Rare waits can be missed. Render-ready waits include waiting for the producer/frame cap and are not GPU work. Compare detailed profiling off/on before trusting measured gains.

Detailed mode subdivides AnimalUpdatePacket parse/write/process, AnimalPacket parsing, IsoAnimal load/addToWorld and synchronization requests. It also separates WorldStreamer decompression, buffer capacity checks, DoChunkAlways, IsoChunk.LoadChunk/loadInWorldStreamerThread and ChunkSaveWorker.Update. These are inclusive phase timings and may overlap; background chunk timings are not automatically main-thread stalls. Successful decompression reports cumulative `totalInputBytes`/`totalOutputBytes`; no buffers, animal identities, locations or payloads are retained. Counts and bytes reset with the existing profiler reset. These measurements do not defer packets, animal updates or chunk work.

For the next comparison, use the same warmed route, fixed zoom, crowd, Fast Move and shout sequence, with analytics on and adaptive budgets off. Capture detailed mode on and off with matching optimizer options. Loading/exit samples must be excluded from movement comparisons. This update prepares diagnosis; it does not claim an additional engine optimization.

The embedded Windows launcher may omit `sun.java.command`, and Windows ProcessHandle may not expose arguments. Bridge 0.7.2 reads GetCommandLineW once at startup through the JDK 25 foreign-function API, using the native-access permission already supplied by the installers. It retains no command text and starts no subprocess. Without that existing native-access permission it falls back to Java command arguments or the explicit native `-Ddebug` flag; it never requests access or produces a warning to open diagnostics. Saved preferences alone cannot enable the debug gate.
