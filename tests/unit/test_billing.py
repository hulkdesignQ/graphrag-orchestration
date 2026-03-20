"""
Tests for billing API — plan upgrade/downgrade and cancel endpoints.

Tests cover:
  - POST /billing/change-plan (upgrade, downgrade, validation)
  - POST /billing/cancel
  - Edge cases (no subscription, same plan, invalid plan, B2B rejection)
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

from src.core.roles import PlanTier, TIER_TO_STRIPE_PRICE, STRIPE_PRICE_TO_TIER


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_sub_record(
    user_id="test-user-123",
    plan_tier="pro",
    status="active",
    stripe_customer_id="cus_test123",
    stripe_subscription_id="sub_test456",
):
    """Create a mock SubscriptionRecord."""
    from src.core.models.subscription import SubscriptionRecord
    return SubscriptionRecord(
        user_id=user_id,
        email="test@example.com",
        stripe_customer_id=stripe_customer_id,
        stripe_subscription_id=stripe_subscription_id,
        plan_tier=plan_tier,
        status=status,
        current_period_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        current_period_end=datetime(2026, 4, 1, tzinfo=timezone.utc),
        cancel_at_period_end=False,
    )


def _make_stripe_sub(price_id="price_pro_plus_test", status="active"):
    """Create a mock Stripe Subscription object (dict-like)."""
    return {
        "id": "sub_test456",
        "status": status,
        "items": {
            "data": [
                {
                    "id": "si_item_001",
                    "price": {"id": price_id},
                }
            ]
        },
        "current_period_start": 1740787200,  # 2025-03-01
        "current_period_end": 1743465600,    # 2025-04-01
        "cancel_at_period_end": False,
    }


@pytest.fixture
def mock_stripe():
    """Mock the stripe module."""
    stripe_mock = MagicMock()
    stripe_mock.Subscription.retrieve.return_value = _make_stripe_sub()
    stripe_mock.Subscription.modify.return_value = _make_stripe_sub(
        price_id="price_pro_plus_test"
    )
    stripe_mock.Invoice.upcoming.return_value = {"amount_due": 2900}
    return stripe_mock


@pytest.fixture
def mock_cosmos():
    """Mock the Cosmos DB client."""
    cosmos = AsyncMock()
    cosmos.get_subscription = AsyncMock(return_value=_make_sub_record())
    cosmos.upsert_subscription = AsyncMock()
    return cosmos


@pytest.fixture
def mock_enforcer():
    """Mock the quota enforcer."""
    enforcer = AsyncMock()
    enforcer.set_plan = AsyncMock()
    return enforcer


# ---------------------------------------------------------------------------
# change-plan endpoint tests
# ---------------------------------------------------------------------------

class TestChangePlan:
    """Tests for POST /billing/change-plan."""

    @pytest.mark.asyncio
    async def test_upgrade_pro_to_pro_plus(self, mock_stripe, mock_cosmos, mock_enforcer):
        """Upgrading from Pro to Pro Plus should modify the Stripe subscription."""
        from src.api_gateway.routers.billing import change_plan, ChangePlanRequest

        # Ensure price mapping exists for the test
        with patch("src.api_gateway.routers.billing._require_stripe", return_value=mock_stripe), \
             patch("src.api_gateway.routers.billing.get_cosmos_client", return_value=mock_cosmos), \
             patch("src.api_gateway.routers.billing.get_quota_enforcer", return_value=mock_enforcer), \
             patch("src.api_gateway.routers.billing.TIER_TO_STRIPE_PRICE", {
                 PlanTier.PRO: "price_pro_test",
                 PlanTier.PRO_PLUS: "price_pro_plus_test",
             }):

            result = await change_plan(
                body=ChangePlanRequest(plan="pro_plus"),
                user_id="test-user-123",
            )

        assert result.previous_plan == "pro"
        assert result.new_plan == "pro_plus"
        assert result.status == "active"
        assert result.proration_amount == 2900

        # Verify Stripe was called correctly
        mock_stripe.Subscription.retrieve.assert_called_once_with("sub_test456")
        mock_stripe.Subscription.modify.assert_called_once()
        call_kwargs = mock_stripe.Subscription.modify.call_args
        assert call_kwargs[0][0] == "sub_test456"
        assert call_kwargs[1]["items"] == [{"id": "si_item_001", "price": "price_pro_plus_test"}]
        assert call_kwargs[1]["proration_behavior"] == "create_prorations"

        # Verify local records updated
        mock_cosmos.upsert_subscription.assert_called_once()

    @pytest.mark.asyncio
    async def test_downgrade_pro_plus_to_pro(self, mock_stripe, mock_cosmos, mock_enforcer):
        """Downgrading from Pro Plus to Pro should work with proration credit."""
        from src.api_gateway.routers.billing import change_plan, ChangePlanRequest

        mock_cosmos.get_subscription.return_value = _make_sub_record(plan_tier="pro_plus")
        mock_stripe.Invoice.upcoming.return_value = {"amount_due": -1500}
        mock_stripe.Subscription.modify.return_value = _make_stripe_sub(
            price_id="price_pro_test"
        )

        with patch("src.api_gateway.routers.billing._require_stripe", return_value=mock_stripe), \
             patch("src.api_gateway.routers.billing.get_cosmos_client", return_value=mock_cosmos), \
             patch("src.api_gateway.routers.billing.get_quota_enforcer", return_value=mock_enforcer), \
             patch("src.api_gateway.routers.billing.TIER_TO_STRIPE_PRICE", {
                 PlanTier.PRO: "price_pro_test",
                 PlanTier.PRO_PLUS: "price_pro_plus_test",
             }):

            result = await change_plan(
                body=ChangePlanRequest(plan="pro"),
                user_id="test-user-123",
            )

        assert result.previous_plan == "pro_plus"
        assert result.new_plan == "pro"
        assert result.proration_amount == -1500

    @pytest.mark.asyncio
    async def test_same_plan_rejected(self, mock_stripe, mock_cosmos, mock_enforcer):
        """Changing to the same plan should return 400."""
        from src.api_gateway.routers.billing import change_plan, ChangePlanRequest
        from fastapi import HTTPException

        with patch("src.api_gateway.routers.billing._require_stripe", return_value=mock_stripe), \
             patch("src.api_gateway.routers.billing.get_cosmos_client", return_value=mock_cosmos), \
             patch("src.api_gateway.routers.billing.TIER_TO_STRIPE_PRICE", {
                 PlanTier.PRO: "price_pro_test",
             }):

            with pytest.raises(HTTPException) as exc:
                await change_plan(
                    body=ChangePlanRequest(plan="pro"),
                    user_id="test-user-123",
                )
            assert exc.value.status_code == 400
            assert "Already on this plan" in exc.value.detail

    @pytest.mark.asyncio
    async def test_invalid_plan_rejected(self, mock_stripe, mock_cosmos):
        """An invalid plan value should return 400."""
        from src.api_gateway.routers.billing import change_plan, ChangePlanRequest
        from fastapi import HTTPException

        with patch("src.api_gateway.routers.billing._require_stripe", return_value=mock_stripe), \
             patch("src.api_gateway.routers.billing.get_cosmos_client", return_value=mock_cosmos):

            with pytest.raises(HTTPException) as exc:
                await change_plan(
                    body=ChangePlanRequest(plan="nonexistent"),
                    user_id="test-user-123",
                )
            assert exc.value.status_code == 400
            assert "Invalid plan" in exc.value.detail

    @pytest.mark.asyncio
    async def test_b2b_plan_rejected(self, mock_stripe, mock_cosmos):
        """B2B plans should be rejected with 400."""
        from src.api_gateway.routers.billing import change_plan, ChangePlanRequest
        from fastapi import HTTPException

        with patch("src.api_gateway.routers.billing._require_stripe", return_value=mock_stripe), \
             patch("src.api_gateway.routers.billing.get_cosmos_client", return_value=mock_cosmos):

            with pytest.raises(HTTPException) as exc:
                await change_plan(
                    body=ChangePlanRequest(plan="enterprise"),
                    user_id="test-user-123",
                )
            assert exc.value.status_code == 400
            assert "B2B" in exc.value.detail

    @pytest.mark.asyncio
    async def test_free_plan_rejected(self, mock_stripe, mock_cosmos):
        """Downgrade to free should be rejected (use /cancel instead)."""
        from src.api_gateway.routers.billing import change_plan, ChangePlanRequest
        from fastapi import HTTPException

        with patch("src.api_gateway.routers.billing._require_stripe", return_value=mock_stripe), \
             patch("src.api_gateway.routers.billing.get_cosmos_client", return_value=mock_cosmos):

            with pytest.raises(HTTPException) as exc:
                await change_plan(
                    body=ChangePlanRequest(plan="free"),
                    user_id="test-user-123",
                )
            assert exc.value.status_code == 400
            assert "cancel" in exc.value.detail.lower()

    @pytest.mark.asyncio
    async def test_no_subscription_rejected(self, mock_stripe, mock_cosmos):
        """Users without a subscription should get 400."""
        from src.api_gateway.routers.billing import change_plan, ChangePlanRequest
        from fastapi import HTTPException

        mock_cosmos.get_subscription.return_value = None

        with patch("src.api_gateway.routers.billing._require_stripe", return_value=mock_stripe), \
             patch("src.api_gateway.routers.billing.get_cosmos_client", return_value=mock_cosmos), \
             patch("src.api_gateway.routers.billing.TIER_TO_STRIPE_PRICE", {
                 PlanTier.PRO_PLUS: "price_pro_plus_test",
             }):

            with pytest.raises(HTTPException) as exc:
                await change_plan(
                    body=ChangePlanRequest(plan="pro_plus"),
                    user_id="test-user-123",
                )
            assert exc.value.status_code == 400
            assert "No active subscription" in exc.value.detail

    @pytest.mark.asyncio
    async def test_past_due_subscription_rejected(self, mock_stripe, mock_cosmos):
        """Past-due subscriptions should not allow plan changes."""
        from src.api_gateway.routers.billing import change_plan, ChangePlanRequest
        from fastapi import HTTPException

        mock_cosmos.get_subscription.return_value = _make_sub_record(status="past_due")

        with patch("src.api_gateway.routers.billing._require_stripe", return_value=mock_stripe), \
             patch("src.api_gateway.routers.billing.get_cosmos_client", return_value=mock_cosmos), \
             patch("src.api_gateway.routers.billing.TIER_TO_STRIPE_PRICE", {
                 PlanTier.PRO_PLUS: "price_pro_plus_test",
             }):

            with pytest.raises(HTTPException) as exc:
                await change_plan(
                    body=ChangePlanRequest(plan="pro_plus"),
                    user_id="test-user-123",
                )
            assert exc.value.status_code == 400
            assert "past_due" in exc.value.detail

    @pytest.mark.asyncio
    async def test_proration_preview_failure_non_blocking(self, mock_stripe, mock_cosmos, mock_enforcer):
        """If proration preview fails, the change should still proceed."""
        from src.api_gateway.routers.billing import change_plan, ChangePlanRequest

        mock_stripe.Invoice.upcoming.side_effect = Exception("Preview failed")

        with patch("src.api_gateway.routers.billing._require_stripe", return_value=mock_stripe), \
             patch("src.api_gateway.routers.billing.get_cosmos_client", return_value=mock_cosmos), \
             patch("src.api_gateway.routers.billing.get_quota_enforcer", return_value=mock_enforcer), \
             patch("src.api_gateway.routers.billing.TIER_TO_STRIPE_PRICE", {
                 PlanTier.PRO: "price_pro_test",
                 PlanTier.PRO_PLUS: "price_pro_plus_test",
             }):

            result = await change_plan(
                body=ChangePlanRequest(plan="pro_plus"),
                user_id="test-user-123",
            )

        assert result.new_plan == "pro_plus"
        assert result.proration_amount is None
        mock_stripe.Subscription.modify.assert_called_once()


# ---------------------------------------------------------------------------
# cancel endpoint tests
# ---------------------------------------------------------------------------

class TestCancelSubscription:
    """Tests for POST /billing/cancel."""

    @pytest.mark.asyncio
    async def test_cancel_active_subscription(self, mock_stripe, mock_cosmos):
        """Cancelling should set cancel_at_period_end=True."""
        from src.api_gateway.routers.billing import cancel_subscription

        mock_stripe.Subscription.modify.return_value = {
            **_make_stripe_sub(),
            "cancel_at_period_end": True,
        }

        with patch("src.api_gateway.routers.billing._require_stripe", return_value=mock_stripe), \
             patch("src.api_gateway.routers.billing.get_cosmos_client", return_value=mock_cosmos):

            result = await cancel_subscription(user_id="test-user-123")

        assert result.cancel_at_period_end is True
        assert result.plan == "pro"

        mock_stripe.Subscription.modify.assert_called_once_with(
            "sub_test456",
            cancel_at_period_end=True,
        )
        mock_cosmos.upsert_subscription.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_no_subscription(self, mock_stripe, mock_cosmos):
        """Cancel with no subscription should return 404."""
        from src.api_gateway.routers.billing import cancel_subscription
        from fastapi import HTTPException

        mock_cosmos.get_subscription.return_value = None

        with patch("src.api_gateway.routers.billing._require_stripe", return_value=mock_stripe), \
             patch("src.api_gateway.routers.billing.get_cosmos_client", return_value=mock_cosmos):

            with pytest.raises(HTTPException) as exc:
                await cancel_subscription(user_id="test-user-123")
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_cancel_already_canceled(self, mock_stripe, mock_cosmos):
        """Cancel on already-canceled subscription should return 400."""
        from src.api_gateway.routers.billing import cancel_subscription
        from fastapi import HTTPException

        mock_cosmos.get_subscription.return_value = _make_sub_record(status="canceled")

        with patch("src.api_gateway.routers.billing._require_stripe", return_value=mock_stripe), \
             patch("src.api_gateway.routers.billing.get_cosmos_client", return_value=mock_cosmos):

            with pytest.raises(HTTPException) as exc:
                await cancel_subscription(user_id="test-user-123")
            assert exc.value.status_code == 400
            assert "already canceled" in exc.value.detail.lower()
