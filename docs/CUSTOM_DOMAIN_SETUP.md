# Custom Domain Setup Guide

## Overview

The GraphRAG platform supports custom domains for both B2B (enterprise) and B2C (consumer) endpoints:

| Endpoint | Domain | Container App |
|----------|--------|---------------|
| B2C (consumers) | `evidoc.hulkdesign.com` | `graphrag-api-b2c` |
| B2B (enterprise) | `evidoc-enterprise.hulkdesign.com` | `graphrag-api` |

## Step 1: Get Container App FQDNs

If you've **already deployed**, retrieve the FQDNs from your existing container apps (no redeployment needed):

```bash
az containerapp show -n graphrag-api -g rg-graphrag-feature --query "properties.configuration.ingress.fqdn" -o tsv
az containerapp show -n graphrag-api-b2c -g rg-graphrag-feature --query "properties.configuration.ingress.fqdn" -o tsv
```

If this is a **first-time deployment**, run `azd up` first, then note the output FQDNs:
- `GRAPHRAG_API_URI` → e.g., `https://graphrag-api.lemonriver-xxxxx.swedencentral.azurecontainerapps.io`
- `GRAPHRAG_API_B2C_URI` → e.g., `https://graphrag-api-b2c.lemonriver-xxxxx.swedencentral.azurecontainerapps.io`

## Step 2: Configure DNS Records

Both records are added in your **DNS provider** (wherever `hulkdesign.com` is managed, e.g., Cloudflare, GoDaddy).

First, get the domain verification ID from Azure — this is the TXT record value:

```bash
az containerapp env show \
  --name graphrag-env \
  --resource-group rg-graphrag-feature \
  --query "properties.customDomainConfiguration.customDomainVerificationId" \
  --output tsv
```

This returns a long hex string like `A1B2C3D4E5F6...`. Use it as the TXT value below.

### B2C Domain (`evidoc.hulkdesign.com`)

| Type | Name | Value | Purpose |
|------|------|-------|---------|
| CNAME | `evidoc` | `graphrag-api-b2c.lemonriver-xxxxx.swedencentral.azurecontainerapps.io` | Routes traffic to your Container App |
| TXT | `asuid.evidoc` | *(the hex string from the command above)* | Proves to Azure you own this domain |

### B2B Domain (`evidoc-enterprise.hulkdesign.com`)

| Type | Name | Value | Purpose |
|------|------|-------|---------|
| CNAME | `evidoc-enterprise` | `graphrag-api.lemonriver-xxxxx.swedencentral.azurecontainerapps.io` | Routes traffic to your Container App |
| TXT | `asuid.evidoc-enterprise` | *(the same hex string from the command above)* | Proves to Azure you own this domain |

> **Note**: Replace `lemonriver-xxxxx.swedencentral.azurecontainerapps.io` with your actual Container App FQDN from Step 1. The TXT value is the **same** for both domains (it's per-environment, not per-app).

## Step 3: Wait for DNS Propagation

Verify DNS is working before proceeding:

```bash
# Check CNAME records
nslookup evidoc.hulkdesign.com
nslookup evidoc-enterprise.hulkdesign.com

# Check TXT records
nslookup -type=TXT asuid.evidoc.hulkdesign.com
nslookup -type=TXT asuid.evidoc-enterprise.hulkdesign.com
```

DNS propagation typically takes 5–30 minutes but can take up to 48 hours.

## Step 4: Provision Custom Domains

Set the domain parameters and provision infrastructure only (**no container rebuild/redeploy**):

```bash
# Set the custom domain parameters
azd env set b2bCustomDomain "evidoc-enterprise.hulkdesign.com"
azd env set b2cCustomDomain "evidoc.hulkdesign.com"

# Provision infrastructure only (does NOT rebuild or redeploy containers)
azd provision
```

> **⚠️ Do NOT use `azd up` here.** `azd up` = `azd provision` + `azd deploy`, which would rebuild Docker images from your local code and redeploy all container apps, causing downtime and potentially deploying untested changes.

This will:
1. Create managed TLS certificates (free, auto-renewed by Azure)
2. Bind the custom domains to the container apps
3. Enable SNI-based TLS

## Step 5: Update Entra ID App Registrations

After custom domains are active, update the redirect URIs in your Entra ID app registrations:

### B2B App Registration
- Add redirect URI: `https://evidoc-enterprise.hulkdesign.com/.auth/login/aad/callback`

### B2C App Registration (External ID)
- Add redirect URI: `https://evidoc.hulkdesign.com/.auth/login/aad/callback`

## Step 6: Verify

```bash
# Test B2C endpoint
curl -I https://evidoc.hulkdesign.com/health

# Test B2B endpoint
curl -I https://evidoc-enterprise.hulkdesign.com/health
```

## Troubleshooting

### Certificate provisioning failed
- Ensure CNAME records are correctly pointing to the Container App FQDN
- Ensure TXT verification records are in place
- Wait for DNS propagation and retry: `azd provision`

### 421 Misdirected Request
- The managed certificate may still be provisioning (can take up to 15 minutes)
- Check certificate status in Azure Portal → Container Apps Environment → Certificates

### Authentication redirect fails
- Update redirect URIs in Entra ID app registration (Step 5)
- Clear browser cookies and retry

## Switching to a Brand Domain Later

When you're ready to move to a dedicated domain (e.g., `evidoc.io`):

1. Register the domain and configure DNS (same CNAME + TXT pattern)
2. Update the parameters and provision:
   ```bash
   azd env set b2bCustomDomain "enterprise.evidoc.io"
   azd env set b2cCustomDomain "app.evidoc.io"
   azd provision
   ```
3. Update Entra ID redirect URIs
4. (Optional) Set up redirects from old domains to new ones
