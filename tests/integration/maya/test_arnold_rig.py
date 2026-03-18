import pytest

from tests.helpers.fake_maya_cmds import install_fake_maya


pytestmark = [pytest.mark.integration, pytest.mark.maya]


@pytest.fixture
def arnold_rig_module(monkeypatch, fresh_import):
    fake_cmds = install_fake_maya(monkeypatch)
    module = fresh_import("archsun.maya.arnold_rig", "archsun.maya")
    return module, fake_cmds


def test_importing_arnold_rig_does_not_load_mtoa(arnold_rig_module):
    _module, fake_cmds = arnold_rig_module
    assert fake_cmds.plugins_loaded["mtoa"] is False


def test_ensure_exists_returns_true_when_rig_is_missing(arnold_rig_module):
    module, fake_cmds = arnold_rig_module
    rig = module.ArnoldDaylightRig()

    assert rig.ensure_exists() is True
    assert fake_cmds.objExists("ARCHSUN_RIG")
    assert fake_cmds.objExists("ARCHSUN_SKY")
    assert fake_cmds.objExists("ARCHSUN_SKY_PhysicalSky")


def test_ensure_exists_returns_false_when_rig_already_exists(arnold_rig_module):
    module, _fake_cmds = arnold_rig_module
    rig = module.ArnoldDaylightRig()

    rig.ensure_exists()
    assert rig.ensure_exists() is False


def test_set_sun_rotation_applies_north_offset_and_returns_state(arnold_rig_module):
    module, fake_cmds = arnold_rig_module
    rig = module.ArnoldDaylightRig()
    rig.ensure_exists()

    applied_state = rig.set_sun_rotation(
        azimuth=45.0,
        altitude=30.0,
        north_offset=15.0,
        intensity_override=2.0,
    )

    assert applied_state.final_azimuth == pytest.approx(60.0)
    assert applied_state.altitude == pytest.approx(30.0)
    assert applied_state.final_intensity == pytest.approx(4.0)
    assert fake_cmds.get_attr("ARCHSUN_SKY_PhysicalSky.azimuth") == pytest.approx(60.0)
    assert fake_cmds.get_attr("ARCHSUN_SKY_PhysicalSky.elevation") == pytest.approx(30.0)
    assert fake_cmds.get_attr("ARCHSUN_SKYShape.intensity") == pytest.approx(4.0)


@pytest.mark.parametrize(
    ("altitude", "expected_intensity"),
    [
        (-5.0, 0.2),
        (30.0, 2.0),
        (90.0, 4.0),
    ],
)
def test_set_sun_rotation_uses_expected_altitude_intensity_curve(
    arnold_rig_module, altitude, expected_intensity
):
    module, _fake_cmds = arnold_rig_module
    rig = module.ArnoldDaylightRig()
    rig.ensure_exists()

    applied_state = rig.set_sun_rotation(
        azimuth=180.0,
        altitude=altitude,
        north_offset=0.0,
        intensity_override=1.0,
    )

    assert applied_state.final_intensity == pytest.approx(expected_intensity)


def test_apply_weather_preset_sets_expected_values(arnold_rig_module):
    module, fake_cmds = arnold_rig_module
    rig = module.ArnoldDaylightRig()
    rig.ensure_exists()

    rig.apply_weather_preset("clear")
    assert fake_cmds.get_attr("ARCHSUN_SKY_PhysicalSky.turbidity") == pytest.approx(2.0)
    assert fake_cmds.get_attr("ARCHSUN_SKYShape.intensity") == pytest.approx(4.0)

    rig.apply_weather_preset("hazy")
    assert fake_cmds.get_attr("ARCHSUN_SKY_PhysicalSky.turbidity") == pytest.approx(5.0)
    assert fake_cmds.get_attr("ARCHSUN_SKYShape.intensity") == pytest.approx(2.5)

    rig.apply_weather_preset("overcast")
    assert fake_cmds.get_attr("ARCHSUN_SKY_PhysicalSky.turbidity") == pytest.approx(10.0)
    assert fake_cmds.get_attr("ARCHSUN_SKYShape.intensity") == pytest.approx(1.5)


def test_apply_weather_preset_raises_for_unknown_preset(arnold_rig_module):
    module, _fake_cmds = arnold_rig_module
    rig = module.ArnoldDaylightRig()
    rig.ensure_exists()

    with pytest.raises(ValueError, match="Unknown preset"):
        rig.apply_weather_preset("stormy")

