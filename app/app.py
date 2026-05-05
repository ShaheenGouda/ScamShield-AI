import sys
import os
from urllib.parse import urlparse

# ✅ Make project root visible
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import joblib
import pandas as pd

from src.extract_features import extract_url_features


# ============================
# PAGE CONFIG
# ============================
st.set_page_config(
    page_title="ScamShield AI",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ ScamShield AI")
st.markdown("### Advanced URL Phishing Detection System (Hybrid ML + Reputation)")
st.markdown("---")


# ============================
# LOAD MODEL + THRESHOLD
# ============================
model = joblib.load("models/scam_model.pkl")
threshold = joblib.load("models/decision_threshold.pkl")

st.info(f"ML Decision Threshold (F1 Optimized): {threshold:.3f}")


# ============================
# LOAD WHITELIST
# ============================
def load_whitelist():
    try:
        with open("data/whitelist.txt", "r") as f:
            return set(line.strip().lower() for line in f.readlines())
    except FileNotFoundError:
        return set()

WHITELIST = load_whitelist()


# ✅ SMART WHITELIST MATCHING
def is_whitelisted(domain):
    domain = domain.lower()

    # Remove www
    if domain.startswith("www."):
        domain = domain[4:]

    for trusted in WHITELIST:
        if domain == trusted or domain.endswith("." + trusted):
            return True
    return False


# ============================
# USER INPUT
# ============================
url_input = st.text_input("Enter URL to analyze:")

if st.button("Analyze URL"):

    if not url_input:
        st.warning("Please enter a URL.")
        st.stop()

    parsed = urlparse(url_input)
    domain = parsed.netloc.lower()

    # ============================
    # WHITELIST OVERRIDE
    # ============================
    if is_whitelisted(domain):
        prob = 0.0
        is_phishing = False
        whitelist_flag = True
    else:
        whitelist_flag = False
        features = extract_url_features(url_input)
        df = pd.DataFrame([features])
        prob = model.predict_proba(df)[0][1]
        is_phishing = prob >= threshold

    # ============================
    # RISK LEVEL CLASSIFICATION
    # ============================
    if prob < 0.20:
        risk_label = "LOW"
        risk_color = "green"
    elif prob < 0.50:
        risk_label = "MEDIUM"
        risk_color = "orange"
    elif prob < 0.75:
        risk_label = "HIGH"
        risk_color = "red"
    else:
        risk_label = "CRITICAL"
        risk_color = "darkred"

    # ============================
    # DISPLAY RESULT
    # ============================
    st.markdown("---")
    col1, col2 = st.columns([1, 1])

    with col1:

        if whitelist_flag:
            st.success("✅ SAFE — Trusted high-reputation domain (Whitelist Override)")
        elif is_phishing:
            st.error("🚨 UNSAFE — Likely Phishing")
        else:
            st.success("✅ SAFE — Appears Legitimate")

        st.metric("Risk Score", f"{prob:.2%}")
        st.progress(min(prob, 1.0))

        st.markdown(
            f"**Risk Level:** <span style='color:{risk_color}; font-weight:bold'>{risk_label}</span>",
            unsafe_allow_html=True
        )

    with col2:

        st.subheader("🔍 Decision Explanation")

        if whitelist_flag:
            st.write("This domain appears in the trusted global domain whitelist.")
        else:
            explanations = []

            if features["suspicious_word_count"] > 0:
                explanations.append("Contains suspicious keywords.")

            if features["has_ip"] == 1:
                explanations.append("Uses raw IP address instead of domain.")

            if features["entropy"] > 4.2:
                explanations.append("High entropy (random-looking structure).")

            if features["digit_ratio"] > 0.20:
                explanations.append("High digit density.")

            if features["path_depth"] > 3:
                explanations.append("Deep URL path structure.")

            if features["num_subdomains"] > 3:
                explanations.append("Multiple subdomains.")

            if explanations:
                for item in explanations:
                    st.write(f"- {item}")
            else:
                st.write("No major structural red flags detected.")

    # ============================
    # TECHNICAL DETAILS
    # ============================
    if not whitelist_flag:
        st.markdown("---")
        st.subheader("📊 Technical Feature Breakdown")
        feature_df = pd.DataFrame(features.items(), columns=["Feature", "Value"])
        st.dataframe(feature_df, use_container_width=True)