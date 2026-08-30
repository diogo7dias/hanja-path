#!/usr/bin/env python3
"""Build mockups/hanja-data.js from the authentic education hanja.

- Parses the ko.wiktionary wikitext (saved in _src/wikitext.json).
- Partitions all chars into 3 levels (beginner / intermediate / advanced).
- Merges a curated core (rich mnemonics, 3 words, sentences, English) with a
  curated word bank that is inverted so every component hanja of a word also
  surfaces that word. Breakdown lines ("사귈 교 + 바꿀 환") are built from the
  real 훈음 parsed from the dataset.
"""
import json, re, collections

SRC = "mockups/_src/wikitext.json"
OUT = "mockups/hanja-data.js"

# ---------------- 1. parse ----------------
def parse():
    data = json.load(open(SRC, encoding="utf-8"))
    wt = data["parse"]["wikitext"]["*"]
    lines = wt.split("\n")
    entries = []
    cur_reading = None
    cell_idx = 0
    TIER = ["J", "G"]
    ENTRY = re.compile(r"\[\[[\s\u200b]*([\u4e00-\u9fff]+?)[\s\u200b]*\]\][\s\u200b]*<small>\(([^)]*)\)</small>")
    INNER = re.compile(r"\[\[([^|\]]+)(?:\|([^\]]+))?\]\][\s\u200b]*([\uac00-\ud7af]+)")
    HANGUL = re.compile(r"([\uac00-\ud7af]+)")
    for line in lines:
        s = line.strip()
        if s == "|}" or s.startswith("|-"):
            cur_reading = None; cell_idx = 0; continue
        m = re.match(r"^!\s+([^\[]+)$", s)
        if m and not s.startswith("! width"):
            cur_reading = m.group(1).strip(); cell_idx = 0; continue
        if s == "|" or s.startswith("| "):
            if cur_reading is None:
                continue
            if cell_idx >= 2:
                cell_idx = 0
            tier = TIER[cell_idx]
            cell_idx += 1
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
                    reading = hm.group(1); hun = reading
                if reading:
                    entries.append({"c": char, "r": reading, "h": hun, "t": tier})
    seen = set(); out = []
    for e in entries:
        if e["c"] not in seen:
            seen.add(e["c"]); out.append(e)
    return out

raw = parse()
print("parsed hanja:", len(raw))

# ---------------- 2. levels ----------------
J = [e for e in raw if e["t"] == "J"]
G = [e for e in raw if e["t"] == "G"]
ordered = J + G
for i, e in enumerate(ordered):
    e["lv"] = 0 if i < 600 else (1 if i < 1200 else 2)
lv_counts = collections.Counter(e["lv"] for e in ordered)
print("level sizes:", dict(lv_counts))

_char = {e["c"]: e for e in ordered}

# ---------------- 4b. real word bank -------------
# words.json = per-hanja candidate words mined from Kengdic + KRV Bible +
# es133lolo vocab, variant-normalized to the education set (see build_words.py).
WORDS = json.load(open("mockups/_src/words.json", encoding="utf-8"))
KOEN = json.load(open("mockups/_src/ko_english.json", encoding="utf-8"))
import english_gloss
ENMANUAL = {**english_gloss.EN, **english_gloss.EN2}
HANGUL = re.compile(r"[\uac00-\ud7af]")
RADICALS = json.load(open("mockups/_src/radicals.json", encoding="utf-8"))

# Kangxi radical names (214 radicals)
RADICAL_NAMES = {
    1:"一",2:"丨",3:"丶",4:"丿",5:"乙",6:"亅",7:"二",8:"亠",9:"人",10:"儿",
    11:"入",12:"八",13:"冂",14:"冖",15:"冫",16:"几",17:"凵",18:"刀",19:"力",20:"勹",
    21:"匕",22:"匚",23:"匸",24:"十",25:"卜",26:"卩",27:"厂",28:"厶",29:"又",30:"口",
    31:"囗",32:"土",33:"士",34:"夂",35:"夊",36:"夕",37:"大",38:"女",39:"子",40:"宀",
    41:"寸",42:"小",43:"尢",44:"尸",45:"屮",46:"山",47:"巛",48:"工",49:"己",50:"巾",
    51:"干",52:"幺",53:"广",54:"廴",55:"廾",56:"弋",57:"弓",58:"彐",59:"彡",60:"彳",
    61:"心",62:"戈",63:"戶",64:"手",65:"支",66:"攴",67:"文",68:"斗",69:"斤",70:"方",
    71:"无",72:"日",73:"曰",74:"月",75:"木",76:"欠",77:"止",78:"歹",79:"殳",80:"毋",
    81:"比",82:"毛",83:"氏",84:"气",85:"水",86:"火",87:"爪",88:"父",89:"爻",90:"爿",
    91:"片",92:"牙",93:"牛",94:"犬",95:"玄",96:"玉",97:"瓜",98:"瓦",99:"甘",100:"生",
    101:"用",102:"田",103:"疋",104:"疒",105:"癶",106:"白",107:"皮",108:"皿",109:"目",110:"矛",
    111:"矢",112:"石",113:"示",114:"禸",115:"禾",116:"穴",117:"立",118:"竹",119:"米",120:"糸",
    121:"缶",122:"网",123:"羊",124:"羽",125:"老",126:"而",127:"耒",128:"耳",129:"聿",130:"肉",
    131:"臣",132:"自",133:"至",134:"臼",135:"舌",136:"舛",137:"舟",138:"艮",139:"色",140:"艸",
    141:"虍",142:"虫",143:"血",144:"行",145:"衣",146:"襾",147:"見",148:"角",149:"言",150:"谷",
    151:"豆",152:"豕",153:"豸",154:"貝",155:"赤",156:"走",157:"足",158:"身",159:"車",160:"辛",
    161:"辰",162:"辵",163:"邑",164:"酉",165:"釆",166:"里",167:"金",168:"長",169:"門",170:"阜",
    171:"隶",172:"隹",173:"雨",174:"青",175:"非",176:"面",177:"革",178:"韋",179:"韭",180:"音",
    181:"頁",182:"風",183:"飛",184:"食",185:"首",186:"香",187:"馬",188:"骨",189:"高",190:"髟",
    191:"鬥",192:"鬯",193:"鬲",194:"鬼",195:"魚",196:"鳥",197:"鹵",198:"鹿",199:"麥",200:"麻",
    201:"黃",202:"黍",203:"黑",204:"黹",205:"黽",206:"鼎",207:"鼓",208:"鼠",209:"鼻",210:"齊",
    211:"齒",212:"龍",213:"龜",214:"龠"
}


# Hand translations for mined words whose Kengdic gloss is empty and which
# are absent from ko_english.json / english_gloss.py. Keys are the Korean word.
EN_GLOSS_FILL = {
 "반계곡경": "a winding stream-side path",
 "합곡": "the joined valleys (LI 4 acupuncture point, web between thumb and index)",
 "강군": "a strong army",
 "화랑도": "the Hwarang, the Silla elite youth corps",
 "십이륙": "one-two-six (a dice game)",
 "명동": "the resounding movement (a name/moving of a case)",
 "일모도궁": "at day's end the road ends — at the end of one's rope",
 "감개무량": "deeply moved, feelings beyond measure",
 "질박": "simple and unadorned, plain",
 "거일반삼": "infer one thing from three — to extrapolate",
 "과부적중": "the few cannot match the many",
 "멸사": "self-denial, selfless devotion",
 "당삼채": "Tang sancai, the Chinese three-color glazed pottery",
 "견아상제": "dog teeth and tiger claws interlocked — locked in stalemate",
 "골육상잔": " flesh and blood destroying each other — bitter infighting",
 "거서간": "Jusugin, the legendary first ruler of Silla",
 "급선": "the vanguard, the front line",
 "가소": "laughable, ridiculous",
 "민속복": "folk costume, traditional dress",
 "교수실": "professor's office",
 "애수": "sorrow, pathos",
 "희열감": "a feeling of joy, elation",
 "영고": "Yeonggo, the Silla winter festival with drumming",
 "관왕": "crown king, champion",
 "내우": "internal worries",
 "고위험": "high-risk",
 "고육책": "a desperate measure, a last resort",
 "궁을": "Gong and Eul (yin and yang; the famous reading on Sungnyemun Gate)",
 "내의적": "of one's inner clothing, undergarment-related",
 "보생이사": "give life and take death — a physician's power over life and death",
 "관존민비": "officials honored, people despised",
 "고종명": "a peaceful natural death (one of the five blessings)",
 "망처": "one's deceased wife",
 "소축척": "a small reduced scale (drawings/maps)",
 "충렬탑": "the Chungnyeol Tower, monument to loyal martyrs",
 "기인취물": "to deceive people and take their property",
 "건치": "healthy teeth",
 "과수댁": "a widow's house",
 "구백팔십": "nine hundred eighty",
 "건필": "vigorous brushwork, a strong pen",
 "구여현하": "speech pouring like a cascading river — eloquent",
 "국화과": "the chrysanthemum family (botany)",
 "숙환": "a chronic illness",
 "강목수생": "wood, metal, water, life (elemental phrasing)",
 "궁내": "within the palace, palace-internal",
 "경금": "Brocade-weave gold (a textile pattern)",
 "금견": "brocade silk",
 "기마전": "cavalry battle, mounted combat",
 "토진": "an earthen fortification, a field camp",
 "경루": "a scripture repository tower (sutra library)",
 "매화": "plum blossom",
 "번다": "troublesome, bothersome",
 "봉명조양": "the phoenix cries at dawn — an auspicious omen for talent rising",
 "의상점": "a clothing store",
 "검색당": "a search hall (library reference desk)",
 "손도": "a reduced escort, a token force",
 "두앙선": "the central line (through the head)",
 "앙화": "disaster, calamity",
 "당기위": "the party discipline committee",
 "방장": "one square zhang — a small room; abbot of a monastery",
 "여반장": "like turning over one's palm — effortlessly",
 "가전속": "provisional ownership, temporary affiliation",
 "공회전": "spinning one's wheels, idling in place",
 "봉접수향": "bees and butterflies follow the fragrance — suitors following beauty",
 "동자주": "a child pillar (short supporting column)",
 "망창": "vast and boundless (of sky/water)",
 "광제창생": "to broadly aid the common people",
 "경책": "a warning whip — a stern admonition",
 "자천": "to recommend oneself",
 "검검청": "the prosecutors' office",
 "무의무탁": "with nothing to rely on — destitute",
 "학무": "a crane dance",
 "분할미": "dividend rice (rice paid as division shares)",
 "채함": "to harvest salt (from salt fields)",
 "호란": "the barbarian invasions (of Joseon)",
 "일호": "one hair's breadth — the tiniest amount",
 "봉환": "to return respectfully (a title, a relic)",
 "잔월효성": "a waning moon and dawn star — lingering into the small hours",
}


def resolve_gl(wd):
    """Fill an English gloss, taking the first candidate that is pure English.
    Source order: Kengdic/NIKL keyword gloss, then hand translations."""
    gl = (wd.get("gl") or "").strip()
    if not gl or HANGUL.search(gl):
        new = None
        for cand in (KOEN.get(wd["ko"]), ENMANUAL.get(wd["ko"]), EN_GLOSS_FILL.get(wd["ko"])):
            if cand and not HANGUL.search(cand):
                new = cand
                break
        wd["gl"] = new or gl
    return wd

# A small conservative top-up of additional *real* Sino-Korean words for
# characters the corpora under-sample. gen.py drops any entry whose helper
# hanja is not itself in the education set. Commented keys intentionally
# omitted when no confident real compound exists.
SOFT_WORDS = {
 "亥": [("亥時", "亥時", "the Hour of the Boar (9–11 PM)")],
 "庚": [("庚子", "庚子", "Gengzi year"), ("庚申", "庚申", "Gengshen year")],
 "戊": [("戊戌", "戊戌", "Mushu year"), ("戊午", "戊午", "Muwu year")],
 "巳": [("巳時", "巳時", "the Hour of the Snake (9–11 AM)"), ("癸巳", "癸巳", "Gyesa year")],
 "卯": [("卯時", "卯時", "the Hour of the Rabbit (5–7 AM)"), ("點卯", "點卯", "roll call, taking attendance")],
 "辰": [("辰時", "辰時", "the Hour of the Dragon (7–9 AM)")],
 "寅": [("寅時", "寅時", "the Hour of the Tiger (3–5 AM)"), ("甲寅", "甲寅", "Gapin year")],
 "貝": [("貨幣", "貨幣", "currency"), ("貝殼", "貝殼", "shell, seashell")],
 "豐": [("豐富", "豐富", "abundant, rich"), ("豐盛", "豐盛", "plentiful, sumptuous")],
 "產": [("產業", "產業", "industry"), ("生產", "生產", "production")],
 "産": [("産業", "産業", "industry"), ("生産", "生産", "production")],
 "梨": [("沙梨", "沙梨", "Asian pear"), ("梨園", "梨園", "pear orchard")],
 "栗": [("栗木板", "栗木板", "chestnut-wood print block"), ("栗米", "栗米", "millet")],
 "龜": [("龜鑑", "龜鑑", "model, mirror, guide"), ("龜甲", "龜甲", "tortoiseshell"), ("烏龜", "烏龜", "turtle")],
 "諒": [("諒解", "諒解", "mutual understanding"), ("諒察", "諒察", "kind consideration")],
 "謁": [("謁見", "謁見", "audience with a superior")],
 "詠": [("詠嘆", "詠嘆", "to chant, to sigh in song")],
 "豈": [("豈敢", "豈敢", "how dare I")],
 "徐": [("徐行", "徐行", "going slowly")],
 "恕": [("寬恕", "寬恕", "forgiveness, clemency")],
 "戀": [("失戀", "失戀", "heartbreak"), ("戀慕", "戀慕", "yearning affection")],
 "掛": [("掛慮", "掛慮", "worry, anxiety")],
 "屯": [("屯兵", "屯兵", "stationing troops"), ("屯所", "屯所", "garrison post")],
 "巷": [("小巷", "小巷", "small alley")],
 "庸": [("庸常", "庸常", "commonplace, ordinary")],
 "朴": [("朴氏", "朴氏", "the Park family")],
 "李": [("李朝", "李朝", "the Yi dynasty")],
 "桑": [("桑田", "桑田", "mulberry field"), ("桑樹", "桑樹", "mulberry tree")],
 "梁": [("棟梁", "棟梁", "pillar of a house — mainstay")],
 "浩": [("浩瀚", "浩瀚", "vast and boundless")],
 "滴": [("水滴", "水滴", "a drop of water"), ("點滴", "點滴", "IV drip, drop by drop")],
 "昔": [("今昔", "今昔", "the past and present"), ("昔年", "昔年", "former years")],
 "曉": [("報曉", "報曉", "the rooster crowing at dawn"), ("曉星", "曉星", "the morning star")],
 "矢": [("飛矢", "飛矢", "a flying arrow")],
 "禾": [("禾本科", "禾本科", "the grass family")],
 "稻": [("水稻", "水稻", "paddy rice"), ("稻作", "稻作", "rice farming")],
 "粟": [("白粟", "白粟", "white millet")],
 "繫": [("繫屬", "繫屬", "to belong to, be attached")],
 "聰": [("聰慧", "聰慧", "bright, intelligent")],
 "肖": [("肖像", "肖像", "portrait"), ("不肖", "不肖", "unworthy")],
 "腰": [("腰刀", "腰刀", "waist sword")],
 "芳": [("芬芳", "芬芳", "fragrance")],
 "蔬": [("蔬菜", "蔬菜", "vegetables")],
 "芽": [("發芽", "發芽", "to sprout, germination"), ("萌芽", "萌芽", "bud, incipient stage")],
 "苗": [("禾苗", "禾苗", "rice seedling")],
 "茂": [("繁茂", "繁茂", "lush, thriving")],
 "涯": [("天涯", "天涯", "the far ends of the earth")],
 "淺": [("深淺", "深淺", "depth")],
 "敦": [("敦厚", "敦厚", "honest and kind"), ("敦睦", "敦睦", "cordial, fostering good ties")],
 "斯": [("斯文", "斯文", "the cultured way")],
 "那": [("那落迦", "那落迦", "Naraka, the Buddhist hell")],
 "浦": [("港浦", "港浦", "harbor"), ("浦邊", "浦邊", "waterside")],
 "鴻": [("飛鴻", "飛鴻", "a wild goose in flight")],
 "雁": [("雁行", "雁行", "a line of wild geese")],
 "厥": [("厥初", "厥初", "in the very beginning")],
 "乎": [("斷乎", "斷乎", "resolutely")],
 "矣": [("已矣", "已矣", "that is all")],
 "刺": [("刺繡", "刺繡", "embroidery"), ("刺激", "刺激", "stimulus")],
 "奈": [("無可奈何", "無可奈何", "nothing can be done")],
 "屢": [("屢次", "屢次", "repeatedly"), ("屢屢", "屢屢", "time after time")],
 "嘗": [("品嘗", "品嘗", "to taste, to sample"), ("嘗味", "嘗味", "savoring the taste")],
 "娛": [("娛樂", "娛樂", "entertainment, recreation"), ("自娛", "自娛", "to amuse oneself")],
 "慙": [("慙愧", "慙愧", "ashamed, remorseful")],
}

# Hanja and source artifacts we never surface as learner examples.
SENSITIVE = set("姦淫")
BAD_GLOSS = re.compile(r"(?:^|\b)(?:nan|unknown|undefined|test|dummy)(?:\b|$)", re.I)
BAD_KO = re.compile(r"(?:으?게으르다|낭불)")
# Kengdic junk: vulgar glosses, question-mark placeholders, dash placeholders
# (e.g. "가-"/"假-"), and glosses with embedded ?? artifacts.
VULGAR_GLOSS = re.compile(r"\bbitch\b", re.I)
JUNK_GLOSS = re.compile(r"\?{2,}")
JUNK_KO = re.compile(r"-\s*$|^-\s*")


def useful_word(w):
    """Reject source artifacts and obscure/non-learner examples."""
    ko = (w.get("ko") or "").strip()
    hj = (w.get("hj") or "").strip()
    gl = (w.get("gl") or "").strip()
    if not ko or not hj or len(ko) > 8 or len(hj) > 5:
        return False
    if BAD_KO.search(ko) or BAD_GLOSS.search(gl):
        return False
    if VULGAR_GLOSS.search(gl) or JUNK_GLOSS.search(gl) or JUNK_KO.search(ko):
        return False
    if any(ch in hj for ch in SENSITIVE):
        return False
    # Compounds should have a Korean syllable for each hanja character.
    if len(re.findall(r"[\uac00-\ud7af]", ko)) != len(hj):
        return False
    return True

# ---------------- 3. curated core ----------------
CURATED = {
 "交": {"eng":"exchange, mix",
   "tip":"다리를 꼰 사람의 모습. 서로 얽히는 모든 일 — 사귀고, 얽히고, 교차하는 것.",
   "words":[("교환","交換","exchange"),("외교","外交","diplomacy"),("교류","交流","interchange")],
   "s":{"ko":"영수증 있으면 교환 가능해요.","en":"If you have the receipt, an exchange is possible.","w":"교환"}},
 "山": {"eng":"mountain",
   "tip":"세 봉우리가 하늘로 솟은 모습. 산의 뾰족한 윤곽을 그대로 재현한 그림 글자.",
   "words":[("산","山","mountain"),("산맥","山脈","mountain range"),("등산","登山","mountain climbing")],
   "s":{"ko":"주말마다 등산을 다녀요.","en":"I go mountain climbing every weekend.","w":"등산"}},
 "日": {"eng":"day, sun",
   "tip":"해의 둥근 모습에 점 하나. 태양과 하루(날)를 뜻하는 기본 그림 글자.",
   "words":[("일요일","日曜日","Sunday"),("생일","生日","birthday"),("일본","日本","Japan")],
   "s":{"ko":"오늘은 제 생일이에요.","en":"Today is my birthday.","w":"생일"}},
 "月": {"eng":"month, moon",
   "tip":"초승달을 옆으로 그린 모습. 달과 한 달(월)을 뜻하는 문자.",
   "words":[("월요일","月曜日","Monday"),("몇월","幾月","which month"),("월급","月給","monthly salary")],
   "s":{"ko":"월급 받는 날이 제일 기분 좋아요.","en":"The day I get my salary feels the best.","w":"월급"}},
 "人": {"eng":"person",
   "tip":"서 있는 사람을 옆에서 본 모습. 다리 두 개로 '사람'을 그린 가장 단순한 글자.",
   "words":[("인간","人間","human being"),("대인","大人","adult"),("사람","人","person")],
   "s":{"ko":"사람 많은 곳에서는 조심해야 해요.","en":"You should be careful in crowded places.","w":"사람"}},
 "上": {"eng":"above, up",
   "tip":"한 줄 위에 짧은 지시선. '위'의 방향을 가리키는 지시 문자.",
   "words":[("위","上","above, on"),("상품","上品","goods"),("상반기","上半期","first half of year")],
   "s":{"ko":"책상 위에 열쇠가 있어요.","en":"The key is on the desk.","w":"위"}},
 "下": {"eng":"below, down",
   "tip":"한 줄 아래에 짧은 지시선. '아래'의 방향을 나타내는 지시 문자.",
   "words":[("아래","下","below"),("하반기","下半期","second half of year"),("지하철","地下鐵","subway")],
   "s":{"ko":"지하철을 타고 회사에 가요.","en":"I go to work by subway.","w":"지하철"}},
 "木": {"eng":"tree, wood",
   "tip":"가지와 뿌리를 가진 나무 모양. 상하좌우로 뻗은 나무를 연상하면 쉽다.",
   "words":[("나무","木","tree"),("목재","木材","lumber"),("꽃나무","花木","flowering tree")],
   "s":{"ko":"공원에 큰 나무가 하나 있어요.","en":"There is a big tree in the park.","w":"나무"}},
 "家": {"eng":"house, family",
   "tip":"집 안(宀)에 돼지(豕). 고대엔 집 안에 돼지를 키웠다는 뜻에서 '집'이 되었다.",
   "words":[("가족","家族","family"),("집","家","house"),("국가","國家","nation")],
   "s":{"ko":"주말에 가족과 함께 외식을 했어요.","en":"I ate out with my family on the weekend.","w":"가족"}},
 "心": {"eng":"heart, mind",
   "tip":"심장의 모양을 그린 글자. 마음이 몸의 중심처럼, 마음·생각을 뜻한다.",
   "words":[("마음","心","heart, mind"),("심장","心臟","heart (organ)"),("관심","關心","interest")],
   "s":{"ko":"그 가수에게 관심이 많아요.","en":"I have a lot of interest in that singer.","w":"관심"}},
 "學": {"eng":"learn, study",
   "tip":"지붕 아래 아이가 지식을 배우는 모습. 어른의 가르침이 아이에게 전해지는 것.",    "words":[("학교","學校","school"),("학생","學生","student"),("학습","學習","study, learning")],
   "s":{"ko":"학교 옆 카페에서 친구를 만났어요.","en":"I met a friend at the café next to school.","w":"학교"}},
 "文": {"eng":"culture, writing",
   "tip":"가슴에 문신을 한 사람의 '무늬'에서 글·문장·문화로 뜻이 넓어졌다.",
   "words":[("문화","文化","culture"),("문자","文字","letter, character"),("한문","漢文","classical Chinese")],
   "s":{"ko":"한국 문화를 배우는 게 정말 재미있어요.","en":"Learning Korean culture is really fun.","w":"문화"}},
 "國": {"eng":"country, nation",
   "tip":"테두리(囗) 안에 창(或). 울타리를 치고 지키는 땅 = 나라.",
   "words":[("한국","韓國","Korea"),("국가","國家","nation"),("중국","中國","China")],
   "s":{"ko":"저는 한국에서 살고 있어요.","en":"I live in Korea.","w":"한국"}},
 "力": {"eng":"strength, power",
   "tip":"팔을 힘껏 뻗는 모습. 튀어나온 근육 획이 힘을 상징한다.",
   "words":[("힘","力","strength"),("노력","努力","effort"),("능력","能力","ability")],
   "s":{"ko":"꾸준한 노력이 중요해요.","en":"Steady effort is important.","w":"노력"}},
 "生": {"eng":"life, birth",
   "tip":"땅에서 새싹이 돋아나는 모습. 싹이 '살아서' 뻗는 것에서 삶·태어남을 뜻한다.",
   "words":[("생일","生日","birthday"),("학생","學生","student"),("인생","人生","life")],
   "s":{"ko":"인생의 재미는 새로운 도전에 있어요.","en":"The joy of life lies in new challenges.","w":"인생"}},
 "德": {"eng":"virtue, moral",
   "tip":"길(彳)+눈(目)+마음(心) — '바른 길을 보며 행하는 마음'이 덕.",
   "words":[("도덕","道德","morality"),("미덕","美德","virtue"),("덕","德","virtue, favor")],
   "s":{"ko":"미덕을 실천하는 사람이 되고 싶어요.","en":"I want to become someone who practices virtue.","w":"미덕"}},
 "義": {"eng":"righteousness, justice",
   "tip":"나(我)를 양(羊)처럼 올바르고 고귀하게 만드는 것. 정의·의리를 뜻한다.",    "words":[("정의","正義","justice"),("의리","義理","loyalty, duty"),("의의","意義","meaning")],
   "s":{"ko":"정의를 지키기 위해 노력했어요.","en":"I tried to uphold justice.","w":"정의"}},
 "愛": {"eng":"love",
   "tip":"한가운데 마음(心)이 있는 얼굴. 마음을 담아 아끼고 사랑하는 것.",
   "words":[("사랑","愛","love"),("애정","愛情","affection"),("애인","愛人","lover")],
   "s":{"ko":"사랑은 말보다 행동으로 보여줘요.","en":"Love is shown by action, not words.","w":"사랑"}},
 "藥": {"eng":"medicine, drug",
   "tip":"풀(艹)로 만들어 즐거움(樂)을 되찾게 하는 것 = 약.",
   "words":[("약","藥","medicine"),("약국","藥局","pharmacy"),("한약","韓藥","Korean herbal medicine")],
   "s":{"ko":"감기에 걸려서 약국에서 약을 샀어요.","en":"I caught a cold and bought medicine at the pharmacy.","w":"약국"}},
 "世": {"eng":"world, generation",
   "tip":"서른 개로 셋을 그은 모습. 오랜 세월(여러 대)이 이어지는 세상.",
   "words":[("세계","世界","world"),("세상","世上","world, society"),("세대","世代","generation")],
   "s":{"ko":"세계 여행이 제 꿈이에요.","en":"Traveling the world is my dream.","w":"세계"}},
 "法": {"eng":"law, method",
   "tip":"물(氵) 가에서 해부(去)해 알아낸 원리 = 법칙·방법.",
   "words":[("법","法","law, method"),("방법","方法","method"),("법률","法律","law (legal)")],
   "s":{"ko":"빨리 기억하는 방법을 찾았어요.","en":"I found a way to remember quickly.","w":"방법"}},
 "道": {"eng":"road, way, path",
   "tip":"길(辶) 위를 걷는 머리(首). 가야 할 길과 도(道)를 뜻하는 글자.",
   "words":[("도로","道路","road"),("지하도","地下道","underpass"),("도를","道","the Way")],
   "s":{"ko":"지하도를 건너면 역이에요.","en":"If you cross the underpass, there's the station.","w":"지하도"}},
}

# ---------------- 4. word bank ----------------
GENERIC_WORDS = [
    ("학교","學校","school"),("학생","學生","student"),("대학","大學","university large"),("학교생활","學校生活","school life"),
    ("국가","國家","nation"),("한국","韓國","Korea"),("중국","中國","China"),("일본","日本","Japan"),
    ("문화","文化","culture"),("역사","歷史","history"),("세계","世界","world"),("세상","世上","world"),
    ("시간","時間","time"),("공간","空間","space"),("의미","意味","meaning"),("인간","人間","human"),
    ("인생","人生","life"),("사랑","愛情","love"),("가족","家族","family"),("가정","家庭","home"),
    ("의사","醫師","doctor"),("병원","病院","hospital"),("약국","藥局","pharmacy"),("신문","新聞","newspaper"),
    ("사진","寫眞","photograph"),("영화","映畫","movie"),("음악","音樂","music"),("운동","運動","exercise"),
    ("요리","料理","cooking"),("여행","旅行","travel"),("휴가","休暇","vacation"),("휴일","休日","holiday"),
    ("친구","親舊","friend (cj)"),("가을","秋季","autumn"),("겨울","冬季","winter"),("봄","春季","spring"),
    ("여름","夏季","summer"),("날씨","天氣","weather"),("비행기","飛行機","airplane"),("기차","汽車","train"),
    ("지하철","地下鐵","subway"),("생활","生活","daily life"),("방","房","room"),("집","家","house"),
    ("전화","電話","telephone"),("운동","運動","exercise"),("사람","人間","person"),
    ("생일","生日","birthday"),("기억","記憶","memory"),("생각","思想","thought"),
    ("결정","決定","decision"),("행동","行動","action"),("습관","習慣","habit"),("노력","努力","effort"),
    ("성공","成功","success"),("실패","失敗","failure"),("약속","約束","promise"),("계획","計劃","plan"),
    ("목표","目標","goal"),("방법","方法","method"),("질문","質問","question"),("대답","對答","answer"),
    ("문제","問題","problem"),("해답","解答","solution"),("정답","正答","correct answer"),("시험","試驗","exam"),
    ("성적","成績","grade"),("숙제","宿題","homework"),("휴식","休息","rest"),("취미","趣味","hobby"),
    ("결혼","結婚","marriage"),("기념일","紀念日","anniversary"),("명절","名節","holiday"),
    ("건강","健康","health"),("몸","身","body"),("마음","心","mind"),("수면","睡眠","sleep"),
    ("식사","食事","meal"),("영양","營養","nutrition"),("침대","寢臺","bed"),("창문","窓門","window"),
    ("문","門","door"),("계단","階段","stairs"),("화장실","淨 所","restroom"),("주방","廚房","kitchen"),
    ("거실","居室","living room"),("교실","敎室","classroom"),("도서관","圖書館","library"),
    ("식당","食堂","restaurant"),("시장","市場","market"),("은행","銀行","bank"),
    ("경찰","警察","police"),("검사","檢事","prosecutor"),("변호사","辯護士","lawyer"),
    ("과학","科學","science"),("수학","數學","math"),("국어","國語","Korean language"),
    ("영어","英語","English"),("중국어","中國語","Chinese"),("일본어","日本語","Japanese"),
    ("한국어","韓國語","Korean"),("정치","政治","politics"),("경제","經濟","economy"),
    ("사회","社會","society"),("법률","法律","law"),("도덕","道德","morality"),("정의","正義","justice"),
    ("의리","義理","loyalty"),("애정","愛情","affection"),("매일","每日","every day"),("이번","今番","this time"),
    ("지난","昨年","last"),("내일","來日","tomorrow"),("어제","昨日","yesterday"),("오늘","今日","today"),
    ("주말","週末","weekend"),("주중","週中","weekday"),("월요일","月曜日","Monday"),("화요일","火曜日","Tuesday"),
    ("수요일","水曜日","Wednesday"),("목요일","木曜日","Thursday"),("금요일","金曜日","Friday"),
    ("토요일","土曜日","Saturday"),("일요일","日曜日","Sunday"),
    # ---- expansion ----
    ("정부","政府","government"),("국민","國民","the people"),("국회","國會","National Assembly"),("국제","國際","international"),
    ("공공","公共","public"),("공무원","公務員","public official"),("공사","工事","construction"),("사무실","事務室","office"),
    ("사업","事業","business"),("산업","産業","industry"),("상업","商業","commerce"),("공업","工業","manufacturing"),
    ("농업","農業","agriculture"),("수산물","水産物","seafood"),("공기","空氣","air"),("물질","物質","matter, substance"),
    ("정신","精神","spirit, mind"),("정서","情緖","emotion"),("감정","感情","feeling"),("기분","氣分","mood"),
    ("성격","性格","personality"),("기질","氣質","temperament"),("태도","態度","attitude"),("습성","習性","habit"),
    ("충성","忠誠","loyalty"),("신뢰","信賴","trust"),("믿음","信","belief"),("약속","約束","promise"),
    ("약속장소","約束場所","meeting place"),("휴가","休暇","vacation"),("공휴일","公休日","public holiday"),("간식","間食","snack"),
    ("아침밥","朝食","breakfast"),("점심밥","晝食","lunch"),("저녁밥","夕食","dinner"),("간장","醬","soy sauce"),
    ("된장","된醬","soybean paste"),("식빵","食麫","bread loaf"),("물컵","水杯","water glass"),("차종류","茶種類","types of tea"),
    ("책상","冊床","desk"),("의자","椅子","chair"),("옷장","衣欌","wardrobe"),("서랍","書櫃","drawer"),
    ("현관","玄關","front door"),("베란다","베란다","veranda"),("복도","複道","corridor"),("엘리베이터","엘리베이터","elevator"),
    ("가구","家具","furniture"),("침실","寢室","bedroom"),("연구실","硏究室","lab"),("강의실","講義室","lecture hall"),
    ("운동장","運動場","sports field"),("화장실","化粧室","restroom"),("대기실","待機室","waiting room"),("회의실","會議室","meeting room"),
    ("도로","道路","road"),("횡단보도","橫斷步道","crosswalk"),("버스정류장","버스停留場","bus stop"),("기차역","汽車驛","train station"),
    ("공항","空港","airport"),("터미널","터미널","terminal"),("주유소","駐油所","gas station"),("주차장","駐車場","parking lot"),
    ("신호등","信號燈","traffic light"),("교통","交通","transportation"),("사고","事故","accident"),("안전","安全","safety"),
    ("위험","危險","danger"),("구조","救助","rescue"),("구급차","救急車","ambulance"),("소방","消防","firefighting"),
    ("화재","火災","fire"),("불났다","火發","fire broke out"),("침수","浸水","flooding"),("가뭄","旱魃","drought"),
    ("홍수","洪水","flood"),("태풍","颱風","typhoon"),("지진","地震","earthquake"),("날씨정보","天氣情報","weather report"),
    ("산불","山火","forest fire"),("환경","環境","environment"),("오염","汚染","pollution"),("청소","淸掃","cleaning"),
    ("쓰레기","塵芥","trash, waste"),("재활용","再活用","recycling"),("분리수거","分離收去","waste sorting"),("에너지","에너지","energy"),
    ("절약","節約","saving"),("낭비","浪費","waste"),("경제성장","經濟成長","economic growth"),("주가","株價","stock price"),
    ("거래","去來","transaction"),("계약","契約","contract"),("보증","保證","guarantee"),("대출","貸出","loan"),
    ("저축","貯蓄","saving money"),("예금","預金","bank deposit"),("이자","利子","interest"),("세금","稅金","tax"),
    ("재산","財産","property"),("부자","富者","rich person"),("가난","家貧","poverty"),("가계","家計","household budget"),
    ("직업","職業","occupation"),("직장인","職場人","office worker"),("실업","失業","unemployment"),("취업","就業","getting a job"),
    ("퇴직","退職","retirement"),("월급","月給","monthly salary"),("보너스","報酬","bonus"),("승진","昇進","promotion"),
    ("연봉","年俸","annual salary"),("복지","福祉","welfare"),("연금","年金","pension"),("보험","保險","insurance"),
    ("면접","面接","interview"),("이력서","履歷書","resume"),("증명서","證明書","certificate"),("출근","出勤","going to work"),
    ("퇴근","退勤","leaving work"),("연장근무","延長勤務","overtime"),("잔업","殘業","overtime work"),("회의","會議","meeting"),
    ("회사사람","會社人","colleague"),("동료","同僚","colleague"),("상사","上司","superior"),("부하","部下","subordinate"),
    ("창립","創立","founding"),("설립","設立","establishment"),("조직","組織","organization"),("기관","機關","institution"),
    ("경영","經營","management"),("관리","管理","management"),("행정","行政","administration"),("법률","法律","law"),
    ("심리","心理","psychology"),("논문","論文","thesis"),("강의","講義","lecture"),("공부법","工夫法","study method"),
    ("어학","語學","language study"),("문법","文法","grammar"),("발음","發音","pronunciation"),("회화","會話","conversation"),
    ("읽기","讀記","reading"),("쓰기","書記","writing"),("듣기","聽記","listening"),("말하기","說話","speaking"),
    ("작문","作文","composition"),("번역","飜譯","translation"),("통역","通譯","interpretation"),("편지","便紙","letter"),
    ("소설","小說","novel"),("시집","詩集","poetry collection"),("동화","童話","fairy tale"),("만화","漫畵","comic"),
    ("그림책","繪本","picture book"),("매주","每週","every week"),("매년","每年","every year"),("매월","每月","every month"),
    ("이번달","今月","this month"),("지난달","昨月","last month"),("다음달","來月","next month"),("연말","年末","year end"),
    ("연초","年始","year start"),("세기","世紀","century"),("십년","十年","ten years"),("백년","百年","a hundred years"),
    ("천년","千年","a thousand years"),("만년","萬年","ten thousand years"),("현재","現在","present"),("과거","過去","past"),
    ("미래","未來","future"),("과거사","過去史","past history"),("과학기술","科學技術","science and technology"),("기술","技術","technology, skill"),
    ("진보","進步","progress"),("발전","發展","development"),("변화","變化","change"),("혁명","革命","revolution"),
    ("운명","運命","fate"),("우주","宇宙","universe"),("자연","自然","nature"),("세상","世上","world"),
    ("목숨","命","life"),("죽음","死","death"),("생명","生命","life"),("생존","生存","survival"),
    ("살아있다","生存","to be alive"),("평화","平和","peace"),("자유","自由","freedom"),("평등","平等","equality"),
    ("인권","人權","human rights"),("민주","民主","democracy"),("인류","人類","humankind"),("역사" ,"歷史","history"),
    ("전통","傳統","tradition"),("예술","藝術","art"),("종교","宗敎","religion"),("철학","哲學","philosophy"),
    ("과학자","科學者","scientist"),("사상가","思想家","thinker"),("작가","作家","writer"),("화가","畵家","painter"),
    ("조각가","彫刻家","sculptor"),("음악가","音樂家","musician"),("지휘자","指揮者","conductor"),("연주","演奏","performance"),
    ("합창","合唱","choir"),("독창","獨唱","solo singing"),("작곡","作曲","composing"),("편곡","編曲","arrangement"),
    ("춤","舞","dance"),("무대","舞臺","stage"),("공연","公演","performance"),("관객","觀客","audience"),
    ("입장권","入場券","entrance ticket"),("예약","豫約","reservation"),("좌석","座席","seat"),("주연","主演","leading role"),
    ("조연","助演","supporting role"),("감독","監督","director"),("각본","脚本","screenplay"),("장면","場面","scene"),
    ("작품","作品","work of art"),("예술가","藝術家","artist"),("명작","名作","masterpiece"),("수상","受賞","winning an award"),
    ("전시회","展示會","exhibition"),("박물관","博物館","museum"),("미술관","美術館","art museum"),("갤러리","갤러리","gallery"),
]
# Each entry in this extra bank is used as-is (ko length == hanja length), real words.
# filter to words whose hanja string contains only chars we know and length matches
GENERIC_WORDS = [g for g in GENERIC_WORDS if len(g[0]) == len(g[1])]

_inv = collections.defaultdict(list)
for ko, hj, gl in GENERIC_WORDS:
    chars = [c for c in hj if "\u4e00" <= c <= "\u9fff"]
    for c in chars:
        if c in _char:
            _inv[c].append({"ko": ko, "hj": hj, "gl": gl})

# ---------------- 5. record assembly ----------------
def breakdown(hj):
    parts = []
    for c in hj:
        if c in _char:
            parts.append(f"{_char[c]['h']}({c})")
    return " + ".join(parts)

records = []
curated_count = 0
for i, e in enumerate(ordered):
    ch = e["c"]
    rec = {"c": ch, "r": e["r"], "h": e["h"], "lv": e["lv"], "idx": i}
    rad = RADICALS.get(ch)
    if rad:
        rec["rad"] = rad
        rec["radName"] = RADICAL_NAMES.get(rad, str(rad))
    cur = CURATED.get(ch)
    if cur:
        curated_count += 1
        rec["eng"] = cur["eng"]
        rec["tip"] = cur["tip"]
        rec["words"] = []
        for ko, hj, gl in cur["words"]:
            rec["words"].append({"ko": ko, "hj": hj, "gl": gl, "b": breakdown(hj)})
        if "s" in cur:
            rec["s"] = cur["s"]
    else:
        cand = []
        seen = set()
        # SOFT_WORDS first (manually-vetted), then the mined bank
        sources = (SOFT_WORDS.get(ch, []), WORDS.get(ch, []), _inv.get(ch, []))
        for src in sources:
            for item in src:
                if isinstance(item, dict):
                    ko, hj, gl = item.get("ko"), item.get("hj"), item.get("gl", "")
                else:
                    ko, hj, gl = item
                if not hj or not ko:
                    continue
                if hj in seen:
                    continue
                hj = ''.join(cc for cc in hj if "\u4e00" <= cc <= "\u9fff")
                if not all(cc in _char for cc in hj):  # skip words whose helper hanja is foreign to the set
                    continue
                word = {"ko": ko, "hj": hj, "gl": gl, "b": breakdown(hj)}
                if not useful_word(word):
                    continue
                seen.add(hj)
                cand.append(word)
                if len(cand) >= 6:
                    break
        # Prefer common-looking short words with reliable English glosses.
        cand.sort(key=lambda w: (0 if w.get("gl") and not HANGUL.search(w["gl"]) else 1, len(w["hj"]), len(w["ko"])))
        if cand:
            rec["words"] = [resolve_gl(w) for w in cand[:3]]
    records.append(rec)

# Assign lessons: group characters into lessons of LESSON_SIZE within each level
LESSON_SIZE = 10
for lv_id in range(3):
    lv_chars = [r for r in records if r["lv"] == lv_id]
    for li, chunk_start in enumerate(range(0, len(lv_chars), LESSON_SIZE)):
        chunk = lv_chars[chunk_start:chunk_start + LESSON_SIZE]
        for pos, r in enumerate(chunk):
            r["lesson"] = li
            r["lessonPos"] = pos
print("lessons per level:", {lv: sum(1 for r in records if r["lv"]==lv and r.get("lessonPos",0)==0) for lv in range(3)})

# Build radical groups for related-characters lookup
from collections import defaultdict
_rad_groups = defaultdict(list)
for r in records:
    if "rad" in r:
        _rad_groups[r["rad"]].append(r["c"])

# Add related characters (up to 8 per character, same radical, excluding self)
for r in records:
    if "rad" in r:
        siblings = [c for c in _rad_groups[r["rad"]] if c != r["c"]]
        r["related"] = siblings[:8]

payload = {
    "total": len(records),
    "levels": [
        {"id": 0, "ko": "초급", "en": "Beginner", "n": lv_counts[0]},
        {"id": 1, "ko": "중급", "en": "Intermediate", "n": lv_counts[1]},
        {"id": 2, "ko": "고급", "en": "Advanced", "n": lv_counts[2]},
    ],
    "hanja": records,
}
js = "/* hanja-data.js — generated by _src/gen.py from the authentic education hanja. */\nwindow.HANJA = " + json.dumps(payload, ensure_ascii=False) + ";\n"
open(OUT, "w", encoding="utf-8").write(js)
print("wrote", OUT, "records:", len(records))
print("curated:", curated_count)
n_with_words = sum(1 for r in records if "words" in r)
print("with example words:", n_with_words)
print("with sentence:", sum(1 for r in records if "s" in r))
by_lv = collections.Counter(r["lv"] for r in records)
print("level sizes:", dict(by_lv))
