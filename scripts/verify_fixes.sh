#!/bin/bash

echo "🔍 Verifying Scalekit Skill Fixes..."
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

EXIT_CODE=0

# Check for validateAccessToken
echo "Checking for validateAccessToken()..."
VALIDATE_ACCESS_COUNT=$(grep -r "validateAccessToken" skills/scalekit-auth/ --exclude-dir=node_modules 2>/dev/null | wc -l | tr -d ' ')
if [ "$VALIDATE_ACCESS_COUNT" -gt 0 ]; then
  echo -e "${RED}❌ FAILED: Found $VALIDATE_ACCESS_COUNT instances of validateAccessToken${NC}"
  grep -r "validateAccessToken" skills/scalekit-auth/ --exclude-dir=node_modules 2>/dev/null
  EXIT_CODE=1
else
  echo -e "${GREEN}✅ PASSED: No validateAccessToken found${NC}"
fi

# Check for scalekit.organizations
echo ""
echo "Checking for scalekit.organizations..."
ORGS_PLURAL_COUNT=$(grep -r "scalekit\.organizations\." skills/scalekit-auth/ --exclude-dir=node_modules 2>/dev/null | wc -l | tr -d ' ')
if [ "$ORGS_PLURAL_COUNT" -gt 0 ]; then
  echo -e "${RED}❌ FAILED: Found $ORGS_PLURAL_COUNT instances of scalekit.organizations${NC}"
  grep -r "scalekit\.organizations\." skills/scalekit-auth/ --exclude-dir=node_modules 2>/dev/null
  EXIT_CODE=1
else
  echo -e "${GREEN}✅ PASSED: No scalekit.organizations found${NC}"
fi

# Check for validateToken with options
echo ""
echo "Checking validateToken() calls have options..."
VALIDATE_TOKEN_LINES=$(grep -r "validateToken(" skills/scalekit-auth/ --exclude-dir=node_modules 2>/dev/null)
if [ -n "$VALIDATE_TOKEN_LINES" ]; then
  VALIDATE_TOKEN_NO_OPTIONS=$(echo "$VALIDATE_TOKEN_LINES" | grep -v "issuer" | grep -v "audience" | wc -l | tr -d ' ')
  if [ "$VALIDATE_TOKEN_NO_OPTIONS" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  WARNING: Found validateToken() calls without options${NC}"
    echo "$VALIDATE_TOKEN_LINES" | grep -v "issuer" | grep -v "audience"
  else
    echo -e "${GREEN}✅ PASSED: All validateToken() calls include options${NC}"
  fi
fi

echo ""
echo "================================"
if [ $EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}✅ All verification checks passed!${NC}"
else
  echo -e "${RED}❌ Verification failed. Please fix the issues above.${NC}"
fi
echo "================================"

exit $EXIT_CODE
