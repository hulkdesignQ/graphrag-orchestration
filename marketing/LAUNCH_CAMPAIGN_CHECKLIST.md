# Evidoc Launch Campaign Checklist

**Last updated:** 2026-03-17

---

## Product Core

| # | Item | Status | Notes |
|---|---|---|---|
| 1 | Multi-route GraphRAG engine (Routes 1-8) | ✅ Done | Auto-routing, benchmarked |
| 2 | Click-to-verify citations (polygon highlighting) | ✅ Done | Word-level PDF highlighting |
| 3 | Cross-document Q&A | ✅ Done | 93.8% inconsistency detection |
| 4 | 15+ document format support | ✅ Done | Azure Document Intelligence OCR |
| 5 | 13-language support + translation + voice | ✅ Done | Azure Translator + Speech |
| 6 | Chat UI with streaming | ✅ Done | React, NDJSON streaming |
| 7 | File management (upload, folders, lifecycle) | ✅ Done | Blob storage + folder hierarchy |
| 8 | User dashboard (usage, plans, stats) | ✅ Done | Credits, storage, activity |
| 9 | Admin dashboard | ✅ Done | Algorithm management, diagnostics |

## Infrastructure

| # | Item | Status | Notes |
|---|---|---|---|
| 10 | Azure Container Apps deployment | ✅ Done | API + Worker, Bicep IaC |
| 11 | CI/CD pipeline | ✅ Done | GitHub Actions, push-to-main auto-deploy |
| 12 | B2B auth (Azure AD groups) | ✅ Done | JWT + JWKS, group-based isolation |
| 13 | B2C auth (Entra External ID / CIAM) | ✅ Done | Self-service signup, ciamlogin.com issuer, Bicep parameterized |
| 14 | Quota enforcement (Redis) | ✅ Done | Atomic daily/monthly/credit limits, fail-open |
| 15 | Usage tracking (Cosmos DB) | ✅ Done | Fire-and-forget, 90-day TTL |
| 16 | Credit metering | ✅ Done | Per-operation USD→credit conversion |
| 17 | Multi-tenant isolation | ✅ Done | Group isolation middleware + Neo4j partition |
| 18 | Health endpoints | ✅ Done | `/health` + `/health/detailed` |
| 19 | Custom domain guide | ✅ Done | `evidoc.hulkdesign.com` documented |
| 20 | Security patching | ✅ Done | 5 CVEs fixed (2 high, 3 moderate) |

## Pricing & Billing

| # | Item | Status | Notes |
|---|---|---|---|
| 21 | Pricing tiers defined (5-tier Copilot model) | ✅ Done | Free/$10 Pro/$39 Pro+/$19 Business/$39 Enterprise |
| 22 | Credit schedule (LLM, embedding, rerank, OCR) | ✅ Done | `credit_schedule.py` |
| 23 | B2C/B2B plan filtering in dashboard | ✅ Done | B2C sees Free/Pro/Pro+, B2B sees Business/Enterprise |
| 24 | Rate limit UX (429 → upgrade prompt) | ✅ Done | Chat shows plan + link to dashboard |
| 25 | Payment integration (Stripe/Paddle) | ✅ Done | Stripe Checkout + webhooks integrated |
| 26 | Plan upgrade/downgrade API | ✅ Done | `POST /billing/change-plan` with Stripe proration |
| 27 | Billing portal | ✅ Done | Stripe Customer Portal linked from Dashboard |

## Marketing Materials

| # | Item | Status | Notes |
|---|---|---|---|
| 28 | Marketing strategy & use cases | ✅ Done | B2C top 5 + B2B top 5, storytelling framework |
| 29 | Competitive landscape (5 segments, 20+ competitors) | ✅ Done | Positioning matrix, risk mitigations |
| 30 | LinkedIn launch post (B2C) | ✅ Done | `marketing/linkedin_launch_post.md` |
| 31 | LinkedIn launch post (B2B) | ✅ Done | `marketing/linkedin_launch_post_b2b.md` |
| 32 | Homepage HTML prototype | ✅ Done | `marketing/evidoc_homepage_preview.html` |
| 33 | Pitch deck (NIA Spark) | ✅ Done | `marketing/evidoc_nia_spark_pitch.pptx` |
| 34 | Brand kit (logo, icon, SVG/AI/EPS) | ✅ Done | `marketing/hulkdesign-*` |

## Public Website

| # | Item | Status | Notes |
|---|---|---|---|
| 35 | Astro site scaffolding | ✅ Done | Astro 5 + Tailwind, 13-language i18n routing |
| 36 | Homepage (from HTML prototype) | ✅ Done | 12 components, 130+ translation keys, builds 13 pages |
| 37 | Pricing page | ✅ Done | Embedded in homepage with Individual/Business tab toggle |
| 38 | How It Works page | ✅ Done | Embedded in homepage as #how-it-works section |
| 39 | Use-case landing pages | 🟡 Later | Legal, manufacturing, procurement (Phase 2) |
| 40 | Blog infrastructure | 🟡 Later | Astro content collections (Phase 2) |
| 41 | Custom domain deployment | 🔴 Pending | DNS + managed cert in Bicep ready |
| 42 | Demo video (60s screen recording) | 🔴 Pending | Upload → Ask → Click-to-verify flow |

## User Experience

| # | Item | Status | Notes |
|---|---|---|---|
| 43 | Onboarding flow + sample documents | ✅ Done | Welcome banner, Getting Started page, 3 sample docs (agreement/invoice/policy) |
| 44 | *(merged into #43)* | ✅ Done | — |
| 45 | Getting Started guide | ✅ Done | `docs/GETTING_STARTED.md` + in-app `/getting-started` page |
| 46 | Error messages (user-friendly) | ✅ Done | Network, timeout, rate limit, server errors |
| 47 | Session expiry handling | ✅ Done | Auto-refresh + re-login prompt |

## Analytics & Monitoring

| # | Item | Status | Notes |
|---|---|---|---|
| 48 | Product analytics (PostHog) | ✅ Done | Opt-in via `VITE_POSTHOG_KEY` env var |
| 49 | Funnel tracking (signup → upload → query) | ✅ Done | Events: query_sent, file_uploaded, citation_clicked, dashboard_viewed |
| 50 | Error tracking (Sentry) | ✅ Done | Frontend `VITE_SENTRY_DSN` + Backend `SENTRY_DSN` |
| 51 | Conversion tracking (free → paid) | ✅ Done | plan_upgrade_clicked + rate_limit_hit events |

## Legal & Compliance

| # | Item | Status | Notes |
|---|---|---|---|
| 52 | Terms of Service | ✅ Done | `docs/legal/TERMS_OF_SERVICE.md` — pending legal review |
| 53 | Privacy Policy | ✅ Done | `docs/legal/PRIVACY_POLICY.md` — pending legal review |
| 54 | Cookie consent banner | ✅ Done | `docs/legal/COOKIE_POLICY.md` + frontend CookieConsentBanner component |
| 55 | Data Processing Agreement (B2B) | 🟡 Later | Phase 2 |
| 56 | GDPR data deletion flow | 🟡 Later | Phase 2 |

## Technical Debt

| # | Item | Status | Notes |
|---|---|---|---|
| 57 | Cypher 25 `id()` migration (17 calls) | ✅ Done | All migrated to `elementId()`, `CYPHER 25` prefix on vector queries |
| 58 | Load testing (Locust) | 🔴 Pending | Current locustfile is upstream template with sample data |
| 59 | Autoscaling validation | 🔴 Pending | No concurrency/OOM testing |

---

## Summary

| Category | Done | Pending | Later |
|---|---|---|---|
| Product Core | 9 | 0 | 0 |
| Infrastructure | 11 | 0 | 0 |
| Pricing & Billing | 7 | 0 | 0 |
| Marketing Materials | 7 | 0 | 0 |
| Public Website | 4 | 1 | 2 |
| User Experience | 5 | 0 | 0 |
| Analytics & Monitoring | 4 | 0 | 0 |
| Legal & Compliance | 3 | 0 | 2 |
| Technical Debt | 1 | 2 | 0 |
| **Total** | **51** | **3** | **4** |

---

## Recommended Launch Phases

### Phase 0 — Waitlist Launch (this week)
- [ ] Deploy Astro site with homepage + email capture
- [ ] Post LinkedIn launch posts (B2C + B2B)
- [ ] Record 60-second demo video
- [ ] Set up Plausible analytics

### Phase 1 — Early Access (free tier)
- [ ] Deploy B2C container app with custom domain
- [ ] Build onboarding flow (welcome + sample docs)
- [ ] Terms of Service + Privacy Policy
- [ ] Basic load test (10 concurrent users)
- [ ] Cypher 25 `id()` migration
- [ ] Error tracking (Sentry)

### Phase 2 — Revenue Launch (paid tiers)
- [ ] Stripe Checkout integration
- [ ] Plan upgrade/downgrade API + webhooks
- [ ] Billing portal (Stripe Customer Portal)
- [ ] Cookie consent banner
- [ ] Full load testing
- [ ] Conversion tracking

### Phase 3 — Growth
- [ ] Use-case landing pages (legal, manufacturing, procurement)
- [ ] Blog (founder story + customer story)
- [ ] LinkedIn content calendar (1 post/week)
- [ ] DPA for B2B customers
- [ ] GDPR data deletion flow
