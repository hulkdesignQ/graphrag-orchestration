# Custom Domain Setup Guide

## Overview

The GraphRAG platform supports custom domains for both B2B (enterprise) and B2C (consumer) endpoints:

| Endpoint | Domain | Container App |
|----------|--------|---------------|
| B2C (consumers) | `evidoc.hulkdesign.com` | `graphrag-api-b2c` |
| B2B (enterprise) | `evidoc-enterprise.hulkdesign.com` | `graphrag-api` |

## Step 1: Deploy Without Custom Domains (first time only)

If you haven't deployed yet, deploy first to get the auto-generated FQDNs:

```bash
azd up
```

Note the output FQDNs:
- `GRAPHRAG_API_URI` → e.g., `https://graphrag-api.lemonriver-xxxxx.swedencentral.azurecontainerapps.io`
- `GRAPHRAG_API_B2C_URI` → e.g., `https://graphrag-api-b2c.lemonriver-xxxxx.swedencentral.azurecontainerapps.io`

## Step 2: Configure DNS Records

In your DNS provider (for `hulkdesign.com`), create the following records:

### B2C Domain (`evidoc.hulkdesign.com`)

| Type | Name | Value |
|------|------|-------|
| CNAME | `evidoc` | `graphrag-api-b2c.lemonriver-xxxxx.swedencentral.azurecontainerapps.io` |
| TXT | `asuid.evidoc` | *(get from Azure Portal → Container App → Custom domains → Add)* |

### B2B Domain (`evidoc-enterprise.hulkdesign.com`)

| Type | Name | Value |
|------|------|-------|
| CNAME | `evidoc-enterprise` | `graphrag-api.lemonriver-xxxxx.swedencentral.azurecontainerapps.io` |
| TXT | `asuid.evidoc-enterprise` | *(get from Azure Portal → Container App → Custom domains → Add)* |

> **Note**: Replace `lemonriver-xxxxx.swedencentral.azurecontainerapps.io` with your actual Container App FQDN from Step 1.

### Getting the TXT verification value

```bash
# Get the domain verification ID for your Container Apps Environment
az containerapp env show \
  --name graphrag-env \
  --resource-group rg-graphrag-feature \
  --query "properties.customDomainConfiguration.customDomainVerificationId" \
  --output tsv
```

Use this value as the TXT record content for both `asuid.evidoc` and `asuid.evidoc-enterprise`.

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

## Step 4: Deploy with Custom Domains

Set the domain parameters and redeploy:

```bash
# Set the custom domain parameters
azd env set b2bCustomDomain "evidoc-enterprise.hulkdesign.com"
azd env set b2cCustomDomain "evidoc.hulkdesign.com"

# Redeploy
azd up
```

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
- Wait for DNS propagation and retry: `azd up`

### 421 Misdirected Request
- The managed certificate may still be provisioning (can take up to 15 minutes)
- Check certificate status in Azure Portal → Container Apps Environment → Certificates

### Authentication redirect fails
- Update redirect URIs in Entra ID app registration (Step 5)
- Clear browser cookies and retry

## Switching to a Brand Domain Later

When you're ready to move to a dedicated domain (e.g., `evidoc.io`):

1. Register the domain and configure DNS (same CNAME + TXT pattern)
2. Update the parameters:
   ```bash
   azd env set b2bCustomDomain "enterprise.evidoc.io"
   azd env set b2cCustomDomain "app.evidoc.io"
   azd up
   ```
3. Update Entra ID redirect URIs
4. (Optional) Set up redirects from old domains to new ones
