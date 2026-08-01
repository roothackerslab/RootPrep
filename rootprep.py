#!/usr/bin/env python3
"""
ROOTPREP CLI
============
A terminal-based CEHv13 + OSCP exam prep console for RootHackersLab.

Developer: Saadullah Abdul Wahid
Powered by: RootHackersLab

Features:
  - CEH Theory MCQ quiz engine with scoring & review
  - CEH Practice Exam mode (timed, random subset, pass/fail scoring)
  - Persistent "missed questions" bookmarking + focused review mode
  - Local stats/history tracking across sessions
  - Interview question flashcards (tap to reveal model answers)
  - Drive library manager: curated + your own links, searchable, with
    one-key "open in browser" access
  - Q&A / MCQ bank format is unchanged, so drop in new questions any time

Run:
    python3 rootprep.py
"""

import json
import os
import random
import sys
import time
import webbrowser
from datetime import datetime
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, IntPrompt, Confirm
    from rich.align import Align
    from rich import box
except ImportError:
    print("Missing dependency 'rich'. Install requirements first:\n")
    print("    pip install -r requirements.txt\n")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths & persistent storage
# ---------------------------------------------------------------------------
APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
CONFIG_DIR = Path.home() / ".rootprep"
CONFIG_DIR.mkdir(exist_ok=True)
USER_LINKS_FILE = CONFIG_DIR / "user_links.json"
STATS_FILE = CONFIG_DIR / "stats.json"
MISSED_FILE = CONFIG_DIR / "missed_questions.json"

EXAM_SIZE = 50
EXAM_PASS_PCT = 70.0

console = Console()

GREEN = "bold spring_green2"
CYAN = "bold cyan"
MAG = "bold magenta"
AMBER = "bold yellow"
DIM = "grey58"

DEVELOPER = "Saadullah Abdul Wahid"
POWERED_BY = "RootHackersLab"

CURATED_LINKS = {
    "CEH Theory": [
        ("CEHv13 eBooks", "https://drive.google.com/drive/mobile/folders/1cTsVYAiuQdQI44vGKFJ4wW-WBw7bYZL7"),
        ("CEHv13 Course Drive (1)", "https://drive.google.com/drive/u/0/mobile/folders/14jjSnprC7AxqPCo8pl6hDZYtg8tuehs-"),
        ("CEHv13 Course Drive (2)", "https://drive.google.com/drive/u/0/mobile/folders/14jjSnprC7AxqPCo8pl6hDZYtg8tuehs-"),
    ],
    "CEH Practical": [],
    "OSCP": [
        ("OSCP Course", "https://drive.google.com/drive/folders/11JpMnLJcIMHw8M7v4MHhNB1LGUkYzWVE"),
        ("OSCP in Hindi (Latest 2026)", "https://tinyurl.com/swnrnka6"),
    ],
}


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_user_links():
    if USER_LINKS_FILE.exists():
        try:
            return load_json(USER_LINKS_FILE)
        except Exception:
            return {}
    return {}


def save_user_links(data):
    with open(USER_LINKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_stats():
    if STATS_FILE.exists():
        try:
            return load_json(STATS_FILE)
        except Exception:
            return {}
    return {}


def save_stats(data):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def update_stats(stats_key, answered, score):
    """Record one quiz session's results under stats_key. Returns this session's accuracy."""
    stats = load_stats()
    entry = stats.setdefault(stats_key, {
        "attempts": 0,
        "best_accuracy": 0.0,
        "last_run": None,
        "total_answered": 0,
        "total_correct": 0,
    })
    accuracy = (score / answered * 100) if answered else 0.0
    entry["attempts"] += 1
    entry["best_accuracy"] = max(entry.get("best_accuracy", 0.0), accuracy)
    entry["last_run"] = datetime.now().isoformat(timespec="seconds")
    entry["total_answered"] += answered
    entry["total_correct"] += score
    save_stats(stats)
    return accuracy


def load_missed():
    if MISSED_FILE.exists():
        try:
            return load_json(MISSED_FILE)
        except Exception:
            return []
    return []


def save_missed(data):
    with open(MISSED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def update_missed(wrong_entries, correct_entries):
    """Add newly-missed questions to the persistent bookmark list, and drop any
    that were just answered correctly (e.g. during a review session)."""
    missed = load_missed()
    correct_texts = {q[0] for q in correct_entries}
    missed = [m for m in missed if m[0] not in correct_texts]
    existing_texts = {m[0] for m in missed}
    for q in wrong_entries:
        if q[0] not in existing_texts:
            missed.append(q)
            existing_texts.add(q[0])
    missed = missed[-300:]  # cap growth
    save_missed(missed)


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
def banner():
    console.clear()
    art = r"""
[bold spring_green2] _____             _   _____                   
|  __ \           | | |  __ \                  
| |__) |___   ___ | |_| |__) | __ ___ _ __     
|  _  // _ \ / _ \| __|  ___/ '__/ _ \ '_ \    
| | \ \ (_) | (_) | |_| |   | | |  __/ |_) |   
|_|  \_\___/ \___/ \__|_|   |_|  \___| .__/    
                                      | |       
                                      |_|       [/]
"""
    console.print(art)
    console.print(Align.center("[bold cyan]CEHv13 + OSCP PREP CONSOLE[/]"))
    console.print(Align.center("[grey58]root@rootprep:~$ status: online[/]"))
    console.print(Align.center(f"[{DIM}]Developer: {DEVELOPER}  //  Powered by {POWERED_BY}[/]\n"))


# ---------------------------------------------------------------------------
# Quiz engine
# ---------------------------------------------------------------------------
def run_quiz(questions, title, stats_key=None, pass_threshold=None):
    """
    questions: list of [question, a, b, c, d, correct_index] entries (already
               loaded/sampled by the caller).
    stats_key: if provided, this session's result is recorded under this key
               in ~/.rootprep/stats.json.
    pass_threshold: if provided (e.g. 70.0), the summary shows PASS/FAIL
               against this percentage — used for exam mode.
    """
    if not questions:
        console.print("[red]No questions found in this bank yet.[/]")
        input("\nPress Enter to return...")
        return

    console.print(Panel.fit(
        f"[bold]{title}[/]  —  {len(questions)} questions loaded\n"
        "[grey58]Type an option letter (A-D), 'q' to quit, or Enter to skip.[/]",
        border_style="spring_green2"
    ))

    mode = Prompt.ask(
        "\nMode",
        choices=["sequential", "random"],
        default="sequential"
    )

    order = list(range(len(questions)))
    if mode == "random":
        random.shuffle(order)

    score = 0
    answered = 0
    wrong_log = []
    wrong_entries = []
    correct_entries = []
    started = time.time()

    for qi, idx in enumerate(order, start=1):
        q = questions[idx]
        question_text, a, b, c, d, correct_i = q
        options = [a, b, c, d]
        letters = ["A", "B", "C", "D"]

        console.clear()
        console.print(Panel.fit(
            f"[grey58]Question {qi}/{len(order)}[/]   [spring_green2]Score: {score}/{answered}[/]",
            border_style="grey42"
        ))
        console.print(f"\n[bold yellow]Q{qi}.[/] {question_text}\n")
        for letter, opt in zip(letters, options):
            console.print(f"   [cyan]{letter}.[/] {opt}")

        choice = Prompt.ask("\nYour answer", default="").strip().lower()
        if choice == "q":
            break
        if choice == "":
            continue

        answered += 1
        chosen_i = letters.index(choice.upper()) if choice.upper() in letters else -1
        if chosen_i == correct_i:
            score += 1
            correct_entries.append(q)
            console.print(f"\n[bold spring_green2]✔ Correct![/] Answer: {letters[correct_i]}. {options[correct_i]}")
        else:
            wrong_entries.append(q)
            console.print(f"\n[bold magenta]✘ Wrong.[/] Correct answer: {letters[correct_i]}. {options[correct_i]}")
            wrong_log.append((question_text, letters[correct_i] + ". " + options[correct_i]))

        input("\nPress Enter to continue...")

    elapsed = int(time.time() - started)
    mins, secs = divmod(elapsed, 60)
    accuracy = (score / answered * 100) if answered else 0.0

    summary = (
        f"[bold]Quiz session complete[/]\n\n"
        f"Answered: {answered}\n"
        f"Correct:  [spring_green2]{score}[/]\n"
        f"Accuracy: {accuracy:.1f}%\n"
        f"Time:     {mins}m {secs}s"
    )
    if pass_threshold is not None:
        result = "PASS" if accuracy >= pass_threshold else "FAIL"
        color = "spring_green2" if result == "PASS" else "magenta"
        summary += f"\n[bold {color}]Result: {result}[/] (pass mark {pass_threshold:.0f}%)"

    console.clear()
    console.print(Panel.fit(summary, title=title, border_style="cyan"))

    if stats_key:
        update_stats(stats_key, answered, score)
    update_missed(wrong_entries, correct_entries)

    if wrong_log and Confirm.ask("\nReview missed questions?", default=True):
        for i, (q, ans) in enumerate(wrong_log, 1):
            console.print(f"\n[yellow]{i}. {q}[/]")
            console.print(f"   [spring_green2]Correct: {ans}[/]")
        input("\nPress Enter to return to menu...")


def run_ceh_quiz():
    questions = load_json(DATA_DIR / "ceh_mcqs.json")
    run_quiz(questions, "CEH Theory MCQ Bank", stats_key="ceh_full")


def run_practice_exam():
    questions = load_json(DATA_DIR / "ceh_mcqs.json")
    size = min(EXAM_SIZE, len(questions))
    sample = random.sample(questions, size)
    run_quiz(
        sample,
        f"CEH Practice Exam ({size} random questions)",
        stats_key="ceh_exam",
        pass_threshold=EXAM_PASS_PCT,
    )


def run_review_missed():
    missed = load_missed()
    if not missed:
        console.clear()
        console.print(Panel.fit(
            "[grey58]No missed questions bookmarked yet — take the CEH quiz or "
            "practice exam first, and anything you get wrong will show up here "
            "for focused review.[/]",
            border_style="grey42"
        ))
        input("\nPress Enter to return...")
        return
    run_quiz(missed, "Review — Previously Missed Questions", stats_key="ceh_review")


# ---------------------------------------------------------------------------
# Interview flashcards
# ---------------------------------------------------------------------------
def run_interview():
    qa = load_json(DATA_DIR / "interview_qa.json")
    console.clear()
    console.print(Panel.fit(f"[bold]OSCP / Pentest Interview Questions[/]  —  {len(qa)} cards", border_style="magenta"))

    for i, (q, a) in enumerate(qa, start=1):
        console.print(f"\n[bold cyan]Q{i}.[/] {q}")
        Prompt.ask("[grey58](Enter to reveal answer)[/]", default="")
        console.print(f"[spring_green2]A:[/] {a}")
        if i < len(qa):
            cont = Prompt.ask("\n[grey58]Enter=next, q=quit[/]", default="")
            if cont.lower() == "q":
                break
    input("\nPress Enter to return to menu...")


# ---------------------------------------------------------------------------
# Stats / history
# ---------------------------------------------------------------------------
def show_stats():
    stats = load_stats()
    missed = load_missed()
    labels = {
        "ceh_full": "CEH Theory MCQ Quiz (full bank)",
        "ceh_exam": "CEH Practice Exam (random, pass/fail)",
        "ceh_review": "Missed-Question Review",
    }

    console.clear()
    console.print(Panel.fit("[bold]Your Progress[/]", border_style="cyan"))

    if not stats:
        console.print("\n[grey58]No quiz history yet — take a quiz to start tracking stats.[/]")
    else:
        for key, entry in stats.items():
            label = labels.get(key, key)
            total_answered = entry.get("total_answered", 0)
            total_correct = entry.get("total_correct", 0)
            lifetime_acc = (total_correct / total_answered * 100) if total_answered else 0.0
            console.print(f"\n[bold cyan]{label}[/]")
            console.print(f"  Attempts:           {entry.get('attempts', 0)}")
            console.print(f"  Best accuracy:      {entry.get('best_accuracy', 0.0):.1f}%")
            console.print(f"  Lifetime accuracy:  {lifetime_acc:.1f}%  ({total_correct}/{total_answered})")
            console.print(f"  Last run:           {entry.get('last_run') or '—'}")

    console.print(f"\n[grey58]Bookmarked missed questions ready for focused review: {len(missed)}[/]")
    input("\nPress Enter to return to menu...")


# ---------------------------------------------------------------------------
# Drive library
# ---------------------------------------------------------------------------
def show_library():
    user_links = load_user_links()
    filter_kw = ""

    while True:
        console.clear()
        header = "[bold]Drive Library[/]"
        if filter_kw:
            header += f"  [grey58](filter: '{filter_kw}')[/]"
        console.print(Panel.fit(header, border_style="cyan"))

        categories = list(CURATED_LINKS.keys())
        flat = []  # (number, category, title, url, is_custom)
        n = 0

        for cat in categories:
            table = Table(title=cat, box=box.SIMPLE, border_style="grey42", show_lines=False)
            table.add_column("#", style="bold yellow", width=4)
            table.add_column("Title", style="cyan")
            table.add_column("Link", style="grey58")

            curated = CURATED_LINKS[cat]
            custom = user_links.get(cat, [])
            rows_added = 0

            def kw_match(title):
                if not filter_kw:
                    return True
                fk = filter_kw.lower()
                return fk in title.lower() or fk in cat.lower()

            for title, url in curated:
                if not kw_match(title):
                    continue
                n += 1
                flat.append((n, cat, title, url, False))
                table.add_row(str(n), title, url)
                rows_added += 1
            for title, url in custom:
                if not kw_match(title):
                    continue
                n += 1
                flat.append((n, cat, title, url, True))
                table.add_row(str(n), f"{title} [grey58](yours)[/]", url)
                rows_added += 1

            if rows_added == 0:
                table.add_row("", "[grey58]— none —[/]", "")
            console.print(table)

        console.print(
            "\n[bold]O[/] open a link by number   [bold]A[/] add a link   "
            "[bold]R[/] remove one of your links"
        )
        console.print("[bold]F[/] search/filter   [bold]C[/] clear filter   [bold]B[/] back")
        choice = Prompt.ask("Choice", default="b").strip().lower()

        if choice == "o":
            if not flat:
                console.print("[grey58]No links match the current view.[/]")
                input("\nPress Enter...")
                continue
            num = IntPrompt.ask("Open which number?", default=0)
            match = next((f for f in flat if f[0] == num), None)
            if not match:
                console.print("[red]Invalid number.[/]")
            else:
                _, _, title, url, _ = match
                console.print(f"[spring_green2]Opening:[/] {title}\n[grey58]{url}[/]")
                try:
                    opened = webbrowser.open(url, new=2)
                except Exception:
                    opened = False
                if not opened:
                    console.print(
                        "[yellow]Couldn't launch a browser automatically on this "
                        "machine — copy the link above manually.[/]"
                    )
            input("\nPress Enter...")

        elif choice == "a":
            cat = Prompt.ask("Category", choices=categories, default=categories[0])
            title = Prompt.ask("Title")
            url = Prompt.ask("Drive link (URL)")
            user_links.setdefault(cat, []).append((title, url))
            save_user_links(user_links)
            console.print("[spring_green2]Saved.[/]")
            input("\nPress Enter...")

        elif choice == "r":
            cat = Prompt.ask("Category", choices=categories, default=categories[0])
            custom = user_links.get(cat, [])
            if not custom:
                console.print("[grey58]No custom links in this category.[/]")
                input("\nPress Enter...")
                continue
            for i, (title, url) in enumerate(custom, start=1):
                console.print(f"  {i}. {title} — {url}")
            num2 = IntPrompt.ask("Remove which number?", default=0)
            if 1 <= num2 <= len(custom):
                removed = custom.pop(num2 - 1)
                user_links[cat] = custom
                save_user_links(user_links)
                console.print(f"[magenta]Removed:[/] {removed[0]}")
            input("\nPress Enter...")

        elif choice == "f":
            filter_kw = Prompt.ask("Search term (matches title or category)", default="").strip()

        elif choice == "c":
            filter_kw = ""

        else:
            break


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------
def main():
    while True:
        banner()
        console.print("[bold]1[/] CEH Theory MCQ Quiz  [grey58](full bank, sequential/random)[/]")
        console.print("[bold]2[/] CEH Practice Exam    [grey58](50 random Qs, timed, pass/fail)[/]")
        console.print("[bold]3[/] Review Missed Questions  [grey58](bookmarked from past sessions)[/]")
        console.print("[bold]4[/] OSCP / Pentest Interview Questions")
        console.print("[bold]5[/] Drive Library  [grey58](search + open links directly)[/]")
        console.print("[bold]6[/] My Stats")
        console.print("[bold]7[/] Exit\n")

        choice = Prompt.ask("root@rootprep", choices=["1", "2", "3", "4", "5", "6", "7"], default="1")

        if choice == "1":
            run_ceh_quiz()
        elif choice == "2":
            run_practice_exam()
        elif choice == "3":
            run_review_missed()
        elif choice == "4":
            run_interview()
        elif choice == "5":
            show_library()
        elif choice == "6":
            show_stats()
        elif choice == "7":
            console.print("\n[grey58]root@rootprep:~$ logout[/]")
            console.print(f"[grey58]Developer: {DEVELOPER}  //  Powered by {POWERED_BY}[/]\n")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[grey58]root@rootprep:~$ logout[/]")
        console.print(f"[grey58]Developer: {DEVELOPER}  //  Powered by {POWERED_BY}[/]\n")
