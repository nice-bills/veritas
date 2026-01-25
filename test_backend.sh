#!/bin/bash
# Veritas Backend Test Script
# Tests all endpoints with user-provided API keys

set -e

# Configuration - User must set these
: "${API_URL:="http://localhost:8000"}"
: "${MINIMAX_KEY:=""}"
: "${CDP_KEY_ID:=""}"
: "${CDP_KEY_SECRET:=""}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "  Veritas Backend Test Suite"
echo "=============================================="
echo ""
echo "API URL: $API_URL"
echo ""

# Check if keys are provided
if [ -z "$MINIMAX_KEY" ]; then
    echo -e "${YELLOW}WARNING: MINIMAX_KEY not set. Tests requiring AI will fail.${NC}"
fi

if [ -z "$CDP_KEY_ID" ] || [ -z "$CDP_KEY_SECRET" ]; then
    echo -e "${YELLOW}WARNING: CDP credentials not set. Blockchain tests will fail.${NC}"
fi

echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# ========================================
# TEST 1: Health Check
# ========================================
echo ""
echo "=============================================="
echo "TEST 1: Health Check"
echo "=============================================="

curl -s "$API_URL/"
echo ""

# ========================================
# TEST 2: Create Agent (Wallet + Token)
# ========================================
echo ""
echo "=============================================="
echo "TEST 2: Create Agent (Wallet + Token)"
echo "=============================================="

AGENT1_RESPONSE=$(curl -s -X POST "$API_URL/agents" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Test-Wallet-Token",
        "brain_provider": "minimax",
        "network": "base-sepolia",
        "capabilities": ["wallet", "token"],
        "minimax_api_key": "'"$MINIMAX_KEY"'",
        "cdp_api_key_id": "'"$CDP_KEY_ID"'",
        "cdp_api_key_secret": "'"$CDP_KEY_SECRET"'"
    }')

echo "$AGENT1_RESPONSE" | head -c 500

AGENT1_ID=$(echo "$AGENT1_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null || echo "")

if [ -n "$AGENT1_ID" ]; then
    echo -e "${GREEN}[PASS] Agent created: $AGENT1_ID${NC}"
else
    echo -e "${RED}[FAIL] Failed to create agent${NC}"
fi

# ========================================
# TEST 3: Create Agent (Aave + Pyth)
# ========================================
echo ""
echo "=============================================="
echo "TEST 3: Create Agent (Aave + Pyth)"
echo "=============================================="

AGENT2_RESPONSE=$(curl -s -X POST "$API_URL/agents" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Test-Aave-Pyth",
        "brain_provider": "minimax",
        "network": "base-sepolia",
        "capabilities": ["aave", "pyth"],
        "minimax_api_key": "'"$MINIMAX_KEY"'",
        "cdp_api_key_id": "'"$CDP_KEY_ID"'",
        "cdp_api_key_secret": "'"$CDP_KEY_SECRET"'"
    }')

echo "$AGENT2_RESPONSE" | head -c 500

AGENT2_ID=$(echo "$AGENT2_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null || echo "")

if [ -n "$AGENT2_ID" ]; then
    echo -e "${GREEN}[PASS] Agent created: $AGENT2_ID${NC}"
else
    echo -e "${RED}[FAIL] Failed to create agent${NC}"
fi

# ========================================
# TEST 4: Run Mission (Balance Check)
# ========================================
echo ""
echo "=============================================="
echo "TEST 4: Run Mission (Balance Check)"
echo "=============================================="

if [ -n "$AGENT1_ID" ]; then
    MISSION1_RESPONSE=$(curl -s -X POST "$API_URL/agents/$AGENT1_ID/run" \
        -H "Content-Type: application/json" \
        -d '{"objective": "Check my ETH balance."}')
    
    echo "$MISSION1_RESPONSE" | head -c 500
    
    if echo "$MISSION1_RESPONSE" | grep -q "session_root"; then
        echo ""
        echo -e "${GREEN}[PASS] Mission completed successfully${NC}"
    else
        echo ""
        echo -e "${YELLOW}[INFO] Mission response received (check for errors above)${NC}"
    fi
else
    echo -e "${RED}[SKIP] No agent available${NC}"
fi

# ========================================
# TEST 5: Error Handling (Invalid Agent)
# ========================================
echo ""
echo "=============================================="
echo "TEST 5: Error Handling (Invalid Agent)"
echo "=============================================="

ERROR_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/agents/invalid-id-123/run" \
    -H "Content-Type: application/json" \
    -d '{"objective": "test"}')

HTTP_CODE=$(echo "$ERROR_RESPONSE" | tail -n1)
BODY=$(echo "$ERROR_RESPONSE" | head -n-1)

echo "HTTP Status: $HTTP_CODE"
echo "Body: $BODY" | head -c 200

if [ "$HTTP_CODE" = "404" ]; then
    echo ""
    echo -e "${GREEN}[PASS] Correctly returned 404 for invalid agent${NC}"
else
    echo ""
    echo -e "${RED}[FAIL] Expected 404, got $HTTP_CODE${NC}"
fi

# ========================================
# TEST 6: Cleanup
# ========================================
echo ""
echo "=============================================="
echo "TEST 6: Cleanup (Delete Agents)"
echo "=============================================="

if [ -n "$AGENT1_ID" ]; then
    DELETE1=$(curl -s -w "\n%{http_code}" -X DELETE "$API_URL/agents/$AGENT1_ID")
    DELETE1_CODE=$(echo "$DELETE1" | tail -n1)
    if [ "$DELETE1_CODE" = "200" ]; then
        echo -e "${GREEN}[PASS] Deleted agent 1${NC}"
    else
        echo -e "${RED}[FAIL] Failed to delete agent 1${NC}"
    fi
fi

if [ -n "$AGENT2_ID" ]; then
    DELETE2=$(curl -s -w "\n%{http_code}" -X DELETE "$API_URL/agents/$AGENT2_ID")
    DELETE2_CODE=$(echo "$DELETE2" | tail -n1)
    if [ "$DELETE2_CODE" = "200" ]; then
        echo -e "${GREEN}[PASS] Deleted agent 2${NC}"
    else
        echo -e "${RED}[FAIL] Failed to delete agent 2${NC}"
    fi
fi

echo ""
echo "=============================================="
echo "TEST SUITE COMPLETE"
echo "=============================================="
