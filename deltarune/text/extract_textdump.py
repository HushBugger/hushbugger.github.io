#!/usr/bin/env python3
"""Generate a lang.json for all chapters in both English and Japanese."""

import io
import json
import pathlib
import re
import subprocess
import sys

# Expected directory structure:
# ├── 1
# │   ├── CodeEntries
# │   └── lang
# │       ├── lang_en.json
# │       └── lang_ja.json
# ├── 2
# │   ├── CodeEntries
# │   └── lang
# │       (etc...)
# ├── 3
# └── 4
# Originally extracted with UnderTale Mod Tool v0.8.1.1
try:
    source = pathlib.Path(sys.argv[1])
except IndexError:
    print(f"Usage: {sys.argv[0]} path/to/deltarune", file=sys.stderr)
    sys.exit(1)


type FunArgs = list[str | None]
type FunCall = tuple[str, FunArgs]


def parse_args(text: str) -> FunArgs:
    args = []
    i = 0
    while i < len(text):
        if text[i] in (",", " "):
            i += 1
        elif text[i] == '"':
            i += 1
            arg = io.StringIO()
            while text[i] != '"':
                if text[i] == "\\":
                    i += 1
                    if text[i] == "\\":
                        arg.write("\\")
                    elif text[i] == '"':
                        arg.write('"')
                    elif text[i] == "n":
                        arg.write("\n")
                    elif text[i] == "t":
                        arg.write("\t")
                    elif text[i] == "f":
                        # 90% sure this is just a missing backslash
                        # but let's stay faithful
                        arg.write("\f")
                    else:
                        assert False, text
                    i += 1
                else:
                    arg.write(text[i])
                    i += 1
            i += 1
            args.append(arg.getvalue())
        elif text[i] == ")":
            break
        else:
            args.append(None)
            depth = 0
            while i < len(text):
                if text[i] == "(":
                    depth += 1
                elif text[i] == ")":
                    depth -= 1
                    if depth < 0:
                        break
                elif text[i] == "," and depth == 0:
                    break
                i += 1
    return args


TEXTFUNCS = [
    "stringsetloc",
    "msgsetloc",
    "msgnextloc",
    "stringsetsubloc",
    "msgsetsubloc",
    "msgnextsubloc",
    "scr_84_get_lang_string",
]
RE_TEXTFUNCS = re.compile(f"({'|'.join(TEXTFUNCS)})\\(")


def parse_line(line: str) -> list[FunCall]:
    if line.startswith("function "):
        return []
    calls: list[FunCall] = []
    for match in RE_TEXTFUNCS.finditer(line):
        func = match.group(1)
        args = parse_args(line[match.end() :])
        calls.append((func, args))
    assert calls, line
    return calls


CHAPTERS = [1, 2, 3, 4]
text = {n: {} for n in CHAPTERS}

for n in CHAPTERS:
    path = source / str(n)
    ja: dict[str, str] = json.loads((path / "lang" / "lang_ja.json").read_text())
    text[n]["ja"] = ja
    if n == 1:
        text[n]["en"] = json.loads((path / "lang" / "lang_en.json").read_text())
        continue
    en: dict[str, str] = {}
    text[n]["en"] = en

    rg = subprocess.run(
        [
            "rg",
            "--sort=path",
            "--no-filename",
            f"({'|'.join(TEXTFUNCS)})\\([^)]",
            path / "CodeEntries",
        ],
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.decode()

    for line in rg.splitlines():
        for func, args in parse_line(line):
            match func, args:
                case "scr_84_get_lang_string", [None]:
                    pass
                case "scr_84_get_lang_string", [str(arg)]:
                    en[arg] = text[1]["ja"][arg]
                case "msgsetloc", [None, r"\C2"]:
                    pass
                case "msgsetsubloc", [None, r"\TX \F0 \E~1 \Fb \T0 %", None]:
                    pass
                case (
                    ("stringsetloc", [str(trans), str(key)])
                    | ("msgsetsubloc", [_, str(trans), *_, str(key)])
                    | ("msgnextsubloc", [str(trans), *_, str(key)])
                    | ("stringsetsubloc", [str(trans), *_, str(key)])
                    | ("msgsetloc", [_, str(trans), str(key)])
                    | ("msgnextloc", [str(trans), str(key)])
                ):
                    assert ' ' not in key, repr(key)
                    en[key] = trans
                case _:
                    print(func, args, line, file=sys.stderr)
                    sys.exit(1)

with open("lang.json", "w") as f:
    json.dump(text, f, indent=0, ensure_ascii=False, sort_keys=True)
