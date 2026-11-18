# GitHub Configuration for spotify-mcp

This directory contains GitHub-specific configuration files for CI/CD, Dependabot, and issue/PR templates.

## Overview

### Workflows

- **`ci.yml`** - Continuous Integration workflow
  - Runs on every push to main and on all pull requests
  - Executes tests with coverage reporting
  - Uploads coverage to Codecov
  - Builds Docker image to verify build process
  - Uses Python 3.11 for testing

- **`cd.yml`** - Continuous Deployment workflow
  - Publishes Docker images to GitHub Container Registry (GHCR) and Docker Hub
  - Triggers on:
    - Pushes to main
    - Version tags (v*)
    - Published releases
    - Manual workflow dispatch
  - Builds multi-platform images (amd64, arm64)

### Dependabot

**Configuration**: `.github/dependabot.yml`

Automatically monitors and updates:
- **GitHub Actions** - Weekly updates on Mondays
- **Docker** - Weekly base image updates on Mondays  
- **Python packages** - Weekly updates on Mondays with grouped PRs:
  - Development dependencies (pytest, black, mypy, pylint, ruff)
  - Production dependencies (spotipy, mcp, python-dotenv)

Labels applied to Dependabot PRs:
- `dependencies` - All dependency updates
- `github-actions` - GitHub Actions updates
- `docker` - Docker image updates
- `python` - Python package updates

### Labels

**Script**: `.github/scripts/create-labels.sh`

Creates standardized labels for the repository. Run once during initial setup:

```bash
# Requires GitHub CLI (gh) installed and authenticated
./.github/scripts/create-labels.sh
```

**Labels created**:
- `dependencies` - Dependency updates
- `github-actions` - GitHub Actions code
- `docker` - Docker-related changes
- `python` - Python code changes
- `security` - Security fixes
- `breaking-change` - Breaking changes
- `enhancement` - New features
- `bug` - Bug reports
- `documentation` - Documentation updates
- `good-first-issue` - Newcomer-friendly issues
- `help-wanted` - Issues needing attention

## Initial Setup

### 1. Create GitHub Labels

```bash
# Install GitHub CLI if not already installed
brew install gh  # macOS
# or
apt install gh   # Ubuntu/Debian

# Authenticate
gh auth login

# Create labels
./.github/scripts/create-labels.sh
```

### 2. Set Up Codecov

1. Go to https://codecov.io/
2. Sign in with GitHub
3. Add the `spotify-mcp` repository
4. Copy the Codecov token
5. Add it to GitHub repository secrets:
   - Go to: Repository → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `CODECOV_TOKEN`
   - Value: (paste the token from Codecov)

### 3. Enable Dependabot (Optional Configuration)

Dependabot is enabled by default when the `.github/dependabot.yml` file exists. To customize:

1. Go to: Repository → Settings → Code security and analysis
2. Enable "Dependabot alerts" (if not already enabled)
3. Enable "Dependabot security updates" (optional)
4. Enable "Dependabot version updates" (automatically enabled by dependabot.yml)

### 4. Set Up Docker Hub Secrets (For CD)

For Docker Hub publishing, add these secrets:
- `DOCKERHUB_USERNAME` - Your Docker Hub username
- `DOCKERHUB_TOKEN` - Docker Hub access token

## Testing Coverage

### Local Coverage Reports

Generate coverage reports locally:

```bash
# HTML report (opens in browser)
make test-cov

# Terminal report only
pytest --cov=spotify_mcp --cov-report=term-missing

# XML report (for Codecov)
pytest --cov=spotify_mcp --cov-report=xml
```

### CI Coverage Reports

Coverage reports are automatically:
1. Generated during CI runs
2. Uploaded to Codecov
3. Commented on pull requests with coverage changes
4. Available at https://codecov.io/gh/Allensy/spotify-mcp

### Coverage Configuration

Coverage settings are defined in `pyproject.toml`:
- Minimum coverage: No hard requirement (set `fail_ci_if_error: false`)
- Excluded patterns: Tests, `__pycache__`, site-packages
- Excluded lines: Type checking blocks, abstract methods, `if __name__`, etc.

## Monitoring Updates

### Dependabot PRs

Dependabot will create PRs automatically:
- **Review schedule**: Every Monday at 9:00 AM Pacific
- **Max open PRs**: 
  - 5 for GitHub Actions
  - 3 for Docker
  - 10 for Python packages
- **Grouping**: Minor and patch updates are grouped together

### Managing Dependabot PRs

Common commands (comment on PR):
```
@dependabot rebase       # Rebase PR with latest main
@dependabot recreate     # Recreate PR from scratch
@dependabot merge        # Auto-merge after CI passes
@dependabot close        # Close PR and ignore this update
```

### Codecov Status Checks

Each PR will show a Codecov status check with:
- Overall coverage percentage
- Coverage change (+/- from base)
- Files with coverage changes
- Link to detailed report

## Troubleshooting

### Codecov Upload Fails

If Codecov upload fails:
1. Check that `CODECOV_TOKEN` secret is set correctly
2. Verify coverage.xml is generated: `ls -la coverage.xml`
3. Check Codecov dashboard for error messages
4. Note: CI won't fail if Codecov upload fails (`fail_ci_if_error: false`)

### Dependabot Label Errors

If Dependabot complains about missing labels:
1. Run `./.github/scripts/create-labels.sh`
2. Or manually create labels in GitHub UI
3. Or remove the `labels:` section from `dependabot.yml`

### Docker Build Failures

If Docker builds fail in CI:
1. Test locally: `docker build -t spotify-mcp:test .`
2. Check Dockerfile syntax
3. Verify all required files are present (not in .dockerignore)

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
- [Codecov Documentation](https://docs.codecov.com/)
- [GitHub CLI Documentation](https://cli.github.com/manual/)

