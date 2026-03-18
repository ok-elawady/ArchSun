from pathlib import Path

import pytest

from archsun.ui.resources import asset_path


pytestmark = pytest.mark.unit


def test_asset_paths_resolve_existing_ui_assets():
    assert Path(asset_path("style.qss")).exists()
    assert Path(asset_path("world_map.png")).exists()
