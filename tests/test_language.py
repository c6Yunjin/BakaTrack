from nlp.language import detect_language


def test_filipino_question():
    assert detect_language("Anong buwan pinakamataas ang presyo?") == "fil"


def test_english_question():
    assert detect_language("Show cattle prices from January to June 2026") == "en"


def test_taglish_with_more_filipino():
    assert detect_language("Ilan ang baka na ibebenta next month?") == "taglish"


def test_default_is_english():
    assert detect_language("???") == "en"


def test_taglish_compare_question():
    assert detect_language("Compare prices ng March at June 2026") == "taglish"


def test_one_borrowed_english_word_stays_filipino():
    assert detect_language("Anong buwan pinakamataas ang price?") == "fil"


def test_month_name_alone_does_not_make_english_filipino():
    assert detect_language("What is the price in Hunyo 2026?") == "en"
