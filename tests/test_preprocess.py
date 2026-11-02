# TC-01 and a few extra cleaning checks.
from nlp.preprocess import clean_text


def test_tc01_cleaning():
    assert clean_text("  KAILAN ang auction??? ") == "kailan ang auction"


def test_spelling_fix():
    assert clean_text("Mag-kano po ang presyo?") == "magkano ang presyo"


def test_symbols_removed():
    assert clean_text("Show chart!!!") == "show chart"
