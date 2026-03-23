"""
Billing API Router — Stripe Checkout, Billing Portal, and Webhooks.

Endpoints:
  POST /billing/create-checkout-session  — start a Stripe Checkout for plan upgrade
  POST /billing/create-portal-session    — open Stripe Billing Portal (manage sub)
  POST /billing/change-plan              — upgrade or downgrade an existing subscription
  POST /billing/cancel                   — cancel subscription at period end
  POST /billing/webhook                  — receive Stripe webhook events (no auth)
  GET  /billing/subscription             — current subscription status
  GET  /billing/config                   — publishable key for frontend

All endpoints are no-ops when STRIPE_SECRET_KEY is not configured.
"""

from datetime import datetime, timezone
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.api_gateway.middleware.auth import get_current_user, get_user_id
from src.core.config import settings
from src.core.roles import (
    PlanTier,
    B2B_TIERS,
    TIER_TO_STRIPE_PRICE,
    STRIPE_PRICE_TO_TIER,
)
from src.core.services.cosmos_client import get_cosmos_client
from src.core.services.quota_enforcer import get_quota_enforcer

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])

# ---------------------------------------------------------------------------
# Lazy Stripe import — only loaded when STRIPE_SECRET_KEY is set
# ---------------------------------------------------------------------------
_stripe = None


def _get_stripe():
    """Lazy-load and configure the stripe module."""
    global _stripe
    if _stripe is not None:
        return _stripe
    if not settings.STRIPE_SECRET_KEY:
        return None
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    _stripe = stripe
    return _stripe


def _require_stripe():
    """Raise 503 if Stripe is not configured."""
    s = _get_stripe()
    if s is None:
        raise HTTPException(status_code=503, detail="Billing is not configured")
    return s


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class CheckoutRequest(BaseModel):
    plan: str  # Target PlanTier value, e.g. "pro" or "pro_plus"
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CheckoutResponse(BaseModel):
    checkout_url: str


class PortalResponse(BaseModel):
    portal_url: str


class SubscriptionResponse(BaseModel):
    has_subscription: bool
    plan: str
    status: str
    stripe_customer_id: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    manage_url: Optional[str] = None


class BillingConfigResponse(BaseModel):
    stripe_enabled: bool
    publishable_key: Optional[str] = None


class ChangePlanRequest(BaseModel):
    plan: str  # Target PlanTier value, e.g. "pro" or "pro_plus"


class ChangePlanResponse(BaseModel):
    previous_plan: str
    new_plan: str
    status: str
    proration_amount: Optional[int] = None  # cents


class CancelResponse(BaseModel):
    plan: str
    cancel_at_period_end: bool
    current_period_end: Optional[str] = None


# ---------------------------------------------------------------------------
# GET /billing/config — frontend needs publishable key
# ---------------------------------------------------------------------------

@router.get("/config", response_model=BillingConfigResponse)
async def billing_config():
    """Return Stripe enabled flag (and publishable key if set)."""
    enabled = bool(settings.STRIPE_SECRET_KEY)
    return BillingConfigResponse(
        stripe_enabled=enabled,
        publishable_key=settings.STRIPE_PUBLISHABLE_KEY if enabled else None,
    )


# ---------------------------------------------------------------------------
# POST /billing/create-checkout-session
# ---------------------------------------------------------------------------

@router.post("/create-checkout-session", response_model=CheckoutResponse)
async def create_checkout_session(
    body: CheckoutRequest,
    request: Request,
    user_id: str = Depends(get_user_id),
    user: dict = Depends(get_current_user),
):
    """Create a Stripe Checkout Session for upgrading to a paid plan."""
    stripe = _require_stripe()

    # Validate target plan
    try:
        target_tier = PlanTier(body.plan)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {body.plan}")

    if target_tier == PlanTier.FREE:
        raise HTTPException(status_code=400, detail="Cannot checkout for Free plan")

    price_id = TIER_TO_STRIPE_PRICE.get(target_tier)
    if not price_id:
        raise HTTPException(
            status_code=400,
            detail=f"No Stripe price configured for {target_tier.value}",
        )

    # Resolve or create Stripe customer
    cosmos = get_cosmos_client()
    sub_record = await cosmos.get_subscription(user_id)
    customer_id = sub_record.stripe_customer_id if sub_record else None

    if not customer_id:
        email = user.get("preferred_username") or user.get("email")
        customer = stripe.Customer.create(
            email=email,
            metadata={"user_id": user_id, "entra_oid": user_id},
        )
        customer_id = customer.id
        logger.info("stripe_customer_created", user_id=user_id, customer_id=customer_id)

    # Build success/cancel URLs
    base_url = str(request.base_url).rstrip("/")
    success_url = body.success_url or f"{base_url}/#/dashboard?billing=success"
    cancel_url = body.cancel_url or f"{base_url}/#/dashboard?billing=cancel"

    # Create Checkout Session
    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": user_id, "target_plan": target_tier.value},
        subscription_data={"metadata": {"user_id": user_id}},
    )

    logger.info(
        "checkout_session_created",
        user_id=user_id,
        target_plan=target_tier.value,
        session_id=session.id,
    )

    return CheckoutResponse(checkout_url=session.url)


# ---------------------------------------------------------------------------
# POST /billing/create-portal-session
# ---------------------------------------------------------------------------

@router.post("/create-portal-session", response_model=PortalResponse)
async def create_portal_session(
    request: Request,
    user_id: str = Depends(get_user_id),
):
    """Create a Stripe Billing Portal session for managing subscription."""
    stripe = _require_stripe()

    cosmos = get_cosmos_client()
    sub_record = await cosmos.get_subscription(user_id)
    if not sub_record or not sub_record.stripe_customer_id:
        raise HTTPException(status_code=404, detail="No subscription found")

    return_url = str(request.base_url).rstrip("/") + "/#/dashboard"

    session = stripe.billing_portal.Session.create(
        customer=sub_record.stripe_customer_id,
        return_url=return_url,
    )

    return PortalResponse(portal_url=session.url)


# ---------------------------------------------------------------------------
# POST /billing/change-plan — upgrade or downgrade existing subscription
# ---------------------------------------------------------------------------

@router.post("/change-plan", response_model=ChangePlanResponse)
async def change_plan(
    body: ChangePlanRequest,
    user_id: str = Depends(get_user_id),
):
    """Upgrade or downgrade an existing Stripe subscription in-place.

    Prorations are applied automatically — the customer is charged or credited
    proportionally for the remaining billing period.

    - Upgrades: prorated charge is created immediately.
    - Downgrades: prorated credit is applied to the next invoice.
    - Free → paid: rejected (use /create-checkout-session instead).
    - Paid → free: rejected (use /cancel instead).
    """
    stripe = _require_stripe()

    # Validate target plan
    try:
        target_tier = PlanTier(body.plan)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {body.plan}")

    if target_tier == PlanTier.FREE:
        raise HTTPException(
            status_code=400,
            detail="To downgrade to Free, use /billing/cancel instead",
        )

    new_price_id = TIER_TO_STRIPE_PRICE.get(target_tier)
    if not new_price_id:
        raise HTTPException(
            status_code=400,
            detail=f"No Stripe price configured for {target_tier.value}",
        )

    # Fetch existing subscription
    cosmos = get_cosmos_client()
    sub_record = await cosmos.get_subscription(user_id)

    if not sub_record or not sub_record.stripe_subscription_id:
        raise HTTPException(
            status_code=400,
            detail="No active subscription. Use /billing/create-checkout-session for new subscriptions",
        )

    if sub_record.status not in ("active", "trialing"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot change plan while subscription is {sub_record.status}",
        )

    previous_plan = sub_record.plan_tier

    if previous_plan == target_tier.value:
        raise HTTPException(status_code=400, detail="Already on this plan")

    # Retrieve current subscription from Stripe to get the item ID
    stripe_sub = stripe.Subscription.retrieve(sub_record.stripe_subscription_id)
    if not stripe_sub["items"]["data"]:
        raise HTTPException(status_code=500, detail="Subscription has no items")

    item_id = stripe_sub["items"]["data"][0]["id"]

    # Preview proration cost
    proration_amount = None
    try:
        preview = stripe.Invoice.upcoming(
            customer=sub_record.stripe_customer_id,
            subscription=sub_record.stripe_subscription_id,
            subscription_items=[{"id": item_id, "price": new_price_id}],
            subscription_proration_behavior="create_prorations",
        )
        proration_amount = preview.get("amount_due")
    except Exception as e:
        logger.warning("proration_preview_failed", error=str(e))

    # Modify the subscription — Stripe handles proration
    updated_sub = stripe.Subscription.modify(
        sub_record.stripe_subscription_id,
        items=[{"id": item_id, "price": new_price_id}],
        proration_behavior="create_prorations",
        metadata={"user_id": user_id},
    )

    # Update local records immediately (webhook will also fire, but this is faster)
    sub_record.plan_tier = target_tier.value
    sub_record.status = updated_sub.get("status", "active")
    sub_record.cancel_at_period_end = updated_sub.get("cancel_at_period_end", False)
    sub_record.current_period_start = datetime.fromtimestamp(
        updated_sub["current_period_start"], tz=timezone.utc
    )
    sub_record.current_period_end = datetime.fromtimestamp(
        updated_sub["current_period_end"], tz=timezone.utc
    )
    sub_record.updated_at = datetime.now(tz=timezone.utc)

    await cosmos.upsert_subscription(sub_record)
    await _update_plan_cache(user_id, target_tier.value)

    logger.info(
        "plan_changed",
        user_id=user_id,
        previous_plan=previous_plan,
        new_plan=target_tier.value,
        proration_amount=proration_amount,
    )

    return ChangePlanResponse(
        previous_plan=previous_plan,
        new_plan=target_tier.value,
        status=updated_sub.get("status", "active"),
        proration_amount=proration_amount,
    )


# ---------------------------------------------------------------------------
# POST /billing/cancel — cancel subscription at end of billing period
# ---------------------------------------------------------------------------

@router.post("/cancel", response_model=CancelResponse)
async def cancel_subscription(
    user_id: str = Depends(get_user_id),
):
    """Cancel the current subscription at the end of the billing period.

    The user retains access to their paid plan until the period ends,
    then reverts to Free automatically (handled by the subscription.deleted webhook).
    """
    stripe = _require_stripe()

    cosmos = get_cosmos_client()
    sub_record = await cosmos.get_subscription(user_id)

    if not sub_record or not sub_record.stripe_subscription_id:
        raise HTTPException(status_code=404, detail="No active subscription to cancel")

    if sub_record.status == "canceled":
        raise HTTPException(status_code=400, detail="Subscription is already canceled")

    # Cancel at period end (not immediately)
    updated_sub = stripe.Subscription.modify(
        sub_record.stripe_subscription_id,
        cancel_at_period_end=True,
    )

    sub_record.cancel_at_period_end = True
    sub_record.updated_at = datetime.now(tz=timezone.utc)
    await cosmos.upsert_subscription(sub_record)

    period_end = None
    if sub_record.current_period_end:
        period_end = sub_record.current_period_end.isoformat()

    logger.info("subscription_cancel_scheduled", user_id=user_id, period_end=period_end)

    return CancelResponse(
        plan=sub_record.plan_tier,
        cancel_at_period_end=True,
        current_period_end=period_end,
    )


# ---------------------------------------------------------------------------
# GET /billing/subscription
# ---------------------------------------------------------------------------

@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(user_id: str = Depends(get_user_id)):
    """Return current subscription status for the authenticated user."""
    cosmos = get_cosmos_client()
    sub = await cosmos.get_subscription(user_id)

    if not sub:
        return SubscriptionResponse(
            has_subscription=False,
            plan=PlanTier.FREE.value,
            status="none",
        )

    return SubscriptionResponse(
        has_subscription=True,
        plan=sub.plan_tier,
        status=sub.status,
        stripe_customer_id=sub.stripe_customer_id,
        current_period_end=(
            sub.current_period_end.isoformat() if sub.current_period_end else None
        ),
        cancel_at_period_end=sub.cancel_at_period_end,
    )


# ---------------------------------------------------------------------------
# POST /billing/webhook — Stripe webhook (NO auth — verified by signature)
# ---------------------------------------------------------------------------

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events.

    This endpoint is called directly by Stripe — it MUST NOT require JWT auth.
    Verification is done via the webhook signature header.

    We always fetch the full resource from the Stripe API rather than relying
    on the event snapshot, ensuring we process the latest data.
    """
    stripe = _require_stripe()
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    # Try both B2B and B2C webhook secrets — each Stripe endpoint has its own
    # signing secret, but both apps share this handler.
    webhook_secrets = [
        s for s in (settings.STRIPE_WEBHOOK_SECRET, settings.STRIPE_WEBHOOK_SECRET_B2C) if s
    ]
    if not webhook_secrets:
        raise HTTPException(status_code=503, detail="Webhook secret not configured")

    event = None
    for secret in webhook_secrets:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, secret)
            break
        except stripe.error.SignatureVerificationError:
            continue
        except Exception as e:
            logger.error("stripe_webhook_parse_failed", error=str(e))
            raise HTTPException(status_code=400, detail="Invalid payload")

    if event is None:
        logger.warning("stripe_webhook_invalid_signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]

    # Extract the resource ID from the event snapshot so we can fetch the
    # latest version of the object from the Stripe API.
    resource_id = event["data"]["object"]["id"]

    logger.info("stripe_webhook_received", event_type=event_type, event_id=event["id"],
                resource_id=resource_id)

    try:
        if event_type == "checkout.session.completed":
            session = stripe.checkout.Session.retrieve(resource_id)
            await _handle_checkout_completed(stripe, dict(session))
        elif event_type == "customer.subscription.updated":
            sub = stripe.Subscription.retrieve(resource_id)
            await _handle_subscription_updated(dict(sub))
        elif event_type == "customer.subscription.deleted":
            sub = stripe.Subscription.retrieve(resource_id)
            await _handle_subscription_deleted(dict(sub))
        elif event_type == "invoice.payment_failed":
            invoice = stripe.Invoice.retrieve(resource_id)
            await _handle_payment_failed(dict(invoice))
        else:
            logger.debug("stripe_webhook_unhandled", event_type=event_type)
    except Exception as e:
        logger.error("stripe_webhook_handler_failed", event_type=event_type, error=str(e))
        # Return 200 to prevent Stripe retries on our bugs
        return JSONResponse({"status": "error", "message": str(e)})

    return JSONResponse({"status": "ok"})


# ---------------------------------------------------------------------------
# Webhook event handlers
# ---------------------------------------------------------------------------

async def _handle_checkout_completed(stripe, session: dict) -> None:
    """Process successful checkout — create/update subscription record."""
    user_id = session.get("metadata", {}).get("user_id")
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")

    if not user_id or not subscription_id:
        logger.warning("checkout_completed_missing_metadata", session_id=session.get("id"))
        return

    # Fetch full subscription to get price → plan mapping
    sub = stripe.Subscription.retrieve(subscription_id)
    price_id = sub["items"]["data"][0]["price"]["id"]
    plan_tier = STRIPE_PRICE_TO_TIER.get(price_id, PlanTier.PRO).value

    cosmos = get_cosmos_client()
    from src.core.models.subscription import SubscriptionRecord

    record = SubscriptionRecord(
        user_id=user_id,
        email=session.get("customer_email"),
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id,
        plan_tier=plan_tier,
        status=sub.get("status", "active"),
        current_period_start=datetime.fromtimestamp(sub["current_period_start"], tz=timezone.utc),
        current_period_end=datetime.fromtimestamp(sub["current_period_end"], tz=timezone.utc),
        cancel_at_period_end=sub.get("cancel_at_period_end", False),
    )

    # Check for existing record to preserve the id
    existing = await cosmos.get_subscription(user_id)
    if existing:
        record.id = existing.id
        record.created_at = existing.created_at

    await cosmos.upsert_subscription(record)

    # Update Redis plan cache for immediate effect
    await _update_plan_cache(user_id, plan_tier)

    logger.info(
        "checkout_completed",
        user_id=user_id,
        plan=plan_tier,
        subscription_id=subscription_id,
    )


async def _handle_subscription_updated(sub: dict) -> None:
    """Process subscription changes (upgrade, downgrade, renewal)."""
    customer_id = sub.get("customer")
    if not customer_id:
        return

    cosmos = get_cosmos_client()
    record = await cosmos.get_subscription_by_stripe_customer(customer_id)
    if not record:
        logger.warning("subscription_updated_no_record", customer_id=customer_id)
        return

    # Resolve new plan from price
    price_id = sub["items"]["data"][0]["price"]["id"]
    new_tier = STRIPE_PRICE_TO_TIER.get(price_id)
    if new_tier:
        record.plan_tier = new_tier.value

    record.status = sub.get("status", record.status)
    record.current_period_start = datetime.fromtimestamp(sub["current_period_start"], tz=timezone.utc)
    record.current_period_end = datetime.fromtimestamp(sub["current_period_end"], tz=timezone.utc)
    record.cancel_at_period_end = sub.get("cancel_at_period_end", False)

    await cosmos.upsert_subscription(record)
    await _update_plan_cache(record.user_id, record.plan_tier)

    logger.info(
        "subscription_updated",
        user_id=record.user_id,
        plan=record.plan_tier,
        status=record.status,
    )


async def _handle_subscription_deleted(sub: dict) -> None:
    """Process subscription cancellation — revert to Free."""
    customer_id = sub.get("customer")
    if not customer_id:
        return

    cosmos = get_cosmos_client()
    record = await cosmos.get_subscription_by_stripe_customer(customer_id)
    if not record:
        return

    record.plan_tier = PlanTier.FREE.value
    record.status = "canceled"
    record.cancel_at_period_end = False

    await cosmos.upsert_subscription(record)
    await _update_plan_cache(record.user_id, PlanTier.FREE.value)

    logger.info("subscription_deleted", user_id=record.user_id)


async def _handle_payment_failed(invoice: dict) -> None:
    """Log payment failure — Stripe handles retries automatically."""
    customer_id = invoice.get("customer")
    logger.warning(
        "payment_failed",
        customer_id=customer_id,
        amount=invoice.get("amount_due"),
        attempt=invoice.get("attempt_count"),
    )

    if customer_id:
        cosmos = get_cosmos_client()
        record = await cosmos.get_subscription_by_stripe_customer(customer_id)
        if record:
            record.status = "past_due"
            await cosmos.upsert_subscription(record)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _update_plan_cache(user_id: str, plan_tier_value: str) -> None:
    """Update the Redis plan cache so quota enforcement picks up the change immediately."""
    try:
        tier = PlanTier(plan_tier_value)
        enforcer = get_quota_enforcer()
        await enforcer.set_plan(user_id, tier)
    except Exception as e:
        logger.warning("plan_cache_update_failed", user_id=user_id, error=str(e))
