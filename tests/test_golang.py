#!/usr/bin/env python3
"""
Assertion test suite for golang role.
Usage: python3 tests/test_golang.py [--home /Users/someone] [--package-manager homebrew]

Maps to leaky abstractions documented in README.md (V8-V11).
"""
import os
import platform
import struct
import subprocess
import sys


def get_args():
    """Parse arguments with defaults."""
    home = os.path.expanduser("~")
    pkg_mgr = "homebrew"
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--home" and i < len(sys.argv) - 1:
            home = sys.argv[i + 1]
        if arg == "--package-manager" and i < len(sys.argv) - 1:
            pkg_mgr = sys.argv[i + 1]
    return home, pkg_mgr


def run_assertions(home_dir, package_manager):
    """Run V8-V11 cross-validation assertions."""
    results = []
    homebrew_prefix = "/opt/homebrew" if platform.machine() == "arm64" else "/usr/local"

    # V8: GOROOT path matches package manager choice
    # Catches L2: GOROOT location mismatch
    try:
        goroot = subprocess.check_output(
            ["go", "env", "GOROOT"], text=True
        ).strip()
        if package_manager == "homebrew":
            expected_prefix = os.path.join(homebrew_prefix, "opt", "go", "libexec")
            passed = goroot == expected_prefix
            detail = f"GOROOT={goroot}, expected={expected_prefix}"
        elif package_manager == "tarball":
            expected = "/usr/local/go"
            passed = goroot == expected
            detail = f"GOROOT={goroot}, expected={expected}"
        else:
            passed = False
            detail = f"Unknown package_manager: {package_manager}"
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        passed = False
        detail = f"go env GOROOT failed: {e}"
    results.append(("V8", "GOROOT matches package manager", passed, detail))

    # V9: Fish config contains golang env exports
    # Catches L4: shell env export
    fish_config = os.path.join(home_dir, ".config", "fish", "config.fish")
    if os.path.isfile(fish_config):
        with open(fish_config) as f:
            content = f.read()
        has_gopath = "GOPATH" in content
        has_gobin = "GOBIN" in content
        has_goroot = "GOROOT" in content
        passed = has_gopath and has_gobin and has_goroot
        missing = []
        if not has_gopath:
            missing.append("GOPATH")
        if not has_gobin:
            missing.append("GOBIN")
        if not has_goroot:
            missing.append("GOROOT")
        detail = f"fish config: {'all present' if passed else 'missing: ' + ', '.join(missing)}"
    else:
        passed = False
        detail = f"Fish config not found: {fish_config}"
    results.append(("V9", "Fish config has golang exports", passed, detail))

    # V10: disk-cleanup cache path matches golang_cache_dir
    # Catches L9: cache path coupling
    disk_cleanup_defaults = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "disk-cleanup", "defaults", "main.yml",
    )
    golang_cache_dir = os.path.join(home_dir, "Library", "Caches", "go-build")
    if os.path.isfile(disk_cleanup_defaults):
        with open(disk_cleanup_defaults) as f:
            content = f.read()
        # Check if disk-cleanup references the golang variable instead of hardcoding
        uses_variable = "golang_cache_dir" in content
        has_hardcoded = "go-build" in content and "golang_cache_dir" not in content
        passed = uses_variable and not has_hardcoded
        detail = (
            f"uses golang_cache_dir variable: {uses_variable}, "
            f"hardcoded go-build: {has_hardcoded}"
        )
    else:
        passed = False
        detail = f"disk-cleanup defaults not found: {disk_cleanup_defaults}"
    results.append(("V10", "disk-cleanup uses golang_cache_dir", passed, detail))

    # V11: Binary file arch matches host
    # Catches L7: tarball arch mismatch
    try:
        go_bin = subprocess.check_output(
            ["which", "go"], text=True
        ).strip()
        # Resolve symlinks to get actual binary
        go_bin = os.path.realpath(go_bin)
        host_arch = platform.machine()  # arm64 or x86_64
        if sys.platform == "darwin":
            # Check Mach-O binary arch via file command
            file_output = subprocess.check_output(
                ["file", go_bin], text=True
            ).strip()
            if host_arch == "arm64":
                passed = "arm64" in file_output
            else:
                passed = "x86_64" in file_output
            detail = f"host={host_arch}, binary: {file_output[:100]}"
        elif sys.platform.startswith("linux"):
            # Check ELF binary arch
            with open(go_bin, "rb") as f:
                f.seek(18)  # e_machine offset in ELF header
                e_machine = struct.unpack("<H", f.read(2))[0]
            expected = 0xB7 if host_arch in ("arm64", "aarch64") else 0x3E
            passed = e_machine == expected
            detail = f"host={host_arch}, ELF e_machine=0x{e_machine:X} (expected 0x{expected:X})"
        else:
            passed = False
            detail = f"Unsupported platform: {sys.platform}"
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        passed = False
        detail = f"Binary arch check failed: {e}"
    results.append(("V11", "Binary arch matches host", passed, detail))

    return results


if __name__ == "__main__":
    home, pkg_mgr = get_args()
    results = run_assertions(home, pkg_mgr)
    passed_count = sum(1 for _, _, p, _ in results if p)
    failed_count = sum(1 for _, _, p, _ in results if not p)
    for vid, desc, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        print(f"{vid}: {desc} — {status}  {detail}")
    print(f"\n{passed_count} passed, {failed_count} failed out of {len(results)} assertions")
    sys.exit(0 if failed_count == 0 else 1)
