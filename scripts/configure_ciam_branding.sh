#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

LOGO_PATH="${REPO_ROOT}/infra/branding/square_logo_512.png"

echo "=========================================="
echo "Configure CIAM / B2C Login Page Branding"
echo "=========================================="
echo ""

# ── 1. Resolve B2C tenant ────────────────────────────────────────────────────
B2C_TENANT_ID=$(azd env get-values 2>/dev/null | grep AZURE_B2C_TENANT_ID | cut -d'=' -f2 | tr -d '"')
B2C_TENANT_NAME=$(azd env get-values 2>/dev/null | grep AZURE_B2C_TENANT_NAME | cut -d'=' -f2 | tr -d '"')

if [ -z "$B2C_TENANT_ID" ]; then
    echo "⚠  AZURE_B2C_TENANT_ID not found in azd env."
    read -rp "Enter B2C / CIAM Tenant ID: " B2C_TENANT_ID
    read -rp "Enter B2C / CIAM Tenant Name (e.g. hulkdesigncustomers): " B2C_TENANT_NAME
fi

echo "Tenant : ${B2C_TENANT_NAME} (${B2C_TENANT_ID})"
echo ""

# ── 2. Authenticate to the CIAM tenant ───────────────────────────────────────
echo "Signing in to CIAM tenant…"
az login --tenant "$B2C_TENANT_ID" --allow-no-subscriptions --use-device-code
echo ""

# ── 3. Get the organisation object id ────────────────────────────────────────
echo "Fetching organisation id…"
ORG_ID=$(az rest --method GET \
    --url "https://graph.microsoft.com/v1.0/organization" \
    --query "value[0].id" -o tsv)

if [ -z "$ORG_ID" ]; then
    echo "❌ Could not retrieve organisation id. Do you have Organization.ReadWrite.All permission?"
    exit 1
fi
echo "Organisation: $ORG_ID"
echo ""

# ── 4. Ensure default branding locale exists ─────────────────────────────────
TOKEN=$(az account get-access-token --tenant "$B2C_TENANT_ID" --resource https://graph.microsoft.com --query accessToken -o tsv)
echo "Ensuring default branding locale exists…"
BRANDING_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    "https://graph.microsoft.com/v1.0/organization/${ORG_ID}/branding")

if [ "$BRANDING_STATUS" != "200" ]; then
    echo "Creating default branding…"
    curl -sf -X PATCH \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"signInPageText":""}' \
        "https://graph.microsoft.com/v1.0/organization/${ORG_ID}/branding"
    echo "✅ Default branding locale created"
else
    echo "✅ Default branding locale already exists"
fi
echo ""

# ── 5. Upload square logo ────────────────────────────────────────────────────
if [ ! -f "$LOGO_PATH" ]; then
    echo "❌ Logo not found at $LOGO_PATH"
    exit 1
fi

echo "Uploading square logo (${LOGO_PATH})…"
curl -sf -X PUT \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: image/png" \
    --data-binary @"$LOGO_PATH" \
    "https://graph.microsoft.com/v1.0/organization/${ORG_ID}/branding/localizations/0/squareLogo"
echo "✅ Square logo uploaded"
echo ""

echo "Uploading square logo (dark theme)…"
curl -sf -X PUT \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: image/png" \
    --data-binary @"$LOGO_PATH" \
    "https://graph.microsoft.com/v1.0/organization/${ORG_ID}/branding/localizations/0/squareLogoDark"
echo "✅ Square logo (dark) uploaded"
echo ""

# ── 6. Set sign-in page text & background ────────────────────────────────────
echo "Setting sign-in page properties…"
curl -sf -X PATCH \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"signInPageText":"Hulkdesign AI · KnowledgeMap","usernameHintText":"Enter your email address","backgroundColor":"#f3f4f6"}' \
    "https://graph.microsoft.com/v1.0/organization/${ORG_ID}/branding"
echo "✅ Sign-in page properties updated"
echo ""

# ── 7. Switch back to default subscription ───────────────────────────────────
DEFAULT_SUB=$(az account list --query "[?isDefault].id" -o tsv 2>/dev/null || true)
if [ -n "$DEFAULT_SUB" ]; then
    az account set --subscription "$DEFAULT_SUB" 2>/dev/null || true
    echo "Switched back to default subscription"
fi

echo ""
echo "=========================================="
echo "✅ CIAM Branding Configuration Complete!"
echo "=========================================="
echo ""
echo "The Hulkdesign logo will now appear on the"
echo "CIAM / External ID sign-in page."
echo ""
echo "To verify, visit:"
echo "  https://${B2C_TENANT_NAME}.ciamlogin.com/${B2C_TENANT_ID}/v2.0/authorize?client_id=<your-client-id>&response_type=code&redirect_uri=https://jwt.ms&scope=openid"
echo ""
