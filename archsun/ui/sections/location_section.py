from archsun.core.locations import CITIES, infer_utc_offset
from archsun.core.models import Location
from archsun.ui import qt_compat
from archsun.ui.map_picker import MapPickerDialog
from archsun.ui.resources import asset_path

qt_compat.ensure_qt()
QtCore = qt_compat.QtCore
QtWidgets = qt_compat.QtWidgets


class LocationSection(QtWidgets.QWidget):
    valuesChanged = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._map_image_path = asset_path("world_map.png")

        self.build_ui()
        self.connect_signals()
        self._update_timezone_hint()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        title = QtWidgets.QLabel("Location")
        title.setStyleSheet("font-weight: bold;")
        title.setToolTip(
            "Location sets the real-world site used for the sun calculation."
        )
        layout.addWidget(title)

        self.city_combo = QtWidgets.QComboBox()
        self.city_combo.addItem("Custom")
        for city in CITIES:
            self.city_combo.addItem(city.name)
        self.city_combo.setToolTip(
            "Choose a nearby city to fill in the location and a starting UTC offset. Verify the offset manually if daylight saving time applies."
        )

        self.map_button = QtWidgets.QPushButton("Pick From Map")
        self.map_button.setToolTip(
            "Pick a place on the map to fill the location. ArchSun will use a nearby city offset when available, otherwise it falls back to a longitude-based guess."
        )

        self.lat_spin = QtWidgets.QDoubleSpinBox()
        self.lat_spin.setRange(-90.0, 90.0)
        self.lat_spin.setDecimals(4)
        self.lat_spin.setValue(40.7128)
        self.lat_spin.setToolTip("Latitude of the project site.")

        self.lon_spin = QtWidgets.QDoubleSpinBox()
        self.lon_spin.setRange(-180.0, 180.0)
        self.lon_spin.setDecimals(4)
        self.lon_spin.setValue(-74.0060)
        self.lon_spin.setToolTip("Longitude of the project site.")

        self.tz_spin = QtWidgets.QDoubleSpinBox()
        self.tz_spin.setRange(-12.0, 14.0)
        self.tz_spin.setDecimals(2)
        self.tz_spin.setSingleStep(0.5)
        self.tz_spin.setValue(-5.0)
        self.tz_spin.setToolTip(
            "Manual UTC offset used to convert the selected local date and time to UTC for the sun calculation. Adjust this if daylight saving time or local timezone rules differ."
        )
        self.tz_help_label = QtWidgets.QLabel("")
        self.tz_help_label.setWordWrap(True)
        self.tz_help_label.setStyleSheet("font-size: 11px; color: #9aa4af;")

        section_block = QtWidgets.QWidget()
        section_block.setObjectName("SectionBlock")

        form_layout = QtWidgets.QFormLayout()
        form_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        form_layout.setSpacing(6)
        form_layout.addRow(self._label("City"), self.city_combo)
        form_layout.addRow("", self.map_button)
        form_layout.addRow(self._label("Latitude"), self.lat_spin)
        form_layout.addRow(self._label("Longitude"), self.lon_spin)
        form_layout.addRow(
            self._label(
                "UTC Offset (Manual)",
                "Manual time offset used for the sun calculation. This is editable and not daylight-savings aware.",
            ),
            self.tz_spin,
        )
        form_layout.addRow("", self.tz_help_label)
        section_block.setLayout(form_layout)

        layout.addWidget(section_block)

    def connect_signals(self):
        self.city_combo.currentTextChanged.connect(self.on_city_changed)
        self.map_button.clicked.connect(self.open_map_picker)
        self.lat_spin.valueChanged.connect(self.emit_values_changed)
        self.lon_spin.valueChanged.connect(self.emit_values_changed)
        self.tz_spin.valueChanged.connect(self.emit_values_changed)
        self.tz_spin.valueChanged.connect(self._update_timezone_hint)

    def emit_values_changed(self, *_args):
        self.valuesChanged.emit()

    def get_location(self) -> Location:
        return Location(
            latitude=self.lat_spin.value(),
            longitude=self.lon_spin.value(),
            timezone_offset=self.tz_spin.value(),
        )

    def open_map_picker(self):
        dialog = MapPickerDialog(self._map_image_path, self)

        if qt_compat.exec_dialog(dialog) and dialog.selected_lat is not None:
            lat = dialog.selected_lat
            lon = dialog.selected_lon

            utc_offset, nearest = infer_utc_offset(lat, lon)
            if nearest:
                city_name = nearest.name
            else:
                city_name = "Custom"

            self._set_location_values(lat, lon, utc_offset, city_name)

    def on_city_changed(self, city_name):
        if city_name == "Custom":
            self.emit_values_changed()
            return

        for city in CITIES:
            if city.name == city_name:
                self._set_location_values(
                    city.latitude,
                    city.longitude,
                    city.utc_offset,
                    city.name,
                )
                break

    def _set_location_values(
        self,
        latitude: float,
        longitude: float,
        utc_offset: float,
        city_name: str,
    ) -> None:
        blockers = [
            QtCore.QSignalBlocker(self.city_combo),
            QtCore.QSignalBlocker(self.lat_spin),
            QtCore.QSignalBlocker(self.lon_spin),
            QtCore.QSignalBlocker(self.tz_spin),
        ]

        self.city_combo.setCurrentText(city_name)
        self.lat_spin.setValue(latitude)
        self.lon_spin.setValue(longitude)
        self.tz_spin.setValue(utc_offset)

        del blockers
        self._update_timezone_hint()
        self.emit_values_changed()

    def _update_timezone_hint(self, *_args):
        offset = self.tz_spin.value()
        sign = "+" if offset >= 0 else "-"
        absolute_offset = abs(offset)
        hours = int(absolute_offset)
        minutes = int(round((absolute_offset - hours) * 60))

        if minutes == 60:
            hours += 1
            minutes = 0

        self.tz_help_label.setText(
            "Used to convert the selected local time to UTC: "
            f"UTC{sign}{hours:02d}:{minutes:02d}. "
            "City and map picks provide a starting value only, so verify daylight saving time for the chosen date."
        )

    def _label(self, text: str, tooltip: str = "") -> QtWidgets.QLabel:
        label = QtWidgets.QLabel(text)
        if tooltip:
            label.setToolTip(tooltip)
        return label
