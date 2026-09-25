# PyInstaller spec for the desktop app.
#
# When something works from source but not in the packaged app, the fix usually lands here:
#   - a file the app reads at runtime          -> add it to `datas`, and read it through
#                                                  backend.environment.Environment.resource_path()
#   - a package that is imported dynamically   -> add it to `hiddenimports`
#   - a package that reads its own version      -> copy_metadata("<dist name>") into `datas`
#     or entry points via importlib.metadata
# PyInstaller reports what it could not find in build/desktop_backend/warn-desktop_backend.txt.
#
# The frontend build must exist first; it is bundled to <bundle>/frontend/dist, which is where
# Environment.default_frontend_target() looks. Set console=True to see startup errors in a terminal.
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, copy_metadata

from backend.packaging import executable_name

BACKEND = Path(SPECPATH)  # noqa: F821 -- SPECPATH is injected by PyInstaller
FRONTEND_DIST = BACKEND.parent / "frontend" / "dist"
APP_NAME = executable_name()  # the executable and its folder are named after the organization title

datas = [(str(FRONTEND_DIST), "frontend/dist")]
datas += copy_metadata("backend")  # ApplicationInfo.version() reads it
datas += collect_data_files("organization_info")  # organization.json, read through importlib.resources
hiddenimports: list[str] = []

analysis = Analysis(  # noqa: F821
    [str(BACKEND / "src" / "backend" / "__main__.py")],
    pathex=[str(BACKEND / "src")],
    datas=datas,
    hiddenimports=hiddenimports,
)
pyz = PYZ(analysis.pure)  # noqa: F821
exe = EXE(  # noqa: F821
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    console=False,
)
COLLECT(exe, analysis.binaries, analysis.datas, name=APP_NAME)  # noqa: F821