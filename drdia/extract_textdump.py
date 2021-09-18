#!/usr/bin/env python3
"""Generate a lang_en.json that's sorta like lang_ja.json."""

import json
import subprocess as sp

from pathlib import Path

GAME = Path.home() / ".steam/debian-installation/steamapps/common/DELTARUNEdemo"
DATA = GAME / "data.win"
LANG = GAME / "lang/lang_ja.json"

strings = {}
last = ""
for line in sp.run(
    ["strings", "-n2", DATA], check=True, capture_output=True, text=True
).stdout.split("\n"):
    strings[last] = line
    last = line

ja = json.load(LANG.open())

d = {}
for k in ja.keys():
    if k == "date":
        continue
    v = strings.get(k)
    if not v or v in ja:
        continue
    d[k] = v

with open("lang_en.js", "w") as f:
    json.dump(d, f, indent=2)
