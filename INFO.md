# World of Final Fantasy Maxima Switch Save Research Notes

## Save Structure

The save contains multiple independent blocks including:

- Battle items
- Key/misc items
- Prism inventory
- Seeds
- Mirajewels
- Champion Medal flags
- Mirage Compendium structures

The editor modifies existing save structures only and does not resize inventory blocks.

---

## Stable Editing Areas

The following sections have proven stable during testing:

- Gil
- Battle items
- Key items
- Misc items
- Prisms
- Mementos
- Seeds
- Mirajewels

These edits are significantly safer than live memory editing.

---

## Experimental Areas

### Champion Medals

Champion Medals are handled through save flags.

Notes:
- Sora is intentionally excluded.
- Some medals may require additional hidden progression flags.
- Use backups before editing.

---

### Mirage Compendium

The Compendium editor currently uses:

- internal save IDs
- Mirage Manual ordering
- seen/caught flags

Some late-game Maxima entries appear to use hidden/internal rows.

Known problematic/special entries may include:

- Shiva-Ixion
- Garland
- Mel

A hidden/internal placeholder row also appears to exist near the late Maxima entries.

---

## Save Handling

Recommended workflow:

```text
JKSV backup
    ↓
Edit ONLY gamedata
    ↓
Restore with JKSV
```

Do NOT edit ZIP archives directly.

---

## Atmosphere / Edizon Notes

Certain cheats can prevent the game from booting.

Particularly risky:

- Save Anywhere cheats
- event flag cheats
- teleport cheats
- unsupported pointer cheats

Inventory editing through the save editor is generally much safer.

---

## Technical Notes

Current known save regions:

```text
Battle items:      0x87A91E0
Compendium:        0x87ABED8
```

Champion Medals appear to use bitflag-based save data.

The Mirage Compendium appears to use:

- internal Mirage IDs
- seen/caught flags
- hidden/internal rows for some Maxima entries
- Mirage Manual ordering for most standard entries

Late-game Maxima entries may not follow the normal row structure exactly.

---

## License

MIT License
