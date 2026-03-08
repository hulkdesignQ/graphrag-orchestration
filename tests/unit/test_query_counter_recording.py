"""
Tests for the robust query counter recording pipeline.

Validates that:
- record_query() propagates Redis failures instead of swallowing them
- check_and_consume() signals recording success/failure via query_recorded
- enforce_plan_limits() reads the signal and sets request.state.query_recorded
- _ensure_query_recorded() retries on transient failure
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from types import SimpleNamespace


# ---------------------------------------------------------------------------
# record_query — must propagate exceptions
# ---------------------------------------------------------------------------

class TestRecordQueryPropagation:
    """record_query() must raise on Redis failure, not return (0, 0)."""

    @pytest.fixture
    def enforcer(self):
        from src.core.services.quota_enforcer import QuotaEnforcer
        redis_svc = MagicMock()
        redis_svc._redis = AsyncMock()
        return QuotaEnforcer(redis_svc)

    @pytest.mark.asyncio
    async def test_success_returns_counts(self, enforcer):
        pipe = AsyncMock()
        pipe.execute = AsyncMock(return_value=[5, True, 12, True])
        enforcer._redis.pipeline = MagicMock(return_value=pipe)

        daily, monthly = await enforcer.record_query("user-1")
        assert daily == 5
        assert monthly == 12

    @pytest.mark.asyncio
    async def test_redis_failure_propagates(self, enforcer):
        """The old code returned (0, 0) here — the fix must raise."""
        pipe = AsyncMock()
        pipe.execute = AsyncMock(side_effect=ConnectionError("Redis down"))
        enforcer._redis.pipeline = MagicMock(return_value=pipe)

        with pytest.raises(ConnectionError, match="Redis down"):
            await enforcer.record_query("user-1")

    @pytest.mark.asyncio
    async def test_pipeline_creation_failure_propagates(self, enforcer):
        enforcer._redis.pipeline = MagicMock(side_effect=RuntimeError("pool exhausted"))

        with pytest.raises(RuntimeError, match="pool exhausted"):
            await enforcer.record_query("user-1")


# ---------------------------------------------------------------------------
# check_and_consume — must signal recording state
# ---------------------------------------------------------------------------

class TestCheckAndConsumeSignal:
    """check_and_consume() result must include query_recorded field."""

    @pytest.fixture
    def enforcer(self):
        from src.core.services.quota_enforcer import QuotaEnforcer
        redis_svc = MagicMock()
        redis_svc._redis = AsyncMock()
        return QuotaEnforcer(redis_svc)

    @pytest.mark.asyncio
    async def test_successful_recording_signals_true(self, enforcer):
        enforcer.get_plan = AsyncMock(return_value=MagicMock(value="free"))
        enforcer.get_usage = AsyncMock(return_value={"queries_today": 0, "queries_this_month": 0})
        enforcer.check_credit_limits = AsyncMock(return_value={
            "credits_allowed": True, "credits_used": 0, "credits_limit": None, "credits_remaining": None
        })

        pipe = AsyncMock()
        pipe.execute = AsyncMock(return_value=[1, True, 1, True])
        enforcer._redis.pipeline = MagicMock(return_value=pipe)

        # Mock PLAN_DEFINITIONS to have high limits
        with patch("src.core.services.quota_enforcer.PLAN_DEFINITIONS") as mock_plans:
            mock_limits = MagicMock()
            mock_limits.queries_per_day = 100
            mock_limits.queries_per_month = 1000
            mock_plans.__getitem__ = MagicMock(return_value=mock_limits)

            result = await enforcer.check_and_consume("user-1")

        assert result["allowed"] is True
        assert result["query_recorded"] is True
        assert result["daily_used"] == 1

    @pytest.mark.asyncio
    async def test_redis_failure_signals_false(self, enforcer):
        """When record_query fails, query_recorded must be False."""
        enforcer.get_plan = AsyncMock(return_value=MagicMock(value="free"))
        enforcer.get_usage = AsyncMock(return_value={"queries_today": 0, "queries_this_month": 0})
        enforcer.check_credit_limits = AsyncMock(return_value={
            "credits_allowed": True, "credits_used": 0, "credits_limit": None, "credits_remaining": None
        })

        pipe = AsyncMock()
        pipe.execute = AsyncMock(side_effect=ConnectionError("Redis timeout"))
        enforcer._redis.pipeline = MagicMock(return_value=pipe)

        with patch("src.core.services.quota_enforcer.PLAN_DEFINITIONS") as mock_plans:
            mock_limits = MagicMock()
            mock_limits.queries_per_day = 100
            mock_limits.queries_per_month = 1000
            mock_plans.__getitem__ = MagicMock(return_value=mock_limits)

            result = await enforcer.check_and_consume("user-1")

        assert result["allowed"] is True  # fail-open — request goes through
        assert result["query_recorded"] is False  # but recording failed
        assert result["daily_used"] == 0


# ---------------------------------------------------------------------------
# enforce_plan_limits — must read query_recorded from result
# ---------------------------------------------------------------------------

class TestEnforcePlanLimitsSignal:
    """enforce_plan_limits must set request.state.query_recorded from result."""

    @pytest.mark.asyncio
    async def test_recording_success_sets_true(self):
        from src.core.services.quota_enforcer import enforce_plan_limits

        mock_request = MagicMock()
        mock_request.state = SimpleNamespace(user_id="user-1")

        mock_result = {
            "allowed": True,
            "query_recorded": True,
            "reason": None, "plan": "free",
            "daily_used": 1, "daily_limit": 100, "daily_remaining": 99,
            "monthly_used": 1, "monthly_limit": 1000, "monthly_remaining": 999,
            "credits_used": 0, "credits_limit": None, "credits_remaining": None,
            "retry_after_seconds": 0,
        }

        with patch("src.core.services.quota_enforcer.get_quota_enforcer") as mock_get:
            mock_enforcer = AsyncMock()
            mock_enforcer.check_and_consume = AsyncMock(return_value=mock_result)
            mock_get.return_value = mock_enforcer

            result = await enforce_plan_limits(mock_request)

        assert mock_request.state.query_recorded is True

    @pytest.mark.asyncio
    async def test_recording_failure_sets_false(self):
        from src.core.services.quota_enforcer import enforce_plan_limits

        mock_request = MagicMock()
        mock_request.state = SimpleNamespace(user_id="user-1")

        mock_result = {
            "allowed": True,
            "query_recorded": False,  # Redis INCR failed
            "reason": None, "plan": "free",
            "daily_used": 0, "daily_limit": 100, "daily_remaining": 100,
            "monthly_used": 0, "monthly_limit": 1000, "monthly_remaining": 1000,
            "credits_used": 0, "credits_limit": None, "credits_remaining": None,
            "retry_after_seconds": 0,
        }

        with patch("src.core.services.quota_enforcer.get_quota_enforcer") as mock_get:
            mock_enforcer = AsyncMock()
            mock_enforcer.check_and_consume = AsyncMock(return_value=mock_result)
            mock_get.return_value = mock_enforcer

            result = await enforce_plan_limits(mock_request)

        assert mock_request.state.query_recorded is False

    @pytest.mark.asyncio
    async def test_total_failure_sets_false(self):
        """When entire check_and_consume throws, query_recorded must be False."""
        from src.core.services.quota_enforcer import enforce_plan_limits

        mock_request = MagicMock()
        mock_request.state = SimpleNamespace(user_id="user-1")
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        with patch("src.core.services.quota_enforcer.get_quota_enforcer") as mock_get:
            mock_get.side_effect = ConnectionError("Redis down")

            result = await enforce_plan_limits(mock_request)

        assert mock_request.state.query_recorded is False
        assert result["allowed"] is True  # fail-open


# ---------------------------------------------------------------------------
# _ensure_query_recorded — retry logic
# ---------------------------------------------------------------------------

class TestEnsureQueryRecordedRetry:
    """Backup path must retry on transient failures."""

    @pytest.mark.asyncio
    async def test_skips_when_already_recorded(self):
        from src.api_gateway.routers.chat import _ensure_query_recorded

        with patch("src.core.services.quota_enforcer.get_quota_enforcer") as mock_get:
            await _ensure_query_recorded("user-1", query_recorded=True)
            mock_get.assert_not_called()

    @pytest.mark.asyncio
    async def test_succeeds_on_first_attempt(self):
        from src.api_gateway.routers.chat import _ensure_query_recorded

        mock_enforcer = AsyncMock()
        mock_enforcer.record_query = AsyncMock(return_value=(1, 1))

        with patch("src.core.services.quota_enforcer.get_quota_enforcer", return_value=mock_enforcer):
            await _ensure_query_recorded("user-1", query_recorded=False)

        mock_enforcer.record_query.assert_called_once_with("user-1")

    @pytest.mark.asyncio
    async def test_retries_on_transient_failure(self):
        from src.api_gateway.routers.chat import _ensure_query_recorded

        mock_enforcer = AsyncMock()
        mock_enforcer.record_query = AsyncMock(
            side_effect=[ConnectionError("blip"), (1, 1)]
        )

        with patch("src.core.services.quota_enforcer.get_quota_enforcer", return_value=mock_enforcer):
            with patch("asyncio.sleep", new_callable=AsyncMock):  # skip actual delay
                await _ensure_query_recorded("user-1", query_recorded=False)

        assert mock_enforcer.record_query.call_count == 2

    @pytest.mark.asyncio
    async def test_exhausts_retries_gracefully(self):
        from src.api_gateway.routers.chat import _ensure_query_recorded

        mock_enforcer = AsyncMock()
        mock_enforcer.record_query = AsyncMock(
            side_effect=ConnectionError("persistent failure")
        )

        with patch("src.core.services.quota_enforcer.get_quota_enforcer", return_value=mock_enforcer):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                # Should not raise — just logs warning
                await _ensure_query_recorded("user-1", query_recorded=False)

        assert mock_enforcer.record_query.call_count == 3
