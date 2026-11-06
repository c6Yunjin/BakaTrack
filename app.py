"""BakaTrack web app (Step 6b). Flask serves the page and three small routes."""
import os
import re
import tempfile

from flask import Flask, Response, jsonify, render_template, request

from database import db
from modules import places
from modules import chat_engine, data_view
from modules.csv_upload import upload_dataset
from nlp.intent_classifier import predict

app = Flask(__name__, template_folder="web/templates", static_folder="web/static")


def _dataset_exists(dataset_id):
    return any(d["id"] == dataset_id for d in db.list_datasets())


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/datasets")
def datasets():
    """One dataset = one tab."""
    return jsonify(db.list_datasets())


@app.route("/api/chat", methods=["POST"])
def chat():
    """Every message carries the tab's dataset_id, so tabs never mix."""
    data = request.get_json(silent=True) or {}
    dataset_id = data.get("dataset_id")
    message = str(data.get("message", ""))
    if not isinstance(dataset_id, int) or not _dataset_exists(dataset_id):
        return jsonify({"error": "Unknown dataset tab."}), 404
    return jsonify(chat_engine.answer(dataset_id, message))


@app.route("/api/upload", methods=["POST"])
def upload():
    """Upload a CSV and create a new tab. Nothing is saved if any check fails."""
    file = request.files.get("file")
    name = request.form.get("name", "").strip()
    if not file or not name:
        return jsonify({"errors": ["Please choose a CSV file and type a tab name."]}), 400
    if db.get_dataset_id(name) is not None:
        return jsonify({"errors": ["A tab with that name already exists."]}), 400

    handle = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    handle.close()
    try:
        file.save(handle.name)
        dataset_id, errors = upload_dataset(handle.name, name, "uploaded in the web page")
    except Exception:
        return jsonify({"errors": ["Could not read that file."]}), 400
    finally:
        os.remove(handle.name)
    if errors:
        return jsonify({"errors": errors}), 400
    location = places.canonical(request.form.get("location", ""))
    if location:
        db.set_dataset_location(dataset_id, location)
    return jsonify({"dataset_id": dataset_id, "name": name})


@app.route("/api/datasets/<int:dataset_id>/info")
def dataset_info(dataset_id):
    """Header details for one dataset: records, date range, SAMPLE flag."""
    match = [d for d in db.list_datasets() if d["id"] == dataset_id]
    if not match:
        return jsonify({"error": "Unknown dataset."}), 404
    info = db.get_dataset_info(dataset_id)
    info["name"] = match[0]["name"]
    info["is_sample"] = "SAMPLE" in match[0]["name"].upper()
    info["location"] = db.get_dataset_location(dataset_id)
    info["location_label"] = places.label(info["location"])
    return jsonify(info)


@app.route("/api/datasets/<int:dataset_id>/history")
def dataset_history(dataset_id):
    """Saved messages of ONE dataset, so the chat survives a page reload."""
    if not _dataset_exists(dataset_id):
        return jsonify({"error": "Unknown dataset."}), 404
    return jsonify({"messages": db.get_chat_history(dataset_id)})


@app.route("/api/datasets/<int:dataset_id>/clear", methods=["POST"])
def dataset_clear(dataset_id):
    """Clear the chat of ONE dataset (rows are hidden, not deleted)."""
    if not _dataset_exists(dataset_id):
        return jsonify({"error": "Unknown dataset."}), 404
    db.clear_chat_history(dataset_id)
    return jsonify({"cleared": True})


@app.route("/api/datasets/<int:dataset_id>/export.csv")
def dataset_export(dataset_id):
    """Download one dataset as CSV: the monthly summary or all raw records."""
    match = [d for d in db.list_datasets() if d["id"] == dataset_id]
    if not match:
        return jsonify({"error": "Unknown dataset."}), 404
    kind = request.args.get("kind", "monthly")
    if kind not in ("monthly", "raw"):
        return jsonify({"error": "kind must be monthly or raw."}), 400
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", match[0]["name"]).strip("_") or "dataset"
    return Response(data_view.export_csv(dataset_id, kind, request.args.get("start"), request.args.get("end")), mimetype="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="%s_%s.csv"' % (safe, kind)})


@app.route("/api/places")
def places_list():
    """The places a dataset can come from (for the upload dropdown)."""
    return jsonify({"places": places.all_places()})


if __name__ == "__main__":
    db.init_db()
    predict("hello")        # load the model now, so the first question is not slow
    app.run(host="0.0.0.0", port=5000, debug=False)
