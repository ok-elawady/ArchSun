# ArchSun

ArchSun is a Python-based Autodesk Maya tool that creates and updates an Arnold daylight setup from real-world location, date, time, and scene north settings.

This project was built as a CG TD trainee portfolio piece. The goal was to make a small but complete Maya tool that combines:
- Qt UI inside Maya
- scene creation and scene updates through `maya.cmds`
- a NOAA-style solar-position calculation
- release packaging for non-technical users

## What It Does

- Creates an Arnold daylight setup in the Maya scene
- Uses latitude, longitude, date, time, and north offset to drive sun direction
- Provides a dockable Maya UI
- Lets the user choose a preset city or pick a point from a world map
- Supports manual scene-side intensity adjustment
- Builds an installable release bundle with install and uninstall scripts

## Current Scene Nodes

ArchSun currently creates and manages these Maya nodes:
- Group: `ARCHSUN_DAYLIGHT_GRP`
- Skydome transform: `ARCHSUN_SKYDOME_LGT`
- Physical sky texture: `ARCHSUN_PHYSICALSKY_TEX`

## Tech Stack

- Python
- Autodesk Maya
- Arnold (`mtoa`)
- PySide2 / PySide6 compatibility layer

## Project Structure

- [archsun/core](/d:/CustomMayaScripts/ArchSun/archsun/core): solar math, data models, location helpers
- [archsun/maya](/d:/CustomMayaScripts/ArchSun/archsun/maya): Maya runtime access, daylight setup creation, installer support
- [archsun/ui](/d:/CustomMayaScripts/ArchSun/archsun/ui): dockable Qt UI, sections, resources, status messaging
- [tests](/d:/CustomMayaScripts/ArchSun/tests): unit, integration, and manual smoke coverage
- [tools](/d:/CustomMayaScripts/ArchSun/tools): release build script

## Main Workflow

1. Launch ArchSun inside Maya.
2. Choose a city or pick a location from the map.
3. Set the date and time.
4. Adjust north offset and intensity if needed.
5. Click `Update Lighting`.
6. ArchSun creates or updates the Arnold daylight setup in the scene.

## Running In Maya

ArchSun is meant to run inside Autodesk Maya.

If the package is available on Maya's Python path, you can launch it with:

```python
from archsun.launcher import show_archsun
show_archsun()
```

## Building A Release

Build the release bundle from the repo root:

```bash
python -m tools.build_release
```

This creates:
- `dist/ArchSun-0.3.3`
- `dist/ArchSun-0.3.3.zip`

The bundle includes:
- `archsun_install_drop.py`
- `archsun_uninstall_drop.py`
- a packaged `archsun` folder
- a simple install readme for Maya users

## Testing

The project includes:
- unit tests for solar logic, status text, launcher behavior, and release packaging
- Maya-facing integration tests built around a fake `maya.cmds` layer
- a manual UI smoke checklist

Typical command:

```bash
python -m pytest -q
```

Install development dependencies with:

```bash
python -m pip install -r requirements-dev.txt
```

## Strengths Of The Project

- Clear separation between core logic, Maya integration, and UI
- Real scene-side behavior instead of a UI-only demo
- Release packaging and shelf-install support
- Naming cleanup for scene nodes
- A test suite that covers multiple layers of the tool

## Current Limitations

- The solar calculation in [solar.py](/d:/CustomMayaScripts/ArchSun/archsun/core/solar.py) is more robust than the original simplified version, but it is still not presented as a fully validated production-grade daylight solver.
- Timezone handling is manual and not daylight-savings aware.
- The tool is currently Arnold-specific.
- UI smoke testing inside Maya is still partly manual.

## Portfolio Framing

If you are reviewing this as a trainee project, the intended value is not that it is a full production-ready daylight system. The intended value is that it shows the ability to:
- identify a useful DCC workflow problem
- design a usable artist-facing UI
- connect UI input to scene behavior
- organize code into maintainable modules
- package a tool for delivery instead of stopping at a script

## Suggested Next Improvements

- Validate solar output against trusted reference cases
- Improve timezone handling
- Add clearer debug logging for Maya/Arnold failures
- Add screenshots or a short demo GIF to this README
- Add a small preset or batch workflow feature
