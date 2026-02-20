from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def _get_model():
    try:
        from transformers.pipelines import TokenClassificationPipeline

        original_sanitize = TokenClassificationPipeline._sanitize_parameters

        def _sanitize_parameters_compat(self, **kwargs):
            if "grouped_entities" in kwargs and "aggregation_strategy" not in kwargs:
                grouped = kwargs.pop("grouped_entities")
                kwargs["aggregation_strategy"] = "simple" if grouped else "none"
            return original_sanitize(self, **kwargs)

        TokenClassificationPipeline._sanitize_parameters = _sanitize_parameters_compat
    except Exception:
        # If transformers isn't available yet, let the model init raise a clear error.
        pass

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
