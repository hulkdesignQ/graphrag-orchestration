"""Instrumented LLM wrapper that tracks token usage from every call.

TrackedLLM wraps a LlamaIndex AzureOpenAI instance, intercepting
acomplete() and complete() to:
1. Extract response.raw['usage'] token counts
2. Accumulate on a per-request TokenAccumulator (for RouteResult.usage)
3. Fire-and-forget to UsageTracker (for Cosmos DB persistence)

Inject via LLMService._create_llm_client() so all 22+ call sites are
covered without individual modification.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional, Sequence

import structlog

from src.core.services.token_accumulator import TokenAccumulator
from src.core.services.usage_tracker import get_usage_tracker

logger = structlog.get_logger(__name__)

# Strong references for fire-and-forget background tasks (prevent GC)
_background_tasks: set = set()


def _extract_usage(response: Any) -> dict:
    """Extract token usage from a LlamaIndex CompletionResponse.

    Returns dict with prompt_tokens, completion_tokens, total_tokens
    (all default to 0 if unavailable).
    """
    usage: dict = {}
    try:
        raw = getattr(response, "raw", None)
        if isinstance(raw, dict):
            usage = raw.get("usage", {})
        elif raw is not None:
            # Some LlamaIndex versions wrap raw in an object
            usage = getattr(raw, "usage", {}) or {}
            if hasattr(usage, "prompt_tokens"):
                # Pydantic model (e.g. openai.types.CompletionUsage)
                usage = {
                    "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
                    "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
                    "total_tokens": getattr(usage, "total_tokens", 0) or 0,
                }
    except Exception:
        pass
    return {
        "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
        "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
        "total_tokens": int(usage.get("total_tokens", 0) or 0),
    }


class TrackedLLM:
    """Transparent wrapper around a LlamaIndex LLM that tracks token usage.

    Delegates all attribute access to the underlying LLM so it's a drop-in
    replacement. Only acomplete() and complete() are intercepted.
    """

    def __init__(
        self,
        llm: Any,
        *,
        deployment_name: str,
        group_id: str = "unknown",
        user_id: Optional[str] = None,
        route: Optional[str] = None,
        accumulator: Optional[TokenAccumulator] = None,
    ):
        # Use object.__setattr__ to avoid triggering our __setattr__
        object.__setattr__(self, "_llm", llm)
        object.__setattr__(self, "_deployment_name", deployment_name)
        object.__setattr__(self, "_group_id", group_id)
        object.__setattr__(self, "_user_id", user_id)
        object.__setattr__(self, "_route", route)
        object.__setattr__(self, "_accumulator", accumulator)

    # ── Transparent delegation ───────────────────────────────────────
    def __getattr__(self, name: str) -> Any:
        return getattr(object.__getattribute__(self, "_llm"), name)

    def __setattr__(self, name: str, value: Any) -> None:
        # Route private attrs to wrapper, everything else to underlying LLM
        if name.startswith("_"):
            object.__setattr__(self, name, value)
        else:
            setattr(object.__getattribute__(self, "_llm"), name, value)

    # ── Accumulator management ───────────────────────────────────────
    def set_accumulator(self, accumulator: Optional[TokenAccumulator]) -> None:
        """Attach a per-request accumulator (called by route handler)."""
        object.__setattr__(self, "_accumulator", accumulator)

    def set_route(self, route: str) -> None:
        """Update the route label for Cosmos DB records."""
        object.__setattr__(self, "_route", route)

    # ── Intercepted methods ──────────────────────────────────────────
    async def acomplete(self, prompt: str, **kwargs: Any) -> Any:
        """Async completion with automatic token tracking."""
        llm = object.__getattribute__(self, "_llm")
        response = await llm.acomplete(prompt, **kwargs)
        self._record_usage(response)
        return response

    def complete(self, prompt: str, **kwargs: Any) -> Any:
        """Sync completion with automatic token tracking."""
        llm = object.__getattribute__(self, "_llm")
        response = llm.complete(prompt, **kwargs)
        self._record_usage(response)
        return response

    async def astream_complete(self, prompt: str, **kwargs: Any) -> Any:
        """Async streaming — delegate without tracking (tokens unavailable mid-stream)."""
        llm = object.__getattribute__(self, "_llm")
        return await llm.astream_complete(prompt, **kwargs)

    # ── Internal ─────────────────────────────────────────────────────
    def _record_usage(self, response: Any) -> None:
        """Extract usage from response and dispatch to accumulator + Cosmos."""
        usage = _extract_usage(response)
        prompt_tokens = usage["prompt_tokens"]
        completion_tokens = usage["completion_tokens"]
        total_tokens = usage["total_tokens"]

        if total_tokens == 0:
            return  # No usage data available

        deployment = object.__getattribute__(self, "_deployment_name")
        group_id = object.__getattribute__(self, "_group_id")
        user_id = object.__getattribute__(self, "_user_id")
        route = object.__getattribute__(self, "_route")
        accumulator = object.__getattribute__(self, "_accumulator")

        # 1. Accumulate for RouteResult.usage
        if accumulator is not None:
            accumulator.add(
                model=deployment,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )

        # 2. Fire-and-forget to Cosmos via UsageTracker
        try:
            tracker = get_usage_tracker()
            loop = asyncio.get_event_loop()
            task = loop.create_task(tracker.log_llm_usage(
                partition_id=group_id,
                model=deployment,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                user_id=user_id,
                route=route,
            ))
            _background_tasks.add(task)
            task.add_done_callback(_background_tasks.discard)
        except Exception:
            pass  # Fire-and-forget: never block the pipeline

        logger.debug(
            "llm_token_usage_recorded",
            model=deployment,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            group_id=group_id,
            route=route,
        )
