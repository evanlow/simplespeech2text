from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from punctuation import punctuate_text


class TestPunctuation(unittest.TestCase):
    def test_empty_input_returns_empty(self) -> None:
        self.assertEqual(punctuate_text(""), "")
        self.assertEqual(punctuate_text("   "), "")

    def test_punctuate_calls_model(self) -> None:
        fake_model = Mock()
        fake_model.restore_punctuation.return_value = "Hello, world."

        with patch("punctuation._get_model", return_value=fake_model):
            result = punctuate_text("hello world")

        self.assertEqual(result, "Hello, world.")
        fake_model.restore_punctuation.assert_called_once_with("hello world")


if __name__ == "__main__":
    unittest.main()
