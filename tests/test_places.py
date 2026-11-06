import sqlite3

import pandas as pd

from database import db
from modules import places


def test_the_34_places():
    assert len(places.PLACES) == 34
    assert sum(1 for p in places.PLACES if p["kind"] == "city") == 5
    assert len({p["name"] for p in places.PLACES}) == 34
    names = {p["name"] for p in places.PLACES}
    assert {"Lipa City", "Batangas City", "Tanauan City", "Santo Tomas City", "Calaca City",
            "Padre Garcia", "Mabini", "Tuy"} <= names


def test_find_place_handles_spelling_variants():
    assert places.find_place("show data for Lipa") == "Lipa City"
    assert places.find_place("data of the City of Lipa") == "Lipa City"
    assert places.find_place("Sto. Tomas records") == "Santo Tomas City"
    assert places.find_place("mataas na kahoy") == "Mataasnakahoy"
    assert places.find_place("sta. teresita") == "Santa Teresita"
    assert places.find_place("Padre Garcia") == "Padre Garcia"
    assert places.find_place("show data for Cebu") is None


def test_batangas_city_is_not_the_province():
    assert places.find_place("Batangas City") == "Batangas City"
    assert places.find_place("city of batangas") == "Batangas City"
    assert places.find_place("data for batangas") == places.PROVINCE
    assert places.find_place("batangas province") == places.PROVINCE


def test_canonical_and_label_and_dropdown_list():
    assert places.canonical("lipa") == "Lipa City"
    assert places.canonical("Batangas") == "Batangas"
    assert places.canonical("xyz") is None and places.canonical("") is None
    assert places.label("Lipa City") == "Lipa City, Batangas" and places.label(None) is None
    assert places.label("Batangas") == "Batangas (province-wide)"
    listed = places.all_places()
    assert len(listed) == 35 and listed[0]["name"] == "Batangas"


def make_dataset(tmp_path, monkeypatch, name="A"):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    df = pd.DataFrame({"date": ["2026-01-15"], "head_count": [10], "total_kilos": [1000.0],
                       "price_per_kilo": [100.0]})
    return db.create_dataset_with_records(name, "test", df)


def test_dataset_location_is_saved_per_dataset(tmp_path, monkeypatch):
    a = make_dataset(tmp_path, monkeypatch, "A")
    b = make_dataset(tmp_path, monkeypatch, "B")
    assert db.get_dataset_location(a) is None
    db.set_dataset_location(a, "Lipa City")
    assert db.get_dataset_location(a) == "Lipa City" and db.get_dataset_location(b) is None
    db.set_dataset_location(a, None)
    assert db.get_dataset_location(a) is None


def test_old_database_is_upgraded_without_losing_datasets(tmp_path, monkeypatch):
    path = str(tmp_path / "old.db")
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE datasets (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE,"
                 " source TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("INSERT INTO datasets (name, source) VALUES ('Old', 'x')")
    conn.commit()
    conn.close()
    monkeypatch.setattr(db, "DB_PATH", path)
    db.init_db()
    assert db.get_dataset_location(1) is None
    db.set_dataset_location(1, "Padre Garcia")
    assert db.get_dataset_location(1) == "Padre Garcia"
    assert [d["name"] for d in db.list_datasets()] == ["Old"]
