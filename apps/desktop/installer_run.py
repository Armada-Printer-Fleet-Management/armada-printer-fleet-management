#!/usr/bin/env python3
"""Builds the desktop app's Windows installer: runs build_run.py, then wraps its PyInstaller
bundle in a setup program with NSIS. Windows only.
Output: installer/dist/<name>-Setup-<version>.exe. NSIS comes from scripts/install_nsis.py.

--skip-build reuses the existing bundle. --smoke-test then installs the result silently for the
current user, checks the app landed, and uninstalls it again."""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys

import build_run
from _build_common import fail, resolve, run, step

ROOT = pathlib.Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
INSTALLER = ROOT / "installer"
LICENSE = ROOT.parents[1] / "LICENSE"


def installer_info() -> dict[str, str]:
    code = (
        "import json; from armada_runtime.packaging import installer_info as i; "
        "print(json.dumps(i()))"
    )
    result = subprocess.run(
        [resolve("uv"), "run", "--project", str(BACKEND), "python", "-c", code],
        capture_output=True, text=True, check=True,
    )
    info: dict[str, str] = json.loads(result.stdout)
    return info


def makensis() -> str:
    found = shutil.which("makensis")
    if found:
        return found
    default = pathlib.Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
    if (default / "NSIS" / "makensis.exe").exists():
        return str(default / "NSIS" / "makensis.exe")
    fail("NSIS is not installed. Run 'python scripts/install_nsis.py'.")


def smoke_test(setup: pathlib.Path, app_name: str) -> None:
    install_dir = pathlib.Path(os.environ["LOCALAPPDATA"]) / "Programs" / app_name
    # The setup asks admin accounts for elevation; RunAsInvoker skips that, as for a non-admin.
    env = {**os.environ, "__COMPAT_LAYER": "RunAsInvoker"}
    print(f"$ {setup.name} /S /CurrentUser", flush=True)
    subprocess.run([str(setup), "/S", "/CurrentUser"], env=env, check=True)
    if not (install_dir / f"{app_name}.exe").exists():
        fail(f"the silent install did not put {app_name}.exe in {install_dir}")
    # _?= keeps the uninstaller in place instead of copying itself to %TEMP% and returning early.
    uninstall = [str(install_dir / "Uninstall.exe"), "/S", "/CurrentUser", f"_?={install_dir}"]
    print(f"$ {' '.join(uninstall)}", flush=True)
    subprocess.run(uninstall, env=env, check=True)
    (install_dir / "Uninstall.exe").unlink()
    install_dir.rmdir()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-build", action="store_true",
                        help="reuse the existing PyInstaller bundle")
    parser.add_argument("--smoke-test", action="store_true",
                        help="install silently for the current user, check, then uninstall")
    args = parser.parse_args()

    if sys.platform != "win32":
        fail("the desktop installer is Windows only")

    if not args.skip_build:
        build_run.main()

    info = installer_info()
    bundle = BACKEND / "dist" / info["app_name"]
    if not (bundle / f"{info['app_name']}.exe").exists():
        fail(f"{bundle} has no {info['app_name']}.exe. Run without --skip-build.")

    setup = INSTALLER / "dist" / f"{info['app_name']}-Setup-{info['version']}.exe"
    with step("Building installer"):
        setup.parent.mkdir(parents=True, exist_ok=True)
        defines = {
            "APP_NAME": info["app_name"],
            "DISPLAY_NAME": info["display_name"],
            "DESCRIPTION": info["description"],
            "URL": info["url"],
            "VERSION": info["version"],
            "NUMERIC_VERSION": info["numeric_version"],
            "SOURCE_DIR": str(bundle),
            "LICENSE_FILE": str(LICENSE),
            "OUT_FILE": str(setup),
        }
        run(
            [makensis(), "/V3", "/INPUTCHARSET", "UTF8",
             *(f"/D{key}={value}" for key, value in defines.items()),
             str(INSTALLER / "installer.nsi")],
            cwd=INSTALLER,
        )
        if not setup.exists():
            fail(f"makensis did not produce {setup}")

    if args.smoke_test:
        with step("Smoke-testing installer"):
            smoke_test(setup, info["app_name"])

    print(f"Built {setup}", flush=True)


if __name__ == "__main__":
    main()