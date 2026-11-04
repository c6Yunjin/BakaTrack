"""Easter eggs (hand-written rules, no AI model).

A short, whole message like "gooood morning everyone!" or "tell me a joke" gets a fun reply.
Only WHOLE short messages can match, so a real question is never taken over by an egg.
Set ENABLED = False to switch every egg off (for example, for a serious defense run).
"""
import random
import re

ENABLED = True

FILLERS = {"po", "ha", "please", "pls", "plz", "paki", "pakiusap", "nga", "naman", "mo", "kindly"}

INTENT_GREETING = "egg_greeting"
INTENT_RICKROLL = "egg_rickroll"
INTENT_COWS = "egg_cows"
INTENT_COMPLY = "egg_comply"
INTENT_JOKE = "egg_joke"
INTENT_WHO = "egg_who_made_you"
INTENT_GRADE = "egg_grade"
INTENT_LIFE = "egg_life"
INTENT_SING = "egg_sing"
INTENTS = {INTENT_GREETING, INTENT_RICKROLL, INTENT_COWS, INTENT_COMPLY, INTENT_JOKE,
           INTENT_WHO, INTENT_GRADE, INTENT_LIFE, INTENT_SING}

# "goooood morning", "gooood evening everyone": 3 or more o's, then a time word, then up to 3 words
STRETCHED = re.compile(r"^go{3,}d (morning|afternoon|evening|day|night)(?: [a-z0-9\u00f1]+){0,3}$")

RICKROLL = {"rickroll", "rick roll", "rickrolled", "rickroll me", "rick roll me", "play rickroll",
            "play rick roll", "rickroll mp4", "play rickroll mp4", "rick astley"}
COWS = {"cow animation", "cows animation", "play animation", "show animation", "play cow animation",
        "cow party", "cows", "moo animation"}
COMPLY = {"i cant comply", "cant comply", "cannot comply", "i cannot comply", "i can not comply",
          "unable to comply", "i am unable to comply", "hindi ako makakasunod", "di ako makakasunod"}
JOKE = {"tell me a joke", "tell a joke", "joke", "another joke", "tell me another joke",
        "tell me joke", "magbiro ka", "pabiro", "magbiro ka ulit", "magkwento ka ng joke"}
WHO = {"who made you", "who built you", "who created you", "who developed you",
       "who is your developer", "who is your creator", "sino gumawa sayo", "sino gumawa sa iyo",
       "sino ang gumawa sayo", "sino ang gumawa sa iyo"}
GRADE = {"1 0", "10", "grade me", "give me 1 0", "give me a 1 0", "pass us", "pasado na"}
LIFE = {"meaning of life", "what is the meaning of life", "whats the meaning of life",
        "the meaning of life", "ano ang kahulugan ng buhay"}
SING = {"sing", "sing for me", "sing a song", "can you sing", "kumanta ka", "kumanta", "kanta ka", "kanta"}

SETS = [(INTENT_RICKROLL, RICKROLL), (INTENT_COWS, COWS), (INTENT_COMPLY, COMPLY), (INTENT_JOKE, JOKE),
        (INTENT_WHO, WHO), (INTENT_GRADE, GRADE), (INTENT_LIFE, LIFE), (INTENT_SING, SING)]

JOKES = {
    "en": ["Why did the cow go to space? To see the Moooon.",
           "What do you call a cow that does math? A Moo-ltiplication table.",
           "Where do cows go to study? Moo-niversity.",
           "Why are cattle prices like a good song? Because they always have a rising chorus. Check the chart!"],
    "fil": ["Magkano ang baka ngayon? Baka mahal, baka mura. Tingnan mo ang chart!",
            "Anong tawag sa baka na magaling sa math? Baka-lculator!",
            "Bakit laging kalmado ang baka sa palengke? Kasi baka-sakali lang ang presyo niya."],
}

REPLIES = {
    INTENT_COMPLY: {"en": "Daaaahil?", "fil": "Daaaahil?"},
    INTENT_RICKROLL: {"en": "You just got rickrolled. \U0001F604 Press the X or Esc to close the video.",
                      "fil": "Na-rickroll ka! \U0001F604 Pindutin ang X o Esc para isara ang video."},
    INTENT_COWS: {"en": "Moo-ve over, here come the cows! \U0001F404",
                  "fil": "Padaan ang mga baka! \U0001F404"},
    INTENT_WHO: {"en": "I was built from scratch as a final project for CS 312 and CSE 103. Ask my developer for the details!",
                 "fil": "Binuo ako mula sa simula bilang final project para sa CS 312 at CSE 103. Itanong mo sa developer ko para sa mga detalye!"},
    INTENT_GRADE: {"en": "That is up to the panel, but all my tests pass. \U0001F604",
                   "fil": "Panel ang magpapasya niyan, pero pasado ang lahat ng test ko. \U0001F604"},
    INTENT_LIFE: {"en": "42. But for the price per kilo, ask me about the data. \U0001F604",
                  "fil": "42. Pero para sa presyo kada kilo, itanong mo sa akin ang datos. \U0001F604"},
    INTENT_SING: {"en": "I cannot carry a tune, but I can forecast next month's price. Try \"forecast next month\".",
                  "fil": "Hindi ako marunong kumanta, pero kaya kong magtaya ng presyo sa susunod na buwan. Subukan mo ang \"forecast next month\"."},
}
WIDGETS = {INTENT_RICKROLL: "rickroll", INTENT_COWS: "cows"}


def _normalize(text):
    text = str(text).lower().replace("'", "").replace("\u2019", "")
    words = re.findall(r"[a-z0-9\u00f1]+", text)
    return " ".join(w for w in words if w not in FILLERS)


def match(message):
    """Returns the egg intent, or None when no egg fits."""
    if not ENABLED:
        return None
    text = _normalize(message)
    if not text or len(text.split()) > 8:
        return None
    if STRETCHED.match(text):
        return INTENT_GREETING
    if text.startswith("never gonna"):
        return INTENT_RICKROLL
    for intent, phrases in SETS:
        if text in phrases:
            return intent
    return None


def reply(intent, message, lang):
    """Returns (text, widget). The widget is None, or {'widget': 'egg', 'kind': ...} for the page."""
    if intent == INTENT_GREETING:
        when = STRETCHED.match(_normalize(message)).group(1)
        text = "Good %s, Maam Marianne! :) I am BakaTrack. Ask me about cattle kilos, head count or prices (and yes, I counted every o)." % when
        return text, None
    if intent == INTENT_JOKE:
        pool = JOKES["fil"] if lang == "fil" else (JOKES["en"] + JOKES["fil"] if lang == "taglish" else JOKES["en"])
        return random.choice(pool), None
    text = REPLIES[intent].get(lang, REPLIES[intent]["en"])
    kind = WIDGETS.get(intent)
    return text, ({"widget": "egg", "kind": kind} if kind else None)
