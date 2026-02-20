from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def _get_model():
    from deepmultilingualpunctuation import PunctuationModel

    return PunctuationModel()


def punctuate_text(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return ""

    model = _get_model()
    return model.restore_punctuation(cleaned)
