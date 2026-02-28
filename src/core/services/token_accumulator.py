"""Per-request token accumulator for tracking LLM usage across a query pipeline.

Each query request creates one TokenAccumulator that is threaded through
orchestrator → route → synthesis. All acomplete()/complete() calls via
TrackedLLM add their token counts here, and the route reads the snapshot
to populate RouteResult.usage.
"""

import threading
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class _CallRecord:
    """One LLM call's token usage."""
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class TokenAccumulator:
    """Thread-safe accumulator for LLM token usage within a single request.

    Usage::

        acc = TokenAccumulator()
        # ... pass acc through pipeline; TrackedLLM calls acc.add() ...
        usage = acc.snapshot()  # {"prompt_tokens": N, "completion_tokens": M, ...}
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._calls: List[_CallRecord] = []
        self._prompt_tokens: int = 0
        self._completion_tokens: int = 0
        self._total_tokens: int = 0
        self._model: Optional[str] = None

    def add(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int = 0,
    ) -> None:
        """Record token usage from one LLM call."""
        total = total_tokens or (prompt_tokens + completion_tokens)
        with self._lock:
            self._calls.append(_CallRecord(
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total,
            ))
            self._prompt_tokens += prompt_tokens
            self._completion_tokens += completion_tokens
            self._total_tokens += total
            # Keep track of last model used (typically the synthesis model)
            self._model = model

    def snapshot(self) -> Dict[str, Any]:
        """Return a summary dict suitable for RouteResult.usage."""
        with self._lock:
            return {
                "prompt_tokens": self._prompt_tokens,
                "completion_tokens": self._completion_tokens,
                "total_tokens": self._total_tokens,
                "model": self._model,
                "llm_calls": len(self._calls),
            }

    @property
    def total_tokens(self) -> int:
        with self._lock:
            return self._total_tokens

    @property
    def call_count(self) -> int:
        with self._lock:
            return len(self._calls)
