from __future__ import annotations

import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import gdown
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
        # Use gdown for Google Drive downloads (handles auth, virus scans, etc.)
        is_google_drive = True
    else:
        is_google_drive = False
    
    # Validate URL format
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid URL format: {url}")
    
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix="stt_download_"))
    
    try:
        # Use gdown for Google Drive files (more reliable)
        if is_google_drive:
            # Extract file ID from URL
            file_id_match = re.search(r'id=([a-zA-Z0-9_-]+)', url)
            if not file_id_match:
                raise ValueError("Cannot extract file ID from Google Drive URL")
            
            file_id = file_id_match.group(1)
            
            # Use gdown.cached_download which handles filenames better
            # Or download and rename based on content inspection
            import os
            original_cwd = os.getcwd()
            try:
                # Change to temp directory so gdown downloads there
                os.chdir(str(temp_dir))
                
                # Download using gdown - fuzzy mode will try to get the real filename
                output_path = gdown.download(
                    f"https://drive.google.com/uc?id={file_id}",
                    quiet=False,
                    fuzzy=True
                )
            except Exception as exc:
                raise RuntimeError(
                    f"Google Drive download failed: {exc}. "
                    "Please ensure the file sharing is set to 'Anyone with the link can view'."
                ) from exc
            finally:
                os.chdir(original_cwd)
            
            # Find the downloaded file
            if output_path and Path(output_path).exists():
                return Path(output_path)
            
            # Fallback: look for any file in temp_dir
            actual_files = list(temp_dir.glob("*"))
            if not actual_files:
                raise RuntimeError("Google Drive download completed but file not found")
            
            downloaded_file = actual_files[0]
            if downloaded_file.stat().st_size == 0:
                raise RuntimeError("Downloaded file is empty")
            
            return downloaded_file
        
        # For non-Google Drive URLs, use requests
        # Determine file extension from URL (will try headers if not found)
        url_path = Path(parsed.path)
        suffix = url_path.suffix.lower() if url_path.suffix else None
        
        # Download with streaming to handle large files
        response = requests.get(url, stream=True, timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        # Try to get filename and extension from Content-Disposition header
        if not suffix:
            content_disp = response.headers.get('Content-Disposition', '')
            if 'filename=' in content_disp:
                # Extract filename from header
                match = re.search(r'filename="?([^";\r\n]+)"?', content_disp)
                if match:
                    filename = match.group(1)
                    detected_suffix = Path(filename).suffix.lower()
                    if detected_suffix:
                        suffix = detected_suffix
        
        # If still no suffix, use .tmp
        if not suffix:
            suffix = ".tmp"
        
        temp_file = temp_dir / f"downloaded{suffix}"
        
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
