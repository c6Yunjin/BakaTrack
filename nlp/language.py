"""Language detector (hand-written, no AI): decides English, Filipino or Taglish for the reply.

It counts Filipino marker words and English marker words.
- 1 or more Filipino AND 2 or more English words -> 'taglish'
- otherwise the bigger count wins ('fil' or 'en')
- a tie (or no marker words) gives English
Month names are NOT counted, because people use them in every language.
"""
import re

FILIPINO_WORDS = set("""
ilang ilan ano anong ang ng mga sa na noong ngayon ngayong buwan presyo magkano
pinakamataas pinakamababa mula hanggang taon ulo kumusta salamat paalam tulong
paano bakit kailan nakaraang nakaraan ba po ako ko mo ipakita pakita gaano
""".split())

ENGLISH_WORDS = set("""
what how show many the is of price prices from to in highest lowest month months much
hello hi thanks thank bye help total last this next compare chart year are can you me my
""".split())


def detect_language(text):
    """Returns 'fil', 'en' or 'taglish'."""
    words = re.findall(r"[a-zñ]+", str(text).lower())
    fil = sum(1 for w in words if w in FILIPINO_WORDS)
    eng = sum(1 for w in words if w in ENGLISH_WORDS)
    if fil >= 1 and eng >= 2:          # both languages clearly present
        return "taglish"
    return "fil" if fil > eng else "en"
