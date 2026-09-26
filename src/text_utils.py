"""Shared text helpers: content-word tokenization for the lexical signals
used by the router (question/chunk overlap) and the faithfulness metric."""

import re

STOPWORDS = frozenset(
    "a an the and or but of to in on for with is are was were be been "
    "do does did how what when where which who whom whose why can could "
    "should would will it its this that these those i you we they he she "
    "my your our their me him her us them at by from as not no yes".split()
)

CITATION_RE = re.compile(r"\[source:[^\]]+\]")


def _stem(word: str) -> str:
    """Tiny rule-based stemmer: plurals and common inflections.

    Naive on purpose (no nltk dependency) — good enough that "password" and
    "passwords", "limit" and "limits" count as the same token for overlap.
    """
    if len(word) > 4:
        if word.endswith("ies") and len(word) > 5:
            return word[:-3] + "y"  # policies -> policy
        for suffix in ("es", "ed", "ing", "ly"):
            if word.endswith(suffix) and len(word) - len(suffix) >= 3:
                return word[: -len(suffix)]
        if word.endswith("s") and not word.endswith("ss"):
            return word[:-1]
    return word


def content_tokens(text: str) -> set[str]:
    return {
        _stem(w.strip(".,;:!?()\"'").lower())
        for w in CITATION_RE.sub("", text).split()
        if len(w.strip(".,;:!?()\"'")) > 2
    } - STOPWORDS


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in CITATION_RE.sub("", text).replace("\n", " ").split(". ") if s.strip()]
