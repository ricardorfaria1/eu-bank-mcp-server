"""Text normalisation shared by the seed, the repository callers and the guards."""

import unicodedata


def normalise(s: str) -> str:
    """Lower-case, strip accents and collapse whitespace: "  João  Pedro" -> "joao pedro"."""
    decomposed = unicodedata.normalize("NFKD", s)
    without_marks = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(without_marks.lower().split())
