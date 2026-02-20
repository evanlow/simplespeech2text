from __future__ import annotations

import os
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

DEFAULT_MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
REQUIRED_MODEL_DIRS = ("am", "conf", "graph", "ivector")


def _has_model_layout(path: Path) -> bool:
    return all((path / folder).is_dir() for folder in REQUIRED_MODEL_DIRS)


def _find_model_dir(search_root: Path) -> Path | None:
    if _has_model_layout(search_root):
        return search_root

    for candidate in search_root.rglob("*"):
        if candidate.is_dir() and _has_model_layout(candidate):
            return candidate

    return None


def _download_model_archive(model_url: str, zip_path: Path) -> None:
    with urllib.request.urlopen(model_url) as response, zip_path.open("wb") as target:
        shutil.copyfileobj(response, target)


def ensure_model_available(cache_dir: Path | None = None, model_url: str = DEFAULT_MODEL_URL) -> Path:
    configured_path = os.getenv("VOSK_MODEL_PATH")
    if configured_path:
        configured_model = Path(configured_path)
        if configured_model.is_dir():
            return configured_model
        raise FileNotFoundError(
            f"Configured VOSK_MODEL_PATH does not exist: {configured_model}"
        )

    cache_root = Path(cache_dir) if cache_dir is not None else Path(tempfile.gettempdir()) / "simpletext2speech_model"
    cache_root.mkdir(parents=True, exist_ok=True)

    existing_model = _find_model_dir(cache_root)
    if existing_model is not None:
        os.environ["VOSK_MODEL_PATH"] = str(existing_model)
        return existing_model

    zip_path = cache_root / "vosk-model.zip"
    _download_model_archive(model_url, zip_path)

    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(cache_root)

    model_path = _find_model_dir(cache_root)
    if model_path is None:
        raise RuntimeError(
            "Downloaded Vosk archive but could not find a valid model directory layout."
        )

    os.environ["VOSK_MODEL_PATH"] = str(model_path)
    return model_path
