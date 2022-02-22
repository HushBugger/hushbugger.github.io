#!/usr/bin/env python3
import argparse, json, os, re, readline

from xml.etree import ElementTree as ET

START_MARK = '<?xml version="1.0" encoding="utf-8"?>\n<TranslationTable_XML'
END_MARK = "</TranslationTable_XML>"

parser = argparse.ArgumentParser()
parser.add_argument(
    "file",
    nargs="?",
    default=os.path.expanduser(
        "~/.steam/debian-installation/steamapps/common/"
        "Outer Wilds/OuterWilds_Data/resources.assets"
    ),
)
args = parser.parse_args()

with open(args.file, errors="surrogateescape") as f:
    text = f.read()

start = 0
langs = ["es", "en", "tr", "pt", "it", "fr", "pl", "ko", "cn", "de", "ru", "jp"]
docs = []
while True:
    start = text.find(START_MARK, start + 1)
    if start == -1:
        break
    end = text.find(END_MARK, start) + len(END_MARK)
    docs.append(ET.fromstring(text[start:end]))

translations = {
    lang: [
        (
            entry.find("key").text.strip(),
            (entry.find("value").text or entry.find("key").text)
            .strip()
            .replace("\\\\n", "\n"),
        )
        for entry in [
            *doc.iterfind("entry"),
            *doc.find("table_shipLog").iterfind("TranslationTableEntry"),
            *doc.find("table_ui").iterfind("TranslationTableEntryUI"),
        ]
    ]
    for lang, doc in zip(langs, docs, strict=True)
}

entries = translations["en"]

with open("labels.json") as f:
    old = json.load(f)

labels = {}
need_update = False
try:
    cur = None
    for i, (key, value) in enumerate(entries):
        if existing := old.get(key):
            labels[key] = existing
            continue
        print()
        print(key)
        print(value)
        guess = cur
        if ":" in value:
            label, *_ = value.split(":")
            if label.isalpha() and label.isupper():
                guess = label.title()
        print()
        inp = input(f"({guess}) > ") or guess
        if inp == "/":
            assert guess
            labels[key] = guess + "/Me"
        else:
            labels[key] = inp
            cur = inp
        need_update = True
        print(f"{i + 1}/{len(entries)}")
finally:
    if need_update:
        os.rename("labels.json", "labels.json.bak")
        with open("labels.json", "w") as f:
            json.dump(labels, f, indent=0)

# Future-proofing, IDs will stay consistent if text is added/removed in future
with open("keymap.json") as f:
    keymap = json.load(f)
top = max(keymap.values(), default=0)
need_update = False
for key, value in entries:
    if key not in keymap:
        top += 1
        keymap[key] = top
        need_update = True
if need_update:
    with open("keymap.json", "w") as f:
        json.dump(keymap, f, indent=0)


def write_json(name, obj):
    with open(f"{name}.js", "w") as f:
        f.write(f"var {name} = ")
        json.dump(obj, f, indent=0)
        f.write(";\n")


TAGS = {
    "color=red": '<span class="red">',
    "color=lightblue": '<span class="lightblue">',
    "color=orange": '<span class="orange">',
    "color=grey": '<span class="grey">',
    "color=black": "<span>",
    "/color": "</span>",
    "i": "<em>",
    "/i": "</em>",
    "b": "<strong>",
    "/b": "</strong>",
    "/size": "</span>",
    "Pause/": "",
    "pause": "",
    "Pause": "",
    "Pause /": "",
    "Pause=1": "",
    "Pause=2": "",
    "Pause=3": "",
    "Pause=0.5": "",
    "NbTimeloops": '<span class="template">&lt;NbTimeloops&gt;</span>',
    "FirstLoop": '<span class="template">&lt;FirstLoop&gt;</span>',
    "MinutesSinceRedGiant": '<span class="template">&lt;MinutesSinceRedGiant&gt;</span>',
    "SecondsSinceRedGiant": '<span class="template">&lt;SecondsSinceRedGiant&gt;</span>',
    "MinutesToRedGiant": '<span class="template">&lt;MinutesToRedGiant&gt;</span>',
    "SecondsToRedGiant": '<span class="template">&lt;SecondsToRedGiant&gt;</span>',
    "RemainingMinutes": '<span class="template">&lt;RemainingMinutes&gt;</span>',
    "RemainingSeconds": '<span class="template">&lt;RemainingSeconds&gt;</span>',
    "TimeMinutes": '<span class="template">&lt;TimeMinutes&gt;</span>',
    "TimeSeconds": '<span class="template">&lt;TimeSeconds&gt;</span>',
    "TimeMinutesRemaining": '<span class="template">&lt;TimeMinutesRemaining&gt;</span>',
    "Profile Name": '<span class="template">&lt;Profile Name&gt;</span>',
    "!": "",  # Some kind of beep?
}


def clean_message(message):
    it = iter(re.split("<([^>]*)>", message))
    clean = next(it)
    while True:
        try:
            tag = next(it)
        except StopIteration:
            break
        if tag.startswith("size="):
            if int(tag.removeprefix("size=")) < 35:
                clean += '<span class="small">'
            else:
                clean += '<span class="big">'
        elif tag.startswith("color=\n"):
            clean += "<span>"
        else:
            clean += TAGS[tag]
        clean += next(it)
    clean = "<br>".join(map(str.strip, clean.split("\n")))
    return clean


for lang, entries in translations.items():
    if lang != "en":
        continue
    doc = {}
    for k, v in entries:
        author = label = labels[k]
        if "/" in label:
            author, label = label.split("/")
        if ";" in author:
            author, _ = author.split(";")
        if ";" in label:
            label, _ = label.split(";")
        val = [clean_message(v), author]
        if label != author:
            val.append(label)
        doc[keymap[k]] = val
    write_json(f"lang_{lang}", doc)
