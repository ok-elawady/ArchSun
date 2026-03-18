from archsun import APP_NAME, DISPLAY_VERSION
from archsun.core.daylight_service import DaylightService
from archsun.maya import runtime
from archsun.maya.arnold_rig import ArnoldDaylightRig
from archsun.ui import qt_compat, status_text
from archsun.ui.resources import asset_path
from archsun.ui.sections import (
    DateTimeSection,
    LocationSection,
    ManualAdjustmentsSection,
    StatusMessageWidget,
)

qt_compat.ensure_qt()
QtWidgets = qt_compat.QtWidgets


WINDOW_TITLE = APP_NAME
WORKSPACE_NAME = "ArchSunWorkspaceControl"


def maya_main_window():
    ptr = runtime.main_window_ptr()
    if not ptr:
        return None
    return qt_compat.wrap_instance(ptr, QtWidgets.QWidget)


class ArchSunWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent or maya_main_window())

        self.setWindowTitle(WINDOW_TITLE)

        self.service = DaylightService()
        self.rig = ArnoldDaylightRig()
        self._has_applied = False

        self.build_ui()
        self.apply_stylesheet()

    def build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(12)

        title = QtWidgets.QLabel(f"{APP_NAME} {DISPLAY_VERSION}")
        title.setObjectName("TitleLabel")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(title)

        self.location_section = LocationSection()
        self.datetime_section = DateTimeSection()
        self.manual_section = ManualAdjustmentsSection()
        self.status_widget = StatusMessageWidget()

        update_btn = QtWidgets.QPushButton("Update Lighting")
        update_btn.clicked.connect(self.update_lighting)

        bottom_layout = QtWidgets.QVBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(10)
        bottom_layout.addWidget(update_btn)
        bottom_layout.addWidget(self.status_widget)

        main_layout.addWidget(self.location_section)
        main_layout.addWidget(self.datetime_section)
        main_layout.addWidget(self.manual_section)
        main_layout.addStretch(1)
        main_layout.addLayout(bottom_layout)

        self.location_section.valuesChanged.connect(self.on_inputs_changed)
        self.datetime_section.valuesChanged.connect(self.on_inputs_changed)
        self.manual_section.valuesChanged.connect(self.on_inputs_changed)

    def apply_stylesheet(self):
        style_path = asset_path("style.qss")

        try:
            with open(style_path, "r", encoding="utf-8") as style_file:
                self.setStyleSheet(style_file.read())
        except OSError:
            return

    def on_inputs_changed(self):
        if not self._has_applied:
            return

        self.status_widget.set_dirty()

    def update_lighting(self):
        try:
            location = self.location_section.get_location()
            dt = self.datetime_section.get_datetime()
            sun_state = self.service.get_sun_state(location, dt)

            was_created = self.rig.ensure_exists()
            applied_state = self.rig.set_sun_rotation(
                azimuth=sun_state.azimuth,
                altitude=sun_state.altitude,
                north_offset=self.manual_section.north_offset(),
                intensity_override=self.manual_section.intensity(),
            )
        except Exception as exc:
            self.status_widget.set_error(f"Could not update ArchSun. {exc}")
            return

        self._has_applied = True
        self.status_widget.set_applied(
            status_text.build_applied_message(was_created, applied_state)
        )

        print(
            f"ArchSun Updated -> Azimuth: {sun_state.azimuth:.2f} "
            f"Altitude: {sun_state.altitude:.2f}"
        )


def show_window():
    cmds = runtime.get_cmds()

    if cmds.workspaceControl(WORKSPACE_NAME, exists=True):
        cmds.deleteUI(WORKSPACE_NAME)

    cmds.workspaceControl(
        WORKSPACE_NAME,
        label=WINDOW_TITLE,
        retain=False,
        initialWidth=320,
        minimumWidth=280,
    )

    if cmds.workspaceControl("ChannelBoxLayerEditor", exists=True):
        cmds.workspaceControl(
            WORKSPACE_NAME,
            edit=True,
            tabToControl=("ChannelBoxLayerEditor", -1),
        )

    cmds.workspaceControl(WORKSPACE_NAME, edit=True, restore=True)

    cmds.workspaceControl(
        WORKSPACE_NAME,
        edit=True,
        widthProperty="preferred",
        width=320,
    )

    control = runtime.find_control(WORKSPACE_NAME)
    if not control:
        raise RuntimeError("Could not find the ArchSun workspace control.")

    workspace_widget = qt_compat.wrap_instance(control, QtWidgets.QWidget)

    layout = workspace_widget.layout()
    if not layout:
        layout = QtWidgets.QVBoxLayout(workspace_widget)
        layout.setContentsMargins(0, 0, 0, 0)

    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()

    window = ArchSunWindow(parent=workspace_widget)
    window.setMinimumWidth(280)
    window.setMaximumWidth(400)

    layout.addWidget(window)
