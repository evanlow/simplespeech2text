from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from download import download_from_url


class TestDownloadFromUrl(unittest.TestCase):
    def test_empty_url_raises_value_error(self) -> None:
        with self.assertRaises(ValueError) as context:
            download_from_url("")
        self.assertIn("cannot be empty", str(context.exception))

    def test_invalid_url_format_raises_value_error(self) -> None:
        with self.assertRaises(ValueError) as context:
            download_from_url("not-a-valid-url")
        self.assertIn("Invalid URL format", str(context.exception))

    def test_request_exception_raises_runtime_error(self) -> None:
        import requests
        
        with patch("download.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
            
            with self.assertRaises(RuntimeError) as context:
                download_from_url("https://example.com/file.mp3")
            
            self.assertIn("Failed to download", str(context.exception))

    def test_http_error_raises_runtime_error(self) -> None:
        import requests
        
        with patch("download.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
            mock_get.return_value = mock_response
            
            with self.assertRaises(RuntimeError) as context:
                download_from_url("https://example.com/missing.mp3")
            
            self.assertIn("Failed to download", str(context.exception))

    def test_successful_download_returns_path(self) -> None:
        fake_content = b"fake audio content"
        
        with patch("download.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.iter_content.return_value = [fake_content]
            mock_get.return_value = mock_response
            
            result_path = download_from_url("https://example.com/audio.mp3")
        
        self.assertTrue(result_path.exists())
        self.assertEqual(result_path.suffix.lower(), ".mp3")
        self.assertEqual(result_path.read_bytes(), fake_content)

    def test_url_without_extension_uses_tmp(self) -> None:
        fake_content = b"content"
        
        with patch("download.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.iter_content.return_value = [fake_content]
            mock_get.return_value = mock_response
            
            result_path = download_from_url("https://example.com/resource")
        
        self.assertTrue(result_path.exists())
        self.assertEqual(result_path.suffix.lower(), ".tmp")

    def test_chunked_download_combines_chunks(self) -> None:
        chunk1 = b"first"
        chunk2 = b"second"
        chunk3 = b"third"
        
        with patch("download.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.iter_content.return_value = [chunk1, chunk2, chunk3]
            mock_get.return_value = mock_response
            
            result_path = download_from_url("https://example.com/file.wav")
        
        self.assertEqual(result_path.read_bytes(), chunk1 + chunk2 + chunk3)


if __name__ == "__main__":
    unittest.main()
