#!/usr/bin/env python3
"""Download the Raft starter shelf and build the search index. Run on Aurelium: python scripts/build_shelf.py"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "services", "agent-backend"))
from raft import library  # noqa: E402

report = library.build(only=set(sys.argv[1:]) or None)
print(json.dumps(report, indent=2))
print("db:", library.DB_PATH, os.path.getsize(library.DB_PATH) // 1024, "KB")
sys.exit(1 if any("error" in r for r in report) else 0)
