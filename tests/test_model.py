import sys
import os
import joblib
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.extract_features import extract_url_features


def load_model():
    model = joblib.load("models/scam_model.pkl")
    threshold = joblib.load("models/decision_threshold.pkl")
    return model, threshold


def predict(url):
    model, threshold = load_model()

    features = extract_url_features(url)
    df = pd.DataFrame([features])

    prob = model.predict_proba(df)[0][1]
    prediction = 1 if prob >= threshold else 0

    return prediction, prob


def test_legitimate_prediction():
    url = "https://www.google.com"
    prediction, prob = predict(url)

    assert prediction == 0


def test_phishing_prediction():
    url = "http://secure-login-paypal-update.com/verify"
    prediction, prob = predict(url)

    assert prediction == 1