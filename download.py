from __future__ import annotations

import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import requests


def _convert_google_drive_url(url: str) -> str:
    """
    Convert Google Drive sharing URL to direct download URL.
    
    Args:
        url: Google Drive URL (sharing or direct)
        
    Returns:
        Direct download URL
    """
    # Pattern 1: /file/d/{FILE_ID}/view or /file/d/{FILE_ID}/edit
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    
    # Pattern 2: /open?id={FILE_ID}
    match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    
    # Already a direct download URL or not a Google Drive URL
    return url


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
    
    # Convert Google Drive URLs to direct download format
    if "drive.google.com" in url:
        url = _convert_google_drive_url(url)
    
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
        
        # Handle Google Drive virus scan warning for large files
        if "drive.google.com" in url:
            # Check if we got a virus scan warning page
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                # Look for confirmation token in the response
                chunk = next(response.iter_content(chunk_size=1024), b'')
                text = chunk.decode('utf-8', errors='ignore')
                
                # Search for confirmation token
                match = re.search(r'confirm=([a-zA-Z0-9_-]+)', text)
                if match:
                    confirm_token = match.group(1)
                    # Extract file ID from URL
                    file_id_match = re.search(r'id=([a-zA-Z0-9_-]+)', url)
                    if file_id_match:
                        file_id = file_id_match.group(1)
                        # Make new request with confirmation
                        url = f"https://drive.google.com/uc?export=download&id={file_id}&confirm={confirm_token}"
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
