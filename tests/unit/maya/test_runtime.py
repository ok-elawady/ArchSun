import sys
import types

import pytest

from tests.helpers.fake_maya_cmds import install_fake_maya


pytestmark = pytest.mark.unit


def test_runtime_reports_missing_maya_safely(monkeypatch, fresh_import):
    monkeypatch.setitem(sys.modules, "maya", types.ModuleType("maya"))
    monkeypatch.delitem(sys.modules, "maya.cmds", raising=False)
    monkeypatch.delitem(sys.modules, "maya.OpenMayaUI", raising=False)

    runtime = fresh_import("archsun.maya.runtime", "archsun.maya")

    assert runtime.inside_maya() is False
    assert runtime.main_window_ptr() is None

    with pytest.raises(RuntimeError, match="inside Autodesk Maya"):
        runtime.get_cmds()

    assert runtime.find_control("Anything") is None


def test_runtime_loads_plugins_and_accesses_ui_helpers(monkeypatch, fresh_import):
    fake_cmds = install_fake_maya(
        monkeypatch,
        include_ui=True,
        main_window_ptr=1234,
        control_ptrs={"ArchSunWorkspaceControl": 5678},
    )
    runtime = fresh_import("archsun.maya.runtime", "archsun.maya")

    assert runtime.inside_maya() is True
    assert runtime.ensure_plugin_loaded("mtoa") is True
    assert fake_cmds.plugins_loaded["mtoa"] is True
    assert runtime.ensure_plugin_loaded("mtoa") is False
    assert runtime.main_window_ptr() == 1234
    assert runtime.find_control("ArchSunWorkspaceControl") == 5678

