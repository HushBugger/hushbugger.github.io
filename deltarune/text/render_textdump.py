#!/usr/bin/env python3
"""Convert lang.json to the data we want to show on the page."""

import html
import io
import json
import re
import sys
import typing


def render(text: str | None, msgid: str, lang: str) -> str | None:
    if not text:
        return None
    if text in ("/*", "/＊") and "shop" in msgid:
        # Dummy message that shows up in shops if murder == 1.
        # murder is always 0. A carryover from Undertale's murder route
        # where it's used to blank out the sidebar.
        # The shop code has been getting copy/pasted ever since...
        return ""
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
            case "/" if msgid == "obj_dw_churchb_rotatingtower_slash_Create_0_gml_90_0":
                # Postfixed with "j" ("/%j"). Probably a typo.
                break
            case "/" if not msgid.startswith(
                (
                    "obj_controller_city_mice2_slash_Draw_0_gml_28_0",
                    "obj_fusionmenu_slash_Draw_0_gml_181_0",
                    "obj_overworldc_slash_Draw_0_gml_37_0",
                    "obj_overworldc_slash_Draw_0_gml_69_0",
                    "scr_armorinfo_slash_scr_armorinfo_gml_433_0_b",
                    "scr_armorinfo_slash_scr_armorinfo_gml_553_0",
                    "scr_armorinfo_slash_scr_armorinfo_gml_791_0",
                    "scr_armorinfo_slash_scr_armorinfo_gml_791_0",
                    "scr_spellinfo_slash_scr_spellinfo_gml_109_0",
                    "obj_overworldc_slash_Draw_0_gml_68_0",
                )
            ):
                assert text[i + 1 :].strip("%/~1 ") == "", msgid + " " + text
                break
            case "&" if (
                msgid.startswith(
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
                )
                and msgid
                not in [
                    "scr_monstersetup_slash_scr_monstersetup_gml_27_0",
                    "obj_fusionmenu_slash_Draw_0_gml_182_0",
                ]
                and not msgid.startswith(("obj_credits_ch4",))
            ):
                out.write("&amp;")
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
            case "%" if (
                msgid.startswith(
                    (
                        "scr_weaponinfo",
                        "scr_armorinfo",
                        "scr_iteminfo",
                        "scr_itemdesc",
                        "scr_monstersetup",
                    )
                )
                and not msgid.startswith(("scr_itemdesc_oldtype",))
                or msgid
                in [
                    "scr_text_slash_scr_text_gml_8925_0",
                    "scr_text_slash_scr_text_gml_8926_0",
                    "obj_battlecontroller_slash_Draw_0_gml_171_0",
                    "obj_battlecontroller_slash_Draw_0_gml_280_0",
                    "obj_fusionmenu_slash_Step_0_gml_144_0",
                    "obj_shop_ch2_spamton_slash_Create_0_gml_89_0",
                ]
            ):
                out.write("%")
            case "%":
                assert text[i + 1 :] in ("", "%", "%%", "/%"), msgid + " " + text
                break
            case ">":
                out.write("&gt;")
            case "<":
                out.write("&lt;")
            case "`":
                out.write(text[i + 1] if text[i + 1] != "&" else "&amp;")
                i += 1
            case "~" if i + 1 < len(text) and text[i + 1].isdigit():
                # Some tildes are just part of the message.
                # I think whether they're meaningful depends on the script that's called?
                # This heuristic is good enough.
                assert text[i + 1] in "12345"
                out.write(f'<span class="param">~{text[i + 1]}</span>')
                i += 1
            case "N" if msgid == "obj_dw_church_intro_guei_slash_Step_0_gml_169_0":
                # The game hardcodes this in a really bizarre way.
                out.write("Ñ")
            case char:
                out.write(char)
        i += 1
    if color != "W":
        out.write("</span>")
    rendered = out.getvalue()
    if (
        lang == "en"
        and rendered.startswith("* ")
        and "\n" in rendered
        and r"\C" not in text
    ):
        rendered = re.sub(r"\n *([^*])", "\n  \\1", rendered)
    rendered = rendered.rstrip("\n")
    if lang == "en" and rendered.startswith("* ") and "\n" in rendered:
        # `text-indent: each-line` would be even easier. But Blink only got
        # support in March 2026, two weeks ago as of writing. So let's wait
        # until 2027 or 2028.
        rendered = (
            '<div class="indented">'
            + rendered.replace("\n", '</div><div class="indented">')
            + "</div>"
        )
    return rendered


RE_STRETCH = re.compile(r"(\[[^\]]*\])")


def your_____long(text: str, id: str) -> str:
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
    ident = ident.replace("_DUP", "")

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

    assert ishtmlsafe(ident)

    return ident


EVENTS = [
    "PreCreate",
    "Create",
    "Draw",
    "Step",
    "KeyPress",
    "Mouse",
    "Other",
    "Alarm",
    "Destroy",
    "CleanUp",
]


def smartsort(key: str):
    pieces = key.split("_")
    for i, piece in enumerate(pieces):
        if piece.isdigit():
            # Natsort of integers (particularly line numbers)
            pieces[i] = piece.rjust(16, "0")
        if piece in EVENTS:
            # Try to order GameMaker events, e.g. Create text is usually
            # shown earlier than Alarm text
            pieces[i] = str(EVENTS.index(piece)).rjust(3, "0")

    # Further sort by the actual line order in the files
    if "gml" in pieces:
        assert pieces.count("gml") == 1
        # (using `n` here is mildly criminal, scope-wise)
        if key in sourcemap[n]:
            filename, lineno = sourcemap[n][key].split("#L")
            lineno = int(lineno)
        else:
            filename = "zzzzzz"
            lineno = 9999999
        # obj_npc_room_slash_Other_10_gml_1189_0 fits better at the end, not the start
        filename = filename.replace("room_animated_other", "room_other_animated")
        pieces.insert(pieces.index("gml") + 1, str(lineno).rjust(10, "0"))
        # Some translation keys that indicate the same file belong to different files
        # e.g. DEVICE_MENU_slash_Create_0_gml_107_0 and DEVICE_MENU_slash_Create_0_gml_17_0
        # are on similar lines in different files and we don't want them together
        pieces.insert(pieces.index("gml") + 1, filename)

    return pieces


def ishtmlsafe(text: str) -> bool:
    return not any(c in text for c in "\"'<>&")


lang: dict[str, dict[typing.Literal["en", "ja"], dict[str, str]]] = json.load(
    open("lang.json", encoding="utf-8")
)
sourcemap: dict[str, dict[str, str]] = json.load(
    open("sourcemap.json", encoding="utf-8")
)
rendered: dict[
    str, dict[str, dict[str, dict[typing.Literal["en", "ja"], str | None]]]
] = {}
for n in lang:
    rendered[n] = {}
    ks = sorted(lang[n]["en"].keys() | lang[n]["ja"].keys(), key=smartsort)
    for k in ks:
        assert ishtmlsafe(k)
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
                ren = your_____long(ren, k)
            if (ren and ren.strip()) or (rja and rja.strip()):
                rendered[n].setdefault(group, {})
                rendered[n][group][k] = {"en": ren, "ja": rja}

# Mainly for reference in the git diff.
# Easier for other programs to ingest than the JS file below.
with open("rendered.json", "w", encoding="utf-8") as f:
    json.dump(rendered, f, indent=0, ensure_ascii=False)

# https://v8.dev/blog/cost-of-javascript-2019#json
# TL;DR: JSON parsed from a string literal is faster than an object literal.
# This saves ~60ms in the node.js CLI on my laptop.
with open("rendered.json.js", "w", encoding="utf-8") as f:
    as_json = json.dumps(
        rendered, indent=None, ensure_ascii=False, separators=(",", ":")
    )
    f.write("var rendered = JSON.parse('")
    f.write(as_json.replace("\\", "\\\\").replace("'", "\\'"))
    f.write("');")


def plainify_html(text: str) -> str:
    text = text.replace('</div><div class="indented">', "\n")
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return text


# This renders poorly on mobile devices...
# It's OK if this and the chapter headers look like shit but
# let's not do box characters beyond that.
HEADER = """
 ▄██████████████████████████████████████████████████████▄
██▀                                                    ▀██
██    █     █  █   ▄                       ███ █ █ ███  ██
██  ███ ███ █ ███ █♥︎█ █▀█ █ ██ ████ ███     █   █   █   ██
██  ███ █▄▄ █  █  █▀█ █   ████ ██ █ █▄▄  ▄  █  █ █  █   ██
██                                                      ██
██            unofficial deltarune text dump            ██
██                                                      ██
▀██▄   https://hushbugger.github.io/deltarune/text/   ▄██▀
  ▀██▄                                              ▄██▀
    ▀████████████████████████████████████████████████▀


"""

CHAPTER = """

▀▀██▄▄▄▄ ● ▄▄▄▄██▀▀
   ▲ CHAPTER % ▲
         ▼

"""


def render_plain(lang: typing.Literal["en", "ja"]) -> str:
    # duplicated logic from index.html
    out = io.StringIO()
    out.write(HEADER)
    dedup = {}
    for chap, groups in rendered.items():
        out.write(CHAPTER.replace("%", chap))
        for title, group in groups.items():
            pending_title = title.replace("_slash_", "/")
            for key, contents in group.items():
                content = contents[lang]
                if not content:
                    continue
                if dedup.get(key) == content:
                    continue
                dedup[key] = content
                if pending_title:
                    out.write("\n")
                    out.write("=" * len(pending_title))
                    out.write("\n")
                    out.write(pending_title)
                    out.write("\n")
                    out.write("=" * len(pending_title))
                    out.write("\n\n")
                    pending_title = None
                out.write(plainify_html(content))
                out.write("\n\n")

    return out.getvalue().strip("\n") + "\n"


with open("DELTARUNE.txt", "w", encoding="utf-8") as f:
    # CRLF for max compatibility (maybe somebody's using notepad.exe on Windows 7).
    # BOM since it seems the most portable/reliable way to indicate encoding.
    f.write("\N{BYTE ORDER MARK}" + render_plain("en").replace("\n", "\r\n"))

with open("DELTARUNE_ja.txt", "w", encoding="utf-8") as f:
    f.write("\N{BYTE ORDER MARK}" + render_plain("ja").replace("\n", "\r\n"))
