/* Fakes for the core's ports. Plain objects, so the tests run in bare Node. */

/* in-memory storage port: get(key) -> parsed value or null, set(key, value) -> void */
function store(seed) {
  const values = Object.assign({}, seed || {});
  return {
    get(key) {
      return key in values ? values[key] : null;
    },
    set(key, value) {
      values[key] = value;
    },
    /* test helper: what is actually stored right now */
    raw() {
      return Object.assign({}, values);
    },
  };
}

/* settable clock port */
function clock(day) {
  let current = day === undefined ? 20000 : day;
  return {
    today() {
      return current;
    },
    now() {
      return current * 86400000;
    },
    advance(days) {
      current += days;
      return current;
    },
    set(value) {
      current = value;
    },
  };
}

/* scripted randomness: repeats the queued values, then zeroes */
function rand(values) {
  const queue = (values || []).slice();
  return {
    float() {
      return queue.length ? queue.shift() : 0;
    },
  };
}

/* tiny dataset: 家 佳 街 share the reading 가, so homophone questions exist */
function data() {
  const records = [
    { c: "家", r: "가", h: "집", lv: 0, idx: 0, lesson: 0, lessonPos: 0, eng: "house",
      words: [{ ko: "가족", hj: "家族", gl: "family", b: "집(家) + 겨레(族)" }],
      s: { ko: "가족.", en: "Family.", w: "가족" }, tip: "집 안에 돼지" },
    { c: "佳", r: "가", h: "아름다울", lv: 0, idx: 1, lesson: 0, lessonPos: 1, eng: "beautiful",
      words: [{ ko: "가작", hj: "佳作", gl: "fine work", b: "아름다울(佳)" }] },
    { c: "街", r: "가", h: "거리", lv: 0, idx: 2, lesson: 0, lessonPos: 2, eng: "street",
      words: [{ ko: "가로", hj: "街路", gl: "street", b: "거리(街)" }] },
    { c: "學", r: "학", h: "배울", lv: 1, idx: 3, lesson: 0, lessonPos: 0, eng: "study",
      words: [{ ko: "학교", hj: "學校", gl: "school", b: "배울(學)" }] },
  ];
  return {
    total: records.length,
    levels: [
      { id: 0, ko: "초급", en: "Beginner", n: 3 },
      { id: 1, ko: "중급", en: "Intermediate", n: 1 },
    ],
    hanja: records,
  };
}

module.exports = { store, clock, rand, data };
