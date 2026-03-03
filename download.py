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
    
    # Determine file extension from URL (will try headers if not found)
    url_path = Path(parsed.path)
    suffix = url_path.suffix.lower() if url_path.suffix else None
    
    # Create temporary file
    temp_dir = Path(tempfile.mkdtemp(prefix="stt_download_"))
    
    try:
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
        
        # Handle Google Drive virus scan warning for large files
        is_google_drive = "drive.google.com" in url
        if is_google_drive:
            # Check if we got a virus scan warning page
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                # Read the content to check for virus scan warning
                content = b''
                for chunk in response.iter_content(chunk_size=8192):
                    content += chunk
                    if len(content) > 100000:  # Only check first 100KB
                        break
                
                text = content.decode('utf-8', errors='ignore')
                
                # Look for Google Drive virus scan confirmation
                confirm_match = re.search(r'confirm=([a-zA-Z0-9_-]+)', text)
                uuid_match = re.search(r'uuid=([a-zA-Z0-9_-]+)', text)
                
                if confirm_match or 'Google Drive - Virus scan warning' in text:
                    # Extract file ID from URL
                    file_id_match = re.search(r'id=([a-zA-Z0-9_-]+)', url)
                    if not file_id_match:
                        raise RuntimeError(
                            "Google Drive file requires confirmation but file ID not found in URL"
                        )
                    
                    file_id = file_id_match.group(1)
                    
                    # Build confirmation URL
                    confirm_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                    if confirm_match:
                        confirm_url += f"&confirm={confirm_match.group(1)}"
                    if uuid_match:
                        confirm_url += f"&uuid={uuid_match.group(1)}"
                    
                    # Make new request with confirmation
                    response = requests.get(confirm_url, stream=True, timeout=30, allow_redirects=True)
                    response.raise_for_status()
                    
                    # Verify we got actual content this time
                    new_content_type = response.headers.get('Content-Type', '')
                    if 'text/html' in new_content_type:
                        raise RuntimeError(
                            "Google Drive download failed - still receiving HTML. "
                            "The file may not be publicly accessible or the sharing link is incorrect."
                        )
                else:
                    # We got HTML but it's not the virus scan page - probably an error
                    raise RuntimeError(
                        f"Google Drive download returned HTML instead of file. "
                        f"Please check that the file is publicly accessible. Content preview: {text[:200]}"
                    )
        
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
