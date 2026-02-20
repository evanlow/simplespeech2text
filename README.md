# SimpleSpeech2Text

A lightweight speech-to-text web app built with Streamlit and Vosk. Upload audio (m4a, mp3, wav), normalize to 16kHz mono PCM WAV, transcribe, and download results as TXT or JSON. Includes an optional lightweight punctuation pass for more readable transcripts.

## Features

- Upload audio files (m4a, mp3, wav)
- Automatic audio normalization to 16kHz mono PCM WAV
- Speech-to-text transcription using Vosk
- Optional word timestamps in JSON
- Download transcript as TXT or JSON
- Lightweight punctuation heuristic for readability
- Streamlit Cloud ready (auto model download + ffmpeg via packages.txt)

## Requirements

- Python 3.10+ (Streamlit Cloud currently runs 3.13)
- ffmpeg (installed automatically on Streamlit Cloud via packages.txt)

Python dependencies are listed in requirements.txt.

## Local Setup

1. Create and activate a virtual environment:

   ```powershell
   python -m venv .
   .\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   .\Scripts\pip.exe install -r requirements.txt
   ```

3. Run the app:

   ```powershell
   .\Scripts\streamlit.exe run app.py
   ```

4. Open the app in your browser:

   http://localhost:8501

## Vosk Model

The app will automatically download and cache a small English Vosk model on first run. If you want to use a custom model, set:

```
VOSK_MODEL_PATH=/path/to/extracted/model
```

A valid model directory contains these subfolders: am, conf, graph, ivector.

## Output

- TXT: plain transcript text
- JSON: transcript plus optional word timestamps (`result`)

## Punctuation Heuristic

The app applies a lightweight punctuation pass after transcription. If word timestamps are available, it uses timing gaps to insert sentence boundaries. Otherwise, it inserts periodic sentence breaks for readability. This avoids heavy ML dependencies and keeps Streamlit Cloud deployments stable.

## Deployment (Streamlit Community Cloud)

1. Push this repository to GitHub.
2. In Streamlit Cloud, create a new app:
   - Repository: evanlow/simplespeech2text
   - Branch: main
   - Main file path: app.py
3. Deploy.

Note: First startup can take a few minutes while the Vosk model downloads.

## Manual Smoke Test Checklist

- Upload an audio file (mp3/m4a/wav)
- Confirm transcript appears
- Download TXT and JSON successfully
- (Optional) Enable word timestamps and confirm JSON includes `result`

## Project Structure

- app.py: Streamlit UI
- convert.py: ffmpeg WAV conversion
- core.py: Vosk transcription
- model_setup.py: model download and cache
- punctuation.py: lightweight punctuation heuristic
- tests/: backend unit tests
- packages.txt: system deps for Streamlit Cloud
- requirements.txt: Python deps

## License

MIT (add a LICENSE file if you want to formalize this)
