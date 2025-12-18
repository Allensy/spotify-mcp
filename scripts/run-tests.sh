#!/bin/bash
# Comprehensive test runner for Spotify MCP

echo "🧪 Spotify MCP Test Suite"
echo "=========================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall success
ALL_PASSED=true

# Function to run a test category
run_test_category() {
    local name=$1
    local file=$2
    local description=$3
    
    echo -e "${YELLOW}Running: $name${NC}"
    echo "$description"
    echo "---"
    
    if pytest "$file" -v --tb=short; then
        echo -e "${GREEN}✅ $name: PASSED${NC}"
    else
        echo -e "${RED}❌ $name: FAILED${NC}"
        ALL_PASSED=false
    fi
    echo ""
}

# Run test categories
echo "📦 1. Structure Tests"
echo "---"
run_test_category "Structure & Imports" \
    "tests/test_structure.py" \
    "Tests module structure, imports, and basic setup"

echo "🔧 2. MCP Server Tests"
echo "---"
run_test_category "Server Integration" \
    "tests/test_server.py" \
    "Tests MCP server creation, tool registration, and exports"

echo "🛡️ 3. Error Handling Tests"
echo "---"
run_test_category "Error Handling & Robustness" \
    "tests/test_error_handling.py" \
    "Tests timeouts, error messages, signal handling, and config validation"

echo "🔐 4. Authentication Flow Tests"
echo "---"
run_test_category "OAuth & Auth Flow" \
    "tests/test_auth_flow.py" \
    "Tests browser-based auth, manual flow, and callback handling"

echo "🎵 5. Spotify Tools Tests"
echo "---"
run_test_category "Spotify API Integration" \
    "tests/test_tools.py" \
    "Tests Spotify API calls (requires credentials)"

echo ""
echo "=========================="
echo "📊 Test Summary"
echo "=========================="

if [ "$ALL_PASSED" = true ]; then
    echo -e "${GREEN}✅ All test categories passed!${NC}"
    echo ""
    echo "Your Spotify MCP server is ready for:"
    echo "  • Production deployment"
    echo "  • Publishing to Docker registry"
    echo "  • Sharing with users"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo ""
    echo "Please review the failures above and fix any issues."
    echo "Run individual test files for more details:"
    echo "  pytest tests/test_<category>.py -v"
    exit 1
fi

