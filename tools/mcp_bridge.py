#!/usr/bin/env python3
"""Read-only MCP stdio companion for one running ZomboidJBridge process."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.request
from urllib.parse import urlsplit

TOOLS = [
    *[{"name": name, "description": description,
       "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}}
      for name, description in (
          ("engine_diagnostics", "Read debug-only detached renderer batch/state-run/vertex totals, client pending network queues, Lua listener registration counts and MCP request totals. Requires a -debug launch; no gameplay objects, packet payloads or tokens are returned."),
          ("performance_status", "Read detached frame cadence, sampled/full callback and native-phase timings, JVM/GC metrics, cosmetic budgets and evidence-based recommendations. Enable detailed profiling in Options > Bridge > Performance. Inclusive timings overlap; GPU time is not measured."),
          ("mod_plan", "Read declared dependencies, shared contracts and native method overlaps. Flags override risks; does not prove compatibility with undeclared or external Lua/Java patches."))],
    {"name": "performance_history", "description": "Read up to 60 retained one-second performance samples and 32 stutters, correlated with camera movement and player travel. Use afterSequence for incremental reads; generation changes on a new session.",
     "inputSchema": {"type": "object", "properties": {"afterSequence": {"type": "integer", "minimum": 0}, "limit": {"type": "integer", "minimum": 1, "maximum": 60}}, "additionalProperties": False}},
    {"name": "read_game_log", "description": "Read the last part of the explicitly configured game log, optionally filtering errors/warnings. Captures Lua and native game errors outside Java mod hooks. No filename argument or arbitrary file access.",
     "inputSchema": {"type": "object", "properties": {"level": {"type": "string", "enum": ["all", "errors", "warnings"]},
         "lines": {"type": "integer", "minimum": 1, "maximum": 200}}, "additionalProperties": False}},
    {"name": "runtime_status", "description": "Read JVM uptime, Java version, heap use and up to 64 thread states; no game methods are evaluated.",
     "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "hook_status", "description": "Read successful class transformations and instrumentation/extension hook errors, with an optional class prefix.",
     "inputSchema": {"type": "object", "properties": {"prefix": {"type": "string"}}, "additionalProperties": False}},
    *[{"name": name, "description": description,
       "inputSchema": {"type": "object", "properties": {"id": {"type": "string"},
           "afterSequence": {"type": "integer", "minimum": 0}, "limit": {"type": "integer", "minimum": 1, "maximum": 128}},
           "required": ["id"], "additionalProperties": False}}
      for name, description in (
          ("diagnostic_history", "Read up to 16 retained timestamped mod snapshots, sampled at most once per second. Use afterSequence to retrieve newer entries; oldest entries expire."),
          ("debug_events", "Read up to 128 retained mod debug events such as kill rewards, visual effects and hook failures. Use afterSequence for incremental live debugging; oldest entries expire."))],
    {"name": "list_extension_classes", "description": "List compiled classes in a loaded Java extension's own JAR.",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}, "prefix": {"type": "string"},
         "offset": {"type": "integer", "minimum": 0}, "limit": {"type": "integer", "minimum": 1, "maximum": 500}},
         "required": ["id"], "additionalProperties": False}},
    {"name": "read_extension_class", "description": "Inspect a loaded extension's compiled Java or bytecode. Does not execute mod code; reconstructed source may differ from original.",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}, "name": {"type": "string"},
         "format": {"type": "string", "enum": ["java", "bytecode", "signatures"]}}, "required": ["id", "name"], "additionalProperties": False}},
    {"name": "extension_status", "description": "Read immutable game-thread diagnostics and hook errors from loaded Java extensions. Does not invoke extension methods or change gameplay.",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "additionalProperties": False}},
    {"name": "agent_status", "description": "Read agent side, version and installed extensions.",
     "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "list_game_classes", "description": "List original installed zombie.* classes with pagination.",
     "inputSchema": {"type": "object", "properties": {"prefix": {"type": "string"},
         "offset": {"type": "integer", "minimum": 0}, "limit": {"type": "integer", "minimum": 1, "maximum": 500}},
         "additionalProperties": False}},
    {"name": "read_game_class", "description": "Inspect original game bytecode. CFR returns reconstructed Java; javap returns declarations and bytecode. This does not expose original source or modified runtime classes.",
     "inputSchema": {"type": "object", "properties": {"name": {"type": "string"},
         "format": {"type": "string", "enum": ["java", "bytecode", "signatures"]}}, "required": ["name"], "additionalProperties": False}},
]


class Bridge:
    def __init__(self, connection_file, java, javap, cfr=None, game_log=None):
        self.connection_file = Path(connection_file)
        self.java, self.javap = java, javap
        self.cfr = Path(cfr).resolve() if cfr else None
        self.game_log = Path(game_log).resolve() if game_log else None

    def fetch(self, route, binary=False):
        try:
            config = json.loads(self.connection_file.read_text(encoding="utf-8"))
        except FileNotFoundError as missing:
            raise ValueError("No running debug bridge connection. Launch Zomboid with -debug, or the server launcher with -Debug, then retry.") from missing
        url = urlsplit(config["url"])
        if (url.scheme != "http" or url.hostname != "127.0.0.1" or not url.port
                or url.username or url.password or url.path or url.query or url.fragment):
            raise ValueError("Connection file must point to an HTTP IPv4 loopback endpoint")
        request = urllib.request.Request(config["url"] + route,
                                         headers={"Authorization": "Bearer " + config["token"]})
        # Ignore environment proxy settings and refuse redirects that might disclose the token.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        with opener.open(request, timeout=10) as response:
            body = response.read(4 * 1024 * 1024 + 1)
        if len(body) > 4 * 1024 * 1024:
            raise ValueError("Inspection response too large")
        return body if binary else json.loads(body)

    def call(self, name, args):
        if name == "engine_diagnostics":
            if args: raise ValueError("Unexpected arguments")
            return json.dumps(self.fetch("/diagnostics/engine"), indent=2)
        if name in ("performance_status", "mod_plan"):
            if args: raise ValueError("Unexpected arguments")
            return json.dumps(self.fetch("/performance" if name == "performance_status" else "/mod-plan"), indent=2)
        if name == "performance_history":
            if set(args) - {"afterSequence", "limit"}: raise ValueError("Unexpected arguments")
            after, limit = args.get("afterSequence", 0), args.get("limit", 60)
            if type(after) is not int or after < 0 or type(limit) is not int or not 1 <= limit <= 60:
                raise ValueError("Invalid performance cursor or limit")
            result = self.fetch("/performance/history")
            retained = result.get("samples", [])
            entries = [e for e in retained if e["sequence"] > after][:limit]
            cursor = entries[-1]["sequence"] if entries else max(after, result.get("latestSequence", 0))
            return json.dumps({"generation": result.get("generation", 0), "entries": entries,
                "nextSequence": cursor, "latestSequence": result.get("latestSequence", 0),
                "oldestRetainedSequence": retained[0]["sequence"] if retained else None,
                "stutters": result.get("stutters", []), "slowCalls": result.get("slowCalls", [])}, indent=2)
        if name == "read_game_log":
            if set(args) - {"level", "lines"}: raise ValueError("Unexpected arguments")
            level, lines = args.get("level", "errors"), args.get("lines", 100)
            if level not in ("all", "errors", "warnings") or type(lines) is not int or not 1 <= lines <= 200:
                raise ValueError("Invalid log filter or line limit")
            if not self.game_log: raise ValueError("Configure --game-log-file with this process's console log")
            with self.game_log.open("rb") as log:
                log.seek(0, 2)
                size = log.tell()
                start = max(0, size - 1024 * 1024)
                log.seek(start)
                raw = log.read(1024 * 1024)
            text = raw.decode("utf-8", errors="replace").splitlines()
            if start and text: text.pop(0)  # first line may start mid-character/mid-message
            if level != "all":
                pattern = r"error|exception|stack trace" if level == "errors" else r"warn|error|exception|stack trace"
                selected = set()
                for i, line in enumerate(text):
                    if re.search(pattern, line, re.IGNORECASE) and "No errors." not in line:
                        selected.update(range(i, min(len(text), i + 16)))
                text = [line for i, line in enumerate(text) if i in selected]
            return json.dumps({"level": level, "fileSizeBytes": size, "tailLimited": start > 0,
                "lines": [line[:2000] for line in text[-lines:]]}, indent=2)
        if name == "runtime_status":
            if args: raise ValueError("Unexpected arguments")
            return json.dumps(self.fetch("/runtime"), indent=2)
        if name == "hook_status":
            if set(args) - {"prefix"} or not isinstance(args.get("prefix", ""), str):
                raise ValueError("Invalid arguments")
            status = self.fetch("/status")
            return json.dumps({"side": status.get("side"),
                "transformedClasses": [n for n in status.get("transformedClasses", []) if n.startswith(args.get("prefix", ""))],
                "transformationErrors": status.get("transformationErrors", {}),
                "extensionErrors": {k: v.get("errors", {}) for k, v in status.get("extensionDiagnostics", {}).items()}}, indent=2)
        if name in ("diagnostic_history", "debug_events"):
            if set(args) - {"id", "afterSequence", "limit"}: raise ValueError("Unexpected arguments")
            extension_id = args.get("id", "")
            if not isinstance(extension_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,63}", extension_id):
                raise ValueError("Invalid extension id")
            after, limit = args.get("afterSequence", 0), args.get("limit", 32)
            if type(after) is not int or after < 0 or type(limit) is not int or not 1 <= limit <= 128:
                raise ValueError("Invalid event cursor or limit")
            result = self.fetch("/debug/" + extension_id)
            retained = result["history" if name == "diagnostic_history" else "events"]
            entries = [e for e in retained if e["sequence"] > after][:limit]
            # Advance to the last returned item, not past unread entries on a partial page.
            cursor = entries[-1]["sequence"] if entries else max(after, result["latestSequence"])
            return json.dumps({"id": extension_id, "entries": entries, "nextSequence": cursor,
                "oldestRetainedSequence": retained[0]["sequence"] if retained else None,
                "latestSequence": result["latestSequence"]}, indent=2)
        if name in ("list_extension_classes", "read_extension_class"):
            extension_id = args.get("id", "")
            if not isinstance(extension_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,63}", extension_id):
                raise ValueError("Invalid extension id")
            route = "/extension/" + extension_id
            if name == "list_extension_classes":
                if set(args) - {"id", "prefix", "offset", "limit"}: raise ValueError("Unexpected arguments")
                offset, limit, prefix = args.get("offset", 0), args.get("limit", 100), args.get("prefix", "")
                if type(offset) is not int or type(limit) is not int or offset < 0 or not 1 <= limit <= 500 or not isinstance(prefix, str):
                    raise ValueError("Invalid pagination")
                names = [n for n in self.fetch(route + "/classes") if n.startswith(prefix)]
                return json.dumps({"total": len(names), "classes": names[offset:offset + limit],
                    "nextOffset": offset + limit if offset + limit < len(names) else None}, indent=2)
            if set(args) - {"id", "name", "format"}: raise ValueError("Unexpected arguments")
            class_name = args.get("name", "")
            if not isinstance(class_name, str) or not re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*", class_name):
                raise ValueError("Invalid Java class name")
            return self.inspect(class_name, self.fetch(route + "/class/" + class_name, binary=True), args.get("format", "java"))
        if name == "extension_status":
            if set(args) - {"id"}: raise ValueError("Unexpected arguments")
            extension_id = args.get("id")
            if extension_id is not None and (not isinstance(extension_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,63}", extension_id)):
                raise ValueError("Invalid extension id")
            status = self.fetch("/status")
            snapshots = status.get("extensionDiagnostics", {})
            if extension_id is not None:
                if extension_id not in status.get("mods", {}): raise ValueError("Extension not loaded")
                snapshots = {extension_id: snapshots.get(extension_id, {})}
            return json.dumps({"side": status.get("side"), "extensions": snapshots,
                "transformationErrors": status.get("transformationErrors", {})}, indent=2)
        if name == "agent_status":
            if args: raise ValueError("Unexpected arguments")
            return json.dumps(self.fetch("/status"), indent=2)
        if name == "list_game_classes":
            if set(args) - {"prefix", "offset", "limit"}: raise ValueError("Unexpected arguments")
            offset, limit, prefix = args.get("offset", 0), args.get("limit", 100), args.get("prefix", "zombie.")
            if type(offset) is not int or type(limit) is not int or offset < 0 or not 1 <= limit <= 500 or not isinstance(prefix, str):
                raise ValueError("Invalid pagination")
            names = [n for n in self.fetch("/classes") if n.startswith(prefix)]
            return json.dumps({"total": len(names), "classes": names[offset:offset + limit],
                               "nextOffset": offset + limit if offset + limit < len(names) else None}, indent=2)
        if name != "read_game_class": raise ValueError("Unknown tool")
        if set(args) - {"name", "format"}: raise ValueError("Unexpected arguments")
        class_name = args.get("name", "")
        if not isinstance(class_name, str) or not re.fullmatch(r"zombie(?:\.[A-Za-z_$][A-Za-z0-9_$]*)+", class_name):
            raise ValueError("Expected a zombie.* Java class name")
        output_format = args.get("format", "java")
        if output_format not in ("java", "bytecode", "signatures"): raise ValueError("Unknown format")
        data = self.fetch("/class/" + class_name, binary=True)
        return self.inspect(class_name, data, output_format)

    def inspect(self, class_name, data, output_format):
        if output_format not in ("java", "bytecode", "signatures"): raise ValueError("Unknown format")
        with tempfile.TemporaryDirectory(prefix="zjb-inspect-") as folder:
            target = Path(folder) / (class_name.replace(".", "/") + ".class")
            target.parent.mkdir(parents=True)
            target.write_bytes(data)
            if output_format == "java":
                if not self.cfr or not self.cfr.is_file():
                    raise ValueError("Pass --cfr pointing to build/tools/cfr-0.152.jar, or select format=bytecode")
                command = [self.java, "-jar", str(self.cfr), str(target), "--silent", "true"]
            else:
                command = [self.javap, "-p", *([] if output_format == "signatures" else ["-c"]), str(target)]
            result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
            if result.returncode: raise ValueError("Class inspection failed: " + result.stderr[:2000])
            return result.stdout[:100000] + ("\n[truncated; inspect locally for full output]" if len(result.stdout) > 100000 else "")


for tool in TOOLS:
    tool["annotations"] = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}


def dispatch(message, bridge):
    request_id, method = message.get("id"), message.get("method")
    if request_id is None: return None
    params = message.get("params", {})
    if method == "initialize":
        requested = params.get("protocolVersion")
        version = requested if requested in ("2024-11-05", "2025-03-26", "2025-06-18") else "2025-06-18"
        result = {"protocolVersion": version, "capabilities": {"tools": {}},
                  "serverInfo": {"name": "zomboidjbridge", "version": "0.7.2"}}
    elif method == "ping": result = {}
    elif method == "tools/list": result = {"tools": TOOLS}
    elif method == "tools/call":
        try:
            value = bridge.call(params["name"], params.get("arguments", {}))
            result = {"content": [{"type": "text", "text": value}]}
        except Exception as error:
            # Never include connection configuration or the bearer token in output.
            result = {"isError": True, "content": [{"type": "text", "text": str(error)}]}
    else:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "Method not found"}}
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def main():
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--connection-file", required=True)
    parser.add_argument("--java", default=str(Path(os.environ["JAVA_HOME"]) / "bin/java.exe") if os.name == "nt" and "JAVA_HOME" in os.environ else "java")
    parser.add_argument("--javap", default=str(Path(os.environ["JAVA_HOME"]) / "bin/javap.exe") if os.name == "nt" and "JAVA_HOME" in os.environ else "javap")
    parser.add_argument("--cfr")
    parser.add_argument("--game-log-file", help="Optional fixed game console log for live Lua/native error inspection")
    args = parser.parse_args()
    bridge = Bridge(args.connection_file, args.java, args.javap, args.cfr, args.game_log_file)
    for line in sys.stdin:
        if len(line) > 1024 * 1024:
            print("Oversized MCP request", file=sys.stderr)
            continue
        try:
            message = json.loads(line)
            if not isinstance(message, dict): raise ValueError("Expected JSON-RPC object")
            response = dispatch(message, bridge)
        except Exception:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Invalid JSON-RPC request"}}
        if response is not None:
            print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
