"""
Billing API Router — Stripe Checkout, Billing Portal, and Webhooks.

Endpoints:
  POST /billing/create-checkout-session  — start a Stripe Checkout for plan upgrade
  POST /billing/create-portal-session    — open Stripe Billing Portal (manage sub)
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


# ---------------------------------------------------------------------------
# GET /billing/config — frontend needs publishable key
# ---------------------------------------------------------------------------

@router.get("/config", response_model=BillingConfigResponse)
async def billing_config():
    """Return Stripe publishable key (safe to expose) and enabled flag."""
    enabled = bool(settings.STRIPE_SECRET_KEY and settings.STRIPE_PUBLISHABLE_KEY)
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

    if target_tier in B2B_TIERS:
        raise HTTPException(status_code=400, detail="B2B plans require sales contact")

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
    """
    stripe = _require_stripe()
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        logger.warning("stripe_webhook_invalid_signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error("stripe_webhook_parse_failed", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid payload")

    event_type = event["type"]
    data = event["data"]["object"]

    logger.info("stripe_webhook_received", event_type=event_type, event_id=event["id"])

    try:
        if event_type == "checkout.session.completed":
            await _handle_checkout_completed(stripe, data)
        elif event_type == "customer.subscription.updated":
            await _handle_subscription_updated(data)
        elif event_type == "customer.subscription.deleted":
            await _handle_subscription_deleted(data)
        elif event_type == "invoice.payment_failed":
            await _handle_payment_failed(data)
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
