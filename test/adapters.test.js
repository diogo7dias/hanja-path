/* Slice 6: the browser side of the ports.
 *
 * Everything the core refuses to know about — localStorage, fetch, the clock,
 * Math.random, speechSynthesis — arrives here as a small adapter. The adapter
 * takes its dependencies as arguments, so this file is also testable in bare
 * Node with a fake localStorage and a fake fetch.
 */
const test = require("node:test");
const assert = require("node:assert/strict");

const HanjaAdapters = require("../hanja-adapters.js");

function memory(seed) {
  const values = Object.assign({}, seed);
  return {
    getItem(key) {
      return Object.prototype.hasOwnProperty.call(values, key) ? values[key] : null;
    },
    setItem(key, value) {
      values[key] = String(value);
    },
    removeItem(key) {
      delete values[key];
    },
  };
}

test("the store round-trips values as JSON", () => {
  const ports = HanjaAdapters.create({ storage: memory() });
  assert.equal(ports.store.get("missing"), null);
  assert.equal(ports.store.set("hanjaprogress", { 家: "mastered" }), true);
  assert.deepEqual(ports.store.get("hanjaprogress"), { 家: "mastered" });
});

test("the store turns corrupt JSON into nothing, not an exception", () => {
  const ports = HanjaAdapters.create({ storage: memory({ hanjaprogress: "{oops" }) });
  assert.equal(ports.store.get("hanjaprogress"), null);
});

test("the store survives storage that refuses everything", () => {
  const blocked = {
    getItem() {
      throw new Error("blocked");
    },
    setItem() {
      throw new Error("quota");
    },
  };
  const ports = HanjaAdapters.create({ storage: blocked });
  assert.equal(ports.store.get("hanjaprogress"), null);
  assert.equal(ports.store.set("hanjaprogress", {}), false, "the page is told the write failed");
});

test("the store works with no storage at all", () => {
  const ports = HanjaAdapters.create({});
  assert.equal(ports.store.get("hanjaprogress"), null);
  assert.equal(ports.store.set("hanjaprogress", {}), false);
});

test("the clock counts whole days since the epoch", () => {
  const ports = HanjaAdapters.create({});
  assert.equal(ports.clock.today(), Math.floor(Date.now() / 86400000));
  assert.ok(Math.abs(ports.clock.now() - Date.now()) < 1000);
});

test("the randomness stays inside the unit interval", () => {
  const ports = HanjaAdapters.create({});
  for (let i = 0; i < 20; i++) {
    const value = ports.rand.float();
    assert.ok(value >= 0 && value < 1, `out of range: ${value}`);
  }
});

test("stroke data is fetched once per character", async () => {
  let calls = 0;
  const ports = HanjaAdapters.create({
    fetch(url) {
      calls += 1;
      assert.equal(url, "strokes/%E5%AE%B6.json");
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ strokes: [[[0, 0]]], medians: [[0, 0]] }) });
    },
  });

  const first = await ports.strokes.get("家");
  const second = await ports.strokes.get("家");
  assert.equal(calls, 1, "the second call came from the cache");
  assert.deepEqual(first, second);
  assert.deepEqual(first.strokes, [[[0, 0]]]);
});

test("stroke data that is missing, malformed or late resolves to nothing", async () => {
  const missing = HanjaAdapters.create({ fetch: () => Promise.resolve({ ok: false, status: 404 }) });
  assert.equal(await missing.strokes.get("家"), null);

  const malformed = HanjaAdapters.create({ fetch: () => Promise.resolve({ ok: true, json: () => Promise.resolve({ strokes: [] }) }) });
  assert.equal(await malformed.strokes.get("龍"), null);

  const broken = HanjaAdapters.create({ fetch: () => Promise.reject(new Error("offline")) });
  assert.equal(await broken.strokes.get("街"), null);

  const late = HanjaAdapters.create({ fetch: () => new Promise(() => {}), timeoutMs: 5 });
  assert.equal(await late.strokes.get("佳"), null, "a hanging fetch gives up");
});

test("speech speaks Korean and picks a Korean voice when one exists", () => {
  const spoken = [];
  const voices = [{ lang: "en-US", name: "Sam" }, { lang: "ko-KR", name: "Yuna" }];
  function Utterance(text) {
    this.text = text;
  }
  const ports = HanjaAdapters.create({
    synth: {
      cancel() {},
      speak(utterance) {
        spoken.push(utterance);
      },
      getVoices() {
        return voices;
      },
    },
    Utterance,
  });

  ports.speech.speak("가족");
  assert.equal(spoken.length, 1);
  assert.equal(spoken[0].text, "가족");
  assert.equal(spoken[0].lang, "ko-KR");
  assert.equal(spoken[0].rate, 0.9);
  assert.equal(spoken[0].voice.name, "Yuna");
});

test("speech stays silent when the browser has none, and on empty text", () => {
  const silent = HanjaAdapters.create({});
  assert.doesNotThrow(() => silent.speech.speak("家"));
  assert.doesNotThrow(() => silent.speech.speak(""));

  const spoken = [];
  const noisy = HanjaAdapters.create({
    synth: {
      cancel() {},
      speak(utterance) {
        spoken.push(utterance);
      },
      getVoices() {
        return [];
      },
    },
    Utterance: function Utterance(text) {
      this.text = text;
    },
  });
  noisy.speech.speak("");
  assert.equal(spoken.length, 0, "nothing to say, nothing said");
});

test("every adapter plugs straight into the core", () => {
  const storage = memory();
  const ports = HanjaAdapters.create({ storage, rand: undefined });
  const core = require("../hanja-core.js").create(Object.assign({ data: { levels: [], hanja: [{ c: "家", r: "가", h: "집", lv: 0 }] } }, ports));

  assert.equal(core.learn.toggleMastered("家"), true);
  assert.equal(core.learn.isMastered("家"), true);
  core.learn.record("家", true);
  assert.equal(core.learn.streak().n, 1, "the first answer starts the streak");
  assert.deepEqual(storage.getItem("hanjaprogress"), JSON.stringify({ 家: "mastered" }));
});
