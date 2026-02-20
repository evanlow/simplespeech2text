from __future__ import annotations

import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import Mock, patch

import core
from core import get_model, transcribe_file


class FakeRecognizer:
    def __init__(self, _model, _rate):
        self._accept_calls = 0
        self._save_words = False

    def SetWords(self, save_words):
        self._save_words = save_words

    def AcceptWaveform(self, _data):
        self._accept_calls += 1
        return self._accept_calls == 1

    def Result(self):
        if self._save_words:
            return '{"text":"hello","result":[{"word":"hello","start":0.0,"end":0.5}]}'
        return '{"text":"hello"}'

    def FinalResult(self):
        if self._save_words:
            return '{"text":"world","result":[{"word":"world","start":0.5,"end":1.0}]}'
        return '{"text":"world"}'


def create_mono_pcm_wav(path: Path, frames: int = 8000) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x00\x00" * frames)


class TestCore(unittest.TestCase):
    def setUp(self) -> None:
        core._model_instance = None

    def tearDown(self) -> None:
        core._model_instance = None

    def test_get_model_singleton_loads_once(self) -> None:
        with tempfile.TemporaryDirectory(prefix="test_model_dir_") as model_dir:
            model_path = Path(model_dir)
            fake_model = object()

            with patch("core._resolve_model_path", return_value=model_path), patch(
                "core.Model", return_value=fake_model
            ) as model_ctor:
                first = get_model()
                second = get_model()

        self.assertIs(first, second)
        model_ctor.assert_called_once_with(str(model_path))

    def test_transcribe_file_missing_raises(self) -> None:
        with self.assertRaises(FileNotFoundError):
            transcribe_file(Path("missing.wav"))

    def test_transcribe_file_returns_text(self) -> None:
        with tempfile.TemporaryDirectory(prefix="test_core_wav_") as temp_dir:
            wav_path = Path(temp_dir) / "audio.wav"
            create_mono_pcm_wav(wav_path)

            with patch("core.get_model", return_value=object()), patch(
                "core.KaldiRecognizer", side_effect=FakeRecognizer
            ):
                result = transcribe_file(wav_path, save_words=False)

        self.assertEqual(result.get("text"), "hello world")
        self.assertNotIn("result", result)

    def test_transcribe_file_returns_text_and_words(self) -> None:
        with tempfile.TemporaryDirectory(prefix="test_core_wav_") as temp_dir:
            wav_path = Path(temp_dir) / "audio.wav"
            create_mono_pcm_wav(wav_path)

            with patch("core.get_model", return_value=object()), patch(
                "core.KaldiRecognizer", side_effect=FakeRecognizer
            ):
                result = transcribe_file(wav_path, save_words=True)

        self.assertEqual(result.get("text"), "hello world")
        self.assertIn("result", result)
        self.assertEqual(len(result["result"]), 2)
        self.assertEqual(result["result"][0]["word"], "hello")
        self.assertEqual(result["result"][1]["word"], "world")


if __name__ == "__main__":
    unittest.main()
