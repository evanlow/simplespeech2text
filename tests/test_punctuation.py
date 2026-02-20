from __future__ import annotations

import unittest

from punctuation import punctuate_text


class TestPunctuation(unittest.TestCase):
    def test_empty_input_returns_empty(self) -> None:
        self.assertEqual(punctuate_text(""), ("", False, None))
        self.assertEqual(punctuate_text("   "), ("", False, None))

    def test_punctuate_with_words(self) -> None:
        words = [
            {"word": "hello", "start": 0.0, "end": 0.3},
            {"word": "world", "start": 0.4, "end": 0.6},
            {"word": "next", "start": 1.6, "end": 1.8},
        ]

        result = punctuate_text("hello world next", words)

        self.assertEqual(result, ("Hello world. Next.", True, None))

    def test_punctuate_without_words(self) -> None:
        result = punctuate_text("one two three four")

        self.assertEqual(result, ("One two three four.", True, None))


if __name__ == "__main__":
    unittest.main()
