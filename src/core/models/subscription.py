"""Subscription model for Stripe billing integration."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class SubscriptionRecord(BaseModel):
    """Persistent subscription record stored in Cosmos DB.

    Partition key: user_id (B2C) or tenant_id (B2B).
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="Entra ID oid — primary lookup key")
    email: Optional[str] = Field(default=None, description="User email for Stripe customer")

    # Stripe identifiers
    stripe_customer_id: str = Field(..., description="Stripe Customer ID (cus_xxx)")
    stripe_subscription_id: Optional[str] = Field(
        default=None, description="Stripe Subscription ID (sub_xxx)"
    )

    # Plan state
    plan_tier: str = Field(default="free", description="Current plan tier value")
    status: str = Field(
        default="active",
        description="Subscription status: active, past_due, canceled, incomplete, trialing",
    )

    # Billing period
    current_period_start: Optional[datetime] = Field(default=None)
    current_period_end: Optional[datetime] = Field(default=None)
    cancel_at_period_end: bool = Field(default=False)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Cosmos DB partition key (same as user_id for B2C)
    @property
    def partition_id(self) -> str:
        return self.user_id
