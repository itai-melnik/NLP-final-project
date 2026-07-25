"""Stage 2 — batch-mode judging (spec §5, batch addendum).

Anthropic's Message Batches API and OpenAI's Batch API give a 50% discount on
input+output tokens with a <=24h completion window, using the exact same
models as the sync path (quality-identical per provider docs). This module
implements a single idempotent "advance" step, re-run until every cell in the
spec has a row:

    python scripts/02_run_judges.py --run-name results_v1 --batch

Each call, per batch-capable judge in the spec:

1. **Collect** — poll any in-flight provider batches recorded in the run's
   state file; for any that finished, append succeeded results as JSONL rows
   (skipping keys already present) and mark them collected. Errored/expired
   items are simply not appended; they count toward that cell's resubmit
   budget.
2. **Submit** — compute the cells still missing (not in the JSONL, not inside
   an in-flight batch, not already exhausted on resubmits), submit a new
   provider batch for them, and record it in the state file. An opportunistic
   immediate collect follows so an instant-complete mock batch finishes in the
   same invocation; real batches simply stay in-flight for the next call.
3. **Report** — a per-judge status the caller can print / use for exit codes.

Cells that have failed ``max_resubmits`` times are never resubmitted — they
are surfaced as "needs sync" (mop up via ``--judges ... `` without ``--batch``).
Judges whose provider has no batch API (the open judge, via an OpenAI-compatible
host) are skipped with an explicit message instead of silently running
hundreds of sync calls under a ``--batch`` flag.

The state file (``artifacts/runs/{run_name}.batches.json``) is safe to delete:
in-flight batches recorded in it are simply forgotten and their cells
resubmit on the next call. The JSONL itself is always the source of truth for
"is this cell done" — the state file only tracks "is this cell in flight",
so a deleted/stale state file can produce redundant provider batches but never
duplicate JSONL rows (``existing_keys`` guards every append, same as sync).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import Config
from .judge import (
    AnthropicJudge,
    JudgeResponse,
    MockJudge,
    OpenAIJudge,
    RunSpec,
    build_result_row,
    cell_key,
    existing_keys,
    load_judge_input,
    parse_anthropic_message,
    parse_openai_response_body,
)
from .prompts import build_judge_user_message, get_judge_prompt

# Providers with a real batch API (spec: no batch for openai_compatible / open judge).
BATCH_CAPABLE_PROVIDERS = {"anthropic", "openai"}


# ---------------------------------------------------------------------------
# Batch state — persisted per run_name, safe to delete
# ---------------------------------------------------------------------------

class BatchState:
    """``artifacts/runs/{run_name}.batches.json``.

    ``{"batches": [{batch_id, provider, judge, cell_keys, n_requests,
    submitted_at, status, collected}], "attempts": {cell_key: n}}``

    Append-only in spirit: batches are added and marked collected in place,
    never removed by this module. Safe to delete entirely — in-flight batches
    are simply forgotten and their cells resubmit (§ module docstring).
    """

    def __init__(self, path: Path):
        self.path = path
        self.batches: list[dict[str, Any]] = []
        self.attempts: dict[str, int] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        self.batches = data.get("batches", [])
        self.attempts = data.get("attempts", {})

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(
            json.dumps({"batches": self.batches, "attempts": self.attempts}, indent=2),
            encoding="utf-8",
        )
        tmp.replace(self.path)

    def add_batch(self, *, batch_id: str, provider: str, judge: str,
                  cell_keys: list[str], status: str) -> None:
        self.batches.append({
            "batch_id": batch_id,
            "provider": provider,
            "judge": judge,
            "cell_keys": cell_keys,
            "n_requests": len(cell_keys),
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "collected": False,
        })

    def mark_collected(self, batch_id: str, *, status: str) -> None:
        for b in self.batches:
            if b["batch_id"] == batch_id:
                b["collected"] = True
                b["status"] = status

    def pending_batches(self, judge: str) -> list[dict[str, Any]]:
        return [b for b in self.batches if b["judge"] == judge and not b["collected"]]

    def in_flight_cells(self, judge: str) -> set[str]:
        out: set[str] = set()
        for b in self.pending_batches(judge):
            out.update(b["cell_keys"])
        return out

    def record_attempt(self, key: str) -> None:
        self.attempts[key] = self.attempts.get(key, 0) + 1


# ---------------------------------------------------------------------------
# Batch request/result plumbing (provider-agnostic)
# ---------------------------------------------------------------------------

@dataclass
class BatchRequestItem:
    custom_id: str  # == cell_key; fits both providers' custom_id constraints
    system: str
    user: str
    schema: dict[str, Any]
    max_tokens: int


@dataclass
class BatchResultItem:
    custom_id: str
    status: str  # "succeeded" | "errored" | "expired" | "canceled"
    response: JudgeResponse | None
    error: str | None


class BaseBatchClient:
    provider: str = "base"
    max_requests_per_batch: int = 10_000
    max_batch_bytes: int = 100 * 1024 * 1024

    def submit(self, items: list[BatchRequestItem]) -> str:
        raise NotImplementedError

    def poll_ended(self, batch_id: str) -> bool:
        """True once the provider batch has reached a terminal state."""
        raise NotImplementedError

    def collect(self, batch_id: str) -> list[BatchResultItem]:
        raise NotImplementedError


class AnthropicBatchClient(BaseBatchClient):
    """Wraps an ``AnthropicJudge`` to reuse its API client + ``build_params``
    so batch request bodies are byte-identical to the sync path."""

    provider = "anthropic"
    # Anthropic Message Batches API limits (well above our ~1,080/judge worst case).
    max_requests_per_batch = 100_000
    max_batch_bytes = 256 * 1024 * 1024

    def __init__(self, judge_cfg: dict[str, Any]):
        self._judge = AnthropicJudge(judge_cfg)

    def submit(self, items: list[BatchRequestItem]) -> str:
        requests = [
            {
                "custom_id": it.custom_id,
                "params": self._judge.build_params(it.system, it.user, it.schema, it.max_tokens),
            }
            for it in items
        ]
        batch = self._judge._client.messages.batches.create(requests=requests)  # noqa: SLF001
        return batch.id

    def poll_ended(self, batch_id: str) -> bool:
        batch = self._judge._client.messages.batches.retrieve(batch_id)  # noqa: SLF001
        return batch.processing_status == "ended"

    def collect(self, batch_id: str) -> list[BatchResultItem]:
        out: list[BatchResultItem] = []
        for entry in self._judge._client.messages.batches.results(batch_id):  # noqa: SLF001
            rtype = entry.result.type
            if rtype == "succeeded":
                resp = parse_anthropic_message(entry.result.message, default_model=self._judge.model)
                out.append(BatchResultItem(entry.custom_id, "succeeded", resp, None))
            else:
                err = getattr(entry.result, "error", None)
                out.append(BatchResultItem(entry.custom_id, rtype, None, str(err) if err else rtype))
        return out


class OpenAIBatchClient(BaseBatchClient):
    """Wraps an ``OpenAIJudge`` to reuse its API client + ``build_params`` so
    the batch input JSONL body is byte-identical to the sync chat-completion
    kwargs."""

    provider = "openai"
    # OpenAI Batch API limits (well above our ~1,080/judge worst case).
    max_requests_per_batch = 50_000
    max_batch_bytes = 200 * 1024 * 1024
    _TERMINAL_STATUSES = {"completed", "failed", "expired", "cancelled"}

    def __init__(self, judge_cfg: dict[str, Any], *, completion_window: str = "24h",
                 scratch_dir: Path):
        self._judge = OpenAIJudge(judge_cfg)
        self.completion_window = completion_window
        self.scratch_dir = scratch_dir

    def submit(self, items: list[BatchRequestItem]) -> str:
        self.scratch_dir.mkdir(parents=True, exist_ok=True)
        scratch_path = self.scratch_dir / f"input_{uuid.uuid4().hex}.jsonl"
        with open(scratch_path, "w", encoding="utf-8") as f:
            for it in items:
                body = self._judge.build_params(it.system, it.user, it.schema, it.max_tokens)
                f.write(json.dumps({
                    "custom_id": it.custom_id,
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": body,
                }, ensure_ascii=False) + "\n")
        with open(scratch_path, "rb") as f:
            file_obj = self._judge._client.files.create(file=f, purpose="batch")  # noqa: SLF001
        batch = self._judge._client.batches.create(  # noqa: SLF001
            input_file_id=file_obj.id,
            endpoint="/v1/chat/completions",
            completion_window=self.completion_window,
        )
        return batch.id

    def poll_ended(self, batch_id: str) -> bool:
        batch = self._judge._client.batches.retrieve(batch_id)  # noqa: SLF001
        return batch.status in self._TERMINAL_STATUSES

    def collect(self, batch_id: str) -> list[BatchResultItem]:
        client = self._judge._client  # noqa: SLF001
        batch = client.batches.retrieve(batch_id)
        out: list[BatchResultItem] = []
        if batch.output_file_id:
            content = client.files.content(batch.output_file_id).text
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                custom_id = entry["custom_id"]
                if entry.get("error"):
                    out.append(BatchResultItem(custom_id, "errored", None, json.dumps(entry["error"])))
                    continue
                body = ((entry.get("response") or {}).get("body")) or {}
                resp = parse_openai_response_body(body, default_model=self._judge.model)
                out.append(BatchResultItem(custom_id, "succeeded", resp, None))
        if batch.error_file_id:
            econtent = client.files.content(batch.error_file_id).text
            for line in econtent.splitlines():
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                out.append(BatchResultItem(entry.get("custom_id", "?"), "errored", None,
                                           json.dumps(entry.get("error") or entry)))
        return out


class MockBatchClient(BaseBatchClient):
    """Instant-complete canned responses (same determinism as ``MockJudge``)
    so ``--mock --batch`` exercises submit/collect/resume with no API and no
    key. Only meaningfully stateful *within* one process — across separate
    invocations, "already collected" is tracked via the persisted state file
    (``collected: true``), which is what makes the resume story correct even
    though this client itself holds no cross-process state."""

    provider = "mock"
    max_requests_per_batch = 100_000
    max_batch_bytes = 256 * 1024 * 1024

    def __init__(self, judge_cfg: dict[str, Any]):
        self._judge = MockJudge(judge_cfg)
        self._pending: dict[str, list[BatchRequestItem]] = {}

    def submit(self, items: list[BatchRequestItem]) -> str:
        batch_id = f"mock-batch-{uuid.uuid4().hex[:16]}"
        self._pending[batch_id] = list(items)
        return batch_id

    def poll_ended(self, batch_id: str) -> bool:
        return True  # instant-complete; unknown ids (already collected) are also "ended"

    def collect(self, batch_id: str) -> list[BatchResultItem]:
        items = self._pending.pop(batch_id, [])
        out = []
        for it in items:
            resp = self._judge.judge(it.system, it.user, it.schema, it.max_tokens)
            out.append(BatchResultItem(it.custom_id, "succeeded", resp, None))
        return out


def make_batch_client(
    judge_cfg: dict[str, Any], *, mock: bool, completion_window: str, scratch_dir: Path,
) -> BaseBatchClient:
    if mock:
        return MockBatchClient(judge_cfg)
    provider = judge_cfg["provider"]
    if provider == "anthropic":
        return AnthropicBatchClient(judge_cfg)
    if provider == "openai":
        return OpenAIBatchClient(judge_cfg, completion_window=completion_window, scratch_dir=scratch_dir)
    raise ValueError(f"provider '{provider}' has no batch API")


def _chunk_requests(items: list[BatchRequestItem], client: BaseBatchClient) -> list[list[BatchRequestItem]]:
    """Split into provider-size-limited chunks (size guard; our worst case —
    ~1,080 requests, ~45MB — fits in one chunk per judge today)."""
    chunks: list[list[BatchRequestItem]] = []
    current: list[BatchRequestItem] = []
    current_bytes = 0
    for it in items:
        approx_bytes = len(it.system) + len(it.user) + 2_000  # rough per-request overhead
        if current and (len(current) >= client.max_requests_per_batch
                        or current_bytes + approx_bytes > client.max_batch_bytes):
            chunks.append(current)
            current, current_bytes = [], 0
        current.append(it)
        current_bytes += approx_bytes
    if current:
        chunks.append(current)
    return chunks


# ---------------------------------------------------------------------------
# Per-judge / overall summaries
# ---------------------------------------------------------------------------

@dataclass
class JudgeBatchStatus:
    judge: str
    provider: str
    skipped_no_batch_api: bool = False
    collected_now: int = 0
    already_done: int = 0
    in_flight: int = 0
    needs_sync: int = 0
    submitted_now: int = 0

    def line(self) -> str:
        if self.skipped_no_batch_api:
            return (f"  [{self.judge}] provider '{self.provider}' has no batch API — "
                    f"run synchronously: --judges {self.judge} (no --batch)")
        parts = [f"done={self.already_done}", f"collected_now={self.collected_now}"]
        if self.submitted_now:
            parts.append(f"submitted={self.submitted_now}")
        if self.in_flight:
            parts.append(f"in_flight={self.in_flight}")
        if self.needs_sync:
            parts.append(f"needs_sync={self.needs_sync} (mop up with --judges {self.judge}, no --batch)")
        return f"  [{self.judge}] " + " ".join(parts)


@dataclass
class BatchRunSummary:
    run_name: str
    total_cells: int
    per_judge: list[JudgeBatchStatus] = field(default_factory=list)
    collected_now: int = 0
    in_flight: int = 0
    needs_sync: int = 0
    done_total: int = 0

    @property
    def complete(self) -> bool:
        """Every cell in the spec is in the JSONL (skipped-judge cells count
        as incomplete — they need a sync run, not a batch re-run)."""
        return self.done_total >= self.total_cells

    @property
    def has_in_flight(self) -> bool:
        return self.in_flight > 0


# ---------------------------------------------------------------------------
# The advance loop
# ---------------------------------------------------------------------------

def run_judges_batch(
    config: Config,
    spec: RunSpec,
    *,
    mock: bool = False,
    progress: bool = True,
) -> BatchRunSummary:
    """One idempotent advance step over ``spec`` in batch mode (module docstring).

    Re-run until :attr:`BatchRunSummary.complete` is true. Writes to the same
    ``artifacts/runs/{run_name}.jsonl`` the sync runner uses; rows differ only
    in ``api_mode``/``batch_id``, so resume and Stage-3 analysis are mode-agnostic.
    """
    runs_dir = config.artifacts_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    output_path = runs_dir / f"{spec.run_name}.jsonl"
    state_path = runs_dir / f"{spec.run_name}.batches.json"
    scratch_dir = runs_dir / f"{spec.run_name}_batch_scratch"

    prompt = get_judge_prompt(spec.prompt_version)
    system, schema = prompt["system"], prompt["schema"]
    max_tokens = config["judging"]["max_output_tokens"]
    judge_cfgs = {j["name"]: j for j in config["judging"]["judges"]}

    batch_cfg = config["judging"].get("batch", {})
    batch_providers = set(batch_cfg.get("providers", sorted(BATCH_CAPABLE_PROVIDERS)))
    completion_window = batch_cfg.get("completion_window", "24h")
    max_resubmits = batch_cfg.get("max_resubmits", 2)

    state = BatchState(state_path)
    done = existing_keys(output_path)

    all_cells = spec.cells()
    key_to_cell: dict[str, tuple[str, str, str, int]] = {}
    cells_by_judge: dict[str, list[tuple[str, str, str, int]]] = {}
    for tid, variant, judge, trial in all_cells:
        key = cell_key(tid, variant, judge, trial, spec.prompt_version)
        key_to_cell[key] = (tid, variant, judge, trial)
        cells_by_judge.setdefault(judge, []).append((tid, variant, judge, trial))

    summary = BatchRunSummary(run_name=spec.run_name, total_cells=len(all_cells))

    with open(output_path, "a", encoding="utf-8") as out:
        for judge, cells in cells_by_judge.items():
            jcfg = judge_cfgs[judge]
            provider = jcfg["provider"]
            jstatus = JudgeBatchStatus(judge=judge, provider=provider)

            if provider not in batch_providers:
                jstatus.skipped_no_batch_api = True
                if progress:
                    print(jstatus.line(), flush=True)
                summary.per_judge.append(jstatus)
                continue

            client = make_batch_client(jcfg, mock=mock, completion_window=completion_window,
                                       scratch_dir=scratch_dir)

            def collect_pending() -> int:
                n_written = 0
                for b in state.pending_batches(judge):
                    if not client.poll_ended(b["batch_id"]):
                        continue
                    results = client.collect(b["batch_id"])
                    seen_keys: set[str] = set()
                    for r in results:
                        seen_keys.add(r.custom_id)
                        if r.custom_id in done:
                            continue
                        cell = key_to_cell.get(r.custom_id)
                        if cell is None:
                            continue  # stale/foreign batch entry; ignore rather than crash
                        tid, variant, j, trial = cell
                        if r.status == "succeeded" and r.response is not None:
                            row = build_result_row(
                                key=r.custom_id, run_name=spec.run_name, task_id=tid,
                                variant=variant, judge=j, trial=trial,
                                prompt_version=spec.prompt_version, model=judge_cfgs[j]["model"],
                                resp=r.response, err=None, mock=mock,
                                api_mode="batch", batch_id=b["batch_id"],
                            )
                            out.write(json.dumps(row, ensure_ascii=False) + "\n")
                            done.add(r.custom_id)
                            n_written += 1
                        else:
                            state.record_attempt(r.custom_id)
                    # Any cell recorded for this batch but absent from the
                    # results (e.g. a whole-batch provider failure) still
                    # counts as a failed attempt, not silent loss.
                    for key in b["cell_keys"]:
                        if key not in seen_keys and key not in done:
                            state.record_attempt(key)
                    out.flush()
                    state.mark_collected(b["batch_id"], status="ended")
                return n_written

            jstatus.collected_now += collect_pending()

            in_flight_keys = state.in_flight_cells(judge)
            missing: list[tuple[str, str, str, int, str]] = []
            for tid, variant, j, trial in cells:
                key = cell_key(tid, variant, j, trial, spec.prompt_version)
                if key in done or key in in_flight_keys:
                    continue
                if state.attempts.get(key, 0) >= max_resubmits:
                    jstatus.needs_sync += 1
                    continue
                missing.append((tid, variant, j, trial, key))

            if missing:
                items = []
                for tid, variant, j, trial, key in missing:
                    ji = load_judge_input(config, tid, variant)
                    user = build_judge_user_message(ji, spec.prompt_version)
                    items.append(BatchRequestItem(key, system, user, schema, max_tokens))
                for chunk in _chunk_requests(items, client):
                    batch_id = client.submit(chunk)
                    state.add_batch(
                        batch_id=batch_id, provider=provider, judge=judge,
                        cell_keys=[it.custom_id for it in chunk], status="in_progress",
                    )
                    jstatus.submitted_now += len(chunk)
                state.save()
                # Opportunistic immediate collect: mock finishes instantly;
                # real batches simply stay in-flight (poll_ended -> False).
                jstatus.collected_now += collect_pending()

            state.save()

            in_flight_keys = state.in_flight_cells(judge)
            jstatus.in_flight = len(in_flight_keys)
            jstatus.already_done = sum(1 for tid, variant, j, trial in cells
                                       if cell_key(tid, variant, j, trial, spec.prompt_version) in done)

            summary.collected_now += jstatus.collected_now
            summary.in_flight += jstatus.in_flight
            summary.needs_sync += jstatus.needs_sync
            summary.per_judge.append(jstatus)

            if progress:
                print(jstatus.line(), flush=True)

    summary.done_total = sum(1 for key in key_to_cell if key in done)
    return summary
