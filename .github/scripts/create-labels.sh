#!/bin/bash
# Script to create GitHub labels for Dependabot and other CI/CD workflows
# Requires GitHub CLI (gh) to be installed and authenticated

set -e

REPO="Allensy/spotify-mcp"

echo "Creating GitHub labels for ${REPO}..."
echo ""

# Function to create or update a label
create_label() {
    local name=$1
    local color=$2
    local description=$3
    
    echo "Creating label: ${name}"
    gh label create "${name}" \
        --repo "${REPO}" \
        --color "${color}" \
        --description "${description}" \
        --force 2>/dev/null || echo "  Label '${name}' already exists"
}

# Dependencies labels
create_label "dependencies" "0366d6" "Pull requests that update a dependency file"
create_label "github-actions" "000000" "Pull requests that update GitHub Actions code"
create_label "docker" "0db7ed" "Pull requests that update Docker code"
create_label "python" "2b67c6" "Pull requests that update Python code"

# Additional useful labels
create_label "security" "ee0701" "Security vulnerability or fix"
create_label "breaking-change" "d93f0b" "Breaking change that requires major version bump"
create_label "enhancement" "a2eeef" "New feature or request"
create_label "bug" "d73a4a" "Something isn't working"
create_label "documentation" "0075ca" "Improvements or additions to documentation"
create_label "good-first-issue" "7057ff" "Good for newcomers"
create_label "help-wanted" "008672" "Extra attention is needed"

echo ""
echo "✓ All labels created successfully!"
echo ""
echo "To verify, run:"
echo "  gh label list --repo ${REPO}"

