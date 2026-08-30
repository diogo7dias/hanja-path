"""Build mockups/_src/words.json — a per-hanja word bank.

Sources (real words, all containing hanja whose every character is in the
education set):
  - Kengdic (surface / hanja / English gloss)  -> everyday vocab + English gloss
  - h2h KRV Bible corpus (hanja compounds)      -> covers chars Kengdic misses
Walks both corpora, indexes each character, and writes an ordered candidate
word list per education hanja. gen.py consumes this to render the 3 example
columns on every study page.
"""
import csv, json, re, collections

ED = "/Users/diogomoreira/Downloads/freebuff/hanja-practice/mockups/hanja-data.js"
KENG = "/tmp/kengdic.tsv"
BIBLE = "/tmp/bible.tsv"
UNIHAN_VAR = "/tmp/var2canon.json"

VAR = json.load(open(UNIHAN_VAR, encoding="utf-8"))


def canon(s):
    """Rewrite variant/simplified hanja chars to their education-set form when known."""
    if not s:
        return s
    return "".join(VAR.get(c, c) for c in s)
OUT = "/Users/diogomoreira/Downloads/freebuff/hanja-practice/mockups/_src/words.json"

# education set + reading map
txt = open(ED, encoding="utf-8").read()
D = json.loads(txt[txt.index("{"):txt.rindex("}") + 1])
educ = {r["c"]: r for r in D["hanja"]}

HJ = re.compile(r"[\u4e00-\u9fff]+")
HZ = re.compile(r"[\uac00-\ud7af]")


def syll(s):
    return "".join(HZ.findall(s))


def normchars(hj):
    return "".join(canon(x) for x in hj)


def add(idx, c, ko, hj, gl):
    if not ko or not hj:
        return
    hj = normchars(hj)
    chars = [x for x in hj if "\u4e00" <= x <= "\u9fff"]
    if not chars or len(chars) > 5:
        return
    if not all(x in educ for x in chars):
        return
    for ch in set(chars):
        lst = idx[ch]
        if any(w["hj"] == hj for w in lst):
            continue
        lst.append({"ko": ko, "hj": hj, "gl": gl})


idx = collections.defaultdict(list)

# --- Kengdic ---
n_k = 0
for r in csv.DictReader(open(KENG, encoding="utf-8"), delimiter="\t"):
    hj = (r["hanja"] or "").replace(" ", "").replace("\u3000", "")
    if not hj:
        continue
    ko = r["surface"].replace(" ", "")
    chars = [x for x in hj if "\u4e00" <= x <= "\u9fff"]
    if not (1 <= len(chars) <= 5):
        continue
    if syll(ko) and len(syll(ko).split()) and len(HZ.findall(ko)) != len(chars):
        continue  # surface syllable count must match hanja length
    gl = (r["gloss"] or "").strip()
    gl = re.split(r"[;\n]", gl)[0].strip()
    add(idx, None, ko, hj, gl)  # c unused
    n_k += 1
print("kengdic indexed:", n_k)

# --- Bible compounds (fallback, no English) ---
n_b = 0
hangul_of = {c: educ[c]["r"] for c in educ}
for line in open(BIBLE, encoding="utf-8"):
    if "\t" not in line:
        continue
    han = line.rstrip("\n").split("\t")[-1]
    for m in HJ.finditer(han):
        w = m.group(0)
        if not (2 <= len(w) <= 4):
            continue
        if not all(c in educ for c in w):
            continue
        try:
            ko = "".join(hangul_of[c] for c in w)
        except KeyError:
            continue
        add(idx, None, ko, w, "")
        n_b += 1
print("bible compounds:", n_b)

# --- es133lolo word CSVs (hangul, hanja, Korean meaning) ---
import csv as _csv
for path, cols, enc in [
    ("/tmp/es_Homophones.csv", (0, 1, 2), "cp949"),
    ("/tmp/es_Synonyms.csv", (0, 1, 2), "cp949"),
    ("/tmp/es_Antonyms.csv", (2, 1, None), "cp949"),
    ("/tmp/es_Four-character_Idioms.csv", (0, 1, 2), "cp949"),
]:
    try:
        fh = open(path, encoding=enc)
        reader = _csv.reader(fh)
        header = next(reader, None)
        idxmax = max(c for c in cols if c is not None)
        for row in reader:
            if len(row) <= idxmax:
                continue
            ko, hj, kdef = row[cols[0]].strip(), row[cols[1]].strip(), row[cols[2]].strip() if cols[2] is not None else ""
            ko = "".join(HZ.findall(ko))
            if not ko or not hj:
                continue
            add(idx, None, ko, hj, kdef)
    except FileNotFoundError:
        pass

word_bank = {c: idx[c] for c in educ}
json.dump(word_bank, open(OUT, "w", encoding="utf-8"),
          ensure_ascii=False, separators=(",", ":"))

# coverage report
cov = {c: v for c, v in word_bank.items()}
overall = sum(1 for c in educ if len(cov[c]) >= 3)
print("education chars:", len(educ))
print("chars with >=3 real candidate words:", overall, f"({overall/len(educ)*100:.1f}%)")
for lvname, lo, hi in [("lv0", 0, 600), ("lv1", 600, 1200), ("lv2", 1200, 1795)]:
    recs = [r for r in D["hanja"] if 0 <= r.get("lv", 0) and False][:0]
short = sorted(c for c in educ if len(cov[c]) < 3)
print("chars with <3 words:", len(short))
print("".join(short))
print("wrote", OUT)