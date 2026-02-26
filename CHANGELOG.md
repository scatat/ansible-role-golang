# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-02-26

### Added

- **4 package managers:** `homebrew` (macOS), `tarball` (cross-platform), `apt` (Debian/Ubuntu), `dnf` (RHEL/Rocky/Fedora)
- **State management:** `golang_state` supports `present`, `latest`, and `absent`
- **Tarball install:** checksum-verified download from Google CDN, idempotent (skips if version matches)
- **Shell interface contract:** `golang_shell_env` dict for shell role consumption
- **Cache path interface:** `golang_cache_dir` for disk-cleanup integration
- **Optional shell profile:** `golang_configure_profile` writes `/etc/profile.d/golang.sh`
- **Ansible local facts:** `golang_export_facts` exports version, paths, and package manager
- **Go packages:** `golang_packages` installs tools via `go install`
- **Extra env vars:** `golang_extra_env` for GOPROXY, GOPRIVATE, etc.
- **Assertions:** V1-V7 verify install, U1-U2 verify uninstall
- **Python cross-validation:** V8-V11 in `tests/test_golang.py`
- **Molecule CI:** `default` (Homebrew/macOS), `tarball` (Ubuntu), `uninstall` (Ubuntu)
- **argument_specs.yml:** 17 validated inputs with type checking
- **Uninstall support:** clean removal with optional cache cleanup
