"""Diagnostic: checks files, page wiring, database, routes and a real server. Changes nothing."""
import os, re, socket, sys, threading, urllib.request

problems = []


def check(label, passed, hint=""):
    print("[ OK ]" if passed else "[FAIL]", label, "" if passed else "-> " + hint)
    if not passed:
        problems.append(label)


def read(path):
    try:
        return open(path, encoding="utf-8").read()
    except Exception:
        return ""


print("\n== 1. Files exist and are not empty ==")
FILES = ["app.py", "config.py", "database/db.py", "modules/query_engine.py",
         "modules/response_builder.py", "modules/chat_engine.py", "modules/csv_upload.py",
         "nlp/intent_classifier.py", "nlp/date_parser.py", "nlp/language.py", "nlp/preprocess.py",
         "web/templates/index.html", "web/static/style.css", "web/static/app.js",
         "models/intent_model.joblib"]
for f in FILES:
    check(f, os.path.isfile(f) and os.path.getsize(f) > 50, "missing or empty, tell me")

print("\n== 2. Page wiring ==")
html, js, css, app_py = (read("web/templates/index.html"), read("web/static/app.js"),
                         read("web/static/style.css"), read("app.py"))
check("index.html loads style.css", "/static/style.css" in html, "link missing")
check("index.html loads app.js", "/static/app.js" in html, "script tag missing")
ids_used = set(re.findall(r'el\("([^"]+)"\)', js))
ids_have = set(re.findall(r'id="([^"]+)"', html))
missing = sorted(ids_used - ids_have)
check("every id used by app.js exists in index.html", not missing, "missing ids: %s" % missing)
check("app.js ends with loadDatasets();", js.strip().endswith("loadDatasets();"), "app.js got cut off")
check("app.js has sendMessage and renderChat", "function renderChat" in js and "async function sendMessage" in js,
      "app.js part 1 or 2 did not paste fully")
check("style.css has the palette", "#3E2723" in css and "#EFEBE9" in css, "style.css is the old one")
for route in ['"/"', '"/api/datasets"', '"/api/chat"', '"/api/upload"', "/api/datasets/<int:dataset_id>/info"]:
    check("app.py route " + route, route in app_py, "route missing in app.py")
check("app.py has the run line", 'app.run(' in app_py and "__main__" in app_py, "end of app.py is broken")

print("\n== 3. Python imports ==")
app_module = None
try:
    import app as app_module
    check("import app", True)
except Exception as e:
    check("import app", False, "%s: %s" % (type(e).__name__, e))

print("\n== 4. Database ==")
try:
    from database import db
    db.init_db()
    ds = db.list_datasets()
    check("datasets found: %d" % len(ds), len(ds) > 0, "run: python load_samples.py")
    for d in ds:
        info = db.get_dataset_info(d["id"])
        print("       -", d["id"], d["name"], "|", info["records"], "records")
except Exception as e:
    check("database", False, "%s: %s" % (type(e).__name__, e))
    ds = []

print("\n== 5. Routes through Flask's test client (no network needed) ==")
if app_module:
    c = app_module.app.test_client()
    check("GET /", c.get("/").status_code == 200, "page route broken")
    check("GET /static/app.js", c.get("/static/app.js").status_code == 200, "static folder not found")
    check("GET /static/style.css", c.get("/static/style.css").status_code == 200, "static folder not found")
    check("GET /api/datasets", c.get("/api/datasets").status_code == 200, "route broken")
    if ds:
        i = ds[0]["id"]
        check("GET /api/datasets/%d/info" % i, c.get("/api/datasets/%d/info" % i).status_code == 200, "info route broken")
        r = c.post("/api/chat", json={"dataset_id": i, "message": "hello"})
        check("POST /api/chat hello", r.status_code == 200 and "reply" in r.get_json(), "chat route broken")

print("\n== 6. A real server on port 8123 (tests the network part) ==")
if app_module:
    try:
        from werkzeug.serving import make_server
        srv = make_server("127.0.0.1", 8123, app_module.app)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        code = urllib.request.urlopen("http://127.0.0.1:8123/", timeout=5).status
        srv.shutdown()
        check("real server answers with 200", code == 200, "got %s" % code)
    except Exception as e:
        check("real server", False, "%s: %s" % (type(e).__name__, e))

print("\n== 7. Ports and Codespace info (information only) ==")
for port in (5000, 8000):
    s = socket.socket()
    s.settimeout(1)
    state = "a server IS running" if s.connect_ex(("127.0.0.1", port)) == 0 else "nothing running"
    s.close()
    print("   port %d: %s" % (port, state))
name = os.environ.get("CODESPACE_NAME")
domain = os.environ.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN")
print("   Codespace name:", name)
if name and domain:
    print("   Public-style link for port 5000: https://%s-5000.%s" % (name, domain))

print("\n== RESULT ==")
if problems:
    print("%d problem(s):" % len(problems))
    for p in problems:
        print("  -", p)
else:
    print("All checks passed. The code is fine, so the problem is only how the browser reaches the Codespace.")
