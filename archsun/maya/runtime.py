try:
    import maya.cmds as _cmds
except ImportError:
    _cmds = None

try:
    import maya.OpenMayaUI as _omui
except ImportError:
    _omui = None


MAYA_AVAILABLE = _cmds is not None
MAYA_UI_AVAILABLE = _omui is not None


def inside_maya() -> bool:
    return MAYA_AVAILABLE


def get_cmds():
    if _cmds is None:
        raise RuntimeError("ArchSun must be run inside Autodesk Maya.")
    return _cmds


def get_open_maya_ui():
    if _omui is None:
        raise RuntimeError("Maya UI APIs are unavailable in this environment.")
    return _omui


def ensure_plugin_loaded(plugin_name: str, quiet: bool = True) -> bool:
    cmds = get_cmds()
    if cmds.pluginInfo(plugin_name, query=True, loaded=True):
        return False

    cmds.loadPlugin(plugin_name, quiet=quiet)
    return True


def main_window_ptr():
    if not MAYA_UI_AVAILABLE:
        return None
    return _omui.MQtUtil.mainWindow()


def find_control(control_name: str):
    if not MAYA_UI_AVAILABLE:
        return None
    return _omui.MQtUtil.findControl(control_name)
