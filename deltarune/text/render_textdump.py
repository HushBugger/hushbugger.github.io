#!/usr/bin/env python3
"""Convert lang.json to the data we want to show on the page."""

import io
import json
import re
import sys
import typing


def render(text: str | None, msgid: str, lang: str) -> str | None:
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
                            if color == "0":
                                color = "W"
                            assert color in "RBYGOASVIW", color
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
            case "&" if msgid.startswith(
                # For finding these it's useful to look for ＆ (CJK ampersand)
                # Though maybe this character isn't used consistently?
                # "obj_credits_slash_Step_0_gml_40_0" has an ASCII ampersand
                # that's probably an actual ampersand
                # Looking for "\n\n" also helps
                (
                    "scr_credit",
                    "obj_credits",
                    "scr_monstersetup",
                    "scr_monstersetup_slash_scr_monstersetup_gml_1612_0",
                    "scr_monstersetup_slash_scr_monstersetup_gml_1614_0",
                    "obj_mike_minigame_tv",
                    "obj_fusionmenu",
                    "obj_b1rocks1",
                    "scr_quiztext",
                    "obj_b3bs_lancerget_lancer",
                    "obj_shop2_slash_Create",
                )
            ) and msgid not in [
                "scr_monstersetup_slash_scr_monstersetup_gml_27_0",
                "obj_fusionmenu_slash_Draw_0_gml_182_0",
            ]:
                out.write("&")
            case "#" if msgid.startswith(
                (
                    "obj_readable_room1",
                    "obj_npc_room_animated_slash_Other_10_gml_41_0",
                    "obj_npc_room_animated_slash_Other_10_gml_57_0",
                )
            ):
                out.write("#")
            case "#" if msgid.startswith("obj_bloxer_enemy_slash_Step_0_gml_135_1"):
                # Becomes a space according to Bloxer footage?
                # Confusing. Maybe the game squeezes double spaces?
                out.write(" ")
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
    rendered = out.getvalue()
    if lang == "en" and rendered.startswith("* ") and "\n" in rendered and r"\C" not in text:
        rendered = re.sub(r"\n *([^*])", "\n  \\1", rendered)
    if lang == 'en' and rendered.startswith('* '):
        rendered = '<p class="indented">' + rendered.replace('\n', '</p><p class="indented">') + '</p>'
    return rendered


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
            + "overflow-wrap: normal; "
            + 'transform-origin: top left; display: inline-block;">'
            + text
            + "</span>"
        )

    out = "".join(pieces)
    if id.endswith("_1"):
        out = f'<span class="B">{out}</span>'
    return out


postfixes = [
    "gml",
    "Draw",
    "Step",
    "Create",
    "Other",
    "Alarm",
    "Destroy",
    "Collision",
    "slash",
]


def groupify(ident: str) -> str:
    if ident.endswith(("_b", "_c")):
        ident = ident[:-2]

    for name in [
        "obj_sneo_kristhrown_slash_Collision",
        "obj_ralseithrown_slash_Collision",
        "obj_werewire_kristhrown_slash_Collision",
        "obj_caradventure_object_slash_Collision",
        "obj_queen_kristhrown_slash_Collision",
        "obj_queen_ralseithrown_slash_Collision",
    ]:
        # Postfixed with UUIDs for some reason
        if ident.startswith(name):
            ident = name

    while True:
        rest, end = ident.rsplit("_", 1)
        if end == "" or end.isdigit() or end in postfixes:
            ident = rest
        else:
            break

    if "_slash_" in ident and len(set(ident.split("_slash_"))) == 1:
        ident = ident.split("_slash_")[0]

    return ident


def natsort(text: str):
    pieces = text.split("_")
    for i, piece in enumerate(pieces):
        if piece.isdigit():
            pieces[i] = piece.rjust(16, "0")
    return pieces


lang: dict[str, dict[typing.Literal["en", "ja"], dict[str, str]]] = json.load(
    open("lang.json", encoding="utf-8")
)
rendered = {}
for n in lang:
    rendered[n] = {}
    ks = sorted(lang[n]["en"].keys() | lang[n]["ja"].keys(), key=natsort)
    for k in ks:
        if k == "date":
            continue
        en = lang[n]["en"].get(k)
        ja = lang[n]["ja"].get(k)
        group = groupify(k)
        if (en and en.strip(" \\C234")) or (ja and ja.strip(" \\C234")):
            ren = render(en, k, "en")
            rja = render(ja, k, "ja")
            if k.startswith("scr_rhythmgame_notechart_"):
                # TODO: stretch Japanese text (different syntax, can't assume font width...)
                assert ren
                ren = youre_too_long(ren, k)
            if (ren and ren.strip()) or (rja and rja.strip()):
                rendered[n].setdefault(group, {})
                rendered[n][group][k] = {"en": ren, "ja": rja}

with open("rendered.js", "w", encoding="utf-8") as f:
    f.write("var rendered = ")
    json.dump(rendered, f, indent=0, ensure_ascii=False)
