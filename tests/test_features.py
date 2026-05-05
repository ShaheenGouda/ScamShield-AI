import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.extract_features import extract_url_features


def test_safe_url():
    url = "https://www.google.com"
    features = extract_url_features(url)

    assert features["is_https"] == 1
    assert features["suspicious_word_count"] == 0
    assert features["has_ip"] == 0


def test_phishing_url():
    url = "http://secure-login-paypal-update.com/verify"
    features = extract_url_features(url)

    assert features["is_https"] == 0
    assert features["suspicious_word_count"] >= 1
    assert features["url_length"] > 10


def test_ip_url():
    url = "http://192.168.0.1/login"
    features = extract_url_features(url)

    assert features["has_ip"] == 1