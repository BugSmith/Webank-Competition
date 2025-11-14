from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Dict, List

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def pipeline_payload() -> Dict[str, Any]:
    return _load_json(FIXTURES_DIR / "pipeline" / "sample_payload.json")


@pytest.fixture
def sample_fund_payload() -> Dict[str, Any]:
    return _load_json(FIXTURES_DIR / "fund_advice" / "sample_fund.json")


@pytest.fixture
def conversation_history() -> List[Dict[str, Any]]:
    return _load_json(FIXTURES_DIR / "conversation" / "history.json")
