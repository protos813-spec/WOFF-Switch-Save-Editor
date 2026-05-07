# WOFF-Switch-Save-Editor
A save editor for World of Final Fantasy Maxima on Switch
World of Final Fantasy Maxima Switch Save Editor

A Python-based save editor for decrypted Nintendo Switch saves from World of Final Fantasy Maxima.

This editor was built around real save structure testing and currently supports safe editing for:

Gil
Battle Items
Key / Misc Items
Prisms
Mementos
Seeds
Mirajewels
Champion Medals (experimental)
Mirage Compendium (experimental)
Features
Safe Editing

These sections have proven stable during testing:

Money/Gil
Battle Items
Key Items
Miscellaneous Items
Prisms
Mementos
Seeds
Mirajewels

The editor only modifies existing save structures and does not resize inventory blocks.

Experimental Features
Champion Medals

Champion Medal editing is included using known save flags.

Notes:

Sora is intentionally excluded.
Some medals may use additional hidden progression flags.
Always keep backups before editing.
Mirage Compendium

The Compendium editor currently works using:

internal save IDs
Mirage Manual ordering
seen/caught flags

Important:

Some late-game Maxima entries appear to use hidden/internal rows.
A few special Mirages may not align perfectly yet.
Compendium editing should be considered experimental.
Requirements
Python 3.10+
Decrypted Nintendo Switch save data
Save dumped using:
JKSV
Checkpoint
Usage
1. Back Up Your Save

Always create a clean JKSV backup before editing.

Example:

JKSV/WOFF/BackupName/
    gamedata
    progress.dat
    meta
2. Edit ONLY gamedata

Do NOT edit ZIP archives directly.

Open only:

gamedata

inside the editor.

3. Run the Editor
python woff_switch_final_named_compendium.py
4. Save Changes

Save the modified file as:

gamedata

Then replace the original gamedata inside your JKSV backup folder.

5. Restore the Save

Use JKSV or Checkpoint to restore the edited save back to the Switch.

Warnings
Keep Backups

Some save regions are still being researched.

Always keep:

an untouched original backup
a second working backup

before experimenting.

Atmosphere / Edizon Cheats

Some cheats can crash the game or prevent booting entirely.

Particularly risky:

Save Anywhere cheats
story/event flag cheats
teleport cheats
unsupported pointer cheats

Inventory editing through the save editor is significantly safer than live memory editing.

Current Research Notes

The save contains:

separate inventory blocks
compendium structures
bitflag-based unlock systems
hidden/internal Mirage entries

Late Maxima entries such as:

Shiva-Ixion
Garland
Mel

appear to behave differently from standard Mirages.

Credits

Research and testing performed using:

Nintendo Switch save analysis
Cheat Engine pointer research
JKSV save testing
community Mirage lists and compendium references

Special thanks to:

the World of Final Fantasy community
Mirage Manual documentation contributors
save structure researchers
