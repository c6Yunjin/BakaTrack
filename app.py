"""BakaTrack web app (Step 6b). Flask serves the page and three small routes."""
import os
import tempfile

from flask import Flask, jsonify, render_template, request

from database import db
from modules import chat_engine
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
    return jsonify({"dataset_id": dataset_id, "name": name})


if __name__ == "__main__":
    db.init_db()
    predict("hello")        # load the model now, so the first question is not slow
    app.run(host="0.0.0.0", port=5000, debug=False)
