# Maya UI Smoke Checklist

- Build a fresh release bundle with `python -m tools.build_release` and confirm `dist/ArchSun-0.2.0` plus `dist/ArchSun-0.2.0.zip` are created.
- Extract the release bundle and drag `install_archsun.py` into Maya.
- Confirm ArchSun is copied into the Maya user scripts folder and opens from the created shelf button.
- Run `archsun.launcher.show_archsun()` manually and confirm the docked window opens on the Maya versions you support.
- Confirm the `Update Lighting` button and the status message stay visually grouped at the bottom of the window.
- Change the city and confirm latitude, longitude, and `UTC Offset (Manual)` update together.
- Use `Pick From Map` and confirm the selected coordinates are written back to the location fields.
- Open the map picker and confirm `OK` stays disabled until a location is chosen.
- Move the time slider and confirm the formatted date/time display updates.
- Adjust `North Offset` and `Intensity`, confirm the reset buttons return them to `0` and `1.0`, and confirm they affect the next lighting update.
- Confirm the tooltips make these meanings clear to an artist:
  - `Location` is the real-world site.
  - `UTC Offset (Manual)` is a manual time offset used in the sun calculation.
  - `North Offset` aligns the daylight setup to the model orientation in Maya.
  - The helper text makes it clear that city and map picks provide a starting offset only and that daylight saving time still needs manual verification.
- Confirm the status message flows through:
  - initial prompt
  - dirty/pending message after changes
  - applied message after `Update Lighting`
  - a clear error message if Arnold cannot be loaded or the setup update fails
- Drag `uninstall_archsun.py` into Maya and confirm the installed files are removed.

