# backend/app/utils.py
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import word_tokenize

# Ensure punkt is available at import time (downloads are quiet)
nltk.download("punkt", quiet=True)

def clean_html(html_text: str) -> str:
    """
    Remove script/style/etc and return cleaned text.
    """
    soup = BeautifulSoup(html_text, "html.parser")
    for tag in soup(["script", "style", "noscript", "iframe", "header", "footer", "svg", "meta", "link"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())

def chunk_by_tokens(text: str, max_tokens: int = 500) -> list:
    """
    Chunk text using NLTK word_tokenize as an approximate tokenization.
    Each chunk contains at most `max_tokens` tokens (words).
    """
    if not text or not text.strip():
        return []
    words = word_tokenize(text)
    chunks = []
    for i in range(0, len(words), max_tokens):
        chunk = " ".join(words[i:i + max_tokens]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks
