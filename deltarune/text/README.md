This is the source code for the Deltarune Text Dump.

- `lang.json` contains the raw strings extracted from the source code, much like `lang_ja.json` from the game files (but with a slightly different structure).

- `extract_textdump.py` in combination with Undertale Mod Tool's output generates `lang.json`.

- `render_textdump.py` turns it into HTML and organizes it, outputting `rendered.json`. This is the most fiddly part of the system.

- `sourcemap.json` maps messages to the line of source code where they appear. It tries to match https://code.deltarune.wiki/ but the details depend on the Deltarune version and possibly the UTMT version so there may be differences.

Issues and pull requests are welcome!

### Licenses

SVG icons from https://commons.wikimedia.org/wiki/File:Bootstrap_link-45deg.svg and https://commons.wikimedia.org/wiki/File:Bootstrap_file-earmark-code.svg.

Copyright © (c) 2019-2023 The Bootstrap authors

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

The Software is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the Software or the use or other dealings in the Software.
