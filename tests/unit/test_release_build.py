import pytest

from tools.build_release import build_release, release_name


pytestmark = pytest.mark.unit


def test_build_release_creates_install_ready_bundle(tmp_path):
    bundle_dir = build_release(tmp_path)
    release_dir = tmp_path / release_name()

    assert bundle_dir == release_dir
    assert (release_dir / "archsun_install_drop.py").exists()
    assert (release_dir / "archsun_uninstall_drop.py").exists()
    assert (release_dir / "README_Install.txt").exists()
    assert (release_dir / "package" / "archsun" / "launcher.py").exists()
    assert (
        release_dir
        / "package"
        / "archsun"
        / "ui"
        / "assets"
        / "icons"
        / "archsun_shelf.png"
    ).exists()
    assert (tmp_path / f"{release_name()}.zip").exists()

    installer_text = (release_dir / "archsun_install_drop.py").read_text(encoding="utf-8")
    uninstall_text = (release_dir / "archsun_uninstall_drop.py").read_text(encoding="utf-8")
    assert "install_from_release" in installer_text
    assert "uninstall_installed_package" in uninstall_text
    assert 'module_name == "archsun" or module_name.startswith("archsun.")' in installer_text
    assert "confirmDialog" in installer_text
    assert "def onMayaDroppedPythonFile(*_args, **_kwargs):" in installer_text
    assert 'if __name__ == "__main__":' in installer_text
    assert "def onMayaDroppedPythonFile(*_args, **_kwargs):" in uninstall_text
    assert 'if __name__ == "__main__":' in uninstall_text
    installer_namespace = {
        "__name__": "archsun_install_drop",
        "__file__": str(release_dir / "archsun_install_drop.py"),
    }
    uninstall_namespace = {
        "__name__": "archsun_uninstall_drop",
        "__file__": str(release_dir / "archsun_uninstall_drop.py"),
    }
    exec(compile(installer_text, "<archsun_install_drop.py>", "exec"), installer_namespace)
    exec(compile(uninstall_text, "<archsun_uninstall_drop.py>", "exec"), uninstall_namespace)
    assert callable(installer_namespace["onMayaDroppedPythonFile"])
    assert callable(uninstall_namespace["onMayaDroppedPythonFile"])

    readme_text = (release_dir / "README_Install.txt").read_text(encoding="utf-8")
    assert "Quick Install" in readme_text
    assert "GitHub Releases and Gumroad" in readme_text
