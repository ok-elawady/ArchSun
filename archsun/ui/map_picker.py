from archsun.ui import qt_compat

qt_compat.ensure_qt()
QtCore = qt_compat.QtCore
QtGui = qt_compat.QtGui
QtWidgets = qt_compat.QtWidgets


class MapWidget(QtWidgets.QLabel):
    locationSelected = QtCore.Signal(float, float)

    def __init__(self, image_path, parent=None):
        super().__init__(parent)

        self.pixmap = QtGui.QPixmap(image_path)
        self.setPixmap(self.pixmap)
        self.setScaledContents(True)

        self._pin_position = None

    def mousePressEvent(self, event):
        if self.pixmap.isNull():
            return

        width = self.width()
        height = self.height()
        if width <= 0 or height <= 0:
            return

        x = event.pos().x()
        y = event.pos().y()

        # Convert pixel to lat/long (equirectangular).
        longitude = (x / width) * 360.0 - 180.0
        latitude = 90.0 - (y / height) * 180.0

        self._pin_position = event.pos()
        self.update()

        self.locationSelected.emit(latitude, longitude)

    def paintEvent(self, event):
        super().paintEvent(event)

        if self._pin_position:
            painter = QtGui.QPainter(self)
            painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
            painter.setPen(QtCore.Qt.NoPen)

            radius = 6
            painter.drawEllipse(self._pin_position, radius, radius)
            painter.end()


class MapPickerDialog(QtWidgets.QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Select Location")

        self.selected_lat = None
        self.selected_lon = None

        layout = QtWidgets.QVBoxLayout(self)

        self.map_widget = MapWidget(image_path)
        self.map_widget.locationSelected.connect(self.on_location_selected)
        layout.addWidget(self.map_widget)

        self.coords_label = QtWidgets.QLabel("Click on the map to choose a location.")
        layout.addWidget(self.coords_label)

        self.button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        layout.addWidget(self.button_box)

    def on_location_selected(self, lat, lon):
        self.selected_lat = lat
        self.selected_lon = lon
        self.coords_label.setText(f"Lat: {lat:.4f}  Lon: {lon:.4f}")
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
