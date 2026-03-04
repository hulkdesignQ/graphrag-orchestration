# ARCHITECTURE: ADLS Gen2 Storage Enablement for Frontend File Management

**Date:** 2026-03-04

## Problem

The frontend's `AdlsBlobManager` requires an ADLS Gen2 storage account (HNS-enabled, `*.dfs.core.windows.net` endpoint) for per-user file uploads with hierarchical namespace and ACL-based access control. The existing storage account `neo4jstorage21224` did not have HNS enabled.

## Root Cause Chain

1. **HNS not enabled** on `neo4jstorage21224` — the account was created as standard Blob Storage (StorageV2 without hierarchical namespace).
2. **HNS migration blocked by Blob Tags** — Microsoft Defender for Storage automatically adds "Malware Scanning" tags to blobs. ADLS Gen2 migration requires all blob tags to be removed first.
3. **`BlobManager` lacks `list_blobs`** — The deployed image (`a3445bab`) used `prepdocslib.BlobManager` (which has no `list_blobs` method) instead of the newer `UserBlobManager` from `src/api_gateway/services/user_blob_manager.py` (commit `e793a626`).

## Resolution

### 1. Storage Account Migration (In-Place)

Upgraded `neo4jstorage21224` to ADLS Gen2 via Azure HNS migration:

```bash
# 1. Clear Defender malware-scan blob tags (blocking migration)
az storage blob tag set --account-name neo4jstorage21224 --container-name <container> --name <blob> --tags "" --auth-mode key

# 2. Validate migration
az storage account hns-migration start --type validation --name neo4jstorage21224 --resource-group rg-graphrag-feature

# 3. Upgrade (irreversible)
az storage account hns-migration start --type upgrade --name neo4jstorage21224 --resource-group rg-graphrag-feature
```

**Result:** `isHnsEnabled: true` — DFS endpoint now available at `https://neo4jstorage21224.dfs.core.windows.net`.

### 2. Container Created

```bash
az storage container create --name user-content --account-name neo4jstorage21224 --auth-mode login --public-access off
```

### 3. Infrastructure Changes

**`infra/core/storage/storage-account.bicep`** (new):
- Reusable storage account module with `isHnsEnabled` parameter.

**`infra/main.bicep`**:
- Added `useUserUpload` flag (default `true`), `userStorageContainerName` param.
- Passes `AZURE_STORAGE_ACCOUNT`, `AZURE_STORAGE_CONTAINER`, `AZURE_USERSTORAGE_ACCOUNT`, `AZURE_USERSTORAGE_CONTAINER` env vars to container apps when `useUserUpload=true`.
- Added `Storage Blob Data Owner` role assignment for container app principals.
- Added `AZURE_USERSTORAGE_ACCOUNT` and `AZURE_USERSTORAGE_CONTAINER` outputs.

**`infra/core/security/role-assignments.bicep`**:
- Added optional `userStorageAccountName` param.
- Added `Storage Blob Data Owner` (`b7e6dc6d-f1e8-4753-8033-0f276bb0955b`) role for ADLS Gen2 file operations.

**`deploy-graphrag.sh`**:
- Added `AZURE_STORAGE_ACCOUNT` and `AZURE_STORAGE_CONTAINER` to ENV_VARS array.
- Fixed `AZURE_USERSTORAGE_CONTAINER` default from `documents` to `user-content`.

### 4. Container App Env Vars Deployed

All three container apps (`graphrag-api`, `graphrag-api-b2c`, `graphrag-worker`) updated with:

| Variable | Value |
|---|---|
| `AZURE_STORAGE_ACCOUNT` | `neo4jstorage21224` |
| `AZURE_STORAGE_CONTAINER` | `content` |
| `AZURE_USERSTORAGE_ACCOUNT` | `neo4jstorage21224` |
| `AZURE_USERSTORAGE_CONTAINER` | `user-content` |

### 5. Code Fix Required (Pending Deploy)

The deployed image `a3445bab` predates commit `e793a626` which introduced `UserBlobManager` with `list_blobs`. A full redeploy (Docker build + push) is needed to pick up the fix.

## Key Learnings

- **HNS migration is possible** on existing accounts (since ~2023), but requires removing all blob tags first.
- **Microsoft Defender blob tags** are invisible via `--auth-mode login` (needs `Storage Blob Data Owner` or `--auth-mode key` to read/clear).
- **Single storage account** works for both global content (Blob API) and user uploads (DFS API) — no need for separate accounts.
- **Deploy script must pass env vars** — Bicep-defined env vars only apply during `azd provision`, but `deploy-graphrap.sh` uses `az containerapp update --set-env-vars` which overrides all env vars.
