import pytest


pytestmark = pytest.mark.unit


def test_qt_compat_imports_without_crashing(fresh_import):
    module = fresh_import("archsun.ui.qt_compat", "archsun.ui")

    assert hasattr(module, "QT_AVAILABLE")
    assert module.QT_BINDING in {None, "PySide2", "PySide6"}

    if module.QT_AVAILABLE:
        module.ensure_qt()
    else:
        with pytest.raises(ImportError):
            module.ensure_qt()


def test_exec_dialog_prefers_exec_then_falls_back_to_exec_(fresh_import):
    module = fresh_import("archsun.ui.qt_compat", "archsun.ui")

    class ModernDialog:
        def exec(self):
            return "modern"

        def exec_(self):
            return "legacy"

    class LegacyDialog:
        def exec_(self):
            return "legacy"

    assert module.exec_dialog(ModernDialog()) == "modern"
    assert module.exec_dialog(LegacyDialog()) == "legacy"

