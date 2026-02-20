from __future__ import annotations

import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from model_setup import ensure_model_available


class TestModelSetup(unittest.TestCase):
    def setUp(self) -> None:
        self.previous_model_path = os.environ.get("VOSK_MODEL_PATH")
        os.environ.pop("VOSK_MODEL_PATH", None)

    def tearDown(self) -> None:
        if self.previous_model_path is None:
            os.environ.pop("VOSK_MODEL_PATH", None)
        else:
            os.environ["VOSK_MODEL_PATH"] = self.previous_model_path

    def _create_model_layout(self, root: Path) -> None:
        for folder in ("am", "conf", "graph", "ivector"):
            (root / folder).mkdir(parents=True, exist_ok=True)

    def test_returns_configured_model_path_when_present(self) -> None:
        with tempfile.TemporaryDirectory(prefix="model_path_") as temp_dir:
            model_dir = Path(temp_dir) / "my_model"
            self._create_model_layout(model_dir)
            os.environ["VOSK_MODEL_PATH"] = str(model_dir)

            result = ensure_model_available()

        self.assertEqual(result, model_dir)

    def test_raises_when_configured_model_path_missing(self) -> None:
        os.environ["VOSK_MODEL_PATH"] = "missing_model_dir"

        with self.assertRaises(FileNotFoundError):
            ensure_model_available()

    def test_uses_cached_model_without_download(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cache_model_") as temp_dir:
            cache_root = Path(temp_dir)
            cached_model = cache_root / "vosk-model-small-en-us-0.15"
            self._create_model_layout(cached_model)

            with patch("model_setup._download_model_archive") as download_mock:
                result = ensure_model_available(cache_dir=cache_root)

        self.assertEqual(result, cached_model)
        download_mock.assert_not_called()

    def test_downloads_and_extracts_when_missing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cache_download_") as temp_dir:
            cache_root = Path(temp_dir)

            def fake_download(_url: str, zip_path: Path) -> None:
                with zipfile.ZipFile(zip_path, "w") as archive:
                    for folder in ("am", "conf", "graph", "ivector"):
                        archive.writestr(
                            f"vosk-model-small-en-us-0.15/{folder}/.keep",
                            "",
                        )

            with patch("model_setup._download_model_archive", side_effect=fake_download):
                result = ensure_model_available(cache_dir=cache_root)
                self.assertTrue(result.is_dir())
                self.assertTrue((result / "am").is_dir())
                self.assertEqual(os.environ.get("VOSK_MODEL_PATH"), str(result))


if __name__ == "__main__":
    unittest.main()
