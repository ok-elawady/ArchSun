from archsun.ui import qt_compat
from archsun.ui import status_text

qt_compat.ensure_qt()
QtCore = qt_compat.QtCore
QtWidgets = qt_compat.QtWidgets


class StatusMessageWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("StatusBlock")
        self._reserved_line_count = 2

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.message_label = QtWidgets.QLabel("")
        self.message_label.setObjectName("StatusMessage")
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.message_label.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred,
            QtWidgets.QSizePolicy.Fixed,
        )
        layout.addWidget(self.message_label)

        self._reserve_message_height()
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred,
            QtWidgets.QSizePolicy.Fixed,
        )

        self.set_initial()

    def _set_message(self, message: str, state: str):
        self.message_label.setText(message)
        self.setProperty("statusState", state)
        self.message_label.setProperty("statusState", state)

        self._refresh_style(self)
        self._refresh_style(self.message_label)
        self._reserve_message_height()

    def set_initial(self):
        self._set_message(status_text.initial_message(), "initial")

    def set_dirty(self):
        self._set_message(status_text.dirty_message(), "dirty")

    def set_applied(self, message: str):
        self._set_message(message, "applied")

    def set_error(self, message: str):
        self._set_message(message, "error")

    def _refresh_style(self, widget):
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)
        widget.update()

    def _reserve_message_height(self) -> None:
        metrics = self.message_label.fontMetrics()
        reserved_height = max(
            metrics.lineSpacing() * self._reserved_line_count,
            metrics.height(),
        )
        reserved_height += 6
        self.message_label.setFixedHeight(reserved_height)
