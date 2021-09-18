#!/usr/bin/env python3
import json
import sys

from collections import defaultdict

d = defaultdict(list)
for k, v in json.load(open(sys.argv[1])).items():
    k = k.split('_slash_')[0]
    if k.startswith(('scr_', 'obj_')):
        k = k[4:]
    k = k.replace('_', ' ')
    k = k.strip()
    d[k].append(v)

with open('textdump.js', 'w') as f:
    f.write('var d = ')
    json.dump(d, f)
    f.write(';')
