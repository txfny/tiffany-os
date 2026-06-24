#!/usr/bin/env python3
"""Normalize an Apple Health Shortcut payload from stdin or a JSON file."""

import json
import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "azure-functions"))

from shared.apple_health import normalize_apple_health_payload  # noqa: E402


def main() -> int:
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as fh:
            payload = json.load(fh)
    else:
        payload = json.load(sys.stdin)

    print(json.dumps(normalize_apple_health_payload(payload), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
