# pzJBridge(0.6.3) dedicated-server tool

Performance analytics now provides separate detailed debug controls, MCP timing/stutter history, JVM/GC reports and declared mod conflicts. Client presets target a configurable 60 FPS through cooperating mods' cosmetics. No simulation throttling or engine rendering/streaming cuts are applied. See [the measurement guide](docs/PERFORMANCE.md) before evaluating gains.

The bridge includes shared Bridge options. The client Options → Bridge tab holds per-computer preferences. Sandbox creation and the server profile's SandboxVars contain world rules under Bridge, including debug toggles declared by extensions. Multiplayer clients use the server's world rules. Debug is off by default; error reporting and current MCP status remain available. Update the startup agent on both sides.

Ready-to-use Windows distribution for the verified Project Zomboid **42.21 dedicated server**, requiring its Java 25 runtime. Includes the built agent, installer, launcher and optional read-only Codex MCP companion. It contains no Project Zomboid classes, game files, account credentials or saved worlds.

Downloads: [server ZIP](https://github.com/rocky6777/pzJBridge-server/releases/download/v0.6.3/pzJBridge-server-0.6.3.zip) and [client ZIP](https://github.com/rocky6777/pzJBridge-server/releases/download/v0.6.3/pzJBridge-client-0.6.3.zip). The server ZIP and this repository also contain `client/pzJBridge-client-0.6.3.zip` for distribution to players. Extract the client ZIP and follow `ZomboidJBridgeClient/Contents/mods/ZomboidJBridgeClient/common/SETUP.md`; it contains the client JAR, installer, MCP tools and Workshop companion. Enabling the Lua companion alone cannot start the Java agent.

## Install and start

Download the ZIP from this repository's **Releases**, extract it to a stable folder, and stop your server normally before installing. Run these commands from the extracted folder, replacing the game directory if necessary:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Install-ServerAgent.ps1 -GameDirectory 'D:\Program Files (x86)\Steam\steamapps\common\Project Zomboid Dedicated Server'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Start-Server.ps1 -GameDirectory 'D:\Program Files (x86)\Steam\steamapps\common\Project Zomboid Dedicated Server' -ServerName 'servertest'
```

The installer verifies the supported login-class fingerprint and bundled agent checksum, backs up `ProjectZomboid64.json`, copies the JAR to `%LOCALAPPDATA%\ZomboidJBridgeServer`, and adds a server startup option while preserving other JVM options. It refuses unsupported game profiles. `-WhatIf` previews installation; `-Uninstall` removes the bridge startup option and retains backups and the stable JAR.

**Use the supplied Start-Server.ps1.** Stock `StartServer64.bat` constructs its own JVM command and ignores `ProjectZomboid64.json`. The supplied launcher reads the modified JSON, inherits its memory/Windows JVM settings, uses the bundled runtime, and keeps the console available. Optional `-CacheDirectory 'C:\PZServerData'` selects a separate cache/world location; `-DryRun` prints the invocation without launching. This launcher does not change existing server profiles, passwords or worlds. First-run account prompts are handled by the game. Stop with the console `quit` command.

The launcher sets `SteamAppId` and `SteamGameId` to the game's `108600` for the server process, then restores the calling shell's values. The dedicated tool's `380870` identity can answer server-info queries while Steam client connections time out at Getting server info. Installed Steam files are left untouched.

The server requires client agent 0.6.3 and any matching server-required Java extensions before admitting players. A missing agent or incompatible Java mod is rejected before admission with a detailed explanation, all missing/wrong-version components, manual client installer steps and a direct client ZIP URL. Vanilla clients use the game's translated missing-mod wrapper around that explanation. Workshop subscription alone does not install the startup agent. This is compatibility checking, not anti-cheat. No economy or MMO gameplay is included.

## Automatic Workshop Java extensions

Version 0.6.3 automatically discovers extensions declared by modders in `pzjbridge.properties`. The supplied launcher reads your profile's `WorkshopItems` setting and passes the selected IDs to the bridge. Pre-download those items before starting the JVM: use the game's normal server launcher/SteamCMD to finish downloads, stop it, then start with this launcher. A missing selected item fails startup. Downloads made by the game after startup cannot be instrumented during that run; restart afterwards.

The server's internal `steamapps/workshop/content/108600` cache is preferred, with the Steam library cache as a fallback. Custom layouts can use installer `-WorkshopDirectory 'D:\path\workshop\content\108600'`; `-DisableWorkshop` disables discovery. Manual `mods` extensions remain supported. With no profile Workshop IDs, automatic server discovery loads nothing.

Clients install bridge 0.6.3 once, subscribe to compatible extension items, wait for Steam to download them, then restart. Both sides need bridge 0.6.3. The client uses Steam's installed-item index, not the Lua enabled-mod list, so disabling a Lua companion does not unload its Java extension. Modders must include a declaration; unrelated Workshop JARs are ignored. See [the included modding guide](docs/MODDING.md) for the declaration format and [release details](docs/CHANGELOG.md). The small `java/zomboidjbridge-0.6.3-api.jar` is included for extension authors; use it and Byte Buddy 1.17.8 as compile-only dependencies.

## Codex MCP setup for mod development

MCP is optional for players/server operation. **Both agent-side MCP enablement and Codex settings are required for Codex inspection.** Install Python 3.9+ and JDK 25 (including `java` and `javap`). Re-run installation with MCP enabled:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Install-ServerAgent.ps1 -GameDirectory 'D:\Program Files (x86)\Steam\steamapps\common\Project Zomboid Dedicated Server' -EnableMcp -McpFile 'C:\PZBridge\connections\server.json'
```

Start the server using the supplied launcher. Merge `codex-mcp.example.toml` into `%USERPROFILE%\.codex\config.toml` (or a trusted project's `.codex/config.toml`), replacing every example path with the extracted package, Python/JDK and connection-file paths on your machine. Keep existing Codex settings and other MCP entries. Do not duplicate an existing `zomboid_server` table. Restart Codex after the change. This follows [official OpenAI MCP configuration](https://learn.chatgpt.com/docs/extend/mcp).

Ask Codex to call `zomboid_server.agent_status`, then inspect `zombie.network.packets.connection.LoginPacket` using `read_game_class` with `format=java` or `format=bytecode`. The bundled CFR decompiler reconstructs Java from the original installed game bytes; it cannot recover exact original source. Nothing in this package evaluates game methods or writes gameplay state through MCP.

The connection file is created only while the agent runs and contains a private bearer token. Never publish it. MCP binds only to `127.0.0.1`; do not expose it to the internet. For a remote server, run the companion on that host through your remote development setup. The installer does not edit Codex configuration or install Python/JDK automatically.

## Updates, uninstall and scope

Stop the server, extract the updated distribution and rerun the installer. Steam updates can replace the launcher JSON; rerun installation afterwards. Verify hook compatibility before supporting another game build. To uninstall:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Install-ServerAgent.ps1 -GameDirectory 'D:\Program Files (x86)\Steam\steamapps\common\Project Zomboid Dedicated Server' -Uninstall
```

After uninstalling, use the game's normal server launcher. Linux/macOS users must configure their launcher manually with `-javaagent:/stable/path/zomboidjbridge-0.6.3.jar=side=server;gameJar=/path/to/server/java/projectzomboid.jar`.

The agent embeds Byte Buddy 1.17.8 and its Apache 2.0 license/notice. CFR 0.152 is distributed with its MIT license under `licenses/`. Bridge distribution files are maintained by rocky6777; this is an unofficial Project Zomboid tool. See `BUILD_INFO.json` and `SHA256SUMS.txt` for the original agent build revision and binary checksums. Installer tests cover backup, repeat installation, option preservation, MCP, uninstall, and unsupported-profile refusal; the launcher is verified in dry-run mode. Version 0.6.3 Workshop extension loading, login instrumentation and MCP were verified in isolated JVMs using both installed game JARs. The previous 0.2.0 agent passed live multiplayer acceptance/rejection against local 42.21 client/server installations; full gameplay with 0.6.3 Workshop extensions remains untested.

## Optional Performance Boost 0.1.1

`optional/pzJBridge-Performance-0.1.1.zip` contains the companion mod and one Java extension JAR for client/single-player/dedicated-server use. Extract its `PzJBridgePerformance/Contents/mods/PzJBridgePerformance` folder into the appropriate Zomboid mods folder, then enable PzJBridgePerformance for the save/server. Install bridge 0.6.3 first. Client settings appear in Options > Bridge; server maintenance settings appear in Sandbox > Bridge. Disabling the companion mod removes the optimizer. No Steam upload is required for a local install. See the included Performance Boost README for limits and comparison instructions.
