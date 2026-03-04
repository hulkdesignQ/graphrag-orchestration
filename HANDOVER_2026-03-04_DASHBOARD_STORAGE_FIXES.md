# Handover: Dashboard & Storage Fixes — 2026-03-04

## Summary

Enabled ADLS Gen2 for frontend file management, fixed multiple deployment issues (storage auth, Redis connectivity, Cosmos RBAC, credential selection), and wired usage tracking from the `/chat` endpoint into Cosmos DB so the dashboard can display live query data.

**Dashboard still shows zeros** — Cosmos RBAC now granted to both B2B and B2C apps, but data still not appearing. Root cause likely deeper than RBAC (see end-of-day update below).

---

## What Was Done

### 1. ADLS Gen2 Enabled on Existing Storage Account
- Cleared Microsoft Defender blob tags blocking HNS migration (`--auth-mode key`)
- Upgraded `neo4jstorage21224` to ADLS Gen2 (irreversible)
- Created `user-content` container for frontend file uploads
- Updated `infra/main.bicep`, `infra/core/security/role-assignments.bicep`, and `deploy-graphrag.sh`

### 2. Credential Selection Fix
- Added `RUNNING_IN_PRODUCTION=true` to `deploy-graphrag.sh` for all 3 container apps
- Without this, `main.py` uses `AzureDeveloperCliCredential` (unavailable in containers) instead of `ManagedIdentityCredential`

### 3. Redis Connectivity Fix
- Redis `publicNetworkAccess` was `Disabled` with no private endpoint → completely unreachable
- Enabled public access: `az redis update --name graphrag-redis-... --set publicNetworkAccess=Enabled`
- Added `asyncio.wait_for()` timeouts (10s) on all Redis calls in `dashboard.py`

### 4. Frontend Auth Retry
- `dashboard.ts` and `files.ts` used raw `fetch()` — no 401 retry
- Changed to `fetchWithAuthRetry()` which calls `.auth/refresh` then retries on 401

### 5. Cosmos DB Usage Tracking
- Added `get_cosmos_client().initialize()` at app startup in `main.py`
- Wired `/chat/completions` endpoint to write `UsageRecord` to Cosmos (fire-and-forget)
  - Sync path, streaming path, and async job path all covered
  - Redis counters already incremented by `enforce_plan_limits` dependency — no double-counting
- Granted Cosmos `Built-in Data Contributor` role to B2B app managed identity `82d924eb-a960-4fc0-8b2e-3fd314788311`

---

## Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| ADLS Gen2 storage | ✅ Working | File upload/list functional |
| Chat queries | ✅ Working | All routes functional |
| Redis connection | ✅ Working | Public access enabled, counters incrementing |
| Cosmos DB init at startup | ✅ Working | `cosmos_usage_tracking_initialized` in logs |
| Frontend auth retry | ✅ Working | 401s handled with refresh/redirect |
| Dashboard loads fast | ✅ Working | Redis timeouts prevent blocking |
| **Dashboard data** | ❌ **Zeros** | **RBAC granted, deeper investigation needed** |

---

## Root Cause: Dashboard Shows No Data

### Cosmos RBAC Only Granted to B2B App

The user accesses the app via `evidoc.hulkdesign.com` → `graphrag-api-b2c` container app. But Cosmos RBAC was only granted to the B2B app's managed identity:

| Container App | Managed Identity (principalId) | Cosmos RBAC Granted? |
|---|---|---|
| `graphrag-api` (B2B) | `82d924eb-a960-4fc0-8b2e-3fd314788311` | ✅ Yes |
| `graphrag-api-b2c` | `d00678ee-9258-4e8e-841c-801d8edf8fbf` | ✅ Yes (granted end of session) |
| `graphrag-worker` | (check with `az containerapp show`) | ❌ Unknown |

**Error from logs:**
```
Forbidden: principal [d00678ee-9258-4e8e-841c-801d8edf8fbf] does not have required RBAC permissions
to perform action [Microsoft.DocumentDB/databaseAccounts/readMetadata] on resource [/]
```

### Fix (1 command)

```bash
# Get Cosmos account resource ID
COSMOS_ID=$(az cosmosdb show -n graphrag-cosmos-wg3temevssbja -g rg-graphrag-feature --query id -o tsv)

# Grant Cosmos Built-in Data Contributor to B2C app
az cosmosdb sql role assignment create \
  --account-name graphrag-cosmos-wg3temevssbja \
  --resource-group rg-graphrag-feature \
  --role-definition-id "$COSMOS_ID/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002" \
  --principal-id d00678ee-9258-4e8e-841c-801d8edf8fbf \
  --scope "$COSMOS_ID"
```

No redeploy needed — RBAC takes effect immediately.

---

## Commits (this session)

| Commit | Description |
|--------|-------------|
| `cc6c0375` | feat(infra): add ADLS Gen2 user storage |
| `4c9e190b` | feat(infra): enable ADLS Gen2 on existing storage account |
| `eb64f181` | fix(deploy): add AZURE_STORAGE_ACCOUNT/CONTAINER |
| `e96b37ef` | fix(deploy): add RUNNING_IN_PRODUCTION env var |
| `65dd3cbe` | feat: wire dashboard usage tracking to Redis + Cosmos DB |
| `8384eb9c` | fix: add Cosmos RBAC + timeout guards for dashboard Redis calls |
| `c4e6d25e` | fix(frontend): use fetchWithAuthRetry in dashboard and files APIs |
| `507f49ee` | fix: initialize Cosmos usage client at startup + enable Redis public access |
| `c77b11f2` | feat: add Cosmos usage tracking to /chat endpoint for dashboard |

---

## Files Changed

### Backend
- `src/api_gateway/main.py` — Cosmos usage client init at startup
- `src/api_gateway/routers/chat.py` — `_write_cosmos_usage()` helper + fire-and-forget tracking on all paths
- `src/api_gateway/routers/dashboard.py` — Redis timeout guards (10s)
- `src/api_gateway/routers/hybrid.py` — pass `user_id` to `track_query()`
- `src/core/instrumentation/hooks.py` — Redis + Cosmos write in `_log_query_async`

### Frontend
- `frontend/app/frontend/src/api/dashboard.ts` — `fetchWithAuthRetry`
- `frontend/app/frontend/src/api/files.ts` — `fetchWithAuthRetry`

### Infrastructure
- `deploy-graphrag.sh` — `RUNNING_IN_PRODUCTION=true`, storage env vars
- `infra/main.bicep` — user storage params, conditional env vars
- `infra/core/security/role-assignments.bicep` — Storage Blob Data Owner role
- `infra/core/storage/storage-account.bicep` — new module

---

## Architecture Notes

### Dashboard Data Flow
```
User query via /chat/completions
  → enforce_plan_limits (Redis: increment daily/monthly counters)
  → _execute_query (GraphRAG pipeline)
  → _write_cosmos_usage (Cosmos: UsageRecord with route, tokens, query_id)

Dashboard /me endpoint
  → Redis QuotaEnforcer.get_usage() → queries_today, queries_this_month

Dashboard /me/usage endpoint
  → Cosmos query_usage(partition_id=user_oid, usage_type="llm_completion") → recent_queries
  → Cosmos query_usage(partition_id=user_oid, usage_type="document_intelligence") → documents_count
```

### Key Technical Details
- **Cosmos RBAC** uses built-in role `00000000-0000-0000-0000-000000000002` (Data Contributor), NOT Azure RBAC
- **Each container app has its own managed identity** — all must be granted Cosmos RBAC individually
- **`DefaultAzureCredential`** in Cosmos client picks up `ManagedIdentityCredential` when `RUNNING_IN_PRODUCTION=true`
- **Redis `enforce_plan_limits`** already increments counters — `_write_cosmos_usage` in chat.py only writes Cosmos, no Redis double-count
- **HNS migration** requires clearing ALL blob tags first (Defender malware scan tags invisible via `--auth-mode login`)

---

## End-of-Day Update (23:30 UTC)

### Cosmos RBAC Granted to B2C App — Dashboard Still Shows Zeros

The Cosmos RBAC grant to B2C app (`d00678ee`) **completed successfully**:
```
id: .../sqlRoleAssignments/04f17f38-deca-4fca-80eb-6b3dc786e43c
principalId: d00678ee-9258-4e8e-841c-801d8edf8fbf
roleDefinitionId: .../sqlRoleDefinitions/00000000-0000-0000-0000-000000000002
```

However, **dashboard still shows no data**. This means the issue is NOT just RBAC. Possible remaining causes:

1. **No UsageRecords exist in Cosmos yet** — the `_write_cosmos_usage` code was deployed in commit `c77b11f2` but may not have been exercised by any real queries since deployment. Need to make a test query and check Cosmos directly.
2. **Cosmos container/database mismatch** — `CosmosDBClient` may be writing to a different database/container than what dashboard reads.
3. **`_write_cosmos_usage` silently failing** — the fire-and-forget pattern (`asyncio.create_task`) swallows exceptions. Need to check container app logs for Cosmos write errors.
4. **`partition_id` mismatch** — dashboard queries Cosmos with `user_oid` but `_write_cosmos_usage` may be writing a different partition key.
5. **Redis `get_usage()` returning zeros** — even though `enforce_plan_limits` increments counters, the `get_usage()` query path may use different keys.

---

## Tomorrow's TODO

1. ~~**Grant Cosmos RBAC to B2C app**~~ ✅ Done
2. **Debug why dashboard still shows zeros** despite RBAC being granted:
   - Check Cosmos Data Explorer for any `UsageRecord` documents
   - Check container app logs for Cosmos write errors after a test query
   - Verify `_write_cosmos_usage` partition key matches dashboard query
   - Verify Redis key format: `enforce_plan_limits` writes vs `get_usage()` reads
3. **Grant Cosmos RBAC to Worker app** if it needs Cosmos access
4. **Consider adding Cosmos RBAC grants to `deploy-graphrag.sh`** or Bicep for reproducibility
