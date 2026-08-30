#!/usr/bin/env python3
import json, re, collections

with open("mockups/_src/wikitext.json", encoding="utf-8") as f:
    data = json.load(f)
wt = data["parse"]["wikitext"]["*"]
lines = wt.split("\n")

entries = []
cur_reading = None
cell_idx = 0
TIER = ["J", "G"]  # 중학교, 고등학교

ENTRY = re.compile(r"\[\[[\s\u200b]*([\u4e00-\u9fff]+?)[\s\u200b]*\]\][\s\u200b]*<small>\(([^)]*)\)</small>")
INNER = re.compile(r"\[\[([^|\]]+)(?:\|([^\]]+))?\]\][\s\u200b]*([\uac00-\ud7af]+)")
HANGUL = re.compile(r"([\uac00-\ud7af]+)")

for line in lines:
    s = line.strip()
    if s == "|}" or s.startswith("|-"):
        cur_reading = None
        cell_idx = 0
        continue
    if s.startswith("|}"):
        continue
    m = re.match(r"^!\s+([^\[]+)$", s)
    if m and not s.startswith("! width"):
        cur_reading = m.group(1).strip()
        cell_idx = 0
        continue
    # cell line: "|" or "| ..." 
    if s == "|" or s.startswith("| "):
        if cur_reading is None:
            continue
        if cell_idx >= 2:
            cell_idx = 0
        tier = TIER[cell_idx]
        cell_idx += 1  # advance even for empty cells
        for mm in ENTRY.finditer(s):
            char = mm.group(1)
            inner = mm.group(2)
            im = INNER.match(inner)
            if im:
                disp = im.group(2) or im.group(1)
                reading = im.group(3)
                hun = disp.strip()
            else:
                hm = HANGUL.search(inner)
                if not hm:
                    continue
                reading = hm.group(1)
                hun = reading
            if not reading:
                continue
            entries.append({"c": char, "r": reading, "h": hun, "t": tier})

print("total entries:", len(entries))
tier_counts = collections.Counter(e["t"] for e in entries)
print("tier counts:", tier_counts)
chars = [e["c"] for e in entries]
dup = {c: n for c, n in collections.Counter(chars).items() if n > 1}
print("duplicate chars:", dup)
# check 交, 德 present
for want in ["交","德","藥","義","愛","山","日","月","人","家","學","國"]:
    print(want, any(e["c"]==want for e in entries))