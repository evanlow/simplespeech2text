from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

import streamlit as st

from convert import convert_to_wav
from core import transcribe_file
from model_setup import ensure_model_available
from punctuation import punctuate_text


st.set_page_config(page_title="Simple Text2Speech - Speech to Text", page_icon="🎙️")
st.title("Speech to Text")
st.write("Upload an audio file (m4a, mp3, wav) to transcribe it.")

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

uploaded_file = st.file_uploader(
    "Choose an audio file",
    type=["m4a", "mp3", "wav"],
)

save_words = st.checkbox("Include word timestamps in JSON output", value=False)

if uploaded_file is not None:
    suffix = Path(uploaded_file.name).suffix.lower()

    if suffix not in {".m4a", ".mp3", ".wav"}:
        st.error("Unsupported file type. Please upload m4a, mp3, or wav.")
        st.stop()

    file_bytes = uploaded_file.getvalue()
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    upload_key = f"{uploaded_file.name}:{len(file_bytes)}:{file_hash}:{save_words}"

    if st.session_state.get("last_upload_key") != upload_key:
        with tempfile.TemporaryDirectory(prefix="stt_upload_") as temp_dir:
            temp_path = Path(temp_dir)
            source_path = temp_path / uploaded_file.name
            source_path.write_bytes(file_bytes)

            try:
                with st.spinner("Preparing audio..."):
                    wav_path = convert_to_wav(source_path)

                with st.spinner("Transcribing..."):
                    transcription = transcribe_file(wav_path, save_words=save_words)
            except Exception as exc:
                st.error(f"Processing failed: {exc}")
                st.stop()

        with st.spinner("Adding punctuation..."):
            punctuated_text, punctuation_applied = punctuate_text(
                transcription.get("text", "")
            )

        transcription["text"] = punctuated_text

        st.session_state["last_upload_key"] = upload_key
        st.session_state["last_transcription"] = transcription
        st.session_state["last_punctuated"] = punctuated_text
        st.session_state["punctuation_applied"] = punctuation_applied
        st.session_state["last_file_stem"] = Path(uploaded_file.name).stem

    transcription = st.session_state.get("last_transcription", {})
    transcript_text = transcription.get("text", "")
    punctuation_applied = st.session_state.get("punctuation_applied", True)

    if not punctuation_applied:
        st.info(
            "Punctuation model unavailable in this environment; showing raw transcript."
        )

    st.subheader("Transcript")
    st.text_area("Full transcript", value=transcript_text, height=300)

    txt_bytes = transcript_text.encode("utf-8")
    json_bytes = json.dumps(transcription, indent=2, ensure_ascii=False).encode("utf-8")

    file_stem = st.session_state.get("last_file_stem", Path(uploaded_file.name).stem)

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
