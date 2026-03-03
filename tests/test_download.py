from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from download import download_from_url, _convert_google_drive_url


class TestGoogleDriveUrlConversion(unittest.TestCase):
    def test_converts_sharing_url_with_view(self) -> None:
        """Test conversion of standard sharing URL with /view."""
        url = "https://drive.google.com/file/d/1IYXWXmdMPVkO36fMnioxHT3BWPZtrJ9d/view?usp=sharing"
        result = _convert_google_drive_url(url)
        expected = "https://drive.google.com/uc?export=download&id=1IYXWXmdMPVkO36fMnioxHT3BWPZtrJ9d"
        self.assertEqual(result, expected)
    
    def test_converts_sharing_url_with_edit(self) -> None:
        """Test conversion of sharing URL with /edit."""
        url = "https://drive.google.com/file/d/abc123XYZ-_/edit"
        result = _convert_google_drive_url(url)
        expected = "https://drive.google.com/uc?export=download&id=abc123XYZ-_"
        self.assertEqual(result, expected)
    
    def test_converts_open_id_format(self) -> None:
        """Test conversion of open?id= format."""
        url = "https://drive.google.com/open?id=abc123XYZ"
        result = _convert_google_drive_url(url)
        expected = "https://drive.google.com/uc?export=download&id=abc123XYZ"
        self.assertEqual(result, expected)
    
    def test_leaves_direct_download_url_unchanged(self) -> None:
        """Test that direct download URLs are not modified."""
        url = "https://drive.google.com/uc?export=download&id=abc123"
        result = _convert_google_drive_url(url)
        self.assertEqual(result, url)
    
    def test_leaves_non_google_drive_url_unchanged(self) -> None:
        """Test that non-Google Drive URLs are not modified."""
        url = "https://example.com/file.mp3"
        result = _convert_google_drive_url(url)
        self.assertEqual(result, url)


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
            mock_response.headers = {'Content-Type': 'audio/mpeg'}
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
            mock_response.headers = {'Content-Type': 'application/octet-stream'}
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
            mock_response.headers = {'Content-Type': 'audio/mpeg'}
            mock_get.return_value = mock_response
            
            result_path = download_from_url("https://example.com/file.wav")
        
        self.assertEqual(result_path.read_bytes(), chunk1 + chunk2 + chunk3)

    def test_google_drive_sharing_url_converted(self) -> None:
        """Test that Google Drive sharing URLs are converted to direct download."""
        fake_content = b"audio data"
        sharing_url = "https://drive.google.com/file/d/abc123/view?usp=sharing"
        
        with patch("download.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.iter_content.return_value = [fake_content]
            mock_response.headers = {'Content-Type': 'audio/mpeg'}
            mock_get.return_value = mock_response
            
            download_from_url(sharing_url)
            
            # Verify the converted URL was used
            called_url = mock_get.call_args[0][0]
            self.assertIn("uc?export=download", called_url)
            self.assertIn("id=abc123", called_url)


if __name__ == "__main__":
    unittest.main()
