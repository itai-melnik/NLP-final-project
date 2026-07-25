"""Shared configuration loading, hashing, and path resolution.

Every stage loads the same ``config/experiment.yaml`` through here and stamps
the resulting :func:`config_hash` into its frozen artifact, so any number in the
paper is traceable to the exact configuration that produced it (spec §7).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# Repo root = two levels up from this file (src/prjudge/config.py -> repo root).
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "experiment.yaml"

# Load repo-root .env into os.environ (does not override already-exported vars).
# README / .env.example document this as the place for Stage-2 API keys.
load_dotenv(REPO_ROOT / ".env")


class Config:
    """Thin wrapper around the parsed YAML with path resolution + hashing."""

    def __init__(self, data: dict[str, Any], source: Path):
        self._data = data
        self.source = source

    # -- dict-like access ---------------------------------------------------
    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    @property
    def data(self) -> dict[str, Any]:
        return self._data

    # -- paths --------------------------------------------------------------
    def path(self, key: str) -> Path:
        """Resolve a key under ``paths:`` to an absolute path from the repo root."""
        return (REPO_ROOT / self._data["paths"][key]).resolve()

    @property
    def artifacts_dir(self) -> Path:
        return self.path("artifacts_dir")

    # -- hashing ------------------------------------------------------------
    def hash(self) -> str:
        """Stable SHA-256 of the full config (canonical JSON, sorted keys)."""
        return config_hash(self._data)


def load_config(path: str | Path | None = None) -> Config:
    """Load ``config/experiment.yaml`` (or an explicit path)."""
    p = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Config(data, source=p.resolve())


def config_hash(data: Any) -> str:
    """SHA-256 over canonical JSON — order-independent, stable across runs."""
    blob = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()
