/* Slice 3: reading the query string, with the page defaults in one place.

Six pages parse the query string by hand (lessons.html:78, lesson.html:85,
study.html:131, quiz.html:127, reading.html:85, level.html:91), including the
rules that "?l" is 0 for the lesson pages but -1 for the quiz, and that a
non-numeric value means "use the default".
*/
const test = require("node:test");
const assert = require("node:assert/strict");

const HanjaCore = require("../hanja-core.js");
const fakes = require("./fakes.js");

const url = HanjaCore.create({ data: fakes.data(), store: fakes.store() }).url;

test("an integer keeps zero and negative values", () => {
  assert.equal(url.int("?l=1&lesson=2", "l", 0), 1);
  assert.equal(url.int("?l=0", "l", 5), 0);
  assert.equal(url.int("?l=-1", "l", 0), -1, "the quiz uses -1 for every level");
});

test("a missing or unusable integer falls back", () => {
  assert.equal(url.int("", "l", 0), 0);
  assert.equal(url.int("?", "l", 0), 0);
  assert.equal(url.int("?l=", "l", 0), 0);
  assert.equal(url.int("?l=abc", "l", 0), 0);
  assert.equal(url.int(undefined, "l", -1), -1);
  assert.equal(url.int("?l=2.7", "l", 0), 2);
});

test("text returns the raw value and an empty string by default", () => {
  assert.equal(url.text("?han=%E5%AE%B6", "han", ""), "家");
  assert.equal(url.text("?r=", "r", ""), "");
  assert.equal(url.text("?other=1", "r", ""), "");
});

test("a flag is true only for the value 1", () => {
  assert.equal(url.flag("?srs=1", "srs"), true);
  assert.equal(url.flag("?srs=0", "srs"), false);
  assert.equal(url.flag("?srs=yes", "srs"), false);
  assert.equal(url.flag("", "srs"), false);
});
