import sys
import types

import pytest


pytestmark = pytest.mark.unit


def test_importing_launcher_does_not_import_main_window(fresh_import):
    launcher = fresh_import("archsun.launcher", "archsun.ui.main_window")
    assert launcher is not None
    assert "archsun.ui.main_window" not in sys.modules


def test_show_archsun_lazy_imports_and_calls_show_window(monkeypatch, fresh_import):
    launcher = fresh_import("archsun.launcher", "archsun.ui.main_window")
    called = {"value": False}

    stub = types.ModuleType("archsun.ui.main_window")

    def show_window():
        called["value"] = True

    stub.show_window = show_window
    monkeypatch.setitem(sys.modules, "archsun.ui.main_window", stub)

    launcher.show_archsun()

    assert called["value"] is True
