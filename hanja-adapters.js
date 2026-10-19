/* hanja-adapters.js — the browser side of hanja-core's ports.
 *
 * The core refuses to know about localStorage, fetch, Date, Math.random or
 * speechSynthesis. Those live here, behind one factory that both the pages and
 * the Node tests call. Every dependency is an argument, so the Node tests can
 * pass a fake localStorage, a fake fetch and a fake speech engine, and so a
 * page can pass a stub for anything it wants to control.
 *
 * ES5 on purpose, like the core: loaded with a plain <script>, no bundler.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory(root);
  } else {
    root.HanjaAdapters = factory(root);
  }
})(this, function (root) {
  "use strict";

  var DAY_MS = 86400000;
  var STROKE_TIMEOUT_MS = 4000;
  /* same source as stroke.js: the hanzi-writer stroke dataset on jsdelivr */
  var STROKE_BASE = "https://cdn.jsdelivr.net/npm/hanzi-writer-data@2.0.1/";

  function isArray(value) {
    return Object.prototype.toString.call(value) === "[object Array]";
  }

  function defaultStorage(scope) {
    try {
      return scope && scope.localStorage ? scope.localStorage : null;
    } catch (e) {
      /* some browsers throw on the property itself when cookies are blocked */
      return null;
    }
  }

  function defaultFetch(scope) {
    if (scope && typeof scope.fetch === "function" && typeof scope.document !== "undefined") {
      return function (url, init) {
        return scope.fetch(url, init);
      };
    }
    return null;
  }

  function defaultSynth(scope) {
    try {
      return scope && scope.speechSynthesis ? scope.speechSynthesis : null;
    } catch (e) {
      return null;
    }
  }

  function defaultUtterance(scope) {
    return scope && typeof scope.SpeechSynthesisUtterance === "function" ? scope.SpeechSynthesisUtterance : null;
  }

  function withTimeout(promise, ms) {
    return new Promise(function (resolve, reject) {
      var timer = setTimeout(function () {
        reject(new Error("timeout"));
      }, ms);
      promise.then(
        function (value) {
          clearTimeout(timer);
          resolve(value);
        },
        function (error) {
          clearTimeout(timer);
          reject(error);
        }
      );
    });
  }

  function create(options) {
    var config = options || {};
    var scope = config.scope !== undefined ? config.scope : root;
    var storage = "storage" in config ? config.storage : defaultStorage(scope);
    var doFetch = "fetch" in config ? config.fetch : defaultFetch(scope);
    var synth = "synth" in config ? config.synth : defaultSynth(scope);
    var Utterance = "Utterance" in config ? config.Utterance : defaultUtterance(scope);
    var base = config.baseUrl || STROKE_BASE;
    var timeoutMs = config.timeoutMs || STROKE_TIMEOUT_MS;
    var strokeCache = {};

    function readStroke(character) {
      if (typeof doFetch !== "function") {
        return Promise.resolve(null);
      }
      var url = base + encodeURIComponent(character) + ".json";
      return withTimeout(doFetch(url, { mode: "cors" }), timeoutMs)
        .then(function (response) {
          if (!response || !response.ok) {
            throw new Error("http " + (response ? response.status : "unknown"));
          }
          return response.json();
        })
        .then(function (data) {
          if (!data || !isArray(data.strokes) || !data.strokes.length || !isArray(data.medians)) {
            throw new Error("bad stroke data");
          }
          return data;
        });
    }

    return {
      store: {
        get: function (key) {
          if (!storage || typeof storage.getItem !== "function") {
            return null;
          }
          var text;
          try {
            text = storage.getItem(key);
          } catch (e) {
            return null;
          }
          if (text === null || text === undefined || text === "") {
            return null;
          }
          try {
            return JSON.parse(text);
          } catch (e) {
            return null; /* corrupt data is the same as no data */
          }
        },
        set: function (key, value) {
          if (!storage || typeof storage.setItem !== "function") {
            return false;
          }
          try {
            storage.setItem(key, JSON.stringify(value));
            return true;
          } catch (e) {
            return false; /* quota, private mode, blocked storage */
          }
        },
      },
      clock: {
        today: function () {
          return Math.floor(Date.now() / DAY_MS);
        },
        now: function () {
          return Date.now();
        },
      },
      rand: {
        float: function () {
          return Math.random();
        },
      },
      strokes: {
        get: function (character) {
          if (Object.prototype.hasOwnProperty.call(strokeCache, character)) {
            return Promise.resolve(strokeCache[character]);
          }
          return readStroke(character).then(
            function (data) {
              strokeCache[character] = data || null;
              return strokeCache[character];
            },
            function () {
              strokeCache[character] = null;
              return null;
            }
          );
        },
      },
      speech: {
        /* a page can hide its speaker buttons when this is false */
        available: function () {
          return !!synth && !!Utterance;
        },
        speak: function (text, opts) {
          var value = String(text === undefined || text === null ? "" : text);
          if (!synth || !value || !Utterance) {
            return;
          }
          try {
            if (typeof synth.cancel === "function") {
              synth.cancel();
            }
          } catch (e) {
            /* cancelling is best effort */
          }
          var utterance;
          try {
            utterance = new Utterance(value);
          } catch (e) {
            return;
          }
          utterance.lang = "ko-KR";
          utterance.rate = (opts && opts.rate) || 0.9;
          utterance.pitch = 1;
          try {
            var voices = typeof synth.getVoices === "function" ? synth.getVoices() : [];
            for (var i = 0; i < voices.length; i++) {
              if (/^ko(-|_|$)/i.test(voices[i].lang)) {
                utterance.voice = voices[i];
                break;
              }
            }
          } catch (e) {
            /* the default voice will do */
          }
          try {
            synth.speak(utterance);
          } catch (e) {
            /* nothing to do about a refused utterance */
          }
        },
      },
    };
  }

  return {
    create: create,
    browser: function () {
      return create({});
    },
  };
});
