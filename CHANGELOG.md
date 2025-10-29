# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-29

### Added

#### Core Functionality

- MCP server implementation with 31 Spotify control tools
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

#### Audio Analysis & Discovery

- Get audio features for tracks
- Comprehensive track analysis with insights
- Find similar tracks based on audio features
- Filter tracks by specific audio characteristics
- Get personalized recommendations
- Detailed audio analysis (sections, bars, beats, segments)

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

### Planned

- Sphinx documentation website
- Additional audio analysis features
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

