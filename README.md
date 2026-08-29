# Hanja Path

**Live site:** [diogo7dias.github.io/hanja-path](https://diogo7dias.github.io/hanja-path/)

Hanja Path is a minimal study companion for Korean learners who want to understand and remember Sino-Korean vocabulary through hanja.

## Features

- **1,795 education hanja** organized into Beginner, Intermediate, and Advanced levels
- **Structured lessons** — characters grouped into lessons of 10 by pictographic complexity
- **Study pages** — deep-dive for every hanja: reading, meaning, memory tip, 3 example words with breakdowns, and a Korean sentence
- **Interactive quiz** — test yourself with 3 quiz modes: glyph→reading, glyph→meaning, reading→glyph
- **Progress tracking** — mark characters as mastered, see your progress across lessons and levels (saved in your browser)
- **Search and pagination** — find any hanja by glyph, reading, or English meaning
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
| `study.html` | Deep-dive page for any individual hanja |
| `quiz.html` | Interactive quiz with 3 modes |
| `level.html` | Flat grid browser with search (original layout) |
| `levels.html` | Level overview (original layout) |

## Tech Stack

- Static HTML/CSS/JavaScript — no build step, no framework
- `hanja-data.js` — generated dataset of all 1,795 education hanja with readings, meanings, tips, example words, and English glosses
- `localStorage` for progress tracking (no account needed)
- Hosted on GitHub Pages

## Data Source

The hanja dataset is parsed from the official Korean education hanja list (교육용기초한자 1800자) via the ko.wiktionary appendix. Example words are sourced from the Kengdic Korean-English dictionary, the KRV Bible corpus, and curated vocabulary lists.

## Ko-fi

If you find this useful, consider supporting: [ko-fi.com/d7d7m](https://ko-fi.com/d7d7m)
