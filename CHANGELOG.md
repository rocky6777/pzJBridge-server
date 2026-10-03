# pzJBridge binary releases

## 0.4.1

Correct stale menu version labels. Join rejection now lists all missing or incompatible Java components and explains manual agent installation, Workshop extension downloads and restarting. A version-specific client ZIP link is included. The stock missing-mod translation preserves the explanation even on a vanilla client. Both sides must update to 0.4.1. Private gameplay extensions remain excluded.

Automated tests cover the handshake, stale branding, client/server hook installation, MCP and installer behavior. Native translations preserve the reason; live join-screen layout still needs player validation.

## 0.4.0

Client and dedicated-server startup agents, API JAR, installers, client ZIP and optional authenticated local MCP companion. In-game display branding now includes the bridge version; the engine version used by networking and saves is preserved. MCP class inspection adds concise signatures alongside Java and bytecode views. Includes the extension callback API, startup instrumentation audit, bounded mod diagnostics, hook reports, debug events, history, runtime health and optional fixed game logs.

Install/update the startup agent on both client and server and restart both. This package does not include private gameplay extensions. Workshop publishing remains on hold. Build/source provenance and hashes are recorded in BUILD_INFO.json and SHA256SUMS.txt.
