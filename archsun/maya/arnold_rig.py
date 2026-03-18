from archsun.core.models import AppliedLightingState
from archsun.maya import runtime
from archsun.maya.constants import GROUP_NAME, SKY_NAME


def _cmds():
    return runtime.get_cmds()


def _ensure_skydome_light(transform_name: str, parent_group: str) -> tuple[str, str, str]:
    cmds = _cmds()

    runtime.ensure_plugin_loaded("mtoa", quiet=True)

    transform = None
    shape = None
    # Look for existing skydome under group
    if cmds.objExists(parent_group):
        children = cmds.listRelatives(parent_group, children=True) or []
        for child in children:
            shapes = cmds.listRelatives(child, shapes=True) or []
            for s in shapes:
                if cmds.nodeType(s) == "aiSkyDomeLight":
                    transform = child
                    shape = s
                    break

    if not transform:
        # Create new skydome properly
        transform = cmds.shadingNode("aiSkyDomeLight", asLight=True, name=transform_name)
        shape = cmds.listRelatives(transform, shapes=True)[0]
        cmds.parent(transform, parent_group)

    # Create and connect aiPhysicalSky
    phys_sky_name = f"{transform_name}_PhysicalSky"
    if (
        cmds.objExists(phys_sky_name)
        and cmds.nodeType(phys_sky_name) == "aiPhysicalSky"
    ):
        phys_sky = phys_sky_name
    else:
        phys_sky = cmds.shadingNode("aiPhysicalSky", asTexture=True, name=phys_sky_name)

    # Connect to skydome color
    if not cmds.isConnected(f"{phys_sky}.outColor", f"{shape}.color"):
        cmds.connectAttr(f"{phys_sky}.outColor", f"{shape}.color", force=True)

    return transform, shape, phys_sky


class ArnoldDaylightRig:
    """
    Manages an Arnold physical-sky skydome rig in the Maya scene.
    """

    def __init__(self):
        self.group = GROUP_NAME
        self.sky_transform = SKY_NAME

        self._sky_shape = None
        self._phys_sky = None

    def ensure_exists(self) -> bool:
        """
        Create or reuse the rig nodes. Safe to call multiple times.
        """
        cmds = _cmds()
        was_created = False
        cmds.undoInfo(openChunk=True)
        try:
            runtime.ensure_plugin_loaded("mtoa", quiet=True)

            # Ensure group
            if not cmds.objExists(self.group):
                cmds.group(em=True, name=self.group)
                was_created = True

            # Create / reuse sky (Arnold skydome + physical sky)
            phys_sky_name = f"{self.sky_transform}_PhysicalSky"
            had_sky = cmds.objExists(self.sky_transform)
            had_phys_sky = (
                cmds.objExists(phys_sky_name)
                and cmds.nodeType(phys_sky_name) == "aiPhysicalSky"
            )
            sky_t, sky_s, phys_sky = _ensure_skydome_light(self.sky_transform, self.group)
            was_created = was_created or not had_sky or not had_phys_sky

            # Parent to group
            if cmds.listRelatives(sky_t, parent=True) != [self.group]:
                cmds.parent(sky_t, self.group)

            self._sky_shape = sky_s
            self._phys_sky = phys_sky

            if was_created:
                cmds.setAttr(f"{sky_s}.intensity", 1.0)

        finally:
            cmds.undoInfo(closeChunk=True)

        return was_created

    def set_sun_rotation(
        self,
        azimuth: float,
        altitude: float,
        north_offset: float = 0.0,
        intensity_override: float = 1.0,
    ) -> AppliedLightingState:
        """
        Apply azimuth/altitude to the aiPhysicalSky node.

        Conventions:
        - azimuth is degrees from North, clockwise (0=N, 90=E, 180=S, 270=W)
        - altitude is degrees above horizon
        - north_offset rotates the whole compass to match scene north
        """
        cmds = _cmds()

        if not self._phys_sky or not cmds.objExists(self._phys_sky):
            self.ensure_exists()

        # Ensure clean numeric inputs
        az = float(azimuth) + float(north_offset)
        alt = float(altitude)

        # Map directly to Physical Sky attributes
        cmds.setAttr(f"{self._phys_sky}.elevation", alt)
        cmds.setAttr(f"{self._phys_sky}.azimuth", az)

        # Aesthetics
        cmds.setAttr(f"{self._phys_sky}.enable_sun", 1)
        cmds.setAttr(f"{self._phys_sky}.sun_size", 2.5)
        cmds.setAttr(f"{self._phys_sky}.turbidity", 3.5)

        # Smart intensity handling
        if self._sky_shape and cmds.objExists(self._sky_shape):

            if alt <= 0:
                sky_intensity = 0.2
            else:
                normalized = min(max(alt / 90.0, 0.0), 1.0)
                # Boosted baseline intensity, brightest at noon
                sky_intensity = 1.0 + (3.0 * normalized)

            # Physical Sky drives the combined daylight result, so expose one multiplier.
            final_intensity = sky_intensity * intensity_override
            cmds.setAttr(f"{self._sky_shape}.intensity", max(final_intensity, 0.0))
        else:
            final_intensity = 0.0

        return AppliedLightingState(
            final_azimuth=az % 360.0,
            altitude=alt,
            final_intensity=max(final_intensity, 0.0),
        )

    def apply_weather_preset(self, preset: str) -> None:
        """
        Simple presets: clear, hazy, overcast
        """
        cmds = _cmds()
        runtime.ensure_plugin_loaded("mtoa", quiet=True)
        preset = (preset or "").strip().lower()

        if not cmds.objExists(self.sky_transform):
            self.ensure_exists()

        # Re-fetch shapes if needed
        if not self._sky_shape:
            shapes = (
                cmds.listRelatives(self.sky_transform, shapes=True, fullPath=False)
                or []
            )
            self._sky_shape = shapes[0] if shapes else None

        sky = self._sky_shape
        phys = self._phys_sky

        if not sky or not phys:
            return

        if preset == "clear":
            cmds.setAttr(f"{phys}.turbidity", 2.0)
            cmds.setAttr(f"{sky}.intensity", 4.0)

        elif preset == "hazy":
            cmds.setAttr(f"{phys}.turbidity", 5.0)
            cmds.setAttr(f"{sky}.intensity", 2.5)

        elif preset == "overcast":
            cmds.setAttr(f"{phys}.turbidity", 10.0)
            cmds.setAttr(f"{sky}.intensity", 1.5)

        else:
            raise ValueError("Unknown preset. Use: clear, hazy, overcast")
