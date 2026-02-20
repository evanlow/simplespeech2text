from __future__ import annotations

import json
import os
import threading
import wave
from pathlib import Path

from vosk import KaldiRecognizer, Model


_model_instance: Model | None = None
_model_lock = threading.Lock()


def _resolve_model_path() -> Path:
    model_path = os.getenv("VOSK_MODEL_PATH", "model")
    return Path(model_path)


def get_model() -> Model:
    global _model_instance

    if _model_instance is None:
        with _model_lock:
            if _model_instance is None:
                model_path = _resolve_model_path()
                if not model_path.exists() or not model_path.is_dir():
                    raise FileNotFoundError(
                        f"Vosk model directory not found: {model_path}. "
                        "Set VOSK_MODEL_PATH or place a model in ./model"
                    )
                _model_instance = Model(str(model_path))

    return _model_instance


def transcribe_file(wav_path: Path, save_words: bool = False) -> dict:
    source_path = Path(wav_path)

    if not source_path.exists() or not source_path.is_file():
        raise FileNotFoundError(f"WAV file not found: {source_path}")

    with wave.open(str(source_path), "rb") as wav_file:
        if wav_file.getnchannels() != 1:
            raise ValueError("WAV file must be mono (1 channel).")
        if wav_file.getsampwidth() != 2:
            raise ValueError("WAV file must be 16-bit PCM (sample width = 2).")
        if wav_file.getcomptype() != "NONE":
            raise ValueError("WAV file must be uncompressed PCM.")

        recognizer = KaldiRecognizer(get_model(), wav_file.getframerate())
        recognizer.SetWords(save_words)

        final_chunks: list[dict] = []

        while True:
            data = wav_file.readframes(4000)
            if len(data) == 0:
                break

            if recognizer.AcceptWaveform(data):
                final_chunks.append(json.loads(recognizer.Result()))

        final_chunks.append(json.loads(recognizer.FinalResult()))

    text = " ".join(
        chunk.get("text", "").strip()
        for chunk in final_chunks
        if chunk.get("text", "").strip()
    ).strip()

    response = {"text": text}

    if save_words:
        words: list[dict] = []
        for chunk in final_chunks:
            chunk_words = chunk.get("result")
            if isinstance(chunk_words, list):
                words.extend(chunk_words)
        response["result"] = words

    return response
