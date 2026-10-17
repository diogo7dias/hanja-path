/* hanja-core.js — the study core for Hanja Path.
 *
 * One deep module: learner state, spaced repetition, dataset queries and quiz
 * rules. Every crossing to the outside world (storage, clock, randomness,
 * stroke data, speech) arrives as an injected port, so the module runs in a
 * plain browser page and in bare Node tests with fakes.
 *
 * ES5 on purpose: pages load it with a plain <script> tag and no bundler.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.HanjaCore = factory();
  }
})(this, function () {
  "use strict";

  var PROGRESS_KEY = "hanjaprogress";
  var SRS_KEY = "hanjasrs";
  var STREAK_KEY = "hanjastreak";
  var INTERVALS = [0, 1, 3, 7, 14, 30];
  var BACKUP_VERSION = 1;

  var nullStore = {
    get: function () {
      return null;
    },
    set: function () {},
  };

  /* the real clock, unless a test injects its own */
  var systemClock = {
    today: function () {
      return Math.floor(Date.now() / 86400000);
    },
    now: function () {
      return Date.now();
    },
  };

  /* A port may throw or hold anything at all. State is always an object. */
  function readObject(store, key) {
    var value;
    try {
      value = store.get(key);
    } catch (e) {
      return {};
    }
    if (!value || typeof value !== "object" || Object.prototype.toString.call(value) === "[object Array]") {
      return {};
    }
    return value;
  }

  function writeObject(store, key, value) {
    try {
      store.set(key, value);
      return true;
    } catch (e) {
      return false;
    }
  }

  function normalizeList(value) {
    return Object.prototype.toString.call(value) === "[object Array]" ? value : [];
  }

  function create(ports) {
    var store = (ports && ports.store) || nullStore;
    var data = (ports && ports.data) || { levels: [], hanja: [] };
    var clock = (ports && ports.clock) || systemClock;

    function progress() {
      return readObject(store, PROGRESS_KEY);
    }

    function schedule() {
      return readObject(store, SRS_KEY);
    }

    function streakState() {
      return readObject(store, STREAK_KEY);
    }

    function characters(filter) {
      var list = data.hanja || [];
      if (!filter || filter.lv === undefined || filter.lv === null || filter.lv < 0) {
        return list.slice();
      }
      var out = [];
      for (var i = 0; i < list.length; i++) {
        if (list[i].lv === filter.lv) {
          out.push(list[i]);
        }
      }
      return out;
    }

    function isMastered(character) {
      return progress()[character] === "mastered";
    }

    function toggleMastered(character) {
      var known = progress();
      var mastered = known[character] !== "mastered";
      if (mastered) {
        known[character] = "mastered";
      } else {
        delete known[character];
      }
      /* the view follows the intent even if the write was refused */
      writeObject(store, PROGRESS_KEY, known);
      return mastered;
    }

    function masteredCount(characters) {
      var known = progress();
      var list = arguments.length ? characters : data.hanja || [];
      var count = 0;
      for (var i = 0; i < list.length; i++) {
        if (known[list[i].c] === "mastered") {
          count++;
        }
      }
      return count;
    }

    function isDue(entry, scheduleState, day) {
      var record = scheduleState[entry.c];
      return !record || record.d <= day;
    }

    function dueChars(filter) {
      var scheduleState = schedule();
      var day = clock.today();
      var pool = characters(filter);
      var due = [];
      for (var i = 0; i < pool.length; i++) {
        if (isDue(pool[i], scheduleState, day)) {
          due.push(pool[i]);
        }
      }
      return due;
    }

    function bumpStreak() {
      var day = clock.today();
      var state = streakState();
      if (state.last === day) {
        return state;
      }
      state.n = state.last === day - 1 ? (state.n || 0) + 1 : 1;
      state.last = day;
      writeObject(store, STREAK_KEY, state);
      return state;
    }

    function record(character, correct) {
      var scheduleState = schedule();
      var day = clock.today();
      var entry = scheduleState[character];
      if (!entry) {
        entry = { b: 0, d: day, l: 0 };
      }
      if (correct) {
        entry.b = Math.min((entry.b || 0) + 1, INTERVALS.length - 1);
        entry.d = day + INTERVALS[entry.b];
      } else {
        entry.b = 0;
        entry.d = day;
        entry.l = (entry.l || 0) + 1;
      }
      scheduleState[character] = entry;
      writeObject(store, SRS_KEY, scheduleState);
      bumpStreak();
      return { b: entry.b, d: entry.d, l: entry.l };
    }

    function streak() {
      var state = streakState();
      return { n: state.n || 0, last: state.last || 0 };
    }

    function exportProgress() {
      return JSON.stringify({
        version: BACKUP_VERSION,
        progress: progress(),
        schedule: schedule(),
        streak: streakState(),
      });
    }

    function importProgress(text) {
      var backup;
      try {
        backup = JSON.parse(text);
      } catch (e) {
        return false;
      }
      if (!backup || typeof backup !== "object" || backup.version !== BACKUP_VERSION) {
        return false;
      }
      var wrote = true;
      var parts = [
        [PROGRESS_KEY, normalizeObject(backup.progress)],
        [SRS_KEY, normalizeObject(backup.schedule)],
        [STREAK_KEY, normalizeObject(backup.streak)],
      ];
      for (var i = 0; i < parts.length; i++) {
        if (!writeObject(store, parts[i][0], parts[i][1])) {
          wrote = false;
        }
      }
      return wrote;
    }

    function normalizeObject(value) {
      if (!value || typeof value !== "object") {
        return {};
      }
      return normalizeList(value).length ? {} : value;
    }

    return {
      data: data,
      learn: {
        isMastered: isMastered,
        toggleMastered: toggleMastered,
        masteredCount: masteredCount,
        record: record,
        dueCount: function (filter) {
          return dueChars(filter).length;
        },
        dueChars: dueChars,
        streak: streak,
        exportProgress: exportProgress,
        importProgress: importProgress,
      },
    };
  }

  return { create: create };
});
