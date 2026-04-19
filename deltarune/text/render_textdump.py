#!/usr/bin/env python3
"""Convert lang.json to the data we want to show on the page."""

import html
import io
import json
import math
import os
import re
import sys
import typing
import xml.etree.ElementTree

from dataclasses import dataclass, field

from render_data import ALT_TEXTS, FUNNYTEXT_DIMS


MAX_LINE_LEN = 33

BONUS_HEIGHTS: dict[tuple[str, str], int] = {}


def render(text: str | None, msgid: str, lang: str) -> str | None:
    if not text:
        return None
    if text in ("/*", "/＊") and "shop" in msgid:
        # Dummy message that shows up in shops if murder == 1.
        # murder is always 0. A carryover from Undertale's murder route
        # where it's used to blank out the sidebar.
        # The shop code has been getting copy/pasted ever since...
        return None
    if msgid.startswith("scr_quiztext_slash_scr_quiztext_gml_"):
        # These trigger smaller text.
        text = text.lstrip("~")

    # TODO: I think the first is English and the second Japanese,
    # extract as such?
    if msgid == "obj_ch2_keyboardpuzzle_controller_slash_Create_0_gml_38_0":
        assert text == "GIAEEFSBISSFLBALAELRHEIGSFFEBRSI"
        text = "GIAEEFSB\nISSFLBAL\nAELRHEIG\nSFFEBRSI"
    if msgid == "obj_ch2_keyboardpuzzle_controller_slash_Create_0_gml_56_0":
        assert text == "UPIOMAOIOTSUGNINMGUSIFIOPEKIFUSIORATEGUI"
        text = "UPIOMAOIOT\nSUGNINMGUS\nIFIOPEKIFU\nSIORATEGUI"

    # ASCII control characters that presumably don't do anything
    if lang == "en" and msgid == "obj_cutscene_test_slash_Step_0_gml_51_0":
        text = text.replace("\u0016", "")
    if lang == "en" and msgid == "obj_pipis_enemy_slash_Step_0_gml_97_0":
        text = text.replace("\u000c", "")

    if msgid == "scr_weaponinfo_slash_scr_weaponinfo_gml_352_0" and lang == "ja":
        # Unused description that's missing a line wrap.
        # I'm just guessing about a better place to wrap.
        assert (
            text
            == "ポジティブで前向きなイメージの#カラフルなマフラー。#"
            + "クリティカルダメージを受けたときに獲得するTPが増える。"
        )
        text = (
            "ポジティブで前向きなイメージの#カラフルなマフラー。#"
            + "クリティカルダメージを受けた#ときに獲得するTPが増える。"
        )
    if msgid == "scr_armorinfo_slash_scr_armorinfo_gml_568_0" and lang == "en":
        # Similar case.
        assert (
            text
            == "A lodestone token inscribed with the record of#a legend athlete. Enemy bullets give a bit more TP."
        )
        text = "A lodestone token inscribed with the record of#a legend athlete. Enemy bullets give a bit#more TP."

    if msgid == "scr_quiztext_slash_scr_quiztext_gml_547_0" and lang == "ja":
        # Long message, seemingly displayed using smaller text, but I'll
        # insert an arbitrary line break.
        assert text == "教会にも行かずにずっと見てるテレビしか見ないテレビがすべて"
        text = "教会にも行かずにずっと見てる\nテレビしか見ないテレビがすべて"

    out = io.StringIO()
    color = "W"
    i = 0
    linelen = 0

    def wrapline():
        nonlocal out, linelen
        if "rhythmgame" in msgid:
            return
        if (
            linelen > MAX_LINE_LEN
            and "\n" not in text
            and (
                "#" not in text
                or msgid.startswith(
                    (
                        "obj_readable_room1",
                        "obj_npc_room_animated_slash_Other_10_gml_41_0",
                        "obj_npc_room_animated_slash_Other_10_gml_57_0",
                    )
                )
                or "`#" in text
            )
            and not out.getvalue().endswith((" ", "\u3000"))
        ):
            *head, tail = out.getvalue().rsplit("\n", 1)
            if "\u3000" in tail:
                tail, tailtail = tail.rsplit("\u3000", 1)
            elif " " in tail:
                i = len(tail) - 1
                intag = False
                while i >= 0:
                    match tail[i]:
                        case ">":
                            intag = True
                        case "<":
                            intag = False
                        case " " if not intag:
                            tail, tailtail = tail[:i], tail[i + 1 :]
                            break
                    i -= 1
                else:
                    assert False, "no split found"
            elif lang == "ja":
                return
            else:
                assert msgid in [
                    "obj_ch2_keyboardpuzzle_controller_slash_Create_0_gml_56_0",
                    "obj_lancerboss3_slash_Step_0_gml_258_0",
                    "obj_shop_ch2_spamton_slash_Draw_0_gml_737_0",
                ]
                return
            if tail == "*":
                assert "obj_musical_controller" in msgid or msgid in [
                    "obj_lancerboss3_slash_Step_0_gml_258_0"
                ]
                return
            new = (head[0] + "\n" if head else "") + tail

            hardwrap = msgid in [
                # We want to unwrap messages at >=800px.
                # These are the only ones that don't fit.
                "scr_recruit_info_slash_scr_recruit_info_gml_434_0_b",
                "scr_recruit_info_slash_scr_recruit_info_gml_449_0",
                "scr_recruit_info_slash_scr_recruit_info_gml_465_0",
                "scr_recruit_info_slash_scr_recruit_info_gml_481_0",
                "scr_recruit_info_slash_scr_recruit_info_gml_512_0",
                "scr_recruit_info_slash_scr_recruit_info_gml_528_0",
                "scr_recruit_info_slash_scr_recruit_info_gml_544_0",
                "obj_shop1_slash_Draw_0_gml_414_0",
                "obj_shop2_slash_Draw_0_gml_372_0",
                "obj_poppup_enemy_slash_Step_0_gml_494_0",
                "obj_shop_ch2_spamton_slash_Draw_0_gml_719_0",
                "obj_shop_ch2_spamton_slash_Draw_0_gml_720_0",
                "scr_text_slash_scr_text_gml_10220_0",
                "obj_dw_church_waterfalltearoom_slash_Step_0_gml_920_0",
                "obj_shop1_slash_Draw_0_gml_479_0_b",
                # This one has a 2D layout that relies on hardwrapping.
                "obj_ch3_PGS01F_slash_Step_0_gml_325_0",
            ]

            if not hardwrap:
                new += '<span class="break">'
            new += "\n"
            if new.startswith("* "):
                new += "  "
                linelen = 2
            else:
                linelen = 0
            if not hardwrap:
                new += "</span>"
            new += tailtail
            linelen += len(re.sub("<[^>]*>", "", tailtail)) + sum(
                int(match[1]) / 8 for match in re.finditer(r'width="([0-9]+)', tailtail)
            )
            out = io.StringIO(new)
            out.seek(0, 2)

    while i < len(text):
        wrapline()
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
                    case "O":
                        file, x_off, y_off = images[n][msgid][text[i + 2]][lang == "ja"]
                        path = f"img/{file}.gif"
                        assert os.path.exists(path)
                        dims = FUNNYTEXT_DIMS[file]
                        # I don't think these are always right... but they're pretty close
                        x = x_off + dims.width // 2 - dims.origin_x
                        y = y_off + dims.height // 2 - dims.origin_y + 10
                        realheight = 18
                        if file in [
                            "spr_dw_tv_time_funnytext",
                            "spr_funnytext_win_big",
                            "spr_ja_funnytext_win_big",
                            "spr_ja_funnytext_tan",
                            "spr_funnytext_gentle",
                            "spr_ja_funnytext_gentle",
                            "spr_funnytext_alligator",
                            "spr_ja_funnytext_alligator",
                            "spr_funnytext_city_feet",
                            "spr_ja_funnytext_city_feet",
                            "spr_funnytext_game_over",
                            "spr_funnytext_tv_time",
                            "spr_funnytext_physical_challenge",
                            "spr_ja_funnytext_know_tv",
                            "spr_funnytext_special",
                            "spr_funnytext_word",
                            "spr_funnytext_challenge",
                        ]:
                            # Don't clip into the next message.
                            # Clipping into the next line of the same message is OK.
                            realheight = dims.height // 2
                            BONUS_HEIGHTS[lang, msgid] = realheight - 18
                        # I tried shaking CSS. But it wasn't random and looked bad at
                        # half size and was annoying. Not worth the page bloat.
                        out.write(
                            f'<span style="display:inline-block;height:{realheight}px;'
                            f"width:{dims.width // 2}px;overflow:visible;"
                            'vertical-align:top;">'
                            f'<img src="{path}" loading="lazy"'
                            f' style="position:relative;top:{y / 2}px;'
                            f'left:{x / 2}px"'
                            f' alt="{ALT_TEXTS[file].replace("\n", " ")}"'
                            f' width="{dims.width / 2}" height="{dims.height / 2}"/>'
                            "</span>"
                        )
                        linelen += dims.width / 16
                    case "I":
                        # TODO: interface buttons
                        out.write('<span class="picture">[IMG]</span>')
                        linelen += 5
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
                linelen += 1
            case "#" if msgid.startswith(
                (
                    "obj_readable_room1",
                    "obj_npc_room_animated_slash_Other_10_gml_41_0",
                    "obj_npc_room_animated_slash_Other_10_gml_57_0",
                )
            ):
                out.write("#")
                linelen += 1
            case "#" if msgid.startswith("obj_bloxer_enemy_slash_Step_0_gml_135_1"):
                # Becomes a space according to Bloxer footage?
                # Confusing. Maybe the game squeezes double spaces?
                out.write(" ")
                linelen += 1
            case "&" | "#" | "\n":
                out.write("\n")
                linelen = 0
            case "\t":
                out.write(" ")  # TODO
                linelen += 1
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
                linelen += 1
            case "%":
                assert text[i + 1 :] in ("", "%", "%%", "/%"), msgid + " " + text
                break
            case ">":
                out.write("&gt;")
                linelen += 1
            case "<":
                out.write("&lt;")
                linelen += 1
            case "`":
                out.write(text[i + 1] if text[i + 1] != "&" else "&amp;")
                linelen += 1
                i += 1
            case "~" if msgid in [
                "obj_watercooler_enemy_slash_Step_0_gml_266_0",
                "obj_watercooler_enemy_slash_Step_0_gml_272_0",
            ]:
                # "* You asked the watercooler, ~1water~2 they doing later."
                out.write('"')
                i += 1
            case "~" if i + 1 < len(text) and text[i + 1].isdigit():
                # Some tildes are just part of the message.
                # I think whether they're meaningful depends on the script that's called?
                # This heuristic is good enough.
                assert text[i + 1] in "12345"
                out.write(f'<span class="param">~{text[i + 1]}</span>')
                linelen += 2
                i += 1
            case "N" if msgid == "obj_dw_church_intro_guei_slash_Step_0_gml_169_0":
                # The game hardcodes this in a really bizarre way.
                out.write("Ñ")
                linelen += 1
            case char:
                out.write(char)
                linelen += 1
                if lang == "ja" and not char.isascii():
                    linelen += 0.5
        i += 1
    wrapline()
    if color != "W":
        out.write("</span>")
    rendered = out.getvalue()
    if (
        lang == "en"
        and rendered.startswith("* ")
        and "\n" in rendered
        and r"\C" not in text
    ):
        rendered = re.sub(r"\n {0,2}([^*])", "\n  \\1", rendered)
    rendered = rendered.rstrip("\n \u3000")
    return rendered or " "


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
images: dict[
    int,
    dict[str, dict[str, tuple[tuple[str, int, int], tuple[str, int, int]]]],
] = json.load(open("images.json", encoding="utf-8"))


class Message(typing.NamedTuple):
    text: str | None
    duplicate: bool
    narrowheight: int
    wideheight: int


DEDUP: dict[tuple[str, str], str | None] = {}


def wrap_msg(lang: str, key: str, text: str | None) -> Message:
    duplicate = (lang, key) in DEDUP and DEDUP[lang, key] == text
    DEDUP[lang, key] = text
    softbreaks = text.count('class="break"') if text else 0
    hardbreaks = text.count("\n") - softbreaks if text else 0
    bonus_height = BONUS_HEIGHTS.get((lang, key)) or 0
    if text:
        xml.etree.ElementTree.fromstring("<dummy>" + text + "</dummy>")
    return Message(
        text,
        duplicate,
        narrowheight=28 + 18 * (softbreaks + hardbreaks) + bonus_height,
        wideheight=28 + 18 * hardbreaks + bonus_height,
    )


rendered: dict[
    str, dict[str, dict[str, dict[typing.Literal["en", "ja"], Message]]]
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
                rendered[n][group][k] = {
                    "en": wrap_msg("en", k, ren),
                    "ja": wrap_msg("ja", k, rja),
                }

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


def dumpbin():
    @dataclass
    class StringBuf:
        cache: dict[str, tuple[int, int]] = field(default_factory=dict)
        buf: io.StringIO = field(default_factory=io.StringIO)

        def put(self, text: str | None) -> tuple[int, int]:
            if not text:
                return (0, 0)
            if text not in self.cache:
                # We could be more aggressive by also searching for superstrings.
                # But that takes very long and only saves 30KB in total.
                self.cache[text] = (self.buf.tell(), len(text))
                self.buf.write(text)
            return self.cache[text]

        def get(self) -> str:
            value = self.buf.getvalue()
            # Ensure that UTF-16 offsets (JS) match UTF-32 offsets (Python)
            assert max(map(ord, value)) <= 65535
            return value

        def check(self, w1, w2):
            m1 = 0
            m2 = 0
            for n1, n2 in self.cache.values():
                m1 = max(n1, m1)
                m2 = max(n2, m2)
            assert math.ceil(math.log(m1, 128)) == w1
            assert math.ceil(math.log(m2, 128)) == w2

    @dataclass
    class MsgMeta:
        msgid: tuple[int, int]
        en: tuple[int, int]
        ja: tuple[int, int]
        source: tuple[int, int]
        dup: int
        nh_en: int
        wh_en: int
        nh_ja: int
        wh_ja: int

    class SectionIndex(typing.TypedDict):
        meta: dict[typing.Literal["msgid", "en", "ja", "count"], int]
        groups: dict[str, dict[str, list[int]]]

    groups: dict[str, dict[str, list[int]]] = {}
    msgs: list[MsgMeta] = []
    msgidbuf = StringBuf()
    enbuf = StringBuf()
    jabuf = StringBuf()
    sourcebuf = StringBuf()

    def hidxfor(lang: typing.Literal["en", "ja", "both"], all: bool, wide: bool) -> int:
        return wide + 2 * all + 4 * ["en", "ja", "both"].index(lang)

    with open("sourcemap.json", encoding="utf8") as f:
        sourcemap: dict[str, dict[str, str]] = json.load(f)

    midx = 0
    for chap in rendered:
        groups[chap] = {}
        for group in rendered[chap]:
            startmidx = midx
            heights = [0] * 12
            for msgid in rendered[chap][group]:
                msg = rendered[chap][group][msgid]
                msgs.append(
                    MsgMeta(
                        msgidbuf.put(msgid),
                        enbuf.put(msg["en"][0]),
                        jabuf.put(msg["ja"][0]),
                        sourcebuf.put(sourcemap[chap].get(msgid)),
                        msg["en"][1] + 2 * msg["ja"][1],
                        msg["en"][2],
                        msg["en"][3],
                        msg["ja"][2],
                        msg["ja"][3],
                    )
                )
                for thislang in "en", "ja":
                    text, dup, nh, wh = msg[thislang]
                    if text:
                        heights[hidxfor(thislang, False, True)] += wh
                        heights[hidxfor(thislang, False, False)] += nh
                        heights[hidxfor("both", False, True)] += wh
                        heights[hidxfor("both", False, False)] += nh
                        if not dup:
                            heights[hidxfor(thislang, True, True)] += wh
                            heights[hidxfor(thislang, True, False)] += nh
                            heights[hidxfor("both", True, True)] += wh
                            heights[hidxfor("both", True, False)] += nh
                midx += 1
            groups[chap][group] = [startmidx, len(rendered[chap][group]), *heights]

    headerbuf = io.StringIO()

    def writenum(num: int, width: int):
        # Encode offsets as 7-bit digits (i.e. ASCII), little-endian.
        # Heights and lengths are instead encoded as UTF-8. They're
        # usually but not always <128 so this is a nice variable-width
        # encoding scheme.
        # Here's the neatest part: the JS decoder doesn't need to know
        # about this. Decoding a single ASCII value or a single code
        # unit from a UTF-16 JS string is identical.
        # This trick only makes sense because:
        # - It's rare for these values to be >=128 (UTF-8 is actually pretty
        #   inefficient for multi-byte codepoints)
        # - These values are never >=0xD800 (surrogate codepoints that can't be
        #   encoded as UTF-8, and codepoints outside the BMP that take multiple
        #   UTF-16 code units)
        # - The data is transmitted as UTF-8 but decoded from a UTF-16 string
        #   for convoluted browser reasons
        if width == 1:
            assert num < 0xD800
            headerbuf.write(chr(num))
        else:
            for _ in range(width):
                headerbuf.write(chr(num % 128))
                num //= 128
            assert not num

    for msginfo in msgs:
        writenum(msginfo.msgid[0], 3)
        writenum(msginfo.msgid[1], 1)
        writenum(msginfo.en[0], 3)
        writenum(msginfo.en[1], 1)
        writenum(msginfo.ja[0], 3)
        writenum(msginfo.ja[1], 1)
        writenum(msginfo.source[0], 3)
        writenum(msginfo.source[1], 1)
        writenum(msginfo.dup, 1)
        writenum(msginfo.nh_en, 1)
        writenum(msginfo.wh_en, 1)
        writenum(msginfo.nh_ja, 1)
        writenum(msginfo.wh_ja, 1)

    msgidbuf.check(3, 1)
    enbuf.check(3, 2)
    jabuf.check(3, 2)
    sourcebuf.check(3, 1)

    bindata = headerbuf.getvalue()
    msgiddata = msgidbuf.get()
    endata = enbuf.get()
    jadata = jabuf.get()

    assert msgiddata.isascii()

    idx: SectionIndex = {
        "meta": {
            "msgid": len(bindata),
            "en": len(bindata) + len(msgiddata),
            "ja": len(bindata) + len(msgiddata) + len(endata),
            "count": midx,
        },
        "groups": groups,
    }

    with open("groups.json.js", "w", encoding="utf8") as f:
        as_json = json.dumps(
            idx, indent=None, ensure_ascii=False, separators=(",", ":")
        )
        assert as_json.isascii()
        f.write("var groupIndex = JSON.parse('")
        f.write(as_json.replace("\\", "\\\\").replace("'", "\\'"))
        f.write("');")

    # TODO: split en and ja?
    with open("rendered.bin", "w", encoding="utf8") as f:
        f.write(bindata)
        f.write(msgiddata)
        f.write(endata)
        f.write(jadata)

    with open("sourcemap.bin", "w", encoding="utf8") as f:
        f.write(sourcebuf.get())


dumpbin()


def plainify_html(text: str) -> str:
    text = re.sub(r'<span class="break">\s*</span>', " ", text)
    text = re.sub(r'<img[^>]*alt="([^"]*)"[^>]*>', lambda match: f"[{match[1]}]", text)
    assert "\r" not in text
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
    for chap, groups in rendered.items():
        out.write(CHAPTER.replace("%", chap))
        for title, group in groups.items():
            pending_title = title.replace("_slash_", "/")
            for key, contents in group.items():
                content = contents[lang]
                if not content.text:
                    continue
                if content.duplicate:
                    continue
                if pending_title:
                    out.write("\n")
                    out.write("=" * len(pending_title))
                    out.write("\n")
                    out.write(pending_title)
                    out.write("\n")
                    out.write("=" * len(pending_title))
                    out.write("\n\n")
                    pending_title = None
                out.write(plainify_html(content.text))
                out.write("\n\n")

    return out.getvalue().strip("\n") + "\n"


with open("DELTARUNE.txt", "w", encoding="utf-8") as f:
    # CRLF for max compatibility (maybe somebody's using notepad.exe on Windows 7).
    # BOM since it seems the most portable/reliable way to indicate encoding.
    f.write("\N{BYTE ORDER MARK}" + render_plain("en").replace("\n", "\r\n"))

with open("DELTARUNE_ja.txt", "w", encoding="utf-8") as f:
    f.write("\N{BYTE ORDER MARK}" + render_plain("ja").replace("\n", "\r\n"))
