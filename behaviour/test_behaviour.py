"""LLM behaviour suite. Calls the Claude API: run explicitly with -m behaviour.

    uv run --group behaviour pytest behaviour -m behaviour -v
"""

import json
import os
import sys
from pathlib import Path

import pytest

from behaviour.cases import CASES
from behaviour.harness import DEFAULT_MODEL, evaluate, run_case

RUNS_PER_CASE = 3
RESULTS = Path(__file__).parent / "results" / "latest.jsonl"
SERVER = str(Path(sys.executable).parent / "eubank-mcp")


def _has_credentials() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
                or (Path.home() / ".config" / "anthropic").exists())


pytestmark = [
    pytest.mark.behaviour,
    pytest.mark.anyio,
    pytest.mark.skipif(not _has_credentials(), reason="no Anthropic credentials (set ANTHROPIC_API_KEY)"),
]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.id)
async def test_case(case, behaviour_db):
    model = os.environ.get("EUBANK_EVAL_MODEL", DEFAULT_MODEL)
    runs = [await run_case(case, model, behaviour_db, SERVER) for _ in range(RUNS_PER_CASE)]
    verdict = evaluate(case, runs, behaviour_db)
    RESULTS.parent.mkdir(exist_ok=True)
    with RESULTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "case": case.id, "model": model, "runs": verdict.runs, "safety": verdict.safety_passes,
            "tool_choice": verdict.tool_passes, "model_refusals": verdict.model_refusals,
            "passed": verdict.passed, "failures": verdict.failures,
        }, ensure_ascii=False) + "\n")
    assert verdict.passed, "\n".join(verdict.failures)
