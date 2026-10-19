/* Slice 5: choosing which characters to ask about, and which wrong answers to
 * offer.
 *
 * This is the densest duplicated logic in the project: quiz.html builds the
 * session (lines 172-198) and the four question kinds (lines 224-310), and each
 * kind carries a rule that another page repeats or half-repeats:
 *   - reading options must have distinct readings,
 *   - meaning options must not share the hun (집/堂/室 all gloss "집"),
 *   - homophone needs a reading group of at least three,
 *   - a word distractor must not be another spelling of the same Korean word
 *     (구류 = 拘留 and 句留).
 * The four rules live here; the pages keep only the HTML.
 */
const test = require("node:test");
const assert = require("node:assert/strict");

const HanjaCore = require("../hanja-core.js");
const fakes = require("./fakes.js");

/* 12 filler characters plus two spellings of the same Korean word, so every
 * cap, every distinct-reading rule and the word rule have room to be exercised. */
const FILLER = "龍國人山火水木金土日月川石田";

function wide() {
  const base = fakes.data();
  const extra = [];
  for (let i = 0; i < 12; i++) {
    extra.push({
      c: FILLER[i],
      r: "음" + i,
      h: "뜻" + i,
      lv: 1,
      idx: 100 + i,
      lesson: 0,
      lessonPos: i,
      eng: "filler " + i,
      words: [{ ko: "말" + i, hj: "漢" + i, gl: "filler word", b: "x" }],
    });
  }
  extra.push({ c: "拘", r: "구", h: "잡을", lv: 1, words: [{ ko: "구류", hj: "拘留", gl: "detention", b: "x" }] });
  extra.push({ c: "句", r: "구", h: "글귀", lv: 1, words: [{ ko: "구류", hj: "句留", gl: "detention", b: "x" }] });
  return { total: base.hanja.length + extra.length, levels: base.levels, hanja: base.hanja.concat(extra) };
}

function core(store, clock, rand) {
  return HanjaCore.create({ data: wide(), store, clock, rand });
}

function big() {
  return HanjaCore.create({ data: wide(), store: fakes.store(), clock: fakes.clock(20000) });
}

test("a review session hands back the due characters", () => {
  const session = big().quiz.session({ srs: true });
  assert.equal(session.length, 18);
  assert.equal(new Set(session.map((h) => h.c)).size, 18, "no character is asked twice");
});

test("a review session asks the characters with no history first", () => {
  const store = fakes.store({ hanjasrs: { 家: { b: 0, d: 19990, l: 1 } } });
  const core = HanjaCore.create({ data: wide(), store, clock: fakes.clock(20000) });

  const session = core.quiz.session({ srs: true });
  assert.equal(new Set(session.map((h) => h.c)).size, session.length);
  assert.equal(session[session.length - 1].c, "家", "an overdue scheduled character waits behind the new ones");
});

test("a review session grows a short list to ten when the pool allows", () => {
  const schedule = {};
  /* six characters parked until tomorrow, so the other twelve are due */
  wide()
    .hanja.slice(0, 6)
    .forEach((h) => {
      schedule[h.c] = { b: 1, d: 20001, l: 0 };
    });
  const store = fakes.store({ hanjasrs: schedule });
  const core = HanjaCore.create({ data: wide(), store, clock: fakes.clock(20000) });

  const session = core.quiz.session({ srs: true, n: 3 });
  assert.equal(session.length, 10, "a beginner sees at least ten questions");
  assert.equal(new Set(session.map((h) => h.c)).size, 10);
});

test("a random session takes n characters or twenty, deterministically", () => {
  const one = HanjaCore.create({ data: wide(), store: fakes.store(), clock: fakes.clock(20000), rand: fakes.rand([0.1, 0.7, 0.3]) }).quiz.session({});
  const two = HanjaCore.create({ data: wide(), store: fakes.store(), clock: fakes.clock(20000), rand: fakes.rand([0.1, 0.7, 0.3]) }).quiz.session({});
  assert.equal(one.length, 18, "the default is twenty, capped by the pool");
  assert.deepEqual(one.map((h) => h.c), two.map((h) => h.c), "the same randomness repeats");
  assert.equal(big().quiz.session({ n: 5 }).length, 5);
});

test("a session can be limited to one level", () => {
  const session = big().quiz.session({ lv: 0, n: 10 });
  assert.ok(session.every((h) => h.lv === 0));
  assert.equal(session.length, 3, "only three characters sit in level 0");
});

test("reading questions offer distinct readings and one answer", () => {
  const question = big().quiz.question(big().chars.byChar("家"), "reading");
  assert.equal(question.mode, "reading");
  assert.equal(question.prompt.glyph, "家");
  assert.equal(question.options.length, 4);
  assert.equal(question.options.filter((option) => option.correct).length, 1);
  assert.equal(question.options.find((option) => option.correct).label, "가");

  const labels = question.options.map((option) => option.label);
  assert.equal(new Set(labels).size, labels.length, "readings are never repeated");
  assert.ok(!labels.filter((label) => label !== "가").includes("가"), "a wrong answer is never also right");
});

test("meaning questions avoid the trap of two characters sharing a hun", () => {
  const question = big().quiz.question(big().chars.byChar("家"), "meaning");
  const labels = question.options.map((option) => option.label);
  assert.equal(new Set(labels).size, labels.length);
  assert.ok(!labels.filter((label) => label !== "집").includes("집"));
  assert.equal(question.options.find((option) => option.correct).char.c, "家");
});

test("homophone questions pick a reading shared by at least three characters", () => {
  const question = big().quiz.question(big().chars.byChar("家"), "homophone");
  assert.equal(question.mode, "homophone");
  assert.equal(question.options.length, 3, "가 has three characters");
  assert.ok(question.options.every((option) => option.char.r === "가"));
  assert.equal(question.options.filter((option) => option.correct).length, 1);
  assert.equal(question.prompt.reading, "read 가");
  assert.ok(question.prompt.glyph === "", "the prompt shows the meaning, not the glyph");
});

test("homophone falls back to distinct readings when no group is big enough", () => {
  /* three characters with three different readings: no reading reaches three */
  const narrow = {
    levels: fakes.data().levels,
    hanja: [
      { c: "學", r: "학", h: "배울", lv: 1, words: [{ ko: "학교", hj: "學校", gl: "school", b: "x" }] },
      { c: "家", r: "가", h: "집", lv: 0, words: [{ ko: "가족", hj: "家族", gl: "family", b: "x" }] },
      { c: "龍", r: "용", h: "용", lv: 1, words: [{ ko: "용", hj: "龍", gl: "dragon", b: "x" }] },
    ],
  };
  const core = HanjaCore.create({ data: narrow, store: fakes.store(), clock: fakes.clock(20000) });
  const question = core.quiz.question(core.chars.byChar("學"), "homophone");

  assert.equal(question.prompt.reading, "read 학");
  assert.equal(question.options.filter((option) => option.correct).length, 1);
  const wrong = question.options.filter((option) => !option.correct).map((option) => option.char.r);
  assert.ok(wrong.every((reading) => reading !== "학"), "no wrong answer may share the reading");
});

test("word questions exclude another spelling of the same Korean word", () => {
  const question = big().quiz.question(big().chars.byChar("拘"), "word");
  assert.equal(question.mode, "word");
  assert.equal(question.prompt.reading, "구류");
  assert.equal(question.options.find((option) => option.correct).label, "拘留");
  assert.ok(!question.options.some((option) => option.label === "句留"), "句留 is also 구류, so it cannot be a distractor");
  assert.equal(question.word.hj, "拘留");
});

test("word questions fall back to a character that has an example when needed", () => {
  const question = big().quiz.question(big().chars.byChar("學"), "word");
  assert.ok(question.word, "a word is always shown");
  assert.ok(question.options.find((option) => option.correct).label);
});
