from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from punctuation import punctuate_text


class TestPunctuation(unittest.TestCase):
    def test_empty_input_returns_empty(self) -> None:
        self.assertEqual(punctuate_text(""), ("", False, None))
        self.assertEqual(punctuate_text("   "), ("", False, None))

    def test_punctuate_calls_model(self) -> None:
        fake_model = Mock()
        fake_model.restore_punctuation.return_value = "Hello, world."

        with patch("punctuation._get_model", return_value=fake_model):
            result = punctuate_text("hello world")

        self.assertEqual(result, ("Hello, world.", True, None))
        fake_model.restore_punctuation.assert_called_once_with("hello world")

    def test_fallback_returns_raw_text(self) -> None:
        with patch("punctuation._get_model", side_effect=RuntimeError("boom")):
            result = punctuate_text("hello world")

        self.assertEqual(result, ("hello world", False, "boom"))


if __name__ == "__main__":
    unittest.main()
