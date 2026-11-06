"""The 34 cities and municipalities of Batangas (5 cities + 29 municipalities, per the PSA).

Used for a dataset's location and for questions like "show data for Lipa".
Spelling variants are matched ("Lipa City", "city of Lipa", "Sto. Tomas"). Plain "Batangas"
means the whole province; "Batangas City" is the capital city.
"""
import re

PROVINCE = "Batangas"

# (base name, kind, extra aliases)
_RAW = [
    ("Batangas", "city", ["city of batangas"]), ("Lipa", "city", []), ("Tanauan", "city", []),
    ("Santo Tomas", "city", ["sto tomas"]), ("Calaca", "city", []),
    ("Agoncillo", "municipality", []), ("Alitagtag", "municipality", []), ("Balayan", "municipality", []),
    ("Balete", "municipality", []), ("Bauan", "municipality", []), ("Calatagan", "municipality", []),
    ("Cuenca", "municipality", []), ("Ibaan", "municipality", []), ("Laurel", "municipality", []),
    ("Lemery", "municipality", []), ("Lian", "municipality", []), ("Lobo", "municipality", []),
    ("Mabini", "municipality", []), ("Malvar", "municipality", []),
    ("Mataasnakahoy", "municipality", ["mataas na kahoy"]), ("Nasugbu", "municipality", []),
    ("Padre Garcia", "municipality", []), ("Rosario", "municipality", []), ("San Jose", "municipality", []),
    ("San Juan", "municipality", []), ("San Luis", "municipality", []), ("San Nicolas", "municipality", []),
    ("San Pascual", "municipality", []), ("Santa Teresita", "municipality", ["sta teresita"]),
    ("Taal", "municipality", []), ("Talisay", "municipality", []), ("Taysan", "municipality", []),
    ("Tingloy", "municipality", []), ("Tuy", "municipality", []),
]
PROVINCE_ALIASES = ["batangas province", "province of batangas", "lalawigan ng batangas",
                    "probinsya ng batangas", "batangas"]


def _norm(text):
    text = str(text).lower().replace("'", "").replace("\u2019", "")
    return " ".join(re.findall(r"[a-z0-9\u00f1]+", text))


PLACES = []        # [{"name": display name, "kind": "city" or "municipality"}]
ALIAS_MAP = {}     # normalized spelling -> display name
for _base, _kind, _extra in _RAW:
    _display = _base + " City" if _kind == "city" else _base
    PLACES.append({"name": _display, "kind": _kind})
    _aliases = [_display, _base + " City", "city of " + _base] if _kind == "city" else [_base]
    if _base != "Batangas":                       # bare "Batangas" means the province
        _aliases.append(_base)
    for _alias in _aliases + _extra:
        ALIAS_MAP[_norm(_alias)] = _display
for _alias in PROVINCE_ALIASES:
    ALIAS_MAP[_alias] = PROVINCE
_ORDERED = sorted(ALIAS_MAP.items(), key=lambda item: -len(item[0]))     # longest spelling first


def find_place(text):
    """The place named inside a message (display name, or PROVINCE), else None."""
    padded = " " + _norm(text) + " "
    for alias, display in _ORDERED:
        if " " + alias + " " in padded:
            return display
    return None


def canonical(text):
    """A whole text that is exactly one place spelling -> its display name, else None."""
    return ALIAS_MAP.get(_norm(text))


def label(name):
    """'Lipa City' -> 'Lipa City, Batangas'. No location -> None."""
    if not name:
        return None
    return "Batangas (province-wide)" if name == PROVINCE else name + ", Batangas"


def all_places():
    """For the upload dropdown: the province first, then the cities, then the municipalities."""
    out = [{"name": PROVINCE, "label": "Batangas (province-wide)", "kind": "province"}]
    for kind in ("city", "municipality"):
        group = sorted((p for p in PLACES if p["kind"] == kind), key=lambda p: p["name"])
        out += [{"name": p["name"], "label": p["name"] + (" (city)" if kind == "city" else ""),
                 "kind": kind} for p in group]
    return out
