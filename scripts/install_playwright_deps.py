#!/usr/bin/env python3
"""Install Playwright system dependencies in an OS-agnostic way.

Playwright's ``install-deps`` only supports Debian/Ubuntu (apt-get). This
helper detects the package manager and either delegates to Playwright or
installs the equivalent RPM packages on Fedora/RHEL.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys

# Packages needed for Chromium and Firefox on Fedora/RHEL.
# Mapped from Playwright's Debian dependency list; see:
# https://github.com/microsoft/playwright/issues/27890
FEDORA_PACKAGES = [
    "nspr",
    "nss",
    "dbus-libs",
    "atk",
    "at-spi2-atk",
    "cups-libs",
    "at-spi2-core",
    "libX11",
    "libXcomposite",
    "libXdamage",
    "libXext",
    "libXfixes",
    "libXrandr",
    "mesa-libgbm",
    "libxcb",
    "libxkbcommon",
    "pango",
    "cairo",
    "alsa-lib",
    "libdrm",
    "gtk3",
]


def _run(cmd: list[str]) -> None:
    print(f"+ {' '.join(cmd)}", flush=True)
    subprocess.run(
        cmd, check=True
    )  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit


def _install_debian() -> None:
    print("Detected apt-get; delegating to playwright install-deps.")
    _run(["playwright", "install-deps"])


def _install_fedora() -> None:
    dnf = shutil.which("dnf") or shutil.which("yum")
    if dnf is None:
        raise RuntimeError("Neither dnf nor yum found on PATH")

    print(f"Detected RPM-based system ({dnf}); installing Playwright library dependencies.")
    cmd = [dnf, "install", "-y", *FEDORA_PACKAGES]
    if os.geteuid() != 0:
        if shutil.which("sudo") is None:
            raise RuntimeError(
                "Root privileges are required to install system packages, "
                "but sudo was not found. Re-run as root or install sudo."
            )
        cmd = ["sudo", *cmd]
    _run(cmd)


def _skip_macos() -> None:
    print("macOS detected; Playwright browsers bundle their own dependencies. Nothing to do.")


def _unsupported(system: str) -> None:
    packages = " ".join(FEDORA_PACKAGES)
    print(
        f"Unsupported platform for automatic Playwright system deps: {system!r}.\n"
        "Install browser system libraries manually, then re-run tests.\n\n"
        "Debian/Ubuntu:\n"
        "  playwright install-deps\n\n"
        "Fedora/RHEL:\n"
        f"  sudo dnf install -y {packages}\n",
        file=sys.stderr,
    )
    sys.exit(1)


def main() -> None:
    system = platform.system()

    if system == "Darwin":
        _skip_macos()
        return

    if system == "Windows":
        print("Windows detected; Playwright manages browser dependencies. Nothing to do.")
        return

    if system != "Linux":
        _unsupported(system)

    if shutil.which("apt-get"):
        _install_debian()
        return

    if shutil.which("dnf") or shutil.which("yum"):
        _install_fedora()
        return

    _unsupported(system)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"Command failed with exit code {exc.returncode}: {exc.cmd}", file=sys.stderr)
        sys.exit(exc.returncode)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
