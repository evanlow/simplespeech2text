from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import streamlit as st

from convert import convert_to_wav
from core import transcribe_file


st.set_page_config(page_title="Simple Text2Speech - Speech to Text", page_icon="🎙️")
st.title("Speech to Text")
st.write("Upload an audio file (m4a, mp3, wav) to transcribe it.")

default_model_path = os.getenv("VOSK_MODEL_PATH", "model")
model_path_input = st.text_input(
    "Vosk model directory",
    value=default_model_path,
    help="Path to an extracted Vosk model folder (contains am/, conf/, graph/, ivector/).",
)
os.environ["VOSK_MODEL_PATH"] = model_path_input.strip() or default_model_path
model_path = Path(os.environ["VOSK_MODEL_PATH"])

if not model_path.exists() or not model_path.is_dir():
    st.warning(
        "Model not found. Download and extract a Vosk model, then set its folder path above. "
        "You can also place it in ./model."
    )

uploaded_file = st.file_uploader(
    "Choose an audio file",
    type=["m4a", "mp3", "wav"],
)

save_words = st.checkbox("Include word timestamps in JSON output", value=False)

if uploaded_file is not None:
    if not model_path.exists() or not model_path.is_dir():
        st.error(
            "Cannot transcribe yet: Vosk model directory is not configured correctly."
        )
        st.stop()

    suffix = Path(uploaded_file.name).suffix.lower()

    if suffix not in {".m4a", ".mp3", ".wav"}:
        st.error("Unsupported file type. Please upload m4a, mp3, or wav.")
        st.stop()

    with tempfile.TemporaryDirectory(prefix="stt_upload_") as temp_dir:
        temp_path = Path(temp_dir)
        source_path = temp_path / uploaded_file.name
        source_path.write_bytes(uploaded_file.getbuffer())

        try:
            with st.spinner("Preparing audio..."):
                if suffix == ".wav":
                    wav_path = source_path
                else:
                    wav_path = convert_to_wav(source_path)

            with st.spinner("Transcribing..."):
                transcription = transcribe_file(wav_path, save_words=save_words)
        except Exception as exc:
            st.error(f"Processing failed: {exc}")
            st.stop()

    transcript_text = transcription.get("text", "")

    st.subheader("Transcript")
    st.text_area("Full transcript", value=transcript_text, height=300)

    txt_bytes = transcript_text.encode("utf-8")
    json_bytes = json.dumps(transcription, indent=2, ensure_ascii=False).encode("utf-8")

    file_stem = Path(uploaded_file.name).stem

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
