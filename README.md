# Hanja Path

**Live site:** [diogo7dias.github.io/hanja-path](https://diogo7dias.github.io/hanja-path/)

Hanja Path is a minimal study companion for Korean learners who want to understand and remember Sino-Korean vocabulary through hanja.

## Features

- **1,795 education hanja** organized into Beginner, Intermediate, and Advanced levels
- **Structured lessons** — characters grouped into lessons of 10 by pictographic complexity
- **Study pages** — deep-dive for every hanja: reading, meaning, memory tip, 3 example words with breakdowns, a Korean sentence, and a stroke-order viewer
- **Stroke order** — animated per-stroke writing guide on every study page (ordered stroke data loaded at runtime from the MIT-licensed hanzi-writer-data CDN; graceful fallback when offline)
- **Interactive quiz** — 4 quiz modes: glyph→reading, glyph→meaning, homophone disambiguation (same reading, pick the right character), and word→hanja spelling; readings in the reading quiz are guaranteed distinct
- **Spaced repetition** — review sessions schedule characters by Leitner intervals (1/3/7/14/30 days) in your browser; correct answers advance the box, mistakes reset it; a daily streak tracks consistency
- **Korean audio** — play buttons read each character, example word, and sentence aloud using the browser's Korean speech engine (zero dependencies)
- **Reading hubs** — every character grouped by its Korean reading (e.g. all 정 characters on one page) so you can attack homophones head-on
- **Progress tracking** — mark characters as mastered, see your progress across lessons and levels (saved in your browser)
- **Search and pagination** — find any hanja by glyph, reading, English meaning, or the Korean words it appears in (type 가족 to find 家族/家)
- **Responsive design** — works on desktop and mobile, dark editorial aesthetic
- **Ko-fi support link** for the project

## How to Use

1. **Pick a level** — Beginner (초급), Intermediate (중급), or Advanced (고급)
2. **Choose a lesson** — 60 lessons per level, 10 characters each, ordered by complexity
3. **Study** — read the tip, learn the example words, mark as mastered when ready
4. **Quiz** — test your knowledge with multiple-choice questions
5. **Track progress** — your mastery is saved locally in your browser

## Pages

| Page | Description |
|------|-------------|
| `index.html` | Home page with method overview and level picker |
| `lessons.html` | Lesson picker with progress bar per level |
| `lesson.html` | Single lesson view with 10 study cards |
| `study.html` | Deep-dive page for any individual hanja (with ✍️ stroke-order animation) |
| `quiz.html` | Interactive quiz — 4 modes, spaced-repetition reviews (`?srs=1`), streak |
| `reading.html` | Reading hubs — every character grouped by Korean reading (homophones) |
| `level.html` | Flat grid browser with search (original layout) |
| `levels.html` | Level overview (original layout) |

## Tech Stack

- Static HTML/CSS/JavaScript — no build step, no framework
- `hanja-data.js` — generated dataset of all 1,795 education hanja with readings, meanings, tips, example words, and English glosses
- `hanja-core.js` — the study core: learner state, spaced repetition, dataset queries, quiz rules and query-string parsing, with storage, clock, randomness, stroke data and speech injected as ports
- `hanja-adapters.js` — the browser side of those ports (localStorage with guards, Date, Math.random, the stroke CDN, speechSynthesis)
- `stroke.js` — dependency-free stroke-order viewer (loads ordered stroke data from the hanzi-writer-data CDN at runtime)
- `localStorage` for progress tracking (no account needed)
- Hosted on GitHub Pages

Every page loads `hanja-data.js`, `hanja-core.js` and `hanja-adapters.js`, then creates one core:

```js
var ports = HanjaAdapters.browser();
var core = HanjaCore.create({ data: window.HANJA, store: ports.store, clock: ports.clock, rand: ports.rand, speech: ports.speech });
core.learn.isMastered('家');        // hanjaprogress, guarded
core.learn.record('家', true);      // hanjasrs + hanjastreak, Leitner boxes 0..5
core.quiz.session({ lv: -1, srs: true });
core.quiz.question(core.chars.byChar('家'), 'reading');
```

The module is plain ES5 with no dependencies, so it runs from a `<script>` tag in the browser and from `require` in Node:

```sh
node --test test/     # 49 tests, no npm install
```

`test/fakes.js` supplies an in-memory store, a settable clock, scripted randomness and a small dataset, so the rules (interval steps, streak reset, distinct readings, distinct hun, the homophone minimum, the same-word distractor rule) are tested without a browser.

## Regenerating the dataset

`hanja-data.js` at the repo root is the only copy the site loads, and `tools/build.py` is its only writer (no copy step):

```sh
python3 tools/build.py            # parse -> build -> validate -> write hanja-data.js (and tools/educ.json)
python3 tools/validate_hanja.py   # check the committed file against the contract; exit 1 on drift
python3 -m unittest discover -s tools/tests   # the contract and layout tests
```

`tools/validate_hanja.py` pins the shape the pages rely on: totals and level split, level/lesson/slot numbering, the known gaps (16 characters without radical data, 23 without example words, 22 with a curated tip and sentence), and the two words that use a hanja outside the education set. A build that breaks any of that fails and changes nothing.

Everything under `tools/` that the build reads (`wikitext.json`, `words.json`, `ko_english.json`, `radicals.json`) is a frozen committed input. `words.json` cannot be rebuilt from a clean checkout, because `tools/build_words.py` needs corpora that are not in the repo.

## Data Source

The hanja dataset is parsed from the official Korean education hanja list (교육용기초한자 1800자) via the ko.wiktionary appendix. Example words are sourced from the Kengdic Korean-English dictionary, the KRV Bible corpus, and curated vocabulary lists.

## Ko-fi

If you find this useful, consider supporting: [ko-fi.com/d7d7m](https://ko-fi.com/d7d7m)
