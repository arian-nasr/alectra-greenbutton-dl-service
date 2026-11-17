"""Check that the configured OpenRouter model supports tool/function calling.

Run manually before starting the service:
    python scripts/smoke_test_model.py

This file is intentionally not imported by the service.
"""
from __future__ import annotations

import json
import os
import sys
from urllib import error, request

from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
API_KEY = os.getenv("OPENROUTER_API_KEY", "")


def main() -> int:
    if not API_KEY:
        print("OPENROUTER_API_KEY is not set", file=sys.stderr)
        return 1

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": "Use the calculator tool to add 2 and 2.",
            }
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "Add two integers",
                    "parameters": {
                        "type": "object",
                        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
                        "required": ["a", "b"],
                    },
                },
            }
        ],
        "tool_choice": "required",
    }
    req = request.Request(
        f"{BASE_URL}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        print(f"OpenRouter returned HTTP {exc.code}: {exc.read().decode('utf-8')}", file=sys.stderr)
        return 1
    except error.URLError as exc:
        print(f"Could not reach OpenRouter: {exc}", file=sys.stderr)
        return 1

    tool_calls = body.get("choices", [{}])[0].get("message", {}).get("tool_calls") or []
    if not tool_calls:
        print(f"{MODEL} did not emit a tool call; it is not suitable for Browser Use.", file=sys.stderr)
        return 1

    print(f"OK: {MODEL} supports tool calling")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
