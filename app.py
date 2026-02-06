import os
# CONFIG FIRST
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import streamlit as st
import json
import random
import soundfile as sf
import io
import tempfile
import cv2
import numpy as np
import librosa # Required for the new audio fix

# Libraries
from transformers import pipeline
from deepface import DeepFace
from streamlit_option_menu import option_menu
import easyocr
from pypdf import PdfReader

# Custom UI
import ui_components as ui

# ==========================================
# 1. SETUP
# ==========================================
st.set_page_config(page_title="SYSTEM LOGS", layout="wide", page_icon="📼")
ui.load_css()

if 'stress_score' not in st.session_state:
    st.session_state['stress_score'] = 5.0

# Apply visual effects
ui.apply_rapido(st.session_state['stress_score'])

# ==========================================
# 2. LOAD RESOURCES
# ==========================================
@st.cache_resource
def load_ai_engines():
    # Only Emotion & Audio models (No more text generation)
    txt_model = pipeline("text-classification", model="bhadresh-savani/distilbert-base-uncased-emotion")
    aud_model = pipeline("audio-classification", model="ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition")
    ocr_model = easyocr.Reader(['en'], gpu=False)
    return txt_model, aud_model, ocr_model

@st.cache_data
def load_reply_bank():
    # Load the JSON replies
    try:
        with open("replies.json", "r") as f:
            return json.load(f)
    except:
        return {"neutral": ["System stable."]}

# Load everything
if 'models' not in st.session_state:
    with st.spinner("BOOTING SYSTEM..."):
        st.session_state.models = load_ai_engines()
        st.session_state.replies = load_reply_bank()

# ==========================================
# 3. LOGIC HANDLERS
# ==========================================
def update_stress(emotion):
    # Mapping
    map_e = {'joy': 2.0, 'happy': 2.0, 'neutral': 5.0, 'sadness': 7.0, 'fear': 8.5, 'anger': 9.5}
    target = map_e.get(emotion.lower(), 5.0)
    current = st.session_state['stress_score']
    # Smooth update
    st.session_state['stress_score'] = round((current * 0.7) + (target * 0.3), 1)

def get_json_reply(emotion):
    # Fetch from JSON bank
    bank = st.session_state.replies
    key = emotion.lower()
    # Fallback if key not found
    if key not in bank:
        key = "neutral"
    
    return random.choice(bank[key])

# ==========================================
# 4. MAIN INTERFACE
# ==========================================
def main():
    
    # --- SIDEBAR (STRESSOMETER) ---
    with st.sidebar:
        # Render the new Vertical Widget
        color = ui.render_stressometer(st.session_state['stress_score'])
        st.divider()
        st.caption("SYSTEM: ONLINE")

    # --- TOP NAV ---
    selected = option_menu(
        menu_title=None,
        options=["Daily Logs", "Voice Phone", "Scrapbook", "Face Mirror"],
        icons=["journal-text", "mic", "paperclip", "person"],
        orientation="horizontal",
        styles={
            "container": {"background-color": "#000"},
            "nav-link": {"font-family": "VT323", "font-size": "20px"},
            "nav-link-selected": {"background-color": "#222", "color": color, "border": f"1px solid {color}"}
        }
    )

    # --- TAB 1: DAILY LOGS ---
    if selected == "Daily Logs":
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("### 🖊️ NEW ENTRY")
            text = st.text_area("...", height=150, label_visibility="collapsed")
            if st.button("LOG ENTRY"):
                if text:
                    model = st.session_state.models[0]
                    # Analyze
                    pred = model(text[:512])[0]
                    emo = pred['label']
                    
                    update_stress(emo)
                    reply = get_json_reply(emo)
                    
                    ui.render_log_card("TEXT LOG", emo, reply, color)

    # --- TAB 2: VOICE PHONE (UPDATED FIX) ---
    elif selected == "Voice Phone":
        st.markdown("<br>", unsafe_allow_html=True)
        _, c2, _ = st.columns([1,2,1])
        with c2:
            st.markdown(f'<div style="border:2px solid {color}; padding:20px; background:#050505;">', unsafe_allow_html=True)
            st.markdown("<h3 style='text-align:center;'>LEAVE MESSAGE</h3>", unsafe_allow_html=True)
            
            audio_in = st.audio_input("RECORD")
            
            if audio_in:
                try:
                    # 1. Read Bytes
                    b = io.BytesIO(audio_in.getvalue())
                    data, samplerate = sf.read(b)

                    # 2. Ensure Mono
                    if len(data.shape) > 1:
                        data = np.mean(data, axis=1)

                    # 3. Resample to 16kHz
                    if samplerate != 16000:
                        data = librosa.resample(data, orig_sr=samplerate, target_sr=16000)
                        samplerate = 16000

                    # 4. Predict directly from raw array
                    # Note: We must ensure float32 type for transformers
                    data = data.astype(np.float32)
                    
                    mod = st.session_state.models[1]
                    pred = mod(data) # Pipeline handles raw array
                    emo = pred[0]['label']

                    update_stress(emo)
                    reply = get_json_reply(emo)
                    ui.render_log_card("VOICE MESSAGE", emo, reply, color)
                except Exception as e:
                    st.error(f"STATIC INTERFERENCE: {e}")
            
            st.markdown('</div>', unsafe_allow_html=True)

    # --- TAB 3: SCRAPBOOK ---
    elif selected == "Scrapbook":
        st.markdown("### 📎 FILE READER")
        f = st.file_uploader("UPLOAD", type=['png','jpg','pdf'])
        if f:
            with st.spinner("SCANNING..."):
                txt = ""
                if f.name.endswith(".pdf"):
                    pdf = PdfReader(f)
                    for p in pdf.pages: txt += p.extract_text()
                else:
                    ocr = st.session_state.models[2]
                    res = ocr.readtext(f.getvalue(), detail=0)
                    txt = " ".join(res)
                
                if txt:
                    # Use text model on extracted text
                    model = st.session_state.models[0]
                    emo = model(txt[:512])[0]['label']
                    
                    update_stress(emo)
                    reply = get_json_reply(emo)
                    
                    ui.render_log_card("FILE CONTENT", emo, reply, color)

    # --- TAB 4: MIRROR ---
    elif selected == "Face Mirror":
        st.markdown("### 🪞 REFLECTION")
        c1, c2 = st.columns(2)
        with c1:
            img = st.camera_input("LOOK")
        with c2:
            if img:
                b = img.getvalue()
                cv_img = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR)
                try:
                    res = DeepFace.analyze(cv_img, actions=['emotion'], enforce_detection=False)
                    emo = res[0]['dominant_emotion']
                    
                    update_stress(emo)
                    reply = get_json_reply(emo)
                    
                    ui.render_log_card("VISUAL SCAN", emo, reply, color)
                except:
                    st.warning("NO FACE DETECTED")

if __name__ == "__main__":
    main()