from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st

from convert import convert_to_wav
from core import transcribe_file
from download import download_from_url
from model_setup import ensure_model_available
from punctuation import punctuate_text


st.set_page_config(page_title="Simple Text2Speech - Speech to Text", page_icon="🎙️")
st.title("Speech to Text")
st.write("Upload an audio or video file (m4a, mp3, mp4, wav) to transcribe it.")
st.caption("💡 For large files (>200MB), use the URL option below (supports Google Drive, Dropbox, direct links).")

@st.cache_resource
def prepare_model() -> Path:
    return ensure_model_available()


try:
    with st.spinner("Preparing speech model..."):
        model_path = prepare_model()
except Exception as exc:
    st.error(f"Model setup failed: {exc}")
    st.info(
        "Set VOSK_MODEL_PATH to a valid extracted model folder, or allow automatic download."
    )
    st.stop()

st.caption(f"Model ready: {model_path}")

# Two input methods: upload or URL
input_method = st.radio(
    "Choose input method:",
    ["Upload file", "Download from URL"],
    horizontal=True
)

uploaded_file = None
url_input = None
source_name = None

if input_method == "Upload file":
    uploaded_file = st.file_uploader(
        "Choose an audio or video file",
        type=["m4a", "mp3", "mp4", "wav"],
    )
    if uploaded_file is not None:
        source_name = uploaded_file.name
else:
    url_input = st.text_input(
        "Enter URL to audio/video file:",
        placeholder="https://example.com/audio.mp3"
    )
    if url_input:
        # Extract filename from URL for display
        url_path = Path(urlparse(url_input).path)
        source_name = url_path.name if url_path.name else "download"

save_words = st.checkbox("Include word timestamps in JSON output", value=False)

# Process the file (either uploaded or from URL)
if uploaded_file is not None or url_input:
    # Determine file suffix and create cache key
    if uploaded_file is not None:
        suffix = Path(uploaded_file.name).suffix.lower()
        file_bytes = uploaded_file.getvalue()
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        cache_key = f"upload:{uploaded_file.name}:{len(file_bytes)}:{file_hash}:{save_words}"
    else:
        # For URL, use URL itself as part of cache key
        suffix = Path(urlparse(url_input).path).suffix.lower() or ".tmp"
        cache_key = f"url:{url_input}:{save_words}"
    
    if suffix not in {".m4a", ".mp3", ".mp4", ".wav", ".tmp"}:
        st.error("Unsupported file type. Please use m4a, mp3, mp4, or wav files.")
        st.stop()

    if st.session_state.get("last_cache_key") != cache_key:
        with tempfile.TemporaryDirectory(prefix="stt_process_") as temp_dir:
            temp_path = Path(temp_dir)
            
            # Get the source file (either from upload or URL)
            if uploaded_file is not None:
                source_path = temp_path / uploaded_file.name
                source_path.write_bytes(file_bytes)
            else:
                try:
                    with st.spinner("Downloading file from URL..."):
                        source_path = download_from_url(url_input)
                except Exception as exc:
                    st.error(f"Download failed: {exc}")
                    st.stop()

            try:
                with st.spinner("Preparing audio..."):
                    wav_path = convert_to_wav(source_path)

                with st.spinner("Transcribing..."):
                    transcription = transcribe_file(wav_path, save_words=save_words)
            except Exception as exc:
                st.error(f"Processing failed: {exc}")
                st.stop()

        with st.spinner("Adding punctuation..."):
            punctuated_text, punctuation_applied, punctuation_error = punctuate_text(
                transcription.get("text", ""),
                transcription.get("result"),
            )

        transcription["text"] = punctuated_text

        st.session_state["last_cache_key"] = cache_key
        st.session_state["last_transcription"] = transcription
        st.session_state["last_punctuated"] = punctuated_text
        st.session_state["punctuation_applied"] = punctuation_applied
        st.session_state["punctuation_error"] = punctuation_error
        st.session_state["last_file_stem"] = Path(source_name).stem

    transcription = st.session_state.get("last_transcription", {})
    transcript_text = transcription.get("text", "")
    punctuation_applied = st.session_state.get("punctuation_applied", True)
    punctuation_error = st.session_state.get("punctuation_error")

    if not punctuation_applied:
        st.info(
            "Punctuation model unavailable in this environment; showing raw transcript."
        )
        if punctuation_error:
            st.caption(f"Punctuation detail: {punctuation_error}")

    st.subheader("Transcript")
    st.text_area("Full transcript", value=transcript_text, height=300)

    txt_bytes = transcript_text.encode("utf-8")
    json_bytes = json.dumps(transcription, indent=2, ensure_ascii=False).encode("utf-8")

    file_stem = st.session_state.get("last_file_stem", "transcript")

    st.download_button(
        label="Download .txt",
        data=txt_bytes,
        file_name=f"{file_stem}_transcript.txt",
        mime="text/plain",
    )

    st.download_button(
        label="Download .json",
        data=json_bytes,
        file_name=f"{file_stem}_transcript.json",
        mime="application/json",
    )
