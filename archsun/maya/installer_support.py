from __future__ import annotations

import shutil
import sys
from pathlib import Path

from archsun import APP_NAME, DISPLAY_VERSION
from archsun.maya import runtime


SHELF_BUTTON_DOC_TAG = "archsun_launch"
LAUNCH_COMMAND = "from archsun.launcher import show_archsun\nshow_archsun()"
SHELF_ICON_RELATIVE_PATH = Path("ui") / "assets" / "icons" / "archsun_shelf.png"


def release_package_dir(release_root: str | Path) -> Path:
    return Path(release_root).resolve() / "package" / "archsun"


def user_maya_dir() -> Path:
    cmds = runtime.get_cmds()
    return Path(cmds.internalVar(userAppDir=True))


def installed_package_dir() -> Path:
    return user_maya_dir() / "scripts" / "archsun"


def installed_shelf_icon_path() -> Path:
    return installed_package_dir() / SHELF_ICON_RELATIVE_PATH


def install_from_release(release_root: str | Path) -> tuple[Path, bool]:
    source_dir = release_package_dir(release_root)
    if not source_dir.exists():
        raise FileNotFoundError(
            "Could not find the packaged ArchSun files next to the installer."
        )

    destination_dir = installed_package_dir()
    destination_dir.parent.mkdir(parents=True, exist_ok=True)

    if destination_dir.exists():
        shutil.rmtree(destination_dir)

    shutil.copytree(
        source_dir,
        destination_dir,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )

    _clear_loaded_archsun_modules()
    shelf_created = create_shelf_button()
    return destination_dir, shelf_created


def uninstall_installed_package() -> tuple[bool, bool]:
    destination_dir = installed_package_dir()
    package_removed = False

    if destination_dir.exists():
        shutil.rmtree(destination_dir)
        package_removed = True

    shelf_removed = remove_shelf_buttons()
    _clear_loaded_archsun_modules()
    return package_removed, shelf_removed


def create_shelf_button() -> bool:
    cmds = runtime.get_cmds()
    shelf_top_level = _shelf_top_level()
    if not shelf_top_level or not cmds.shelfTabLayout(shelf_top_level, exists=True):
        return False

    current_shelf = cmds.shelfTabLayout(
        shelf_top_level,
        query=True,
        selectTab=True,
    )
    if not current_shelf or not cmds.shelfLayout(current_shelf, exists=True):
        return False

    _remove_buttons_from_shelf(current_shelf)

    icon_path = installed_shelf_icon_path()
    icon_name = str(icon_path) if icon_path.exists() else "commandButton.png"

    cmds.shelfButton(
        parent=current_shelf,
        label=APP_NAME,
        annotation=f"Launch {APP_NAME} {DISPLAY_VERSION}",
        command=LAUNCH_COMMAND,
        sourceType="Python",
        image1=icon_name,
        docTag=SHELF_BUTTON_DOC_TAG,
    )
    return True


def remove_shelf_buttons() -> bool:
    cmds = runtime.get_cmds()
    shelf_top_level = _shelf_top_level()
    if not shelf_top_level or not cmds.shelfTabLayout(shelf_top_level, exists=True):
        return False

    removed_any = False
    for shelf_name in cmds.shelfTabLayout(
        shelf_top_level,
        query=True,
        childArray=True,
    ) or []:
        removed_any = _remove_buttons_from_shelf(shelf_name) or removed_any

    return removed_any


def install_success_message(install_path: Path, shelf_created: bool) -> str:
    lines = [
        f"{APP_NAME} {DISPLAY_VERSION} installed successfully.",
        "",
        f"Files copied to: {install_path}",
    ]

    if shelf_created:
        lines.append("")
        lines.append("A shelf button was added to the current shelf.")
    else:
        lines.append("")
        lines.append(
            "No shelf button was added automatically. You can launch ArchSun with:"
        )
        lines.append(LAUNCH_COMMAND)

    return "\n".join(lines)


def uninstall_success_message(package_removed: bool, shelf_removed: bool) -> str:
    if not package_removed and not shelf_removed:
        return f"{APP_NAME} was not found in your Maya user scripts."

    lines = [f"{APP_NAME} was removed from your Maya user scripts."]
    if shelf_removed:
        lines.append("")
        lines.append("Matching shelf buttons were removed too.")
    else:
        lines.append("")
        lines.append("If you added a shelf button manually, remove it from Maya by hand.")

    return "\n".join(lines)


def _clear_loaded_archsun_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "archsun" or module_name.startswith("archsun."):
            sys.modules.pop(module_name, None)


def _remove_buttons_from_shelf(shelf_name: str) -> bool:
    cmds = runtime.get_cmds()
    if not cmds.shelfLayout(shelf_name, exists=True):
        return False

    removed_any = False
    for child in cmds.shelfLayout(shelf_name, query=True, childArray=True) or []:
        try:
            if cmds.objectTypeUI(child) != "shelfButton":
                continue
        except RuntimeError:
            continue

        if cmds.shelfButton(child, query=True, docTag=True) == SHELF_BUTTON_DOC_TAG:
            cmds.deleteUI(child)
            removed_any = True

    return removed_any


def _shelf_top_level() -> str | None:
    try:
        import maya.mel as mel
    except ImportError:
        return None

    try:
        return mel.eval("$archsunShelfTopLevel = $gShelfTopLevel")
    except RuntimeError:
        return None
