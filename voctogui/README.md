# Voctogui - The gui-frontend for voctocore

![Screenshot of voctogui in action](voctomix.png)

## Keyboard Shortcuts
### Composition Modes
- `F1` Fullscreen
- `F2` Picture in Picture
- `F3` Side-by-Side Equal
- `F4` Side-by-Side Preview

### Select A-Source
- `1` Source Nr. 1
- `2` Source Nr. 2
- …

### Select B-Source
- `Ctrl+1` Source Nr. 1
- `Ctrl+2` Source Nr. 2
- …

### Other options
- `t` Cut

### Select an Audio-Source
Click twice on the Selection Combobox, then select your Source within 5 Seconds (It will auto-lock again after 5 Seconds)

## Configuration
On Startup the GUI reads the following Configuration-Files:
 - `<install-dir>/default-config.ini`
 - `<install-dir>/config.ini`
 - `/etc/voctogui.ini`
 - `<homedir>/.voctogui.ini`
 - `<File specified on Command-Line via --ini-file>`

From top to bottom the individual Settings override previous Settings. `default-config.ini` should not be edited, because a missing Setting will result in an Exception.

On startup the GUI fetches all configuration settings from the core and merges them into the GUI config.
