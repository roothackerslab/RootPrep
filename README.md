# ROOTPREP CLI

A terminal-based CEHv13 exam prep console, built for **RootHackersLab**.

**Developer:** Saadullah Abdul Wahid
**Powered by:** RootHackersLab

Companion to the RootHackersLab Study Hub (the HTML/browser version) — same
question bank and drive library, but runnable straight from your terminal.

## Features

- **CEH Theory MCQ Quiz** — exam-level question bank (267 questions and
  growing) covering all core CEH domains: footprinting/recon, scanning,
  enumeration, system hacking, malware, sniffing, social engineering, DoS,
  session hijacking, evading IDS/firewalls, web servers/apps, SQL injection,
  wireless, mobile, IoT, cloud, cryptography, threat intel, and more.
  Sequential or randomized order, live scoring, timing, and a review of
  missed questions at the end.
- **CEH Practice Exam** — a 50-question random draw from the bank, scored
  against a 70% pass mark with a clear PASS/FAIL result, closer to sitting
  the real exam.
- **Missed-Question Review** — anything you get wrong is automatically
  bookmarked to `~/.rootprep/missed_questions.json`. Jump into "Review
  Missed Questions" any time for focused practice; questions you finally
  answer correctly drop off the list.
- **My Stats** — attempts, best accuracy, lifetime accuracy, and last-run
  timestamp per mode, stored in `~/.rootprep/stats.json`.
- **Interview Flashcards** — OSCP / pentest-role interview questions with
  model answers, revealed one at a time.
- **Drive Library** — curated CEH/OSCP course drive links plus your own
  saved links (`~/.rootprep/user_links.json`), now with:
  - a numbered flat view across all categories
  - **O**pen a link directly in your default browser by number
  - **F**ilter/search by title or category, **C**lear the filter

> Note: the standalone OSCP MCQ quiz has been removed. CEH/OSCP-relevant
> interview flashcards and the OSCP drive library are still included.

## Requirements

- Python 3.8+
- pip

## Install

```bash
git clone <this-folder-or-repo> rootprep-cli
cd rootprep-cli
pip install -r requirements.txt
```

(If you just have the folder locally, skip the `git clone` step.)

## Run

```bash
python3 rootprep.py
```

You'll get a menu:

```
1  CEH Theory MCQ Quiz        (full bank, sequential/random)
2  CEH Practice Exam          (50 random Qs, timed, pass/fail)
3  Review Missed Questions    (bookmarked from past sessions)
4  OSCP / Pentest Interview Questions
5  Drive Library              (search + open links directly)
6  My Stats
7  Exit
```

During a quiz:
- Answer with `A`, `B`, `C`, or `D`
- Press Enter with no input to skip a question
- Type `q` to end the quiz early and see your score

In the Drive Library:
- `O` then a number opens that link in your default browser
- `A` adds a link, `R` removes one of your own links
- `F` filters the view by keyword, `C` clears the filter

## Project structure

```
rootprep-cli/
├── rootprep.py          # main CLI app
├── requirements.txt
├── README.md
└── data/
    ├── ceh_mcqs.json     # CEH theory question bank
    └── interview_qa.json # interview flashcards
```

Local, persistent data lives under `~/.rootprep/` (created automatically):
- `user_links.json` — your saved drive links
- `stats.json` — attempts/accuracy history per mode
- `missed_questions.json` — bookmarked questions you've gotten wrong

None of this is uploaded anywhere; it all stays on your machine.

## Updating the question banks

Each JSON file is a list of `[question, option_A, option_B, option_C, option_D, correct_index]`
entries (`correct_index` is 0-based: 0=A, 1=B, 2=C, 3=D). Drop in new entries
and they'll show up automatically — no code changes needed.

`interview_qa.json` is a list of `[question, answer]` pairs.

## Notes

- The CEH Theory bank currently sits at 267 questions and can keep growing —
  re-drop `ceh_mcqs.json` here as new batches are produced.
- Your added drive links, stats, and missed-question bookmarks are stored
  only on your machine (`~/.rootprep/`), never uploaded anywhere.
