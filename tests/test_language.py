from nlp.language import detect_language


def test_filipino_question():
    assert detect_language("Anong buwan pinakamataas ang presyo?") == "fil"


def test_english_question():
    assert detect_language("Show cattle prices from January to June 2026") == "en"


def test_taglish_with_more_filipino():
    assert detect_language("Ilan ang baka na ibebenta next month?") == "fil"


def test_default_is_english():
    assert detect_language("???") == "en"
