# Golang Role

Install and configure the Go language SDK with package manager abstraction,
shell-agnostic environment export, uninstall support, and assertion-driven
verification.

**License:** GPL-3.0-only
**Galaxy:** `scatat.golang`
**Minimum Ansible:** 2.15

## Prerequisites

- **Python 3.9+** and **pip**
- **Ansible 2.15+:** `pip install ansible-core`
- **community.general collection:** `ansible-galaxy collection install community.general`
- **Homebrew** (macOS only, if using `golang_package_manager: homebrew`)

## Quick Start

### Install the Role

```bash
ansible-galaxy install scatat.golang
```

Or add to `requirements.yml`:

```yaml
roles:
  - src: scatat.golang
```

### Standalone Playbook

If you don't have a separate shell configuration role, enable
`golang_configure_profile` so that `go` is available in new shells immediately:

```yaml
# playbook.yml
- hosts: localhost
  roles:
    - role: scatat.golang
      golang_configure_profile: true
      tags: [golang]
```

### With a Shell Role

If a shell role (e.g., fish-setup) consumes `golang_shell_env`, omit
`golang_configure_profile`:

```yaml
- hosts: localhost
  roles:
    - role: scatat.golang
      tags: [golang]
    - role: fish-setup
      tags: [fish]
```

### Common Commands

```bash
# Install (default: Homebrew on macOS)
ansible-playbook playbook.yml --tags golang

# Verify only
ansible-playbook playbook.yml --tags verify

# Upgrade to latest available
ansible-playbook playbook.yml --tags golang -e golang_state=latest

# Uninstall
ansible-playbook playbook.yml --tags golang -e golang_state=absent
```

### Available Tags

| Tag | Scope |
|-----|-------|
| `golang` | Full role (install/upgrade/uninstall + all sub-tasks) |
| `verify` | Assertions only (V1-V7) |
| `profile` | Shell profile configuration only |
| `facts` | Ansible local facts export only |
| `packages` | Go package installation only |

### Privilege Escalation (`become`)

Some tasks require `become: true` depending on the package manager:

| Package Manager | `become` Required | Why |
|-----------------|-------------------|-----|
| `homebrew` | No | Homebrew runs as the current user |
| `tarball` | **Yes** | Installs to `/usr/local/go` (root-owned) |
| `apt` | **Yes** | System package manager requires root |
| `dnf` | **Yes** | System package manager requires root |

Additionally, `golang_configure_profile: true` writes to `/etc/profile.d/` (requires
`become`), and `golang_export_facts: true` writes to `/etc/ansible/facts.d/` (requires
`become`). The role applies `become` per-task where needed — you do **not** need to set
`become: true` at the play level unless using tarball, apt, or dnf.

## Design Principles

This role follows an assertion-driven design:

- **Package manager abstraction:** `golang_package_manager` selects the install
  method. Add `tasks/install-<manager>.yml` to support new ones.
- **Shell-agnostic interface:** `golang_shell_env` is a dict of env vars and
  PATH entries. Shell roles consume this — the golang role never writes shell
  config directly.
- **Cache path interface:** `golang_cache_dir` exported for disk-cleanup
  integration. No hardcoded paths in consumers.
- **Testable assertions:** `verify.yml` runs on every converge. Catches stale
  installs, missing directories, arch mismatches, and broken GOROOT.
- **Uninstall support:** `golang_state: absent` cleanly removes Go and
  optionally clears the build cache.

## Version Management

This role offers **two paths** for managing Go versions. Choose based on your
needs:

### Path 1: System Package Managers (constrained)

Use `homebrew`, `apt`, or `dnf`. The package manager controls which version
you get — you cannot pin to a specific Go release.

| Manager | Platform | Version You Get | Upgrade Behaviour |
|---------|----------|----------------|-------------------|
| `homebrew` | macOS | Latest stable (currently 1.26.x) | `state: latest` runs `brew upgrade` |
| `apt` | Debian/Ubuntu | Distro-packaged (often 1-2 releases behind) | `state: latest` runs `apt upgrade` |
| `dnf` | RHEL/Rocky/Fedora | Distro-packaged (often 1-2 releases behind) | `state: latest` runs `dnf upgrade` |

**Want a newer version than your distro ships?** You can add third-party
repositories (PPAs, COPR, etc.), but that is your own dependency to manage.
Alternatively, use the tarball path below.

### Path 2: Tarball (recommended for version control)

Use `golang_package_manager: tarball`. You set the exact version via
`golang_version` and the role downloads, checksums, and extracts the official
Go tarball. This is the [Go team's recommended install method](https://go.dev/doc/install)
for Linux and works on any OS/arch combination.

```yaml
# Pin to exact version
golang_package_manager: tarball
golang_version: "1.26.0"
```

To upgrade, bump `golang_version` and re-run the role. The new tarball has a
different filename so it downloads fresh and replaces the old installation.

### Which Path Should I Choose?

| I want... | Use |
|-----------|-----|
| Always latest, zero maintenance | `homebrew` (macOS) |
| Distro-standard, enterprise consistency | `apt` or `dnf` |
| Exact version pinning | `tarball` |
| Reproducible CI builds | `tarball` |
| Multiple Go versions side-by-side | Out of scope — use [asdf](https://asdf-vm.com/) or [goenv](https://github.com/go-nv/goenv) |

### GOROOT by Package Manager

Each method installs to a different location. The role derives `golang_goroot`
automatically:

| Manager | GOROOT | Binary |
|---------|--------|--------|
| `homebrew` | `/opt/homebrew/opt/go/libexec` | `/opt/homebrew/bin/go` |
| `tarball` | `/usr/local/go` (configurable) | `/usr/local/go/bin/go` |
| `apt` | `/usr/lib/go` | `/usr/bin/go` |
| `dnf` | `/usr/lib/golang` | `/usr/bin/go` |

> **Note:** Only one package manager should be active per machine. They install
> to different paths so they won't conflict on disk, but only one
> `golang_shell_env` is exported to your shell.

## Variables

### Core

| Variable | Default | Description |
|----------|---------|-------------|
| `golang_enabled` | `true` | Enable/disable the role |
| `golang_state` | `present` | `present` (install if missing), `latest` (install or upgrade), `absent` (uninstall) |
| `golang_package_manager` | `homebrew` | Install method: `homebrew`, `tarball`, `apt`, `dnf` |
| `golang_version` | `1.26.0` | Go version (tarball only — other managers track their own) |
| `golang_minimum_version` | `1.22` | Minimum version for verify assertions |

### Paths

| Variable | Default | Description |
|----------|---------|-------------|
| `golang_goroot` | (derived) | SDK root. Auto-derived from package manager. |
| `golang_gopath` | `~/go` | User workspace |
| `golang_gobin` | `~/go/bin` | Binary install location |
| `golang_cache_dir` | (OS-dependent) | Build cache: `~/Library/Caches/go-build` (macOS), `~/.cache/go-build` (Linux) |

### Tarball-Specific

| Variable | Default | Description |
|----------|---------|-------------|
| `golang_tarball_mirror` | `https://go.dev/dl` | Download mirror |
| `golang_tarball_install_dir` | `/usr/local/go` | Extract location |
| `golang_tarball_download_dir` | `~/.ansible/tmp/downloads` | Download cache |

### Features (opt-in)

| Variable | Default | Description |
|----------|---------|-------------|
| `golang_packages` | `[]` | Go packages to install via `go install` (include `@version`) |
| `golang_configure_profile` | `false` | Write env to `/etc/profile.d/golang.sh` (self-contained mode) |
| `golang_profile_path` | `/etc/profile.d/golang.sh` | Custom profile path when `golang_configure_profile` is true |
| `golang_export_facts` | `false` | Export `ansible_local.golang.general.*` facts for cross-role discovery |

### Extensible

| Variable | Default | Description |
|----------|---------|-------------|
| `golang_extra_env` | `{}` | Additional env vars (GOPROXY, GOPRIVATE, etc.) |
| `golang_clean_cache_on_uninstall` | `true` | Clean build cache on uninstall |

## Shell Interface Contract

The `golang_shell_env` variable is the loose interface between this role and
any shell configuration role. The golang role defines it; shell roles consume it.

```yaml
golang_shell_env:
  vars:           # Environment variables to export
    GOPATH: ~/go
    GOBIN: ~/go/bin
    GOROOT: /opt/homebrew/opt/go/libexec  # or /usr/local/go for tarball
  paths:          # Directories to add to PATH
    - <GOROOT>/bin
    - <GOBIN>
```

### Shell Role Integration

**Fish** (fish-setup role):
```jinja2
{% for var_name, var_value in golang_shell_env.vars.items() %}
set -x {{ var_name }} {{ var_value }}
{% endfor %}
{% for path_item in golang_shell_env.paths %}
fish_add_path {{ path_item }}
{% endfor %}
```

**Zsh/Bash** (hypothetical):
```jinja2
{% for var_name, var_value in golang_shell_env.vars.items() %}
export {{ var_name }}="{{ var_value }}"
{% endfor %}
export PATH="{{ golang_shell_env.paths | join(':') }}:$PATH"
```

## Leaky Abstractions

| ID | Abstraction | What Leaks | Silent Failure Mode |
|----|-------------|-----------|---------------------|
| L1 | Go binary in PATH | Homebrew PATH not in shell env | `go version` fails |
| L2 | GOROOT location | Differs homebrew vs tarball | stdlib not found |
| L3 | GOPATH/GOBIN dirs | Never created by role | `go install` writes wrong location |
| L4 | Shell env export | Install done, shell not configured | `go env` correct, shell broken |
| L5 | Package manager | Homebrew missing on Linux | Cryptic brew error |
| L6 | Version currency | Old Go meets min, misses patches | False currency |
| L7 | Tarball arch | Wrong arch downloaded | Binary segfaults |
| L8 | Uninstall completeness | Binary gone, shell env stale | Shell refs dead path |
| L9 | Cache path coupling | disk-cleanup hardcodes go-build | Cache location mismatch |
| L10 | Version opacity | homebrew/apt/dnf ignore `golang_version` | User sets version, gets something else |

## Assertions

### verify.yml (V1-V7 — runs on every converge)

| V# | Catches | Assertion |
|----|---------|-----------|
| V1 | L1 | go binary is executable |
| V2 | L6 | go version ≥ `golang_minimum_version` |
| V3 | L2 | GOROOT contains `bin/go` |
| V4 | L3 | GOPATH directory exists and is dir |
| V5 | L3 | GOBIN directory exists and is dir |
| V6 | L7 | `go env GOARCH` matches host architecture |
| V7 | L5 | go binary at expected GOROOT path |

### verify-absent.yml (U1-U2 — after uninstall)

| U# | Catches | Assertion |
|----|---------|-----------|
| U1 | L8 | go binary NOT found at GOROOT |
| U2 | L8 | Package absent |

### Python tests (V8-V11 — cross-validation)

| V# | Catches | Assertion |
|----|---------|-----------|
| V8 | L2 | GOROOT path matches package manager choice |
| V9 | L4 | Fish config contains golang env exports |
| V10 | L9 | disk-cleanup cache path = `golang_cache_dir` |
| V11 | L7 | Binary file arch matches host |

### Known Gaps (not bugs)

| Gap | Why Not Asserted | Mitigation |
|-----|-----------------|------------|
| Go tools version (gopls) | Editor concern, not SDK | `golang_packages` installs them |
| GOPROXY correctness | Org-specific | Extensible via `golang_extra_env` |
| Shell env loaded in session | Requires interactive shell | V9 checks config file statically |

## Scope Exclusions

These are **not supported** by design:

- **Multiple Go versions side-by-side** — Use [asdf](https://asdf-vm.com/) or
  [goenv](https://github.com/go-nv/goenv) for version switching.
- **Third-party repository management** (PPAs, COPR) — If your distro's Go is
  too old, use `tarball` instead. Adding repos is your responsibility.
- **GOPROXY/GOPRIVATE** — Extensible via `golang_extra_env` when needed.
- **Build Go from source** — Too niche for a general-purpose role.

## Supported Platforms

| Platform | Package Manager | Tested |
|----------|----------------|--------|
| macOS (Apple Silicon) | Homebrew | ✅ (primary) |
| macOS (Intel) | Homebrew | Should work (untested) |
| Ubuntu 22.04 | Tarball, apt | Molecule CI |
| Ubuntu 24.04 | Tarball, apt | Molecule CI |
| Debian 12 | Tarball, apt | Should work (untested) |
| Rocky/Alma 9 | Tarball, dnf | Molecule CI |
| Fedora (latest) | Tarball, dnf | Should work (untested) |

## Contributing

Contributions welcome! To keep the project maintainable:

### Requirements for PRs

1. **Molecule must pass.** CI runs the full test matrix on every PR. If it's
   red, the PR cannot merge.
2. **New assertions need L-table mapping.** If you add a V-check, document
   which L (leaky abstraction) it catches. If it doesn't map to a leak,
   it's testing the wrong thing.
3. **New install methods need tasks + assertions.** Adding a package manager?
   Create `tasks/install-<manager>.yml`, `tasks/uninstall-<manager>.yml`, and
   add Molecule scenario coverage.
4. **Follow conventional commits.** `feat:`, `fix:`, `docs:`, `test:`, `ci:`.
   Releases are automated from commit messages.

### Development Setup

```bash
# Clone
git clone https://github.com/scatat/ansible-role-golang.git
cd ansible-role-golang

# Install test dependencies
pip install molecule molecule-plugins ansible-core ansible-lint yamllint

# Run default scenario (macOS Homebrew)
molecule test

# Run specific scenario
molecule test --scenario-name tarball
molecule test --scenario-name uninstall

# Lint
yamllint .
ansible-lint
```

### Adding a New Package Manager

1. Create `tasks/install-<manager>.yml` and `tasks/uninstall-<manager>.yml`
2. Update `defaults/main.yml` with any manager-specific variables
3. Add a Molecule scenario in `molecule/<manager>/`
4. Update this README's Supported Platforms table
5. Update the CI matrix in `.github/workflows/ci.yml`

## License

This project is licensed under the **GNU General Public License v3.0** — see
[LICENSE](LICENSE) for details.

All forks and derivative works must also be distributed under GPL-3.0.
