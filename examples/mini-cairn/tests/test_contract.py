import subprocess
import sys
from pathlib import Path

import mini_cairn


def test_mini_cairn_module_and_public_exports():
    assert mini_cairn.Cairn is not None
    assert mini_cairn.FakeModelClient is not None
    assert not hasattr(mini_cairn, "MiniAgent")
    result = subprocess.run([sys.executable, "-m", "mini_cairn", "--help"], capture_output=True, text=True, check=True)
    assert "Teaching-sized Cairn agent harness" in result.stdout


def test_readme_main_mapping_points_to_existing_files():
    repo_root = Path(__file__).resolve().parents[3]
    main_files = [
        "cairn/cli.py",
        "cairn/runtime.py",
        "cairn/agent_loop.py",
        "cairn/context_manager.py",
        "cairn/providers/clients.py",
        "cairn/tool_executor.py",
        "cairn/tools.py",
        "cairn/task_state.py",
        "cairn/run_store.py",
        "cairn/workspace.py",
    ]
    for path in main_files:
        assert (repo_root / path).exists()
