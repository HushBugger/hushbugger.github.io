#!/usr/bin/env python3
"""Generate a lang.json for all chapters in both English and Japanese."""

import io
import json
import pathlib
import re
import subprocess
import sys
import typing
from dataclasses import dataclass

# Expected directory structure:
# ├── ch1
# │   ├── *.gml
# │   ├── lang_en.json
# │   └── lang_ja.json
# ├── ch2
# │   ├── *.gml
# │   └── lang_ja.json
# ├── ch3
# └── ch4
# Use https://github.com/utdrwiki/code-viewer's ExportCodeFormatted.csx script
# or the line numbers will be off.
# Extracted with UnderTale Mod Tool v0.8.4.1.
try:
    source = pathlib.Path(sys.argv[1])
except IndexError:
    print(f"Usage: {sys.argv[0]} path/to/deltarune", file=sys.stderr)
    sys.exit(1)


@dataclass(frozen=True)
class Var:
    name: str


type FunArgs = list[str | Var | None]
type FunCall = tuple[str, FunArgs]


def parse_args(text: str) -> FunArgs:
    args: FunArgs = []
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
            depth = 0
            idx_start = i
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
            arg = text[idx_start:i]
            if arg.isidentifier():
                args.append(Var(arg))
            else:
                args.append(None)
    return args


TEXTFUNCS = [
    "stringsetloc",
    "msgsetloc",
    "msgnextloc",
    "stringsetsubloc",
    "msgsetsubloc",
    "msgnextsubloc",
    "scr_84_get_lang_string",
    "scr_funnytext_init",
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
    location: str
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
            location=(
                result["data"]["path"]["text"].removesuffix(".gml").lower()
                + "#L"
                + str(result["data"]["line_number"])
            ),
            text=result["data"]["lines"]["text"],
        )


class TextImg(typing.NamedTuple):
    sprite: str
    x: int
    y: int


CHAPTERS = [1, 2, 3, 4]
text = {n: {} for n in CHAPTERS}
sourcemap: dict[int, dict[str, str]] = {n: {} for n in CHAPTERS}
images: dict[int, dict[str, dict[int, tuple[TextImg, TextImg]]]] = {
    n: {} for n in CHAPTERS
}
var_names: dict[int, dict[str, list[str]]] = {n: {} for n in CHAPTERS}

for n in CHAPTERS:
    path = source / f"ch{n}"
    ja: dict[str, str] = json.loads((path / "lang_ja.json").read_text())
    text[n]["ja"] = ja
    if n == 1:
        text[n]["en"] = json.loads((path / "lang_en.json").read_text())
        for location, line in rg(r"scr_84_get_lang_string\(", path):
            for func, args in parse_line(line):
                match func, args:
                    case "scr_84_get_lang_string", [str(arg)]:
                        # setdefault() so that the first one wins. Why?
                        # 1. Predictable ordering: if we overrid then keys would
                        #    be ordered by first match but contain last match.
                        # 2. Better results for obj_ch2_scene26_powers_combined.
                        sourcemap[n].setdefault(arg, location)
                    case _:
                        print(func, args, line, file=sys.stderr)
                        sys.exit(1)
        continue
    en: dict[str, str] = {}
    text[n]["en"] = en

    curfile = None
    curimg: dict[int, tuple[TextImg, TextImg]] = {}

    for location, line in rg(f"({'|'.join(TEXTFUNCS)})\\([^)]", path):
        if location.split("#")[0] != curfile:
            curfile = location.split("#")[0]
            curimg = {}

        for func, args in parse_line(line):
            match func, args:
                case "scr_84_get_lang_string", [Var(_)]:
                    pass
                case "scr_84_get_lang_string", [str(arg)]:
                    en[arg] = text[1]["en"][arg]
                    sourcemap[n].setdefault(arg, location)
                case "msgsetloc", [Var(_) | None, str(r"\C2")]:
                    pass
                case "msgsetsubloc", [Var(_), str(r"\TX \F0 \E~1 \Fb \T0 %"), None]:
                    pass
                case (
                    ("stringsetloc", [str(trans), *args, str(key)])
                    | ("msgsetsubloc", [_, str(trans), *args, str(key)])
                    | ("msgnextsubloc", [str(trans), *args, str(key)])
                    | ("stringsetsubloc", [str(trans), *args, str(key)])
                    | ("msgsetloc", [_, str(trans), *args, str(key)])
                    | ("msgnextloc", [str(trans), *args, str(key)])
                ):
                    assert " " not in key, repr(key)
                    # Sometimes the same key has multiple English versions.
                    # (Mostly (exclusively?) for debug stuff.)
                    while key in en and en[key] != trans:
                        key += "_DUP"
                    en[key] = trans
                    sourcemap[n].setdefault(key, location)
                    if r"\O" in trans:
                        thisimg = curimg.copy()
                        if key == "obj_ch3_GSB01_slash_Step_0_gml_191_0":
                            thisimg[4] = (
                                TextImg("spr_funnytext_lovers", 0, -10),
                                TextImg("spr_ja_funnytext_lovers", 0, -10),
                            )
                        elif key == "obj_ch3_GSB01_slash_Step_0_gml_197_0":
                            thisimg[5] = (
                                TextImg("spr_funnytext_gentle", 0, 0),
                                TextImg("spr_ja_funnytext_gentle", 0, 0),
                            )
                        images[n].setdefault(key, thisimg)

                    variables = [arg.name for arg in args if isinstance(arg, Var)]
                    if variables:
                        var_names[n].setdefault(key, variables)
                case ("scr_funnytext_init", *_):
                    if args := re.match(
                        r"^\s*scr_funnytext_init\((.*), (.*), "
                        + r'(.*), scr_84_get_sprite\("(.*)"\),'
                        + r"(.*), (.*)\);$",
                        line,
                    ):
                        sprite = str(args[4])
                        en_sprite = sprite
                        ja_sprite = sprite.replace("spr_funnytext", "spr_ja_funnytext")
                        if ja_sprite == "spr_ja_funnytext_physical_challenges":
                            ja_sprite = "spr_ja_funnytext_physical_challenge"
                        if en_sprite == "spr_ja_funnytext_daisuki":
                            en_sprite = "spr_funnytext_love"
                    elif args := re.match(
                        r"^\s*scr_funnytext_init\((.*), (.*), "
                        + r"(.*), (.*),"
                        + r"(.*), (.*)\);$",
                        line,
                    ):
                        BY_ID = {
                            "1223": "spr_funnytext_breaking_news",
                            "1272": "spr_funnytext_big",
                            "130": "spr_funnytext_over_small",
                            # "1724": "spr_funnytext_star",
                            # "4818": "spr_ja_funnytext_stars",
                            "star_text": (
                                "spr_funnytext_star",
                                "spr_ja_funnytext_stars",
                            ),
                            "1817": "spr_funnytext_stop",
                            "2843": "spr_funnytext_tv_time",
                            # "4245": "spr_dw_tv_time_funnytext",
                            "tv_time_sprite": (
                                "spr_funnytext_tv_time",
                                "spr_dw_tv_time_funnytext",
                            ),
                            "2914": "spr_funnytext_game_over",
                            "2916": "spr_funnytext_fun_loop",
                            "3055": "spr_funnytext_round",
                            # "3603": "spr_funnytext_rounds",
                            "round_sprite": (
                                "spr_funnytext_rounds",
                                "spr_funnytext_round",
                            ),
                            "4464": "spr_funnytext_round_1",
                            "4487": "spr_funnytext_bonus_round",
                            "464": "spr_funnytext_resumes",
                            "4659": "spr_funnytext_game",
                            "883": "spr_funnytext_special",
                            "923": "spr_funnytext_free",
                            "spr_funnytext_challenge": "spr_funnytext_challenge",
                        }
                        sprite = BY_ID[args[4]]

                        if isinstance(sprite, str):
                            en_sprite = ja_sprite = sprite
                        else:
                            en_sprite, ja_sprite = sprite
                    else:
                        assert False, line

                    if args[3] == "y_offset":
                        y_en, y_ja = {
                            "spr_funnytext_physical_challenge": (-10, -20),
                            "spr_funnytext_physical_challenges": (-10, -20),
                            "spr_funnytext_grand_prize": (-14, -10),
                            "spr_funnytext_star": (-10, 0),
                            "spr_funnytext_green_room": (-14, -20),
                        }[en_sprite]
                    else:
                        y_en = y_ja = int(args[3])

                    curimg[int(args[1])] = (
                        TextImg(en_sprite, int(args[2]), y_en),
                        TextImg(ja_sprite, int(args[2]), y_ja),
                    )

                case _:
                    print(func, args, repr(line), file=sys.stderr)
                    sys.exit(2)

# Scrambled fragments. Only the Japanese translation uses a translation key.
# The Japanese translation actually has one fragment more, that's probably
# why these aren't translated normally.
# FIXME: Do this in render_textdump.py instead.
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
with open("lang_meta.json", "w", encoding="utf-8") as f:
    json.dump(
        dict(images=images, var_names=var_names),
        f,
        indent=0,
        ensure_ascii=False,
        sort_keys=True,
    )

with open("sourcemap.json.js", "w", encoding="utf-8") as f:
    as_json = json.dumps(
        sourcemap, indent=None, ensure_ascii=False, separators=(",", ":")
    )
    f.write("var sourcemap = JSON.parse('")
    f.write(as_json.replace("\\", "\\\\").replace("'", "\\'"))
    f.write("');")
