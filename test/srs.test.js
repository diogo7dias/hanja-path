/* Slice 2: Leitner scheduling and the daily streak, with time injected.

The pages do this with Date.now() inline (quiz.html:140-170), so none of it can
be tested and a wrong interval silently changes how often a learner sees a
character.
*/
const test = require("node:test");
const assert = require("node:assert/strict");

const HanjaCore = require("../hanja-core.js");
const fakes = require("./fakes.js");

function core(store, clock) {
  return HanjaCore.create({ data: fakes.data(), store, clock });
}

test("a correct answer moves the box one step and schedules the next day", () => {
  const store = fakes.store();
  const learn = core(store, fakes.clock(20000)).learn;

  assert.deepEqual(learn.record("家", true), { b: 1, d: 20001, l: 0 });
  assert.deepEqual(store.raw()["hanjasrs"]["家"], { b: 1, d: 20001, l: 0 });
});

test("the box stops at five, so the longest gap is thirty days", () => {
  const store = fakes.store();
  const learn = core(store, fakes.clock(20000)).learn;

  for (let i = 0; i < 6; i++) {
    learn.record("家", true);
  }
  assert.deepEqual(learn.record("家", true), { b: 5, d: 20030, l: 0 });
});

test("a wrong answer resets the box, makes it due today and counts a lapse", () => {
  const store = fakes.store();
  const learn = core(store, fakes.clock(20000)).learn;

  learn.record("家", true);
  learn.record("家", true);
  assert.deepEqual(learn.record("家", false), { b: 0, d: 20000, l: 1 });
  assert.deepEqual(learn.record("家", false), { b: 0, d: 20000, l: 2 });
});

test("new characters are due, and a schedule waits for its day", () => {
  const clock = fakes.clock(20000);
  const learn = core(fakes.store(), clock).learn;

  assert.equal(learn.dueCount({}), 4, "everything is new on the first pass");
  learn.record("家", true); // correct, so due tomorrow
  learn.record("佳", false); // wrong, so still due today

  assert.deepEqual(
    learn.dueChars({}).map((record) => record.c),
    ["佳", "街", "學"],
    "the correct answer steps out, the wrong one stays"
  );

  clock.advance(1);
  assert.equal(learn.dueCount({}), 4, "yesterday's correct answer comes back");
});

test("due counts and lists can be limited to one level", () => {
  const learn = core(fakes.store(), fakes.clock(20000)).learn;
  assert.equal(learn.dueCount({ lv: 1 }), 1);
  assert.deepEqual(learn.dueChars({ lv: 1 }).map((record) => record.c), ["學"]);
});

test("the streak counts consecutive days once each", () => {
  const clock = fakes.clock(20000);
  const learn = core(fakes.store(), clock).learn;

  learn.record("家", true);
  assert.deepEqual(learn.streak(), { n: 1, last: 20000 });

  learn.record("佳", true);
  assert.deepEqual(learn.streak(), { n: 1, last: 20000 }, "same day does not double count");

  clock.advance(1);
  learn.record("街", false);
  assert.deepEqual(learn.streak(), { n: 2, last: 20001 });

  clock.advance(2);
  learn.record("學", true);
  assert.deepEqual(learn.streak(), { n: 1, last: 20003 }, "a missed day resets");
});

test("progress can be exported and imported again", () => {
  const store = fakes.store();
  const learn = core(store, fakes.clock(20000)).learn;
  learn.toggleMastered("家");
  learn.record("佳", true);

  const backup = learn.exportProgress();
  assert.equal(typeof backup, "string");

  const restoreStore = fakes.store();
  core(restoreStore, fakes.clock(20000)).learn.importProgress(backup);

  const restored = core(restoreStore, fakes.clock(20000)).learn;
  assert.equal(restored.isMastered("家"), true);
  assert.deepEqual(store.raw()["hanjasrs"], restoreStore.raw()["hanjasrs"]);
});

test("importing rubbish leaves the learner's real data alone", () => {
  const store = fakes.store();
  const learn = core(store, fakes.clock(20000)).learn;
  learn.toggleMastered("家");

  learn.importProgress("{not json");
  assert.equal(learn.isMastered("家"), true);
});

test("an answer outside review starts the streak without scheduling anything", () => {
  const store = fakes.store();
  const learn = core(store, fakes.clock(20000)).learn;

  assert.deepEqual(learn.streak(), { n: 0, last: 0 });
  learn.touchStreak();
  assert.deepEqual(learn.streak(), { n: 1, last: 20000 });
  assert.equal(store.raw()["hanjasrs"], undefined, "the schedule is left alone");

  learn.touchStreak();
  assert.deepEqual(learn.streak(), { n: 1, last: 20000 }, "the same day counts once");
});
