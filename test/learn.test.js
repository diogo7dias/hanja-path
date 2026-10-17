/* Slice 1: mastery state lives behind one door and never throws.

Today every page parses hanjaprogress itself, and four of them crash to a blank
page when the stored value is corrupt or when storage is unavailable (Safari
private mode throws on write). This is the behaviour the module must own.
*/
const test = require("node:test");
const assert = require("node:assert/strict");

const HanjaCore = require("../hanja-core.js");
const fakes = require("./fakes.js");

function core(store) {
  return HanjaCore.create({ data: fakes.data(), store });
}

test("a fresh learner has nothing mastered", () => {
  assert.equal(core(fakes.store()).learn.isMastered("家"), false);
});

test("toggling reports the new state and persists it", () => {
  const store = fakes.store();
  const learn = core(store).learn;

  assert.equal(learn.toggleMastered("家"), true);
  assert.equal(learn.isMastered("家"), true);
  assert.deepEqual(store.raw()["hanjaprogress"], { "家": "mastered" });

  assert.equal(learn.toggleMastered("家"), false);
  assert.equal(learn.isMastered("家"), false);
  assert.deepEqual(store.raw()["hanjaprogress"], {});
});

test("mastery survives a new session over the same storage", () => {
  const store = fakes.store();
  core(store).learn.toggleMastered("街");
  assert.equal(core(store).learn.isMastered("街"), true);
});

test("a corrupt stored value reads as empty instead of throwing", () => {
  const store = fakes.store({ hanjaprogress: "not an object" });
  const learn = core(store).learn;
  assert.equal(learn.isMastered("家"), false);
  assert.equal(learn.masteredCount(), 0);
});

test("storage that throws on read or write never breaks the page", () => {
  const hostile = {
    get() {
      throw new Error("blocked");
    },
    set() {
      throw new Error("quota");
    },
  };
  const learn = HanjaCore.create({ data: fakes.data(), store: hostile }).learn;

  assert.equal(learn.isMastered("家"), false);
  assert.equal(learn.toggleMastered("家"), true, "the view still updates");
  assert.equal(learn.masteredCount(), 0, "nothing was persisted, so nothing is stored");
});

test("masteredCount counts only the characters it is asked about", () => {
  const store = fakes.store();
  const learn = core(store).learn;
  learn.toggleMastered("家");
  learn.toggleMastered("學");

  assert.equal(learn.masteredCount(), 2);
  assert.equal(learn.masteredCount([{ c: "家" }, { c: "佳" }]), 1);
});
