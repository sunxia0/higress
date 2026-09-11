#!/usr/bin/env python3
"""Verification-only overlay: compare sessions in memory; never publish them."""
import os
import sys
from http.server import ThreadingHTTPServer

sys.path.insert(0, os.environ.get("MCP_HARNESS_DIR", "/harness"))
import auto_backend
import backend


def session_identity(method, key, session):
    needs_session = method in ("notifications/initialized", "tools/call")
    return {
        "requestSessionMatches": (key in ("alice", "bob") and session == "auto-session-" + key) if needs_session else None,
        "unexpectedEarlySession": bool(session) if not needs_session else False,
    }


original_event_fields = auto_backend.event_fields


def precise_event_fields(handler, request):
    event = original_event_fields(handler, request)
    event.update(session_identity(request.get("method"), handler.headers.get("baggage", ""),
                                  handler.headers.get("Mcp-Session-Id", "")))
    return event


auto_backend.event_fields = precise_event_fields

if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), backend.Handler).serve_forever()
