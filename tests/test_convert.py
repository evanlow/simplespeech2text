from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from convert import convert_to_wav


class TestConvertToWav(unittest.TestCase):
    def test_missing_input_file_raises(self) -> None:
        missing = Path("does_not_exist.mp3")

        with self.assertRaises(FileNotFoundError):
            convert_to_wav(missing)

    def test_ffmpeg_missing_raises_runtime_error(self) -> None:
        with tempfile.TemporaryDirectory(prefix="test_convert_src_") as temp_dir:
            source_path = Path(temp_dir) / "sample.mp3"
            source_path.write_bytes(b"audio")

            with patch("convert.subprocess.run", side_effect=FileNotFoundError):
                with self.assertRaises(RuntimeError) as context:
                    convert_to_wav(source_path)

        self.assertIn("ffmpeg is not installed", str(context.exception))

    def test_ffmpeg_non_zero_exit_raises_runtime_error(self) -> None:
        with tempfile.TemporaryDirectory(prefix="test_convert_src_") as temp_dir:
            source_path = Path(temp_dir) / "sample.mp3"
            source_path.write_bytes(b"audio")

            mock_result = Mock(returncode=1, stderr="conversion failed")
            with patch("convert.subprocess.run", return_value=mock_result):
                with self.assertRaises(RuntimeError) as context:
                    convert_to_wav(source_path)

        self.assertIn("ffmpeg conversion failed", str(context.exception))

    def test_success_returns_generated_wav_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="test_convert_src_") as src_dir:
            source_path = Path(src_dir) / "sample.mp3"
            source_path.write_bytes(b"audio")

            def fake_run(command, capture_output, text, check):
                output_path = Path(command[-1])
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(b"RIFF")
                return Mock(returncode=0, stderr="")

            with patch("convert.subprocess.run", side_effect=fake_run):
                output_path = convert_to_wav(source_path)

        self.assertTrue(output_path.exists())
        self.assertEqual(output_path.suffix.lower(), ".wav")


if __name__ == "__main__":
    unittest.main()
