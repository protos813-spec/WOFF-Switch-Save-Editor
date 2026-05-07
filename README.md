# World of Final Fantasy Maxima Switch Save Editor

A Python save editor for decrypted Nintendo Switch saves from **World of Final Fantasy Maxima**.

## Features

- Gil editing
- Battle item editing
- Key/misc item editing
- Prism editing
- Memento editing
- Seed editing
- Mirajewel editing
- Champion Medal editing *(experimental)*
- Mirage Compendium editing *(experimental)*

## Requirements

- Python 3
- Decrypted `gamedata` from JKSV or Checkpoint

## Usage

1. Back up your save with JKSV.
2. Open only the `gamedata` file.
3. Run:

```bash
woff_switch_final_update.py
```

4. Edit your save.
5. Save the modified `gamedata`.
6. Restore with JKSV.

## Warnings

- Keep backups.
- Do not edit ZIP archives directly.
- Compendium and Champion Medal editing are experimental.
- I am not responsible for any corrupt saves or data that come from using this. There is a rollback feature in the editor that should work as intended.

## Screenshot

![Editor Screenshot](screenshots/editor.png)

## Pre-release EXE Build

A pre-release standalone `.exe` build may be provided in the GitHub Releases section.

### Notes

- Windows may flag unsigned builds with SmartScreen warnings.
- The `.exe` is portable and does not require Python.
- Always keep JKSV backups before editing saves.
- The executable build is considered experimental/pre-release.
- If issues occur, use the Python version instead.

### Running the EXE

1. Download the latest pre-release from Releases.
2. Extract the archive if needed.
3. Run the `.exe`.
4. Open your decrypted `gamedata` file.
5. Save edited data and restore with JKSV.

## Pre-release EXE Build

![Windows Build Screenshot](screenshots/winbuild.png)
