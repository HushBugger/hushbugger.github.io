#!/usr/bin/env python3
"""Generate a lang.json for all chapters in both English and Japanese."""

import io
import json
import pathlib
import re
import subprocess
import sys
import typing

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


class RgResult(typing.NamedTuple):
    filename: str
    lineno: int
    text: str


def rg(pattern: str, path: pathlib.Path) -> typing.Iterable[RgResult]:
    output = subprocess.run(
        [
            "rg",
            "--json",
            "--sort=path",
            "--no-filename",
            "--",
            pattern,
        ],
        stdout=subprocess.PIPE,
        check=True,
        cwd=path,
    ).stdout.decode()

    for result in output.splitlines():
        result = json.loads(result)
        if result["type"] != "match":
            continue
        yield RgResult(
            filename=result["data"]["path"]["text"],
            lineno=result["data"]["line_number"],
            text=result["data"]["lines"]["text"],
        )


CHAPTERS = [1, 2, 3, 4]
text = {n: {} for n in CHAPTERS}
sourcemap = {n: {} for n in CHAPTERS}

for n in CHAPTERS:
    path = source / str(n)
    ja: dict[str, str] = json.loads((path / "lang" / "lang_ja.json").read_text())
    text[n]["ja"] = ja
    if n == 1:
        text[n]["en"] = json.loads((path / "lang" / "lang_en.json").read_text())
        for filename, lineno, line in rg(
            r"scr_84_get_lang_string\(",
            path / "CodeEntries",
        ):
            for func, args in parse_line(line):
                match func, args:
                    case "scr_84_get_lang_string", [str(arg)]:
                        sourcemap[n][arg] = f"{filename}:{lineno}"
                    case _:
                        print(func, args, line, file=sys.stderr)
                        sys.exit(1)
        continue
    en: dict[str, str] = {}
    text[n]["en"] = en

    for filename, lineno, line in rg(
        f"({'|'.join(TEXTFUNCS)})\\([^)]",
        path / "CodeEntries",
    ):
        for func, args in parse_line(line):
            match func, args:
                case "scr_84_get_lang_string", [None]:
                    pass
                case "scr_84_get_lang_string", [str(arg)]:
                    en[arg] = text[1]["ja"][arg]
                    sourcemap[n][arg] = f"{filename}:{lineno}"
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
                    assert " " not in key, repr(key)
                    en[key] = trans
                    sourcemap[n][key] = f"{filename}:{lineno}"
                case _:
                    print(func, args, line, file=sys.stderr)
                    sys.exit(1)

# Scrambled fragments. Only the Japanese translation uses a translation key.
# The Japanese translation actually has one fragment more, that's probably
# why these aren't translated normally.
text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_90_0"] = "where "
text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_91_0"] = "the "
text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_92_0"] = "tail. "
text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_93_0"] = "pointed "
text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_94_0"] = "the "
text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_95_0"] = "children "
text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_96_0"] = "would "
text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_97_0"] = "grow,"
text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_98_0"] = "the "
text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_99_0"] = "Lost "
text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_100_0"] = "forest "
text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_101_0"] = "followed "
text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_102_0"] = None

with open("lang.json", "w", encoding="utf-8") as f:
    json.dump(text, f, indent=0, ensure_ascii=False, sort_keys=True)
with open("sourcemap.json", "w", encoding="utf-8") as f:
    json.dump(sourcemap, f, indent=0, ensure_ascii=False, sort_keys=True)
