#!/usr/bin/env python3
"""Backward-compatible wrapper for the ai-sdd-bootstrap package.

Kimi Code skills historically place the entry script under scripts/.
This thin wrapper keeps that convention while the real implementation
lives in the ai_sdd_bootstrap package.
"""

import sys
from pathlib import Path

# Ensure the repository root (which contains the ai_sdd_bootstrap package)
# appears before this script's own directory on sys.path. Otherwise Python
# would try to import `ai_sdd_bootstrap` from this very file.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai_sdd_bootstrap.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
