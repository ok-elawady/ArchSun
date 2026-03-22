from typing import Optional

from archsun.core.models import AppliedLightingState
from archsun.maya import runtime
from archsun.maya.constants import GROUP_NAME, PHYSICAL_SKY_NAME, SKY_NAME


def _cmds():
    return runtime.get_cmds()


def _find_skydome_light(parent_group: str) -> tuple[Optional[str], Optional[str]]:
    cmds = _cmds()

    if not cmds.objExists(parent_group):
        return None, None

    children = cmds.listRelatives(parent_group, children=True, fullPath=True) or []
    for child in children:
        shapes = cmds.listRelatives(child, shapes=True, fullPath=True) or []
        for shape in shapes:
            if cmds.nodeType(shape) == "aiSkyDomeLight":
                return child, shape

    return None, None


def _node_name(node_path: str) -> str:
    return node_path.split("|")[-1]


def _try_rename_skydome_transform(
    transform: str, requested_name: str, parent_group: str
) -> tuple[str, str]:
    cmds = _cmds()

    if _node_name(transform) == requested_name:
        shapes = cmds.listRelatives(transform, shapes=True, fullPath=True) or []
        if not shapes:
            raise RuntimeError(f"Arnold skydome transform '{transform}' has no shape.")
        return transform, shapes[0]

    try:
        cmds.rename(transform, requested_name)
    except Exception:
        pass

    transform, shape = _find_skydome_light(parent_group)
    if not transform or not shape:
        raise RuntimeError("ArchSun could not resolve the Arnold skydome light.")

    return transform, shape


def _ensure_skydome_light(
    transform_name: str, physical_sky_name: str, parent_group: str
) -> tuple[str, str, str]:
    cmds = _cmds()

    runtime.ensure_plugin_loaded("mtoa", quiet=True)

    transform, shape = _find_skydome_light(parent_group)

    if not transform:
        # Create new skydome properly
        created_transform = cmds.shadingNode(
            "aiSkyDomeLight", asLight=True, name=transform_name
        )
        parent_result = cmds.parent(created_transform, parent_group) or [created_transform]
        transform = parent_result[0]

    transform, shape = _try_rename_skydome_transform(
        transform, transform_name, parent_group
    )

    # Create and connect aiPhysicalSky
    if (
        cmds.objExists(physical_sky_name)
        and cmds.nodeType(physical_sky_name) == "aiPhysicalSky"
    ):
        phys_sky = physical_sky_name
    else:
        phys_sky = cmds.shadingNode(
            "aiPhysicalSky", asTexture=True, name=physical_sky_name
        )

    # Connect to skydome color
    if not cmds.isConnected(f"{phys_sky}.outColor", f"{shape}.color"):
        cmds.connectAttr(f"{phys_sky}.outColor", f"{shape}.color", force=True)

    return transform, shape, phys_sky

class ArnoldDaylightSetup:
    """
    Manages an Arnold physical-sky skydome daylight setup in the Maya scene.
    """

    def __init__(self):
        self.group = GROUP_NAME
        self.sky_transform = SKY_NAME
        self.physical_sky = PHYSICAL_SKY_NAME

        self._sky_shape = None
        self._phys_sky = None

    def ensure_exists(self) -> bool:
        """
        Create or reuse the setup nodes. Safe to call multiple times.
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
            had_sky = _find_skydome_light(self.group)[0] is not None
            had_phys_sky = (
                cmds.objExists(self.physical_sky)
                and cmds.nodeType(self.physical_sky) == "aiPhysicalSky"
            )
            sky_t, sky_s, phys_sky = _ensure_skydome_light(
                self.sky_transform, self.physical_sky, self.group
            )
            was_created = was_created or not had_sky or not had_phys_sky

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
