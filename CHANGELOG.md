# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- `list_devices` tool now includes device IDs in output, making it easier to use with `transfer_playback`

## [1.0.0] - 2025-10-29

### Added

#### Core Functionality

- MCP server implementation with 25 Spotify control tools
- Complete Spotify API integration via spotipy
- Docker support with authentication flow
- OAuth token caching for persistent sessions

#### Playback Control

- Basic playback controls (play, pause, next, previous)
- Play specific tracks or playlists by ID or name
- Currently playing track information
- Device management (list devices, transfer playback)
- Advanced controls (shuffle, repeat, seek, volume)

#### Library Management

- List user playlists
- List liked songs with pagination
- List songs in specific playlists
- Add songs to liked songs
- Add songs to playlists
- Get total count of liked songs

#### User Analytics

- Recently played tracks
- Top tracks by time period (short/medium/long term)
- Top artists by time period (short/medium/long term)

#### Queue Management

- Add tracks to playback queue
- View current playback queue

#### Developer Experience

- Comprehensive test suite (unit, integration, structure validation)
- Type hints throughout codebase
- Detailed documentation (README, TESTING.md)
- CI/CD with GitHub Actions
- Docker containerization
- Zero-install OAuth flow

### Infrastructure

- MIT License
- Proper Python package structure (`src/` layout)
- PyPI-ready with pyproject.toml
- Contributor guidelines (CONTRIBUTING.md)
- Code of Conduct (CODE_OF_CONDUCT.md)
- Issue and PR templates
- Makefile for development tasks
- Pre-commit hooks configuration
- Comprehensive testing framework

### Documentation

- Complete README with examples
- Detailed testing guide (TESTING.md)
- API documentation
- Docker setup instructions
- Zero-install authentication guide

## [Unreleased]

### Added

- **CI/CD Enhancements**
  - Automated coverage reports on every PR and push to main
  - Dependabot configuration for automated dependency updates
    - GitHub Actions monitoring (weekly)
    - Docker base image monitoring (weekly)
    - Python package monitoring with grouped updates (weekly)
  - GitHub labels automation script for standardized issue/PR labeling

### Removed

- Deprecated audio feature functions: `get_audio_features`, `analyze_track`, `get_audio_analysis`, `find_similar_tracks`, `filter_tracks_by_features`, and `get_track_recommendations` have been removed as they were not fully implemented

### Changed

- **CI Workflow**
  - CI now runs full test suite with coverage reporting
  - Test dependencies are installed during CI runs
  - Coverage reports are generated in XML and HTML formats

### Planned

- Sphinx documentation website
- Playlist management tools
- Enhanced error messages
- Performance optimizations
- Additional test coverage

---

## Version History

### Versioning Scheme

We use [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality in a backwards compatible manner
- **PATCH** version for backwards compatible bug fixes

### Release Notes Format

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes

---
[1.0.0]: https://github.com/yourusername/spotify-mcp/releases/tag/v1.0.0
