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
    {"name": "agent_status", "description": "Read agent side, version and installed extensions.",
     "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "list_game_classes", "description": "List original installed zombie.* classes with pagination.",
     "inputSchema": {"type": "object", "properties": {"prefix": {"type": "string"},
         "offset": {"type": "integer", "minimum": 0}, "limit": {"type": "integer", "minimum": 1, "maximum": 500}},
         "additionalProperties": False}},
    {"name": "read_game_class", "description": "Inspect original game bytecode. CFR returns reconstructed Java; javap returns declarations and bytecode. This does not expose original source or modified runtime classes.",
     "inputSchema": {"type": "object", "properties": {"name": {"type": "string"},
         "format": {"type": "string", "enum": ["java", "bytecode"]}}, "required": ["name"], "additionalProperties": False}},
]


class Bridge:
    def __init__(self, connection_file, java, javap, cfr=None):
        self.connection_file = Path(connection_file)
        self.java, self.javap = java, javap
        self.cfr = Path(cfr).resolve() if cfr else None

    def fetch(self, route, binary=False):
        config = json.loads(self.connection_file.read_text(encoding="utf-8"))
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
        if output_format not in ("java", "bytecode"): raise ValueError("Unknown format")
        data = self.fetch("/class/" + class_name, binary=True)
        with tempfile.TemporaryDirectory(prefix="zjb-inspect-") as folder:
            target = Path(folder) / (class_name.replace(".", "/") + ".class")
            target.parent.mkdir(parents=True)
            target.write_bytes(data)
            if output_format == "java":
                if not self.cfr or not self.cfr.is_file():
                    raise ValueError("Pass --cfr pointing to build/tools/cfr-0.152.jar, or select format=bytecode")
                command = [self.java, "-jar", str(self.cfr), str(target), "--silent", "true"]
            else:
                command = [self.javap, "-p", "-c", str(target)]
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
                  "serverInfo": {"name": "zomboidjbridge", "version": "0.3.0"}}
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
    args = parser.parse_args()
    bridge = Bridge(args.connection_file, args.java, args.javap, args.cfr)
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
