from __future__ import annotations

import uuid


def make_run_id(prefix: str = "quest") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def make_claim_id() -> str:
    return f"claim_{uuid.uuid4().hex[:8]}"
