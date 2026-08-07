import re


def clean_text(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"[^\w\s.,:%()\-À-ÿ]", "", text, flags=re.UNICODE)
    return text.strip()
