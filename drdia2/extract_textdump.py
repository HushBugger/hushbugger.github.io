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
del ja["date"]

def looks_internal(text):
    if "_" in text and not ("K_K" in text or "E_MAIL" in text):
        return True
    # This has a bunch of false positives
    # if text.isalnum() and text.islower():
    #     return True
    return False

d = {}
for k, v in strings.items():
    if k not in ja or v in ja:
        continue
    if looks_internal(v):
        print("SKIP", v)
        continue
    d[k] = v

with open("lang_en.json", "w") as f:
    json.dump(d, f, indent=2)
