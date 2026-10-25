"""Windows-only check for subprocess and encoding (plan M10). Runs without a chain.

Calls the CLIs with sys.executable and cwd at the project root, the same way the API will.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_subprocess_returns_json():
    result = subprocess.run(
        [sys.executable, "-c", 'import json; print(json.dumps({"ok": True}))'],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout) == {"ok": True}


def test_gen_bills_cli_help_runs_from_project_root():
    if not (PROJECT_ROOT / "sim" / "gen_bills.py").exists():
        pytest.skip("sim/ not pulled yet")
    result = subprocess.run(
        [sys.executable, "-m", "sim.gen_bills", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
