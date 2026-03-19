from archsun.ui import qt_compat

qt_compat.ensure_qt()
QtCore = qt_compat.QtCore
QtWidgets = qt_compat.QtWidgets


class ManualAdjustmentsSection(QtWidgets.QWidget):
    valuesChanged = QtCore.Signal()
    INTENSITY_SLIDER_SCALE = 10

    def __init__(self, parent=None):
        super().__init__(parent)

        self.build_ui()
        self.connect_signals()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        title = QtWidgets.QLabel("Manual Adjustments")
        title.setStyleSheet("font-weight: bold;")
        title.setToolTip(
            "Scene-side tweaks. North Offset aligns the daylight setup to your model, and Intensity scales the final dome brightness."
        )
        layout.addWidget(title)

        self.north_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.north_slider.setRange(-360, 360)
        self.north_slider.setValue(0)
        self.north_slider.setToolTip(
            "Rotate scene north to match how your model is oriented in Maya."
        )

        self.north_spin = QtWidgets.QDoubleSpinBox()
        self.north_spin.setRange(-360.0, 360.0)
        self.north_spin.setDecimals(0)
        self.north_spin.setSingleStep(1.0)
        self.north_spin.setValue(0.0)
        self.north_spin.setToolTip(self.north_slider.toolTip())

        self.north_reset_button = QtWidgets.QPushButton("Reset")
        self.north_reset_button.setToolTip("Return North Offset to 0.")

        self.intensity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.intensity_slider.setRange(0, 10 * self.INTENSITY_SLIDER_SCALE)
        self.intensity_slider.setValue(1 * self.INTENSITY_SLIDER_SCALE)
        self.intensity_slider.setToolTip(
            "Scale the final physical-sky dome brightness without changing the sun position."
        )

        self.intensity_spin = QtWidgets.QDoubleSpinBox()
        self.intensity_spin.setRange(0.0, 10.0)
        self.intensity_spin.setDecimals(1)
        self.intensity_spin.setValue(1.0)
        self.intensity_spin.setSingleStep(0.1)
        self.intensity_spin.setToolTip(self.intensity_slider.toolTip())

        self.intensity_reset_button = QtWidgets.QPushButton("Reset")
        self.intensity_reset_button.setToolTip("Return Intensity to 1.0.")

        section_block = QtWidgets.QWidget()
        section_block.setObjectName("SectionBlock")

        form_layout = QtWidgets.QFormLayout()
        form_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        form_layout.setSpacing(6)
        form_layout.addRow(
            "North Offset",
            self._build_control_row(
                self.north_slider,
                self.north_spin,
                self.north_reset_button,
            ),
        )
        form_layout.addRow(
            "Intensity",
            self._build_control_row(
                self.intensity_slider,
                self.intensity_spin,
                self.intensity_reset_button,
            ),
        )
        section_block.setLayout(form_layout)

        layout.addWidget(section_block)

    def connect_signals(self):
        self.north_slider.valueChanged.connect(self._sync_north_from_slider)
        self.north_spin.valueChanged.connect(self.emit_values_changed)
        self.north_spin.valueChanged.connect(self._sync_north_from_spin)
        self.north_reset_button.clicked.connect(self.reset_north_offset)
        self.intensity_slider.valueChanged.connect(self._sync_intensity_from_slider)
        self.intensity_spin.valueChanged.connect(self.emit_values_changed)
        self.intensity_spin.valueChanged.connect(self._sync_intensity_from_spin)
        self.intensity_reset_button.clicked.connect(self.reset_intensity)

    def emit_values_changed(self, *_args):
        self.valuesChanged.emit()

    def _build_control_row(self, slider, spinbox, reset_button):
        row_widget = QtWidgets.QWidget()
        row_layout = QtWidgets.QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)
        row_layout.addWidget(slider, stretch=1)
        row_layout.addWidget(spinbox)
        row_layout.addWidget(reset_button)
        return row_widget

    def _sync_north_from_slider(self, value):
        self.north_spin.blockSignals(True)
        self.north_spin.setValue(float(value))
        self.north_spin.blockSignals(False)
        self.emit_values_changed()

    def _sync_north_from_spin(self, value):
        slider_value = int(round(value))
        if self.north_slider.value() == slider_value:
            return

        self.north_slider.blockSignals(True)
        self.north_slider.setValue(slider_value)
        self.north_slider.blockSignals(False)

    def _sync_intensity_from_slider(self, value):
        intensity = value / float(self.INTENSITY_SLIDER_SCALE)
        self.intensity_spin.blockSignals(True)
        self.intensity_spin.setValue(intensity)
        self.intensity_spin.blockSignals(False)
        self.emit_values_changed()

    def _sync_intensity_from_spin(self, value):
        slider_value = int(round(value * self.INTENSITY_SLIDER_SCALE))
        if self.intensity_slider.value() == slider_value:
            return

        self.intensity_slider.blockSignals(True)
        self.intensity_slider.setValue(slider_value)
        self.intensity_slider.blockSignals(False)

    def north_offset(self) -> float:
        return self.north_spin.value()

    def intensity(self) -> float:
        return self.intensity_spin.value()

    def reset_north_offset(self):
        self.north_spin.setValue(0.0)

    def reset_intensity(self):
        self.intensity_spin.setValue(1.0)
