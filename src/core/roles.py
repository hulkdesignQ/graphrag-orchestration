"""
Role and Plan definitions for RBAC and billing.

Entra ID App Roles:
    Configure these in Azure Portal > App Registrations > App Roles:
    - "Admin"  → Full platform management, user analytics, system config
    - "User"   → Standard chat, file upload, personal dashboard

Payment Plans (B2C and B2B):
    Plans are stored per-user/per-tenant and control feature gates.
    The plan is resolved at login time and cached on the user profile.

Usage:
    from src.core.roles import AppRole, PlanTier, PlanLimits, PLAN_DEFINITIONS
"""

from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel, Field


# ============================================================================
# App Roles (must match Entra ID App Registration > App Roles)
# ============================================================================

class AppRole(str, Enum):
    """Application roles configured in Entra ID app registration."""
    ADMIN = "Admin"
    USER = "User"


# ============================================================================
# Payment Plans
# ============================================================================

class PlanTier(str, Enum):
    """Payment plan tiers — mirrors GitHub Copilot tier structure."""
    FREE = "free"
    PRO = "pro"                # Individual — $10/mo
    PRO_PLUS = "pro_plus"      # Power individual — $39/mo
    BUSINESS = "business"      # Team — $19/user/mo (same credits as Pro, adds governance)
    ENTERPRISE = "enterprise"  # Org — $39/user/mo (highest caps, priority support)

    # Legacy aliases for backward compatibility with cached Redis values
    STARTER = "starter"              # → maps to PRO
    PROFESSIONAL = "professional"    # → maps to PRO_PLUS


class PlanLimits(BaseModel):
    """Resource limits for a payment plan."""
    # Chat limits
    queries_per_day: int = Field(default=10000, description="Safety cap — credits are the primary gate")
    queries_per_month: int = Field(description="Max chat queries per month")
    max_tokens_per_query: int = Field(default=4096, description="Max output tokens per query")
    
    # Credit limits (1 credit = $0.001 USD)
    monthly_credits: Optional[int] = Field(default=None, description="Monthly credit allowance (None = skip enforcement for testing only)")
    
    # Document limits
    max_documents: int = Field(description="Max documents in knowledge base")
    max_document_size_mb: int = Field(default=10, description="Max single document size in MB")
    max_storage_gb: float = Field(default=1.0, description="Max total storage in GB")
    
    # Feature gates
    graphrag_enabled: bool = Field(default=False, description="Access to GraphRAG routes")
    advanced_analytics: bool = Field(default=False, description="Access to usage analytics dashboard")
    custom_models: bool = Field(default=False, description="Ability to select AI models")
    api_access: bool = Field(default=False, description="Programmatic API access")
    priority_support: bool = Field(default=False, description="Priority support queue")
    
    # B2B / governance features
    max_users: Optional[int] = Field(default=None, description="Max users per tenant (B2B only)")
    centralized_billing: bool = Field(default=False, description="Org-wide centralized billing")
    audit_logs: bool = Field(default=False, description="Access to audit logs and usage reports")
    policy_controls: bool = Field(default=False, description="Org-wide policy management")
    sso_enabled: bool = Field(default=False, description="SSO integration (B2B only)")
    custom_branding: bool = Field(default=False, description="Custom branding (B2B only)")
    dedicated_resources: bool = Field(default=False, description="Dedicated compute (B2B only)")


# Plan definitions — these will eventually move to a database/config service
# Pricing mirrors GitHub Copilot tiers: Free / Pro $10 / Pro+ $39 / Business $19/user / Enterprise $39/user
PLAN_DEFINITIONS: Dict[PlanTier, PlanLimits] = {
    PlanTier.FREE: PlanLimits(
        queries_per_month=90,
        max_tokens_per_query=2048,
        monthly_credits=1_350,        # ~$1.35/month — ~90 queries at ~15 credits/query
        max_documents=10,
        max_document_size_mb=5,
        max_storage_gb=0.5,
        graphrag_enabled=False,
        advanced_analytics=False,
        custom_models=False,
        api_access=False,
        priority_support=False,
    ),
    PlanTier.PRO: PlanLimits(
        queries_per_month=5000,
        max_tokens_per_query=4096,
        monthly_credits=3_000,        # ~$3/month — ~200 queries — $10/mo price
        max_documents=50,
        max_document_size_mb=10,
        max_storage_gb=2.0,
        graphrag_enabled=True,
        advanced_analytics=False,
        custom_models=False,
        api_access=False,
        priority_support=False,
    ),
    PlanTier.PRO_PLUS: PlanLimits(
        queries_per_month=20000,
        max_tokens_per_query=8192,
        monthly_credits=15_000,       # ~$15/month — ~1000 queries — $39/mo price
        max_documents=500,
        max_document_size_mb=50,
        max_storage_gb=10.0,
        graphrag_enabled=True,
        advanced_analytics=True,
        custom_models=True,
        api_access=True,
        priority_support=False,
    ),
    PlanTier.BUSINESS: PlanLimits(
        queries_per_month=5000,
        max_tokens_per_query=4096,
        monthly_credits=5_000,        # ~$5/month — ~330 queries — $19/user/mo for governance
        max_documents=50,
        max_document_size_mb=10,
        max_storage_gb=4.0,
        graphrag_enabled=True,
        advanced_analytics=True,
        custom_models=False,
        api_access=True,
        priority_support=False,
        max_users=50,
        centralized_billing=True,
        audit_logs=True,
        policy_controls=True,
    ),
    PlanTier.ENTERPRISE: PlanLimits(
        queries_per_month=50000,
        max_tokens_per_query=16384,
        monthly_credits=14_000,       # ~$14/month — ~930 queries — $39/user/mo (2.8× Business)
        max_documents=999999,
        max_document_size_mb=200,
        max_storage_gb=10.0,
        graphrag_enabled=True,
        advanced_analytics=True,
        custom_models=True,
        api_access=True,
        priority_support=True,
        max_users=500,
        centralized_billing=True,
        audit_logs=True,
        policy_controls=True,
        sso_enabled=True,
        custom_branding=True,
        dedicated_resources=True,
    ),
}

# Backward compatibility: map legacy tier names to new tiers
LEGACY_TIER_MAP: Dict[PlanTier, PlanTier] = {
    PlanTier.STARTER: PlanTier.PRO,
    PlanTier.PROFESSIONAL: PlanTier.PRO_PLUS,
}

# Ensure legacy tiers resolve to the correct plan limits
for _legacy, _current in LEGACY_TIER_MAP.items():
    PLAN_DEFINITIONS[_legacy] = PLAN_DEFINITIONS[_current]

# Tier grouping by billing type — used to filter plans in dashboard
B2C_TIERS = {PlanTier.FREE, PlanTier.PRO, PlanTier.PRO_PLUS}
B2B_TIERS = {PlanTier.BUSINESS, PlanTier.ENTERPRISE}

# Stripe Price ID → PlanTier mapping (populated from env vars at import time)
STRIPE_PRICE_TO_TIER: Dict[str, PlanTier] = {}

def _init_stripe_prices() -> None:
    """Populate STRIPE_PRICE_TO_TIER from env vars (called at module load)."""
    import os
    for env_key, tier in [
        ("STRIPE_PRICE_PRO", PlanTier.PRO),
        ("STRIPE_PRICE_PRO_PLUS", PlanTier.PRO_PLUS),
        ("STRIPE_PRICE_BUSINESS", PlanTier.BUSINESS),
        ("STRIPE_PRICE_ENTERPRISE", PlanTier.ENTERPRISE),
    ]:
        price_id = os.getenv(env_key)
        if price_id:
            STRIPE_PRICE_TO_TIER[price_id] = tier

_init_stripe_prices()

# Reverse mapping: PlanTier → Stripe Price ID
TIER_TO_STRIPE_PRICE: Dict[PlanTier, str] = {v: k for k, v in STRIPE_PRICE_TO_TIER.items()}


# ============================================================================
# User Profile Model
# ============================================================================

class UserProfile(BaseModel):
    """User profile with role and plan information."""
    # Identity (from Entra ID token)
    user_id: str = Field(description="Entra ID object ID (oid)")
    display_name: Optional[str] = Field(default=None, description="Display name")
    email: Optional[str] = Field(default=None, description="Email / UPN")
    tenant_id: Optional[str] = Field(default=None, description="Entra tenant ID")
    
    # Authorization
    roles: list[str] = Field(default_factory=list, description="App roles from Entra ID")
    groups: list[str] = Field(default_factory=list, description="Group memberships")
    is_admin: bool = Field(default=False, description="Convenience flag: has Admin role")
    
    # Payment plan
    plan: PlanTier = Field(default=PlanTier.FREE, description="Current payment plan")
    plan_limits: Optional[PlanLimits] = Field(default=None, description="Resolved plan limits")
    billing_type: str = Field(default="b2c", description="'b2c' (individual) or 'b2b' (organization)")
    
    # Usage (populated on request)
    queries_today: int = Field(default=0, description="Queries used today")
    queries_this_month: int = Field(default=0, description="Queries used this month")
    documents_count: int = Field(default=0, description="Documents in knowledge base")
    storage_used_gb: float = Field(default=0.0, description="Storage used in GB")


def resolve_user_profile(
    user_info: Dict,
    plan_tier: Optional[PlanTier] = None,
    billing_type: str = "b2c",
) -> UserProfile:
    """
    Build a UserProfile from JWT claims and plan data.
    
    In production, plan_tier would be looked up from a billing database
    keyed by user_id (B2C) or tenant_id (B2B).
    """
    roles = user_info.get("roles", [])
    is_admin = any(r.lower() == "admin" for r in roles)
    
    tier = plan_tier or PlanTier.FREE
    # Resolve legacy tier names to current tiers
    tier = LEGACY_TIER_MAP.get(tier, tier)
    limits = PLAN_DEFINITIONS.get(tier)
    
    return UserProfile(
        user_id=user_info.get("oid", ""),
        display_name=user_info.get("name"),
        email=user_info.get("preferred_username") or user_info.get("email"),
        tenant_id=user_info.get("tid"),
        roles=roles,
        groups=user_info.get("groups", []),
        is_admin=is_admin,
        plan=tier,
        plan_limits=limits,
        billing_type=billing_type,
    )
