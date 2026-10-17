/* Slice 4: asking the dataset questions, instead of each page filtering itself.

level.html, reading.html, lessons.html, lesson.html and quiz.html all walk the
1795-record array with their own filters, their own group-by-reading and their
own search predicate (level.html:112-122).
*/
const test = require("node:test");
const assert = require("node:assert/strict");

const HanjaCore = require("../hanja-core.js");
const fakes = require("./fakes.js");

function chars() {
  return HanjaCore.create({ data: fakes.data(), store: fakes.store() }).chars;
}

test("list filters by level, lesson, reading and character", () => {
  const list = chars().list;
  assert.deepEqual(list({ lv: 0 }).map((h) => h.c), ["家", "佳", "街"]);
  assert.deepEqual(list({ lv: 1 }).map((h) => h.c), ["學"]);
  assert.deepEqual(list({ lv: 0, lesson: 0 }).map((h) => h.c), ["家", "佳", "街"]);
  assert.deepEqual(list({ reading: "학" }).map((h) => h.c), ["學"]);
  assert.deepEqual(list({ char: "街" }).map((h) => h.c), ["街"]);
  assert.deepEqual(list({ lv: 99 }), []);
});

test("list with no filter returns the whole set, as a copy", () => {
  const all = chars().list({});
  assert.equal(all.length, 4);
  all.pop();
  assert.equal(chars().list({}).length, 4, "the dataset itself is untouched");
});

test("byChar finds one character and admits when it cannot", () => {
  assert.equal(chars().byChar("家").r, "가");
  assert.equal(chars().byChar("龍"), null);
});

test("group buckets characters by any key, in dataset order", () => {
  const buckets = chars().group(chars().list({}), (h) => h.r);
  assert.deepEqual(Object.keys(buckets), ["가", "학"]);
  assert.deepEqual(buckets["가"].map((h) => h.c), ["家", "佳", "街"]);
});

test("readings groups homophones and puts the biggest group first", () => {
  const groups = chars().readings(chars().list({}));
  assert.deepEqual(groups.map((group) => group.r), ["가", "학"]);
  assert.equal(groups[0].n, 3);
  assert.deepEqual(groups[0].chars.map((h) => h.c), ["家", "佳", "街"]);
  assert.equal(groups[1].n, 1);
});

test("query matches the glyph, the reading, the hun, the gloss and example words", () => {
  const list = chars().list;
  assert.deepEqual(list({ query: "家" }).map((h) => h.c), ["家"]);
  assert.deepEqual(list({ query: "학" }).map((h) => h.c), ["學"]);
  assert.deepEqual(list({ query: "거리" }).map((h) => h.c), ["街"], "hun");
  assert.deepEqual(list({ query: "house" }).map((h) => h.c), ["家"], "English gloss");
  assert.deepEqual(list({ query: "가족" }).map((h) => h.c), ["家"], "example word");
  assert.deepEqual(list({ query: "家族" }).map((h) => h.c), ["家"], "example word in hanja");
  assert.deepEqual(list({ query: "" }), [], "an empty query matches nothing");
});

test("levels returns the level metadata the pills and titles render", () => {
  assert.deepEqual(chars().levels().map((level) => level.en), ["Beginner", "Intermediate"]);
});
