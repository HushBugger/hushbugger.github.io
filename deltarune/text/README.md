This is the source code for the Deltarune Text Dump.

- `lang.json` contains the raw strings extracted from the source code, much like `lang_ja.json` from the game files (but with a slightly different structure).

- `extract_textdump.py` in combination with Undertale Mod Tool's `UMT_DUMP_ALL` command generates `lang.json`.

- `render_textdump.py` turns it into HTML and organizes it, outputting `rendered.json`. This is the most fiddly part of the system.

- `sourcemap.json` maps messages to the line of source code where they appear. This can change depending on Deltarune version and UTMT version so it's not guaranteed to match up exactly. (It's used by the text dump's `c` hotkey, which has very poor UX.)

Issues and pull requests are welcome!
