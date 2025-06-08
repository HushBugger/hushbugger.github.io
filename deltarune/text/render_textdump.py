#!/usr/bin/env python3
"""Convert lang.json to the data we want to show on the page."""

import io
import json
import re
import sys
import typing


def render(text: str | None) -> str | None:
    if not text:
        return None
    out = io.StringIO()
    color = "W"
    i = 0
    while i < len(text):
        match text[i]:
            case "\\":
                match text[i + 1]:
                    case "c":
                        prev_color = color
                        if text[i + 1] == "c":
                            color = text[i + 2]
                        if color != prev_color:
                            if prev_color != "W":
                                out.write("</span>")
                            if color != "W":
                                out.write(f'<span class="{color}">')
                    case "O" | "I":
                        # TODO: Tenna text, interface buttons
                        out.write('<span class="picture">[IMG]</span>')
                        while text[i + 3] in (" ", "\u3000"):
                            i += 1
                    case "M" | "E" | "T" | "F" | "S" | "s":
                        # Modifiers at the start of a message
                        # M = ?
                        # E = emotion?
                        # T = typer?
                        # F = face?
                        # S = sound
                        # s = different sounds?
                        pass
                    case "a":
                        # Something to do with Japanese text?
                        pass
                    case "f":
                        # Something at the end of a message?
                        pass
                    case "C":
                        # Multiple choice
                        pass
                    case "U":
                        # This shows up in just one message, no clue
                        pass
                    case "m":
                        # Sweet/Cap'n/KK faces?
                        pass
                    case ch:
                        print(ch)
                        print(text)
                        sys.exit(1)
                i += 2
            case "/":
                if i + 1 < len(text) and text[i + 1] == "*":
                    i += 1
            case "&" | "#":
                out.write("\n")
            case "\t":
                out.write(" ")  # TODO
            case "^":
                if text[i + 1].isdigit():
                    i += 1
            case "%":
                pass
            case ">":
                out.write("&gt;")
            case "<":
                out.write("&lt;")
            case "`":
                out.write(text[i + 1])
                i += 1
            case char:
                out.write(char)
        i += 1
    if color != "W":
        out.write("</span>")
    return out.getvalue()


RE_STRETCH = re.compile(r"(\[[^\]]*\])")


def youre_too_long(text: str, id: str) -> str:
    text = text.replace("-", "")
    pieces = []
    for piece in RE_STRETCH.split(text):
        if not piece.startswith("["):
            pieces.append(f'<span style="display: inline-block;">{piece}</span>')
            continue
        assert piece[-1] == "]"
        assert piece[2] == ":"
        width = int(piece[1])
        text = piece[3:-1].replace(" ", "\N{NO-BREAK SPACE}")
        pieces.append(
            f'<span style="transform: scaleX(calc({width}/{len(text)})); '
            + f"width: {width * 8}px; "
            + 'transform-origin: top left; display: inline-block;">'
            + text
            + "</span>"
        )

    out = "".join(pieces)
    if id.endswith("_1"):
        out = f'<span class="B">{out}</span>'
    return out


lang: dict[str, dict[typing.Literal["en", "ja"], dict[str, str]]] = json.load(
    open("lang.json")
)
rendered = {}
for n in lang:
    rendered[n] = {}
    ks = sorted(lang[n]["en"].keys() | lang[n]["ja"].keys())
    for k in ks:
        en = lang[n]["en"].get(k)
        ja = lang[n]["ja"].get(k)
        if (en and en.strip(" \\C234")) or (ja and ja.strip(" \\C234")):
            ren = render(en)
            rja = render(ja)
            if k.startswith("scr_rhythmgame_notechart_"):
                # TODO: stretch Japanese text (different syntax, can't assume font width...)
                assert ren
                ren = youre_too_long(ren, k)
            if (ren and ren.strip()) or (rja and rja.strip()):
                rendered[n][k] = {"en": ren, "ja": rja}

with open("rendered.js", "w") as f:
    f.write("var rendered = ")
    json.dump(rendered, f, indent=0, ensure_ascii=False, sort_keys=True)
