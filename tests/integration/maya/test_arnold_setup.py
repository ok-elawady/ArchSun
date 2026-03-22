import pytest

from tests.helpers.fake_maya_cmds import install_fake_maya


pytestmark = [pytest.mark.integration, pytest.mark.maya]


@pytest.fixture
def arnold_setup_module(monkeypatch, fresh_import):
    fake_cmds = install_fake_maya(monkeypatch)
    module = fresh_import("archsun.maya.arnold_setup", "archsun.maya")
    return module, fake_cmds


def test_importing_arnold_setup_does_not_load_mtoa(arnold_setup_module):
    _module, fake_cmds = arnold_setup_module
    assert fake_cmds.plugins_loaded["mtoa"] is False


def test_ensure_exists_returns_true_when_setup_is_missing(arnold_setup_module):
    module, fake_cmds = arnold_setup_module
    setup = module.ArnoldDaylightSetup()

    assert setup.ensure_exists() is True
    assert fake_cmds.objExists("ARCHSUN_DAYLIGHT_GRP")
    assert fake_cmds.objExists("ARCHSUN_SKYDOME_LGT")
    assert fake_cmds.objExists("ARCHSUN_PHYSICALSKY_TEX")


def test_ensure_exists_returns_false_when_setup_already_exists(arnold_setup_module):
    module, _fake_cmds = arnold_setup_module
    setup = module.ArnoldDaylightSetup()

    setup.ensure_exists()
    assert setup.ensure_exists() is False


def test_set_sun_rotation_applies_north_offset_and_returns_state(arnold_setup_module):
    module, fake_cmds = arnold_setup_module
    setup = module.ArnoldDaylightSetup()
    setup.ensure_exists()

    applied_state = setup.set_sun_rotation(
        azimuth=45.0,
        altitude=30.0,
        north_offset=15.0,
        intensity_override=2.0,
    )

    assert applied_state.final_azimuth == pytest.approx(60.0)
    assert applied_state.altitude == pytest.approx(30.0)
    assert applied_state.final_intensity == pytest.approx(4.0)
    assert fake_cmds.get_attr("ARCHSUN_PHYSICALSKY_TEX.azimuth") == pytest.approx(60.0)
    assert fake_cmds.get_attr("ARCHSUN_PHYSICALSKY_TEX.elevation") == pytest.approx(
        30.0
    )
    assert fake_cmds.get_attr("ARCHSUN_SKYDOME_LGTShape.intensity") == pytest.approx(
        4.0
    )


@pytest.mark.parametrize(
    ("altitude", "expected_intensity"),
    [
        (-5.0, 0.2),
        (30.0, 2.0),
        (90.0, 4.0),
    ],
)
def test_set_sun_rotation_uses_expected_altitude_intensity_curve(
    arnold_setup_module, altitude, expected_intensity
):
    module, _fake_cmds = arnold_setup_module
    setup = module.ArnoldDaylightSetup()
    setup.ensure_exists()

    applied_state = setup.set_sun_rotation(
        azimuth=180.0,
        altitude=altitude,
        north_offset=0.0,
        intensity_override=1.0,
    )

    assert applied_state.final_intensity == pytest.approx(expected_intensity)

