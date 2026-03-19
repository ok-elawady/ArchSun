from __future__ import annotations

import shutil
import textwrap
import zipfile
from pathlib import Path

from archsun import APP_NAME, DISPLAY_VERSION, __version__


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACKAGE_DIR = REPO_ROOT / "archsun"


def release_name() -> str:
    return f"{APP_NAME}-{__version__}"


def build_release(output_root: str | Path | None = None) -> Path:
    output_dir = Path(output_root) if output_root else REPO_ROOT / "dist"
    output_dir.mkdir(parents=True, exist_ok=True)

    bundle_dir = output_dir / release_name()
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)

    package_dir = bundle_dir / "package" / "archsun"
    package_dir.parent.mkdir(parents=True, exist_ok=True)

    shutil.copytree(
        SOURCE_PACKAGE_DIR,
        package_dir,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )

    _write_text(bundle_dir / "install_archsun.py", _installer_script("install"))
    _write_text(bundle_dir / "uninstall_archsun.py", _installer_script("uninstall"))
    _write_text(bundle_dir / "README_Install.txt", _install_readme())

    zip_path = output_dir / f"{release_name()}.zip"
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in bundle_dir.rglob("*"):
            archive.write(path, path.relative_to(output_dir))

    return bundle_dir


def _installer_script(mode: str) -> str:
    if mode not in {"install", "uninstall"}:
        raise ValueError("mode must be 'install' or 'uninstall'")

    if mode == "install":
        action = [
            "install_path, shelf_created = install_from_release(release_root)",
            "message = install_success_message(install_path, shelf_created)",
            'title = f"{APP_NAME} Installed"',
        ]
        support_imports = "install_from_release, install_success_message"
    else:
        action = [
            "package_removed, shelf_removed = uninstall_installed_package()",
            "message = uninstall_success_message(package_removed, shelf_removed)",
            'title = f"{APP_NAME} Removed"',
        ]
        support_imports = "uninstall_installed_package, uninstall_success_message"

    lines = [
        "from pathlib import Path",
        "import sys",
        "",
        "release_root = Path(__file__).resolve().parent",
        'package_root = release_root / "package"',
        "if str(package_root) not in sys.path:",
        "    sys.path.insert(0, str(package_root))",
        "",
        "for module_name in list(sys.modules):",
        '    if module_name == "archsun" or module_name.startswith("archsun."):',
        "        sys.modules.pop(module_name, None)",
        "",
        "try:",
        "    import maya.cmds as cmds",
        "except ImportError as exc:",
        '    raise RuntimeError("This script must be run inside Autodesk Maya.") from exc',
        "",
        "from archsun import APP_NAME",
        f"from archsun.maya.installer_support import {support_imports}",
        "",
        "def _main():",
    ]
    lines.extend(f"    {line}" for line in action)
    lines.extend(
        [
            '    cmds.confirmDialog(title=title, message=message, button=["OK"])',
            "",
            "",
            "_main()",
        ]
    )
    return "\n".join(lines) + "\n"


def _install_readme() -> str:
    return textwrap.dedent(
        f"""
        {APP_NAME} {DISPLAY_VERSION}
        ============================

        Quick Install
        -------------
        1. Extract this zip anywhere on your machine.
        2. Drag `install_archsun.py` into Maya, or run it from the Script Editor.
        3. {APP_NAME} will be copied into your Maya user scripts folder.
        4. A shelf button will be added to the current shelf when Maya can do so.

        Quick Uninstall
        ---------------
        - Drag `uninstall_archsun.py` into Maya to remove the installed files.

        Notes
        -----
        - Arnold (`mtoa`) is required when you update the setup.
        - Keep this extracted folder if you want the drag-and-drop uninstall script later.
        - GitHub Releases and Gumroad should ship the same build so version numbers stay aligned.
        """
    ).strip() + "\n"


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    bundle_dir = build_release()
    print(f"Built release bundle: {bundle_dir}")
