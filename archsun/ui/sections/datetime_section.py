from datetime import datetime

from archsun.ui import qt_compat

qt_compat.ensure_qt()
QtCore = qt_compat.QtCore
QtWidgets = qt_compat.QtWidgets


class DateTimeSection(QtWidgets.QWidget):
    valuesChanged = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.build_ui()
        self.connect_signals()
        self.update_display()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        title = QtWidgets.QLabel("Date & Time")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)

        self.date_edit = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self.date_edit.setCalendarPopup(True)

        self.time_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.time_slider.setRange(0, (24 * 60) - 1)  # 00:00 -> 23:59
        self.time_slider.setValue(12 * 60)

        self.datetime_display = QtWidgets.QLabel("")
        self.datetime_display.setAlignment(QtCore.Qt.AlignCenter)
        self.datetime_display.setStyleSheet("padding-top: 4px;")

        section_block = QtWidgets.QWidget()
        section_block.setObjectName("SectionBlock")

        block_layout = QtWidgets.QVBoxLayout()
        block_layout.setSpacing(6)

        date_row = QtWidgets.QHBoxLayout()
        date_row.setContentsMargins(0, 0, 0, 0)

        date_label = QtWidgets.QLabel("Date")
        date_label.setFixedWidth(60)
        date_row.addWidget(date_label)
        date_row.addWidget(self.date_edit)

        block_layout.addLayout(date_row)
        block_layout.addWidget(QtWidgets.QLabel("Time of Day"))
        block_layout.addWidget(self.time_slider)
        block_layout.addWidget(self.datetime_display)

        section_block.setLayout(block_layout)
        layout.addWidget(section_block)

    def connect_signals(self):
        self.time_slider.valueChanged.connect(self.update_display)
        self.time_slider.valueChanged.connect(self.emit_values_changed)
        self.date_edit.dateChanged.connect(self.update_display)
        self.date_edit.dateChanged.connect(self.emit_values_changed)

    def emit_values_changed(self, *_args):
        self.valuesChanged.emit()

    def get_datetime(self) -> datetime:
        qdate = self.date_edit.date()
        total_minutes = self.time_slider.value()
        hours = total_minutes // 60
        minutes = total_minutes % 60

        return datetime(
            qdate.year(),
            qdate.month(),
            qdate.day(),
            hours,
            minutes,
            0,
        )

    def update_display(self, *_args):
        formatted = self.get_datetime().strftime("%A, %B %d, %Y - %I:%M %p")
        self.datetime_display.setText(formatted)
