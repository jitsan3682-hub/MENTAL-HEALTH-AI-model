import streamlit as st

def load_css():
    with open("style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def render_stressometer(score):
    """
    Renders the Vertical Stressometer.
    Uses flat string construction to prevent Markdown errors.
    """
    # 0. Round score
    lvl = int(round(score))
    
    # 1. Emoji Map
    emoji_map = {
        0: "🧘", 1: "😌", 2: "🙂", 3: "😐", 4: "😕", 
        5: "😟", 6: "😰", 7: "😣", 8: "😖", 9: "😫", 10: "🤯"
    }
    emoji = emoji_map.get(lvl, "😐")

    # 2. Theme Logic
    if score < 3.0:
        theme, color, label = "s-zen", "#00ff00", "ZEN"
    elif score < 5.0:
        theme, color, label = "s-happy", "#ffff00", "FINE"
    elif score < 7.0:
        theme, color, label = "s-neutral", "#ffffff", "OKAY"
    elif score < 9.0:
        theme, color, label = "s-warn", "#ff8800", "WARN"
    else:
        theme, color, label = "s-crit", "#ff0000", "CRIT"

    # 3. HTML Construction (Safe Mode)
    # We build the HTML line by line to guarantee it renders as HTML
    html_content = f"""
    <div class="stress-box" style="border-color:{color};">
        <div style="margin-bottom:10px; letter-spacing:2px; font-size:20px;">STRESSOMETER</div>
        <div class="stress-row">
            <div class="emoji-box {theme}">{emoji}</div>
            <div class="v-bar-bg {theme}">
                <div class="v-bar-fill" style="height:{min(score*10, 100)}%;"></div>
            </div>
            <div class="stats-box {theme}">
                <div class="stat-label">{label}</div>
                <div class="stat-sub">LVL: {score}</div>
                <div class="stat-sub">LOAD: {int(score*10)}%</div>
            </div>
        </div>
    </div>
    """
    
    # Render with HTML enabled
    st.markdown(html_content, unsafe_allow_html=True)
    return color

def render_log_card(title, emotion, text, color):
    html_content = f"""
    <div class="log-card" style="border-left-color: {color};">
        <div style="display:flex; justify-content:space-between; color:{color};">
            <span>> {title}</span>
            <span>{emotion.upper()}</span>
        </div>
        <hr style="border-color:#333; margin:5px 0; opacity:0.3;">
        <div style="color:#eee; line-height:1.4;">"{text}"</div>
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)

def apply_rapido(score):
    if score > 8.5:
        st.markdown("""<style>.stApp { animation: shake 0.5s infinite; }</style>""", unsafe_allow_html=True)