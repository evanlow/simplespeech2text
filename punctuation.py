from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def _get_model():
    from deepmultilingualpunctuation import PunctuationModel

    return PunctuationModel()


def punctuate_text(text: str) -> tuple[str, bool, str | None]:
    cleaned = text.strip()
    if not cleaned:
        return "", False, None

    try:
        model = _get_model()
        return model.restore_punctuation(cleaned), True, None
    except Exception as exc:
        return cleaned, False, str(exc)
