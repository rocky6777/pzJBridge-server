# Releases

## 0.3.0 — Workshop Java extension discovery

- Automatically discover declared extension JARs in downloaded client Workshop items, before game class loading. Read Steam's installed-item index; ignore stray folders, authoring drafts and undeclared JARs.
- Support `common/pzjbridge.properties` and a complete `42.21/` profile override. Validate the exact bridge version, side filter, JAR existence and path containment before loading code.
- Merge Workshop JARs with the existing manual mods directory, deduplicate identical real paths and reject ambiguous provider names/duplicate extension IDs. Preserve ID-sorted configuration and server-required client-extension checks.
- Add `workshop=false`, custom `workshopDir` and comma-separated server `workshopItems` options. Add installer switches for disabling discovery or choosing a custom Workshop directory.
- Have the dedicated-server launcher pass the selected profile's `WorkshopItems` list. Missing configured downloads fail startup; download before launching the agent and restart after updates.
- Update client/server packages, modder examples, menu/artwork branding and complete Codex MCP instructions to 0.3.0. Keep the Workshop description's download link pointed at the public repository.

Upgrade the startup agent on both client and server. Automatic discovery uses installed files at startup, not live subscriptions or Lua enablement; it does not hot-load, download mods, or sandbox Java code.

Validation: Gradle unit tests and packaged-agent/extension smoke tests; installed-index selection/removal, profile/side filtering, malformed metadata, missing/incompatible/escaping JARs, duplicate providers/IDs and manual-plus-Workshop merging; isolated JVM checks with the original installed 42.21 client/server JARs, Workshop extension loading, login instrumentation, MCP decompilation/authentication/stdio and cleanup; client/server installer tests and server profile-selection dry run; Lua menu tests and installed-game Workshop validation. Full gameplay with 0.3.0 Workshop extensions has not been tested. The prior 0.2.0 live multiplayer acceptance/rejection results are recorded in MULTIPLAYER_TESTING.md.

## 0.2.0

Client/server agent, versioned admission hello, Java extension API, read-only MCP companion, client Workshop installer and public dedicated-server distribution. Live 42.21 multiplayer testing accepted the agent-enabled client and rejected a vanilla client before admission.
