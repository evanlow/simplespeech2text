from __future__ import annotations

from typing import Iterable


def _sentence_case(token: str) -> str:
    if not token:
        return token
    return token[0].upper() + token[1:]


def _build_from_words(words: Iterable[dict], gap_period: float = 0.8) -> str:
    output: list[str] = []
    previous_end: float | None = None
    start_sentence = True

    for word_info in words:
        token = str(word_info.get("word", "")).strip()
        if not token:
            continue

        start = word_info.get("start")
        if previous_end is not None and isinstance(start, (int, float)):
            gap = start - previous_end
            if gap >= gap_period and output:
                output[-1] = output[-1].rstrip(" ,") + "."
                start_sentence = True

        if start_sentence:
            token = _sentence_case(token)
            start_sentence = False

        output.append(token)

        end = word_info.get("end")
        if isinstance(end, (int, float)):
            previous_end = end

    if output:
        output[-1] = output[-1].rstrip(" ,") + "."

    return " ".join(output).strip()


def _build_from_text(text: str, words_per_sentence: int = 20) -> str:
    tokens = [token for token in text.split() if token]
    if not tokens:
        return ""

    sentences: list[str] = []
    for i in range(0, len(tokens), words_per_sentence):
        segment = tokens[i : i + words_per_sentence]
        if not segment:
            continue
        segment[0] = _sentence_case(segment[0])
        sentences.append(" ".join(segment).rstrip(" ,") + ".")

    return " ".join(sentences).strip()


def punctuate_text(text: str, words: list[dict] | None = None) -> tuple[str, bool, str | None]:
    cleaned = text.strip()
    if not cleaned:
        return "", False, None

    if words:
        punctuated = _build_from_words(words)
    else:
        punctuated = _build_from_text(cleaned)

    return punctuated or cleaned, True, None
