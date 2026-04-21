from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationResult:
    alert_id: str
    condition_met: bool
    error: str | None = None

    def has_error(self) -> bool:
        return self.error is not None
