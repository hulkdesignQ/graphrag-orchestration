# Architecture: EasyAuth Token Refresh on Azure Container Apps

**Date:** 2026-03-04 (updated 2026-03-06)  
**Status:** Implemented & Live  
**Affects:** `graphrag-api` (B2B), `graphrag-api-b2c` (CIAM), Frontend SPA

---

## Problem

Users experienced session expiration after ~60 minutes, resulting in 401 errors and blank pages. The root cause was incomplete EasyAuth configuration across both B2B and B2C Container App deployments.

## Key Difference: App Service vs Container Apps

On **Azure App Service**, the token store uses built-in file storage (`D:\home`). Tokens persist automatically, and `.auth/refresh` works out of the box once a client secret is configured.

On **Azure Container Apps**, there is **no built-in persistent filesystem**. The token store requires an **external Azure Blob Storage** container with a SAS URL. Without it, EasyAuth cannot persist refresh tokens and `.auth/refresh` returns 401.

## Correct EasyAuth Configuration for CIAM (2026-03-06)

Both B2B and B2C use the **standard `azureActiveDirectory` provider** — no custom OIDC provider needed.

### How It Works

EasyAuth with a client secret uses **hybrid flow** (`response_type=code id_token`). CIAM returns both `code` and `id_token` via **form_post** to `/.auth/login/aad/callback`. EasyAuth validates the `id_token`, exchanges the `code` for tokens, and sets the `AppServiceAuthSession` cookie.

### ⚠️ CRITICAL: Two Things That Break CIAM Login

1. **Do NOT enable `validateNonce: true`** — CIAM does not include a nonce claim in id_tokens issued via the hybrid flow form_post. Enabling nonce validation causes EasyAuth to reject the callback → 401.

2. **Do NOT override `response_type=code`** — This disables the hybrid flow. While CIAM correctly exchanges the code, EasyAuth's internal AAD provider token processing silently fails when it receives only a code without an id_token in the callback → redirect loop → 401.

### Correct Issuer URL

Per [Microsoft guidance](https://learn.microsoft.com/en-ca/answers/questions/5615481/issuer-id-is-always-https-sts-windows-net), CIAM issuer uses **tenant ID** (not tenant name) as subdomain:

```
https://{tenantId}.ciamlogin.com/{tenantId}/v2.0
```

Both `{tenantName}.ciamlogin.com` and `{tenantId}.ciamlogin.com` resolve to the same OIDC metadata (both return `issuer: https://{tenantId}.ciamlogin.com/{tenantId}/v2.0`), but the tenant ID format is canonical.

### B2B vs B2C Configuration Matrix

| Setting | B2B (Entra ID) | B2C (CIAM) |
|---|---|---|
| Provider | `azureActiveDirectory` | `azureActiveDirectory` |
| `openIdIssuer` | `https://login.microsoftonline.com/{tid}/v2.0` | `https://{tid}.ciamlogin.com/{tid}/v2.0` |
| `clientSecretSettingName` | ✅ Required | ✅ Required |
| `loginParameters` | `scope=openid profile email offline_access` | `scope=openid profile email offline_access` |
| `response_type` override | ❌ Do not set | ❌ Do not set |
| `nonce.validateNonce` | ✅ `true` | ❌ Must be `null` |
| `tokenStore` with blob storage | ✅ Required | ✅ Required |
| `tokenRefreshExtensionHours` | 72 | 72 |
| `cookieExpiration` (FixedTime) | 08:00:00 | 08:00:00 |
| `.auth/refresh` endpoint | ✅ Works | ✅ Works (with offline_access) |

### Bicep Auth Config (Simplified)

```bicep
// Issuer URL
var openIdIssuerUrl = useExternalIdIssuer
  ? 'https://${authTenantId}.ciamlogin.com/${authTenantId}/v2.0'
  : 'https://login.microsoftonline.com/${authTenantId}/v2.0'

// Auth config (same structure for both B2B and B2C)
identityProviders: {
  azureActiveDirectory: {
    enabled: true
    registration: {
      clientId: authClientId
      clientSecretSettingName: clientSecretSettingName
      openIdIssuer: openIdIssuerUrl
    }
    login: {
      loginParameters: [ 'scope=openid profile email offline_access' ]
    }
  }
}
login: {
  nonce: authType == 'B2B' ? { validateNonce: true } : null
}
```

### Login Callback Flow (Verified 2026-03-06)

```
Browser → /.auth/login/aad
  → 302 to CIAM authorize (response_type=code id_token)
  → User authenticates (email OTP or password)
  → CIAM returns form_post to /.auth/login/aad/callback
     with fields: code, id_token, state, session_state
  → EasyAuth validates id_token, exchanges code for tokens
  → 302 to app with AppServiceAuthSession cookie
  → /.auth/me returns user claims ✓
```

### What Broke on 2026-03-05 (Postmortem)

Four changes were applied together, obscuring the root cause:

| Change | Effect |
|---|---|
| `validateNonce: true` for B2C | ❌ **Broke login** — CIAM hybrid flow id_tokens lack nonce |
| `response_type=code` override | ❌ **Broke login** — Disabled hybrid flow, EasyAuth AAD provider can't process code-only callbacks |
| Issuer URL changed to `{tid}.ciamlogin.com` | ✅ Harmless — both URL formats resolve to same metadata |
| Blob token store enabled | ✅ Harmless — improves token persistence |

Fix: revert nonce + response_type overrides, keep issuer + blob store improvements.

## Architecture: Six Fixes Applied (2026-03-04)

### 1. Backend Bicep: `container-app.bicep`

Unified EasyAuth settings for both B2B and B2C:
- **Both:** `azureActiveDirectory` provider, `offline_access` scope, blob token store, session management
- **B2B only:** `nonce` validation
- **B2C only:** nonce disabled (`null`)

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

If login or token expiration issues return:

1. **Check EasyAuth config:** `az containerapp auth show -n <app> -g rg-graphrag-feature`
   - Both B2B and B2C: must have `azureActiveDirectory` provider, `clientSecretSettingName`, `offline_access` scope, blob storage
   - B2B only: `nonce.validateNonce: true`
   - B2C: `nonce` must be `null` — **never enable nonce validation for CIAM**
   - Neither: must NOT have `response_type=code` in loginParameters — **let EasyAuth use default hybrid flow**
2. **Check secrets exist:** `az containerapp secret list -n <app> -g rg-graphrag-feature`
   - B2B: `aad-client-secret`, `token-store-sas`
   - B2C: `b2c-client-secret`, `token-store-sas`
3. **Check blob storage:** `az storage container list --account-name neo4jstorage21224 --auth-mode login`
   - Container `tokenstore` must exist
4. **Check SAS URL expiry:** SAS URLs expire — regenerate if needed
5. **Check managed identity role:** Both container apps need `Storage Blob Data Contributor` on `neo4jstorage21224`
6. **Check client secret expiry:** `az ad app show --id <client-id> --query "passwordCredentials[].endDateTime"`
7. **Test login flow manually:**
   ```bash
   # Should return 302 with response_type=code+id_token (NOT just code)
   curl -s -o /dev/null -w '%{redirect_url}' https://evidoc.hulkdesign.com/.auth/login/aad
   ```
