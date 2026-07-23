"""Stage 2 — provider judge clients + resumable runner (spec §5).

The runner walks a *run spec* (a subset of the full matrix), skips cells already
present in the run's output file, calls each judge with structured-output
enforcement, retries with backoff, and appends one JSONL row per call carrying
the raw response, parsed fields, token counts, model version, and timestamp.

Resumability lives entirely in the JSONL: a dead process costs nothing — rerun
the same spec and it continues from where it stopped. Pilot runs write their own
files and are never mixed with ``results_v1.jsonl`` (spec §5).
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .config import Config
from .prompts import build_judge_user_message, get_judge_prompt


# ---------------------------------------------------------------------------
# Cell keying
# ---------------------------------------------------------------------------

def cell_key(task_id: str, variant: str, judge: str, trial: int, prompt_version: str) -> str:
    """Stable identity of one judge call. Resume skips keys already in the file."""
    raw = f"{task_id}|{variant}|{judge}|{trial}|{prompt_version}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Provider clients (lazy SDK imports — package loads without anthropic/openai)
# ---------------------------------------------------------------------------

@dataclass
class JudgeResponse:
    parsed: dict[str, Any] | None
    raw_text: str
    model_version: str
    input_tokens: int | None
    output_tokens: int | None
    error: str | None = None


class BaseJudgeClient:
    def __init__(self, judge_cfg: dict[str, Any]):
        self.cfg = judge_cfg
        self.name = judge_cfg["name"]
        self.model = judge_cfg["model"]
        self.temperature = judge_cfg.get("temperature")  # None => provider default / omit

    def judge(self, system: str, user: str, schema: dict, max_tokens: int) -> JudgeResponse:
        raise NotImplementedError


class AnthropicJudge(BaseJudgeClient):
    """Claude-family judge via structured outputs (output_config.format)."""

    def __init__(self, judge_cfg: dict[str, Any]):
        super().__init__(judge_cfg)
        import anthropic  # noqa: PLC0415
        self._client = anthropic.Anthropic()

    def judge(self, system: str, user: str, schema: dict, max_tokens: int) -> JudgeResponse:
        kwargs: dict[str, Any] = dict(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )
        # temperature is removed on Opus 4.8 / Sonnet 5 (400 if sent); only pass
        # it for older pinned models that still accept it.
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        resp = self._client.messages.create(**kwargs)
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        parsed = _safe_json(text)
        return JudgeResponse(
            parsed=parsed, raw_text=text,
            model_version=getattr(resp, "model", self.model),
            input_tokens=getattr(resp.usage, "input_tokens", None),
            output_tokens=getattr(resp.usage, "output_tokens", None),
        )


class OpenAIJudge(BaseJudgeClient):
    """GPT-family or OpenAI-compatible (hosted OSS) judge via json_schema mode."""

    def __init__(self, judge_cfg: dict[str, Any]):
        super().__init__(judge_cfg)
        import openai  # noqa: PLC0415
        api_key = os.environ.get(judge_cfg.get("env_key", ""), None)
        base_url = judge_cfg.get("base_url")
        self._client = openai.OpenAI(api_key=api_key, base_url=base_url)

    def judge(self, system: str, user: str, schema: dict, max_tokens: int) -> JudgeResponse:
        kwargs: dict[str, Any] = dict(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "pr_review", "schema": schema, "strict": True},
            },
            max_tokens=max_tokens,
        )
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        resp = self._client.chat.completions.create(**kwargs)
        text = resp.choices[0].message.content or ""
        parsed = _safe_json(text)
        usage = getattr(resp, "usage", None)
        return JudgeResponse(
            parsed=parsed, raw_text=text,
            model_version=getattr(resp, "model", self.model),
            input_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
            output_tokens=getattr(usage, "completion_tokens", None) if usage else None,
        )


class MockJudge(BaseJudgeClient):
    """Deterministic canned judge — no API, no key. Tests keying/resume/plumbing."""

    def judge(self, system: str, user: str, schema: dict, max_tokens: int) -> JudgeResponse:
        # Deterministic yes/no per item from a hash of the user message, so the
        # same cell always yields the same mock answer (resume idempotency).
        h = hashlib.sha256(user.encode("utf-8")).digest()
        checklist = {
            f"item_{i}": {
                "answer": "yes" if h[i] % 2 else "no",
                "evidence": "mock evidence",
            }
            for i in range(1, 11)
        }
        parsed = {
            "issues": [] if h[0] % 3 else [
                {"file": "mock.py", "approx_line": 1, "severity": "minor",
                 "description": "mock issue"}
            ],
            "checklist": checklist,
            "justification": "mock justification",
        }
        text = json.dumps(parsed)
        return JudgeResponse(parsed=parsed, raw_text=text, model_version="mock",
                             input_tokens=len(user) // 4, output_tokens=len(text) // 4)


def make_client(judge_cfg: dict[str, Any], *, mock: bool) -> BaseJudgeClient:
    if mock:
        return MockJudge(judge_cfg)
    provider = judge_cfg["provider"]
    if provider == "anthropic":
        return AnthropicJudge(judge_cfg)
    if provider in ("openai", "openai_compatible"):
        return OpenAIJudge(judge_cfg)
    raise ValueError(f"unknown judge provider: {provider}")


def _safe_json(text: str) -> dict[str, Any] | None:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Run spec
# ---------------------------------------------------------------------------

@dataclass
class RunSpec:
    """A subset of the full matrix to execute, written to its own output file."""
    run_name: str
    variants: list[str]
    judges: list[str]
    task_ids: list[str]
    trials: int
    prompt_version: str

    def cells(self) -> list[tuple[str, str, str, int]]:
        """Every (task_id, variant, judge, trial) cell in this spec."""
        out = []
        for tid in self.task_ids:
            for v in self.variants:
                for j in self.judges:
                    for t in range(1, self.trials + 1):
                        out.append((tid, v, j, t))
        return out


def resolve_run_spec(
    config: Config,
    *,
    run_name: str,
    variants: list[str] | None = None,
    judges: list[str] | None = None,
    prs: list[str] | None = None,
    limit: int | None = None,
    trials: int | None = None,
    prompt_version: str | None = None,
) -> RunSpec:
    """Build a RunSpec from CLI-style args, defaulting to the full matrix."""
    manifest_path = config.artifacts_dir / f"selection_manifest_{config['versions']['selection']}.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    all_task_ids = list(manifest["task_ids"])

    all_variants = list(config["variants"]["ids"])
    all_judges = [j["name"] for j in config["judging"]["judges"]]

    variants = variants or all_variants
    judges = judges or all_judges
    task_ids = prs if prs else all_task_ids
    if limit is not None:
        task_ids = task_ids[:limit]
    trials = trials if trials is not None else config["judging"]["trials"]
    prompt_version = prompt_version or config["judging"]["prompt_version"]

    _validate(variants, all_variants, "variant")
    _validate(judges, all_judges, "judge")
    _validate(task_ids, all_task_ids, "task_id")

    return RunSpec(run_name, variants, judges, task_ids, trials, prompt_version)


def _validate(subset: Iterable[str], universe: Iterable[str], label: str) -> None:
    unknown = set(subset) - set(universe)
    if unknown:
        raise ValueError(f"unknown {label}(s): {sorted(unknown)}")


# ---------------------------------------------------------------------------
# Variant loading + output file
# ---------------------------------------------------------------------------

def load_judge_input(config: Config, task_id: str, variant: str) -> dict[str, Any]:
    """Read the frozen judge_input fields for one (task_id, variant)."""
    vdir = config.artifacts_dir / f"variants_{config['versions']['variants']}"
    with open(vdir / f"{task_id}__{variant}.json", "r", encoding="utf-8") as f:
        return json.load(f)["judge_input"]


def existing_keys(output_path: Path) -> set[str]:
    """Cell keys already recorded in the run's output file (for resume)."""
    keys: set[str] = set()
    if not output_path.exists():
        return keys
    with open(output_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                keys.add(json.loads(line)["cell_key"])
            except (json.JSONDecodeError, KeyError):
                continue
    return keys


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

@dataclass
class RunSummary:
    run_name: str
    total_cells: int
    already_done: int
    attempted: int
    succeeded: int
    failed: int
    input_tokens: int = 0
    output_tokens: int = 0
    errors: list[str] = field(default_factory=list)


def run_judges(
    config: Config,
    spec: RunSpec,
    *,
    mock: bool = False,
    progress: bool = True,
) -> RunSummary:
    """Execute a run spec resumably, appending JSONL rows to its output file."""
    runs_dir = config.artifacts_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    output_path = runs_dir / f"{spec.run_name}.jsonl"

    prompt = get_judge_prompt(spec.prompt_version)
    system, schema = prompt["system"], prompt["schema"]
    max_tokens = config["judging"]["max_output_tokens"]
    max_retries = config["judging"]["max_retries"]
    base_delay = config["judging"]["retry_base_delay"]
    judge_cfgs = {j["name"]: j for j in config["judging"]["judges"]}

    # Shuffle cell order (seeded) so provider drift can't correlate with any axis.
    cells = spec.cells()
    rng = random.Random(f"{config['seed']}:{spec.run_name}")
    rng.shuffle(cells)

    done = existing_keys(output_path)
    clients: dict[str, BaseJudgeClient] = {}

    summary = RunSummary(spec.run_name, len(cells), 0, 0, 0, 0)

    with open(output_path, "a", encoding="utf-8") as out:
        for idx, (tid, variant, judge, trial) in enumerate(cells, start=1):
            key = cell_key(tid, variant, judge, trial, spec.prompt_version)
            if key in done:
                summary.already_done += 1
                continue

            if judge not in clients:
                clients[judge] = make_client(judge_cfgs[judge], mock=mock)
            client = clients[judge]

            ji = load_judge_input(config, tid, variant)
            user = build_judge_user_message(ji, spec.prompt_version)

            resp, err = _call_with_retry(client, system, user, schema, max_tokens,
                                         max_retries, base_delay)
            summary.attempted += 1
            row = {
                "cell_key": key,
                "run_name": spec.run_name,
                "task_id": tid,
                "variant": variant,
                "judge": judge,
                "trial": trial,
                "prompt_version": spec.prompt_version,
                "model": judge_cfgs[judge]["model"],
                "model_version": resp.model_version if resp else None,
                "mock": mock,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "parsed": resp.parsed if resp else None,
                "raw_response": resp.raw_text if resp else None,
                "input_tokens": resp.input_tokens if resp else None,
                "output_tokens": resp.output_tokens if resp else None,
                "error": err,
            }
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            done.add(key)

            if err or (resp and resp.parsed is None):
                summary.failed += 1
                summary.errors.append(f"{tid}/{variant}/{judge}/t{trial}: {err or 'unparseable'}")
            else:
                summary.succeeded += 1
                summary.input_tokens += resp.input_tokens or 0
                summary.output_tokens += resp.output_tokens or 0

            if progress and idx % 25 == 0:
                print(f"  [{idx}/{len(cells)}] done={summary.already_done} "
                      f"ok={summary.succeeded} fail={summary.failed}", flush=True)

    return summary


def _call_with_retry(client, system, user, schema, max_tokens, max_retries, base_delay):
    """Call a judge with exponential backoff; return (JudgeResponse|None, error|None)."""
    last_err = None
    for attempt in range(max_retries):
        try:
            resp = client.judge(system, user, schema, max_tokens)
            return resp, resp.error
        except Exception as e:  # noqa: BLE001 — record and back off on any provider error
            last_err = f"{type(e).__name__}: {e}"
            if attempt < max_retries - 1:
                time.sleep(min(base_delay * (2 ** attempt), 60.0))
    return None, last_err
