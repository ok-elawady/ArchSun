from archsun.core.models import AppliedLightingState


INITIAL_STATUS_MESSAGE = "Press Update Lighting to create the ArchSun rig."
DIRTY_STATUS_MESSAGE = "Settings changed.\nClick Update Lighting to apply."


def initial_message() -> str:
    return INITIAL_STATUS_MESSAGE


def dirty_message() -> str:
    return DIRTY_STATUS_MESSAGE


def build_applied_message(
    was_created: bool, applied_state: AppliedLightingState
) -> str:
    status_prefix = "ArchSun rig added." if was_created else "ArchSun rig updated."
    summary = build_status_summary(applied_state)
    return f"{status_prefix}\n{summary}."


def build_status_summary(applied_state: AppliedLightingState) -> str:
    direction = _direction_name(applied_state.final_azimuth)
    brightness = _brightness_name(applied_state.final_intensity)
    night_phase = _night_phase_name(applied_state.altitude)

    if night_phase:
        summary = f"{brightness} {night_phase} from the {direction}"
    else:
        parts = [brightness]
        warmth = _warmth_name(applied_state.altitude)
        if warmth:
            parts.append(warmth)
        parts.append(_height_name(applied_state.altitude))
        summary = f"{' '.join(parts)} from the {direction}"

    return _sentence_case(summary)


def _direction_name(azimuth: float) -> str:
    directions = (
        "north",
        "north-east",
        "east",
        "south-east",
        "south",
        "south-west",
        "west",
        "north-west",
    )
    normalized = azimuth % 360.0
    index = int((normalized + 22.5) // 45.0) % len(directions)
    return directions[index]


def _height_name(altitude: float) -> str:
    if altitude < 0.0:
        return "twilight"
    if altitude < 15.0:
        return "low sun"
    if altitude < 45.0:
        return "daylight"
    return "high sun"


def _warmth_name(altitude: float) -> str:
    if altitude < 0.0:
        return ""
    if altitude < 10.0:
        return "warm"
    if altitude < 25.0:
        return "soft"
    return "clear"


def _brightness_name(final_intensity: float) -> str:
    if final_intensity < 0.75:
        return "dim"
    if final_intensity < 1.5:
        return "soft"
    if final_intensity < 3.0:
        return "bright"
    return "very bright"


def _night_phase_name(altitude: float) -> str:
    if altitude < -6.0:
        return "night"
    if altitude < 0.0:
        return "twilight"
    return ""


def _sentence_case(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]
