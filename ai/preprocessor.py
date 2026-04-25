"""
ai/models/preprocessor.py
──────────────────────────────────────────────────────────────────────────────
JournalPreprocessor — mirrors the EXACT preprocessing pipeline used when the
PCD_Sleep_Disorder+Semantic Qdrant collection was built in nlpqdrantfinale.ipynb.

Order of operations (must not change — vectors break if you reorder):
  1. Lowercase
  2. Slang / internet-abbreviation expansion  (uppercase key lookup)
  3. Contractions expansion  (lowercase key lookup — NOTE: these only fire if
     the token is NOT already caught by step 2, because slang_dict.update()
     inserts them with lowercase keys while the lookup uses w.upper())
  4. Punctuation removal  (exact exclude set from notebook)
  5. Repeated-character collapse  (e.g. "sooooo" → "so")

WARNING: Do NOT add stopword removal or spelling correction here. Both are
commented-out in the notebook. Adding them would silently corrupt similarity
scores because the stored vectors were never built with those steps.
"""

import re


class JournalPreprocessor:
    # ── Full slang + contractions dict from nlpqdrantfinale.ipynb ─────────
    # This is the exact dict the notebook used to build Qdrant vectors.
    # Keys are UPPERCASE (internet abbreviations) or lowercase (contractions,
    # added via slang_dict.update(contractions_dict)).
    # The lookup function calls w.upper(), so uppercase abbreviations fire for
    # any casing of the input; lowercase contraction keys only fire if the word
    # happens to be uppercased before lookup — which never happens after
    # step 1 lowercases everything. Replicate this behaviour faithfully.
    SLANG_DICT: dict[str, str] = {
        # ── Internet abbreviations (uppercase keys) ──────────────────────
        "AFAIK":    "As Far As I Know",
        "AFK":      "Away From Keyboard",
        "ASAP":     "As Soon As Possible",
        "ATK":      "At The Keyboard",
        "ATM":      "At The Moment",
        "A3":       "Anytime, Anywhere, Anyplace",
        "BAK":      "Back At Keyboard",
        "BBL":      "Be Back Later",
        "BBS":      "Be Back Soon",
        "BFN":      "Bye For Now",
        "B4N":      "Bye For Now",
        "BRB":      "Be Right Back",
        "BRT":      "Be Right There",
        "BTW":      "By The Way",
        "B4":       "Before",
        "CU":       "See You",
        "CUL8R":    "See You Later",
        "CYA":      "See You",
        "FAQ":      "Frequently Asked Questions",
        "FC":       "Fingers Crossed",
        "FWIW":     "For What Its Worth",
        "FYI":      "For Your Information",
        "GAL":      "Get A Life",
        "GG":       "Good Game",
        "GN":       "Good Night",
        "GMTA":     "Great Minds Think Alike",
        "GR8":      "Great",
        "G9":       "Genius",
        "IC":       "I See",
        "ICQ":      "I Seek you",
        "ILU":      "I Love You",
        "IMHO":     "In My Honest Humble Opinion",
        "IMO":      "In My Opinion",
        "IOW":      "In Other Words",
        "IRL":      "In Real Life",
        "KISS":     "Keep It Simple Stupid",
        "LDR":      "Long Distance Relationship",
        "LMAO":     "Laughing my a off",
        "LOL":      "Laughing Out Loud",
        "LTNS":     "Long Time No See",
        "L8R":      "Later",
        "MTE":      "My Thoughts Exactly",
        "M8":       "Mate",
        "NRN":      "No Reply Necessary",
        "OIC":      "Oh I See",
        "PITA":     "Pain In The A",
        "PRT":      "Party",
        "PRW":      "Parents Are Watching",
        "QPSA":     "Que Pasa",
        "ROFL":     "Rolling On The Floor Laughing",
        "ROFLOL":   "Rolling On The Floor Laughing Out Loud",
        "ROTFLMAO": "Rolling On The Floor Laughing My A Off",
        "SK8":      "Skate",
        "STATS":    "Your sex and age",
        "ASL":      "Age Sex Location",
        "THX":      "Thank You",
        "TTFN":     "Ta Ta For Now",
        "TTYL":     "Talk To You Later",
        "U":        "You",
        "U2":       "You Too",
        "U4E":      "Yours For Ever",
        "WB":       "Welcome Back",
        "WTF":      "What The F",
        "WTG":      "Way To Go",
        "WUF":      "Where Are You From",
        "W8":       "Wait",
        "7K":       "Sick Laughter",
        "TFW":      "That feeling when",
        "MFW":      "My face when",
        "MRW":      "My reaction when",
        "IFYP":     "I feel your pain",
        "TNTL":     "Trying not to laugh",
        "JK":       "Just kidding",
        "IDC":      "I do not care",
        "ILY":      "I love you",
        "IMU":      "I miss you",
        "ADIH":     "Another day in hell",
        "ZZZ":      "Sleeping bored tired",
        "WYWH":     "Wish you were here",
        "TIME":     "Tears in my eyes",
        "BAE":      "Before anyone else",
        "FIMH":     "Forever in my heart",
        "BSAAW":    "Big smile and a wink",
        "BWL":      "Bursting with laughter",
        "BFF":      "Best friends forever",
        "CSL":      "Cannot stop laughing",
        # ── Contractions (lowercase keys — see module docstring) ─────────
        "i'm":      "i am",
        "can't":    "cannot",
        "don't":    "do not",
        "isn't":    "is not",
        "won't":    "will not",
        "i've":     "i have",
        "it's":     "it is",
        "couldn't": "could not",
    }

    # Exact punctuation exclude string from the notebook.
    # Note: '!' '.' '?' are intentionally kept (transformer context).
    _EXCLUDE: str = r'"#$%&\()*+,-/:;<=>@[\]^_`{|}~'

    # Build translation table once at class level — not per call.
    _TRANS_TABLE = str.maketrans("", "", _EXCLUDE)

    # ── Public API ─────────────────────────────────────────────────────────

    def clean(self, text: str) -> str:
        """
        Apply the full preprocessing pipeline.

        Args:
            text: Raw journal entry string.

        Returns:
            Cleaned string ready to be passed to the embedder.
        """
        if not isinstance(text, str) or not text.strip():
            return ""

        # Step 1 — Lowercase (must be first; matches df['text'].str.lower())
        text = text.lower()

        # Step 2+3 — Slang / contraction expansion
        text = self._expand_slang(text)

        # Step 4 — Punctuation removal
        text = self._remove_punctuation(text)

        # Step 5 — Repeated-character collapse ("sooooo" → "so")
        text = re.sub(r"(.)\1{2,}", r"\1", text)

        return text

    # ── Private helpers ────────────────────────────────────────────────────

    def _expand_slang(self, text: str) -> str:
        """
        Word-by-word lookup against SLANG_DICT using w.upper().
        Matches notebook behaviour: uppercase abbreviations are replaced;
        lowercase contraction keys in the dict are unreachable via upper()
        after the text is already lowercased — preserved intentionally.
        """
        words = text.split()
        return " ".join(
            self.SLANG_DICT[w.upper()] if w.upper() in self.SLANG_DICT else w
            for w in words
        )

    def _remove_punctuation(self, text: str) -> str:
        return text.translate(self._TRANS_TABLE)