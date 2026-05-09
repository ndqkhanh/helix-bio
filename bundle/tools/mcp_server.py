"""Helix-Bio MCP server stub.

Tools published:

- ``helix.bind(claim)`` — ontology binding.
- ``helix.review(output)`` — dual-use review.
- ``helix.lookup(name, ontology)`` — direct ontology lookup.
- ``helix.health()`` — adapter health.
"""
from __future__ import annotations

import json
import sys


def main() -> int:
    line = sys.stdin.readline()
    if not line.strip():
        print(json.dumps({"error": "no input"}))
        return 0
    req = json.loads(line)
    tool = req.get("tool", "helix.health")
    args = req.get("args") or {}
    if tool == "helix.bind":
        print(json.dumps({"tool": tool, "result": {"binding": "stub:0000"}}))
    elif tool == "helix.review":
        print(json.dumps({"tool": tool, "result": {"tier": "informational", "blocked": False}}))
    elif tool == "helix.lookup":
        print(json.dumps({"tool": tool, "result": {"id": "stub:0000"}}))
    elif tool == "helix.health":
        print(json.dumps({"tool": tool, "result": {"ok": True}}))
    else:
        print(json.dumps({"tool": tool, "error": f"unknown tool {tool}"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
