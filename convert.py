from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


def convert_to_wav(input_path: Path) -> Path:
    source_path = Path(input_path)

    if not source_path.exists() or not source_path.is_file():
        raise FileNotFoundError(f"Input audio file not found: {source_path}")

    temp_dir = Path(tempfile.mkdtemp(prefix="stt_audio_"))
    output_path = temp_dir / f"{source_path.stem}_16k_mono.wav"

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "ffmpeg is not installed or not available on PATH."
        ) from exc

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg conversion failed: {result.stderr.strip()}")

    if not output_path.exists():
        raise RuntimeError("ffmpeg reported success but no output file was created.")

    return output_path
