# Java extensions

Bridge 0.6.1 adds optional dependency/hook declarations, named profiler sections and explicit per-frame shared work. See [performance diagnostics and the example](PERFORMANCE.md) for contracts, limits and measurement practices. Configuring extensions now follows dependency order, then stable ID order.

## Shared Bridge options

Override `displayName()` and `settings()` on `BridgeMod` to join the client **Bridge** tab and sandbox **Bridge** page:

```java
public String displayName() { return "My Mod"; }
public List<BridgeSetting> settings() {
    return List.of(
        BridgeSetting.toggle("Debug", "Debug mode", "Extra diagnostics", BridgeSetting.Scope.CLIENT, false),
        new BridgeSetting("KillXP", "Kill XP", "Server/world rule", BridgeSetting.Scope.WORLD,
            BridgeSetting.Type.INTEGER, 25, 0, 1000));
}
```

Settings support BOOLEAN, INTEGER and NUMBER values with validated finite bounds. Keys are unique per scope; declare at most 64 settings per extension. The engine-free API rejects collisions in generated native sandbox names. Existing extensions without settings remain compatible and display a group with no local options.

Read local preferences with `BridgeSettings.clientValue(id, key)` / `clientToggle`. Read world rules with `worldValue` after `OnGameStart` / `OnServerStarted`; earlier reads return schema defaults. Example native key: `Bridge.author_my_mod_KillXP`, saved under `Bridge` in SandboxVars. The Bridge UI loads per-computer preferences from `Zomboid/pzjbridge/client-options.properties`. Changing world options in client Options is deliberately unavailable. Clients receive the server's native sandbox rules on joining.

Guard expensive diagnostic payload creation with `BridgeSettings.debugEnabled(id)` before creating maps or formatting log strings. A boolean key named `Debug` enables that mod's debug mode; Bridge's global Debug enables all mods. Latest diagnostic snapshots and hook errors remain available, while verbose event/sample histories are disabled by default. `agent_status.settings` exposes schemas and effective values through the read-only MCP bridge.


Implement `io.github.zomboidjbridge.api.BridgeMod` and place its fully qualified class name in `META-INF/services/io.github.zomboidjbridge.api.BridgeMod`. Starting with bridge 0.3.0, the loader discovers declared JARs inside downloaded Steam Workshop items, merges them with the optional manual `mods` directory, validates unique IDs/versions/providers, then configures extensions in ID order. Restart the game to load changes.

```java
public final class MyMod implements BridgeMod {
    public String id() { return "author.my-mod"; }
    public String version() { return "1.0.0"; }
    public boolean requiresClient() { return true; }
    public AgentBuilder configure(AgentBuilder builder, Side side) {
        // Add narrowly scoped .type(...).transform(...) rules here.
        return builder;
    }
}
```

IDs use lowercase letters, digits, dot, underscore and hyphen, up to 64 characters. Versions use letters, digits, dot, underscore, plus and hyphen, up to 64 characters. `requiresClient()` means that a server loading this extension rejects clients that do not declare this exact ID/version. Server-only extensions should leave it false. The same JAR may configure different hooks using `Side.CLIENT` and `Side.SERVER`.

Use the API JAR and the pinned Byte Buddy dependency as **compile-only** dependencies. Do not bundle copies of the bridge API or Byte Buddy into extension JARs. Dependency JARs may be placed beside extensions; the loader keeps its URLClassLoader for the process lifetime. Avoid referencing game classes from premain or loading them while configuring transforms; use class/method names and Byte Buddy descriptions instead. Game classes should remain unloaded until hooks are installed.

Build the example:

```powershell
.\gradlew.bat :example-mod:jar
```

For manual loading, copy `examples/example-mod/build/libs/example-mod-1.0.0.jar` into your chosen extensions directory and append `;mods=C:/path/to/extensions` to the agent option on both sides. The example prints its side and requires a matching client extension without changing gameplay.

## Publish an extension through Workshop

Include the following under your Workshop item's `Contents` folder:

```text
mods/YourMod/
  common/
    mod.info
    pzjbridge.properties
    java/
      your-extension.jar
      optional-library.jar
  42.21/
    mod.info
    media/lua/client/YourLuaCompanion.lua   (optional)
```

The marker `common/pzjbridge.properties` explicitly opts this mod into Java loading:

```properties
bridgeVersion=0.6.1
sides=client,server
jars=java/your-extension.jar,java/optional-library.jar
```

Use forward-slash paths relative to the declaration folder. Each listed file must exist inside that folder, including after resolving links. Arbitrary JARs elsewhere in the Workshop item are ignored. Use `sides=server` for a server-only extension, and leave `requiresClient()` false in that case. `sides` defaults to both roles. `bridgeVersion` must exactly match the installed bridge; unsupported versions fail startup with the declaration path. Unknown settings, escaping paths, duplicate provider names/IDs and missing JARs also fail startup rather than silently omitting required code.

For this verified game profile, `42.21/pzjbridge.properties` overrides the common declaration **entirely**, including side selection; they are not merged. Other version folders are ignored. Use a common declaration for shared client/server code or put the complete declaration and JARs under `42.21/` for profile-specific code. No game classes or bridge/Byte Buddy copies should be included in your extension.

Clients find `steamapps/workshop/content/108600` from the game JAR location and read Steam's `appworkshop_108600.acf` installed-item index. Stray folders and authoring drafts are not loaded. This is an offline installed-cache lookup performed before Steam initializes; it does not query live subscriptions or download items. Let Steam finish subscription/update/unsubscription processing before launching. Java discovery finds downloaded JARs; activation follows the game's resolved enabled-mod list. Disable the companion in the save/server mod selection to stop its Java hooks. Use `;workshop=false` to disable automatic discovery; manual development JARs still follow their native mod IDs.

Players install the bridge once, subscribe to your item, wait for Steam to finish downloading, and restart. They do not copy your JAR manually. Bridge upgrades still require updating the startup agent once; version 0.6.1 must be installed on both client and server because login admission requires an exact agent version.

Servers use the selected profile's `WorkshopItems` list. The supplied `Start-Server.ps1` reads that list and passes comma-separated IDs as `workshopItems=...` before the JVM starts. The server's internal `steamapps/workshop/content/108600` cache is preferred, falling back to the Steam library cache. Only selected IDs are considered. Missing downloads fail startup: pre-download the configured items using the game's normal server launcher/SteamCMD, stop that process, then start with the bridge. Downloads made after premain are not loaded during that run. With no selected list, automatic server discovery loads nothing; manual `mods` remains available.

Custom layouts can use `;workshopDir=/path/to/workshop/content/108600`. The Windows installers expose `-WorkshopDirectory` and `-DisableWorkshop`. Clients still need the adjacent Steam installed-item index. For another server launcher, pass `;workshopItems=111,222` explicitly. Multiple declarations of the same real JAR are deduplicated, while conflicting provider names/extension IDs fail startup.

The example marker and mod.info are in `examples/example-mod/workshop/common/`. Copy those with the built example JAR under `common/java/` to author a test Workshop item.

The current API exposes transform configuration and side selection. It does not yet provide stable game events, a post-login messaging bus, dependency/version ranges, sandboxing, hot reload, or a scheduler for game-thread operations. The login gate is added after extension configuration. Extensions are trusted JVM code; do not replace the agent builder's listener/ignore policy or hook the bridge's own login methods.

In 0.3.1 and later, use `ExtensionHooks.register(id(), handler)` during `configure` to register a process-lifetime callback. Inlined advice should call `ExtensionHooks.call(id, event, arguments...)` through the parent-agent API, rather than referencing helper classes visible only to the extension's child loader. The callback runs synchronously on the calling thread, so defer game-dependent initialization until a suitable game callback and keep handlers short. Failures return null and are logged once per event; recipe gates should explicitly require `Boolean.TRUE` to fail closed. This is a dispatcher, not a game-thread scheduler or network API. The private [Levels project](../mods/pzjbridge-levels/README.md) demonstrates the pattern with actual B42.21 hooks.

Use MCP to inspect original game classes and generate a narrowly scoped patch. CFR reconstructs Java from bytecode; check bytecode with `format=bytecode` when decompiled control flow is ambiguous. Keep game files and reconstructed game code local rather than shipping them inside extension projects.

Declare concrete required engine class names through `BridgeMod.instrumentationTargets()`. The bridge resolves them without initialization after installing the transformer, repairs missed transformations, and audits every declared target. This handles classes resolved early by the client or another startup component. Advice must support retransformation and must not add fields or change class structure.

To expose read-only runtime diagnostics, publish a snapshot from a normal game callback with `ExtensionHooks.publishDiagnostics(id, Map.of(...))`. Values must be bounded JSON primitives, maps or lists; live actor objects are rejected and the snapshot is copied. Never read live game state on the MCP HTTP thread. `extension_status` returns snapshots and callback errors; `agent_status` includes transformation diagnostics. `list_extension_classes` and `read_extension_class` inspect the loaded extension provider's own selected JAR. They do not inspect arbitrary filesystem paths or execute extension methods.

Emit discrete debugging information with `ExtensionHooks.publishDebugEvent(id, "craft.completed", Map.of("recipe", recipeName, "level", level))`. Event kinds accept 1–64 letters, digits, dots, underscores or hyphens. Each copied payload has a conservative 24 KiB JSON budget; lists/maps have at most 128 elements, nesting at most five levels and strings at most 2,048 characters. The bridge retains the last 128 events and 16 snapshots (sampled at most once per second). Publish only useful transitions, rather than every render/update callback. MCP `debug_events` and `diagnostic_history` read these buffers by sequence without evaluating extension code. First callback failures automatically emit `hook.error`. The example mod demonstrates registration and startup diagnostics.

## Enabled Workshop mods (bridge 0.6.1)

Discovery makes a JAR available; B42’s resolved enabled-mod list controls whether its Java transforms run. The selected Workshop mod.info ID is inferred from the JAR declaration. For manual development JARs implement `BridgeMod.workshopModId()` with the exact native mod.info ID (case sensitive); its default is the extension ID. Levels declares `PzJBridgeLevels`. Server `Mods=` and save-specific/client server selections control activation, including required dependencies.

`configure` runs once to register transforms/settings/handlers, and must not start gameplay or background tasks. Gameplay belongs in transformed engine callbacks. Declare every instrumentation target so already loaded classes can be transformed when enabling. The bridge tracks transformed classes and retransforms them when disabled, restoring native methods even for advice that skips the original method. Callback dispatch is gated during deactivation. Settings remain available for configuration while disabled; MCP reports discovered `mods` separately from `activeMods`. Observer mode remains an isolated development smoke-test mode.

A multiplayer client advertises available JARs during the initial login, before B42 supplies the server’s mod list; gameplay activates only when that list is resolved. The server requires only enabled extensions. Install/update startup JARs with the game closed and restart after Steam changes JAR contents.

## Optional extension integration (0.6.1)

Use `ExtensionHooks.isEnabled("other.mod")` to check whether an optional peer is currently enabled. `ExtensionHooks.callIfEnabled("other.mod", "profile", actor)` returns null when the peer is absent or disabled, and otherwise forwards the event/arguments to its handler with normal error reporting. A null result can also mean that a handler returns no value; do not treat it as proof of failure. Call only on normal game callbacks, never MCP/HTTP threads. Share events through the parent bridge API instead of linking against another extension's classloader. Zombie Types and optional Levels demonstrate this pattern; see `docs/ZOMBIE_MOD_SPLIT.md`.
