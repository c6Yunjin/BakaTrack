# progress_report.py: READ-ONLY status report. Changes nothing in your project or real database.
import os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

LINES = []


def say(text=""):
    print(text)
    LINES.append(str(text))


def section(title):
    say("")
    say("=" * 70)
    say(title)
    say("=" * 70)


def run(cmd, tail=None):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=ROOT)
        text = (out.stdout + out.stderr).strip()
    except Exception as e:
        text = "could not run: %s" % e
    lines = text.splitlines()
    if tail:
        lines = lines[-tail:]
    say("\n".join(lines) if lines else "(nothing printed)")


def read(path):
    try:
        return open(os.path.join(ROOT, path), encoding="utf-8").read()
    except Exception:
        return None


# ---------------------------------------------------------------- 1. git
section("1. GIT")
run(["git", "branch", "--show-current"])
say("-- uncommitted changes (?? = new file, M = edited):")
run(["git", "status", "--short"])
say("-- last 10 commits:")
run(["git", "log", "--oneline", "-10"])
say("-- commits per author:")
run(["git", "shortlog", "-sn", "HEAD"])

# ---------------------------------------------------------------- 2. files
section("2. FILES (size in bytes, or MISSING)")
FILES = [
    "app.py", "config.py", "load_samples.py", "data/intents.json", "data/classmate_questions.csv",
    "models/intent_model.joblib", "training/evidence/results.json",
    "nlp/preprocess.py", "nlp/intent_classifier.py", "nlp/date_parser.py", "nlp/language.py",
    "modules/chat_engine.py", "modules/query_engine.py", "modules/response_builder.py",
    "modules/chart_maker.py", "modules/forecaster.py", "modules/fuzzy_rater.py",
    "modules/smalltalk.py", "modules/data_view.py", "modules/easter_eggs.py", "modules/dataset_info.py",
    "modules/knowledge_base.py", "data/knowledge_base.json",
    "web/templates/index.html", "web/static/app.js", "web/static/style.css",
    "web/static/table_view.js", "web/static/chart_view.js", "web/static/eggs.js",
    "web/static/rickroll.webm",
    "tests/test_easter_eggs.py", "tests/test_data_range.py", "tests/test_dataset_info.py",
]
for f in FILES:
    p = os.path.join(ROOT, f)
    say("  %-38s %s" % (f, os.path.getsize(p) if os.path.exists(p) else "MISSING"))

# ---------------------------------------------------------------- 3. wiring
section("3. FEATURE CHECKS (is the code connected?)")
CHECKS = [
    ("chat engine uses easter eggs", "modules/chat_engine.py", "easter_eggs"),
    ("chat engine uses dataset_info", "modules/chat_engine.py", "dataset_info"),
    ("chat engine uses smalltalk", "modules/chat_engine.py", "smalltalk"),
    ("chat engine uses data_view", "modules/chat_engine.py", "data_view"),
    ("data table has date-range code", "modules/data_view.py", "_range_request"),
    ("note_all_data template exists", "modules/response_builder.py", "note_all_data"),
    ("dataset_info swaps note_keys", "modules/dataset_info.py", "note_keys"),
    ("eggs.js points to rickroll.webm", "web/static/eggs.js", "rickroll.webm"),
    ("download route passes start/end", "app.py", 'request.args.get("start")'),
    ("total_value in query engine", "modules/query_engine.py", "total_value"),
    ("location field in database", "database/db.py", "location"),
]
for label, path, needle in CHECKS:
    text = read(path)
    state = "FILE MISSING" if text is None else ("OK" if needle in text else "NOT FOUND")
    say("  %-38s %s" % (label, state))

say("")
say("-- order of the rule checks inside chat_engine.answer():")
text = read("modules/chat_engine.py") or ""
for i, line in enumerate(text.splitlines(), 1):
    if ".match(" in line:
        say("  line %d: %s" % (i, line.strip()))

# ---------------------------------------------------------------- 4. tests
section("4. TESTS (python -m pytest -q)")
run([sys.executable, "-m", "pytest", "-q", "-x", "--no-header", "-p", "no:cacheprovider"], tail=14)

# ---------------------------------------------------------------- 5. datasets
section("5. DATASETS (read from a temporary copy of the database)")
chat_engine = None
biggest = None
try:
    from config import DB_PATH
    if not os.path.exists(DB_PATH):
        say("No database file at %s (run python load_samples.py)" % DB_PATH)
    else:
        tmp_db = os.path.join(tempfile.mkdtemp(), "copy.db")
        shutil.copy(DB_PATH, tmp_db)
        from database import db
        db.DB_PATH = tmp_db
        datasets = db.list_datasets()
        say("Datasets found: %d" % len(datasets))
        best = -1
        for d in datasets:
            recs = db.get_records(d["id"])
            first = recs[0]["date"] if recs else None
            last = recs[-1]["date"] if recs else None
            say("  id=%s | %s | records=%d | %s to %s" % (d["id"], d["name"], len(recs), first, last))
            if len(recs) > best:
                best, biggest = len(recs), d
        from modules import chat_engine
except Exception as e:
    say("Could not read datasets: %r" % e)

# ---------------------------------------------------------------- 6. questions
section("6. QUESTIONS THE PROFESSOR MAY ASK (run on the biggest dataset)")
QUESTIONS = [
    "How much is the total cost of baka right now",
    "check latest retail price of baka",
    "price of baka",
    "monthly summary of baka",
    "kilos of baka this month",
    "show data for batangas",
    "saan ang baka capital",
    "magkano ang baka ngayon",
    "total value of cattle traded",
    "average price per head",
    "where is this data from",
    "what dates do you have?",
    "Which month has the highest price?",
    "Compare prices of March and June 2026",
]
if chat_engine is None or biggest is None:
    say("Skipped (no dataset or the chat engine could not be loaded).")
else:
    say("Dataset used: %s" % biggest["name"])
    for q in QUESTIONS:
        try:
            out = chat_engine.answer(biggest["id"], q)
            kind = (out["chart"] or {}).get("widget", "chart") if out["chart"] else "none"
            reply = " ".join(str(out["reply"]).split())
            say("\nQ: %s" % q)
            say("   intent=%s conf=%s extra=%s" % (out["intent"], out["confidence"], kind))
            say("   A: %s" % reply[:240])
        except Exception as e:
            say("\nQ: %s\n   ERROR: %r" % (q, e))

# ---------------------------------------------------------------- 7. chips
section("7. WHERE THE FIRST-PAGE SUGGESTION CHIPS COME FROM")
found = False
for path in ("web/static/app.js", "app.py", "web/templates/index.html", "modules/chat_engine.py"):
    text = read(path)
    if not text:
        continue
    for i, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        if "suggest" in low or "try one" in low or "starter" in low or "example" in low:
            say("  %s:%d: %s" % (path, i, line.strip()[:150]))
            found = True
if not found:
    say("  (nothing found)")

# ---------------------------------------------------------------- save
try:
    with open(os.path.join(ROOT, "progress_report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(LINES))
    say("\nSaved a copy in progress_report.txt")
except Exception as e:
    say("\nCould not save progress_report.txt: %r" % e)