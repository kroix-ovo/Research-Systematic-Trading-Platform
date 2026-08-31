from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import sys

import pytest

from fund.a1 import A1Violation, assert_runtime_dependency_boundary
from fund.runtime import ModelCredentialError, assert_no_model_credentials


REPOSITORY = Path(__file__).resolve().parents[2]


def test_runtime_dependency_boundary_is_clean() -> None:
    assert_runtime_dependency_boundary(REPOSITORY / "src" / "fund")


def test_runtime_dependency_boundary_detects_transitive_client(tmp_path: Path) -> None:
    package = tmp_path / "fund"
    shutil.copytree(REPOSITORY / "src" / "fund", package)
    (package / "runtime" / "bad_path.py").write_text(
        "from fund import inference_adapter\n", encoding="utf-8"
    )
    (package / "inference_adapter.py").write_text("import httpx\n", encoding="utf-8")

    with pytest.raises(A1Violation, match=r"fund\.runtime.*httpx"):
        assert_runtime_dependency_boundary(package)


def test_runtime_rejects_model_credentials() -> None:
    assert_no_model_credentials({"BROKER_API_KEY": "allowed"})
    with pytest.raises(ModelCredentialError, match="OPENAI_API_KEY"):
        assert_no_model_credentials({"OPENAI_API_KEY": "must-not-be-here"})


def test_import_linter_a1_contract_is_green() -> None:
    executable = Path(sys.executable).with_name("lint-imports")
    assert executable.exists(), "import-linter must be installed by the dev extra"
    completed = subprocess.run(
        [str(executable), "--config", "pyproject.toml"],
        cwd=REPOSITORY,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_import_linter_contract_breaks_on_transitive_client(tmp_path: Path) -> None:
    executable = Path(sys.executable).with_name("lint-imports")
    package = tmp_path / "fund"
    runtime = package / "runtime"
    runtime.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (runtime / "__init__.py").write_text(
        "from fund.adapter import call_model\n", encoding="utf-8"
    )
    (package / "adapter.py").write_text(
        "import httpx\n\ndef call_model():\n    return httpx\n", encoding="utf-8"
    )
    config = tmp_path / "importlinter.toml"
    config.write_text(
        """[tool.importlinter]
root_package = "fund"
include_external_packages = true

[[tool.importlinter.contracts]]
name = "test A1"
type = "forbidden"
source_modules = ["fund.runtime"]
forbidden_modules = ["httpx"]
""",
        encoding="utf-8",
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(tmp_path)
    completed = subprocess.run(
        [str(executable), "--config", str(config)],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode != 0
    assert "BROKEN" in completed.stdout
