from __future__ import annotations

import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests


def download_from_url(url: str, chunk_size: int = 8192) -> Path:
    """
    Download a file from a URL to a temporary location.
    
    Args:
        url: The URL to download from
        chunk_size: Size of chunks to download (default 8KB)
        
    Returns:
        Path to the downloaded temporary file
        
    Raises:
        ValueError: If URL is invalid or empty
        RuntimeError: If download fails
    """
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")
    
    # Validate URL format
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid URL format: {url}")
    
    # Determine file extension from URL
    url_path = Path(parsed.path)
    suffix = url_path.suffix.lower() if url_path.suffix else ".tmp"
    
    # Create temporary file
    temp_dir = Path(tempfile.mkdtemp(prefix="stt_download_"))
    temp_file = temp_dir / f"downloaded{suffix}"
    
    try:
        # Download with streaming to handle large files
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Write in chunks
        with open(temp_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
        
        if not temp_file.exists() or temp_file.stat().st_size == 0:
            raise RuntimeError("Downloaded file is empty")
        
        return temp_file
        
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Failed to download from URL: {exc}") from exc
