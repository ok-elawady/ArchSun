import importlib


QtCore = None
QtGui = None
QtWidgets = None
QT_AVAILABLE = False
QT_BINDING = None
IMPORT_ERROR = None
_wrap_instance_impl = None


def _load_binding():
    global QtCore, QtGui, QtWidgets
    global QT_AVAILABLE, QT_BINDING, IMPORT_ERROR, _wrap_instance_impl

    binding_candidates = (
        ("PySide6", "shiboken6"),
        ("PySide2", "shiboken2"),
    )

    errors = []
    for binding_name, shiboken_name in binding_candidates:
        try:
            qt_core_module = importlib.import_module(f"{binding_name}.QtCore")
            qt_gui_module = importlib.import_module(f"{binding_name}.QtGui")
            qt_widgets_module = importlib.import_module(f"{binding_name}.QtWidgets")
            shiboken_module = importlib.import_module(shiboken_name)
        except (ImportError, AttributeError) as exc:
            errors.append(exc)
            continue

        QtCore = qt_core_module
        QtGui = qt_gui_module
        QtWidgets = qt_widgets_module
        _wrap_instance_impl = shiboken_module.wrapInstance
        QT_AVAILABLE = True
        QT_BINDING = binding_name
        IMPORT_ERROR = None
        return

    IMPORT_ERROR = errors[-1] if errors else ImportError("Qt binding not found.")


def ensure_qt():
    if not QT_AVAILABLE:
        raise ImportError(
            "ArchSun requires PySide6/shiboken6 or PySide2/shiboken2."
        ) from IMPORT_ERROR


def wrap_instance(ptr, base):
    ensure_qt()
    return _wrap_instance_impl(int(ptr), base)


def exec_dialog(dialog):
    if hasattr(dialog, "exec"):
        return dialog.exec()
    return dialog.exec_()


_load_binding()
