import re
import math
from urllib.parse import urlparse


def entropy(text: str) -> float:
    if not text:
        return 0
    prob = [float(text.count(c)) / len(text) for c in set(text)]
    return -sum([p * math.log2(p) for p in prob])


def extract_url_features(url: str) -> dict:
    parsed = urlparse(url)

    suspicious_words = [
        "login", "verify", "update", "secure",
        "account", "bank", "paypal", "free",
        "confirm", "signin", "wp", "admin"
    ]

    domain = parsed.netloc
    path = parsed.path

    digit_count = sum(c.isdigit() for c in url)

    return {
        "url_length": len(url),
        "hostname_length": len(domain),
        "path_length": len(path),
        "path_depth": path.count("/"),
        "num_dots": url.count("."),
        "num_hyphens": url.count("-"),
        "num_at_symbols": url.count("@"),
        "num_digits": digit_count,
        "digit_ratio": digit_count / len(url) if len(url) > 0 else 0,
        "special_char_ratio": len(re.findall(r"[?=&%]", url)) / len(url) if len(url) > 0 else 0,
        "num_subdomains": domain.count("."),
        "tld_length": len(domain.split(".")[-1]) if "." in domain else 0,
        "entropy": entropy(url),
        "is_https": 1 if parsed.scheme == "https" else 0,
        "has_ip": 1 if re.match(r"\d+\.\d+\.\d+\.\d+", domain) else 0,
        "suspicious_word_count": sum(word in url.lower() for word in suspicious_words),
    }