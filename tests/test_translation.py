from modules import response_builder as rb
from nlp.date_parser import parse_query


def _notes(lang):
    parsed = parse_query("Anong buwan pinakamataas ang presyo?", "2026-10-31")
    return " ".join(rb._translated_notes(lang, parsed))


def test_english_note_stays_english():
    assert "No dates were given" in _notes("en")


def test_filipino_note_has_no_english_sentence():
    text = _notes("fil")
    assert "No dates were given" not in text
    assert "Walang binanggit na petsa" in text


def test_taglish_note():
    assert "latest 6 months" in _notes("taglish")


def test_month_names_follow_the_language():
    assert rb.localize_months("fil", "June 2026 to May 2026") == "Hunyo 2026 to Mayo 2026"
    assert rb.localize_months("fil", "May problema") == "May problema"
    assert rb.localize_months("en", "June 2026") == "June 2026"
    assert rb.localize_months("taglish", "June 2026") == "June 2026"
