"""Language detector (hand-written, no AI): decides English or Filipino for the reply.

It counts Filipino marker words and English marker words. The bigger count wins.
A tie (or no marker words) gives English. Taglish goes to whichever side has more words.
"""
import re

FILIPINO_WORDS = set("""
ilang ilan ano anong ang ng mga sa na noong ngayon ngayong buwan presyo magkano
pinakamataas pinakamababa mula hanggang taon ulo kumusta salamat paalam tulong
paano bakit kailan nakaraang nakaraan ba po ako ko mo ipakita pakita gaano
enero pebrero marso abril mayo hunyo hulyo agosto setyembre oktubre nobyembre disyembre
""".split())

ENGLISH_WORDS = set("""
what how show many the is of price prices from to in highest lowest month months much
hello hi thanks thank bye help total last this next compare chart year are can you me my
""".split())


def detect_language(text):
    """Returns 'fil' or 'en'."""
    words = re.findall(r"[a-zñ]+", str(text).lower())
    fil = sum(1 for w in words if w in FILIPINO_WORDS)
    eng = sum(1 for w in words if w in ENGLISH_WORDS)
    return "fil" if fil > eng else "en"
