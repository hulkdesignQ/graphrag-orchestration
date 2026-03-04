# Architecture: EasyAuth Token Refresh on Azure Container Apps

**Date:** 2026-03-04  
**Status:** Implemented & Live  
**Affects:** `graphrag-api` (B2B), `graphrag-api-b2c` (CIAM), Frontend SPA

---

## Problem

Users experienced session expiration after ~60 minutes, resulting in 401 errors and blank pages. The root cause was incomplete EasyAuth configuration across both B2B and B2C Container App deployments.

## Key Difference: App Service vs Container Apps

On **Azure App Service**, the token store uses built-in file storage (`D:\home`). Tokens persist automatically, and `.auth/refresh` works out of the box once a client secret is configured.

On **Azure Container Apps**, there is **no built-in persistent filesystem**. The token store requires an **external Azure Blob Storage** container with a SAS URL. Without it, EasyAuth cannot persist refresh tokens and `.auth/refresh` returns 401.

## Key Difference: B2B (Entra ID) vs B2C (CIAM / Entra External ID)

### ⚠️ CRITICAL: CIAM Does NOT Support `offline_access` or Nonce

Standard Entra ID (B2B) supports the full EasyAuth feature set:
- `offline_access` scope → Azure AD issues a refresh token
- `response_type=code` → authorization code flow
- Nonce validation → replay attack protection
- `.auth/refresh` endpoint → silent token renewal

**CIAM (Entra External ID) does NOT support:**
- `offline_access` scope in EasyAuth `loginParameters`
- Nonce validation (`validateNonce: true`)
- The `.auth/refresh` endpoint

**Adding `offline_access` or `nonce` to a CIAM EasyAuth config causes a 401 on the post-login callback** — the user authenticates successfully at the CIAM login page, but the callback to the Container App fails silently, resulting in a blank page with 401.

### What CIAM Does Support

| Setting | B2B (Entra ID) | B2C (CIAM) |
|---|---|---|
| `clientSecretSettingName` | ✅ Required | ✅ Required |
| `offline_access` scope | ✅ Required | ❌ Breaks login |
| `nonce.validateNonce` | ✅ Recommended | ❌ Breaks login |
| `tokenStore` with blob storage | ✅ Required | ✅ Required |
| `tokenRefreshExtensionHours` | ✅ Recommended (72h) | ✅ Safe to set |
| `cookieExpiration` (FixedTime) | ✅ Recommended (8h) | ✅ Safe to set |
| `.auth/refresh` endpoint | ✅ Works | ❌ Not supported |

## Architecture: Six Fixes Applied

### 1. Backend Bicep: `container-app.bicep`

Added conditional EasyAuth settings based on `authType`:
- **B2B only:** `offline_access` scope, `nonce` validation, `loginParameters`
- **Both:** `clientSecretSettingName`, blob token store, `cookieExpiration`, `tokenRefreshExtensionHours`

### 2. Frontend Bicep: `container-apps-auth.bicep`

Added `tokenRefreshExtensionHours: 72`, `cookieExpiration` (8h FixedTime), and `nonce` validation to the frontend Container App's EasyAuth config.

### 3. Infrastructure: `main.bicep` + `main.parameters.json`

Wired `authClientSecret` (B2B) and `b2cClientSecret` as Container App secrets. Added `tokenStoreSasSecretName` parameter to pass the blob storage SAS URL secret name to both B2B and B2C modules.

### 4. Frontend: 401 Auto-Retry (`api.ts`)

Added `fetchWithAuthRetry()` wrapper that:
1. Catches 401 responses
2. Calls `.auth/refresh` to renew the token
3. Retries the original request once
4. Falls back to login redirect if refresh fails

Applied to all authenticated API calls (chat, upload, file operations, history).

### 5. Frontend: Proactive Token Refresh (`authConfig.ts`)

Added a background timer that calls `.auth/refresh` **5 minutes before token expiry**, preventing users from ever hitting a 401. Re-schedules itself after each successful refresh.

### 6. Backend: JWT Expiry Verification (`auth.py`)

Enabled `verify_exp: True` in `pyjwt.decode()`. Previously, expired tokens were accepted because `verify_signature: False` also disabled expiry checks. This adds defense-in-depth.

## Infrastructure: Blob Storage Token Store

Both Container Apps use `neo4jstorage21224` (in `rg-graphrag-feature`) with:
- **Container:** `easyauth-tokens`
- **Access:** SAS URL stored as Container App secret `token-store-sas`
- **Identity:** System-assigned managed identity with `Storage Blob Data Contributor` role

## Files Changed

| File | Change |
|---|---|
| `infra/core/host/container-app.bicep` | Conditional B2B/B2C EasyAuth, blob token store, session management |
| `infra/main.bicep` | Wired `authClientSecret`, `tokenStoreSasSecretName` |
| `infra/main.parameters.json` | Added `authClientSecret` parameter |
| `frontend/infra/core/host/container-apps-auth.bicep` | Added session management settings |
| `frontend/app/frontend/src/api/api.ts` | `fetchWithAuthRetry()` wrapper |
| `frontend/app/frontend/src/authConfig.ts` | Proactive background refresh timer |
| `src/api_gateway/middleware/auth.py` | `verify_exp: True` in JWT decode |

## Debugging Checklist

If token expiration issues return:

1. **Check EasyAuth config:** `az containerapp auth show -n <app> -g rg-graphrag-feature`
   - B2B: must have `clientSecretSettingName`, `offline_access`, blob storage
   - B2C: must NOT have `offline_access` or `nonce`
2. **Check secrets exist:** `az containerapp secret list -n <app> -g rg-graphrag-feature`
   - B2B: `aad-client-secret`, `token-store-sas`
   - B2C: `microsoft-provider-authentication-secret`, `token-store-sas`
3. **Check blob storage:** `az storage container list --account-name neo4jstorage21224 --auth-mode login`
   - Container `easyauth-tokens` must exist
4. **Check SAS URL expiry:** SAS URLs expire — regenerate if needed
5. **Check managed identity role:** Both container apps need `Storage Blob Data Contributor` on `neo4jstorage21224`
6. **Check client secret expiry:** `az ad app show --id <client-id> --query "passwordCredentials[].endDateTime"`
