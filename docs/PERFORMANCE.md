# Performance analytics and cooperative optimization

Bridge 0.6.0 adds a configurable 60 FPS target and diagnostics for B42.21. It does not guarantee 60 FPS or alter the engine's chunk radius, combat, collision, physics, XP or multiplayer rules. Levels 0.4.1 and Zombie Types 0.1.1 cooperate with cosmetic budgets. Gameplay still works when adaptive quality or analytics are disabled.

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
