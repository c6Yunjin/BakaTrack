"""Small talk rules (hand-written, no AI model).

A short, whole message like "thank you" or "who are you" gets a friendly reply that points back
to cattle topics. Only a WHOLE short message can match (6 words or fewer), so a real question
is never taken over by a rule. Everything else goes to the neural network as before.
"""
import re

HOW_EN = {"how are you", "how are you doing", "how are u", "how r u", "how is it going", "hows it going"}
HOW_FIL = {"kumusta ka", "kamusta ka", "musta ka", "kumusta ka na", "kamusta ka na"}
WHO_EN = {"who are you", "what are you", "what is your name", "whats your name", "what are you called"}
WHO_FIL = {"sino ka", "sino ka ba", "ano ka", "ano ka ba", "ano pangalan mo", "ano ang pangalan mo"}
THANKS_EN = {"thank you", "thanks", "thanks a lot", "thank you so much", "thank you very much", "ty"}
THANKS_FIL = {"salamat", "maraming salamat"}
ACK = {"ok", "okay", "okie", "oks", "k", "kk", "noted", "got it", "sige", "o sige", "wow", "nice",
       "wow nice", "great", "cool", "galing", "ayos", "good", "okay lang"}
ASK_EN = {"can i ask something", "can i ask a question", "i have a question", "i want to ask",
          "i wanna ask", "may i ask", "i want to ask something"}
ASK_FIL = {"magtatanong lang ako", "magtanong lang ako", "pwede magtanong", "pwede bang magtanong",
           "may tanong ako", "may itatanong ako", "magtatanong ako", "gusto kong magtanong"}

# (intent, phrases, language of the reply; None = detect from the message)
RULES = [
    ("smalltalk_how_are_you", HOW_EN, "en"), ("smalltalk_how_are_you", HOW_FIL, "fil"),
    ("smalltalk_who_are_you", WHO_EN, "en"), ("smalltalk_who_are_you", WHO_FIL, "fil"),
    ("smalltalk_thanks", THANKS_EN, "en"), ("smalltalk_thanks", THANKS_FIL, "fil"),
    ("smalltalk_ack", ACK, None),
    ("smalltalk_ask", ASK_EN, "en"), ("smalltalk_ask", ASK_FIL, "fil"),
]
INTENTS = {rule[0] for rule in RULES}

GREETING_PREFIXES = ["good morning", "good afternoon", "good evening", "magandang umaga",
                     "magandang hapon", "magandang gabi", "hello", "hi", "hey",
                     "kumusta", "kamusta", "musta"]

REPLIES = {
    "smalltalk_how_are_you": {
        "en": "I'm doing fine, thanks for asking! I can help with cattle kilos, head count and prices from the data in this tab. What would you like to know?",
        "fil": "Mabuti naman, salamat! Makakatulong ako sa kilo, bilang ng baka at presyo mula sa datos ng tab na ito. Ano ang gusto mong malaman?",
        "taglish": "Okay naman ako, thanks! Pwede kitang tulungan sa kilos, head count at presyo ng baka mula sa data ng dataset na ito. Ano ang gusto mong malaman?"},
    "smalltalk_who_are_you": {
        "en": "I am BakaTrack, a cattle price chatbot. I answer questions about kilos, head count, prices, ratings and forecasts from the data in this tab. I run on my own trained model, with no online AI service.",
        "fil": "Ako si BakaTrack, isang chatbot para sa presyo ng baka. Sinasagot ko ang mga tanong tungkol sa kilo, bilang ng baka, presyo, rating at pagtataya mula sa datos ng tab na ito. Gumagana ako sa sarili kong trained na model, walang online AI service.",
        "taglish": "Ako si BakaTrack, isang cattle price chatbot. Sinasagot ko ang tanong tungkol sa kilos, head count, price, rating at forecast mula sa data ng dataset na ito. Gumagana ako sa sarili kong trained model, walang online AI service."},
    "smalltalk_thanks": {
        "en": "You're welcome! Ask me anything else about cattle kilos, head count or prices.",
        "fil": "Walang anuman! Magtanong ka pa tungkol sa kilo, bilang ng baka o presyo.",
        "taglish": "You're welcome! Magtanong ka pa tungkol sa kilos, head count o presyo."},
    "smalltalk_ack": {
        "en": "Got it! Ask me about cattle kilos, head count or prices whenever you're ready.",
        "fil": "Sige! Magtanong ka lang tungkol sa kilo, bilang ng baka o presyo kapag handa ka na.",
        "taglish": "Sige! Tanong ka lang tungkol sa kilos, head count o presyo anytime."},
    "smalltalk_ask": {
        "en": "Of course, go ahead! You can ask about cattle kilos, head count, prices, ratings or forecasts.",
        "fil": "Sige, magtanong ka lang! Maaari mong itanong ang kilo, bilang ng baka, presyo, rating o pagtataya.",
        "taglish": "Sure, go ahead! Pwede mong itanong ang kilos, head count, price, rating o forecast."},
}


def _normalize(text):
    text = str(text).lower().replace("'", "").replace("\u2019", "")
    words = re.findall(r"[a-z\u00f1]+", text)
    return " ".join(w for w in words if w not in ("po", "ha"))


def _strip_greeting(text):
    """Remove greeting words at the start: 'good evening magtatanong lang ako' -> 'magtatanong lang ako'."""
    changed = True
    while changed:
        changed = False
        for prefix in GREETING_PREFIXES:
            if text.startswith(prefix + " "):
                text = text[len(prefix) + 1:]
                changed = True
    return text


def match(message):
    """Returns (intent, language_hint). (None, None) when no rule fits."""
    text = _normalize(message)
    if not text or len(text.split()) > 6:
        return None, None
    for intent, phrases, lang in RULES:
        if text in phrases:
            return intent, lang
    rest = _strip_greeting(text)
    if rest != text:
        for intent, phrases, lang in RULES:
            if intent == "smalltalk_ask" and rest in phrases:
                return intent, lang
    return None, None


def reply(intent, lang):
    return REPLIES[intent].get(lang, REPLIES[intent]["en"])
