# backend/app/main.py
import os
import time
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
from requests.adapters import HTTPAdapter, Retry

from sentence_transformers import SentenceTransformer
import numpy as np
from pymilvus import connections, Collection
from .utils import clean_html, chunk_by_tokens

# Optional: Playwright fallback if installed
_playwright_available = True
try:
    from playwright.sync_api import sync_playwright
except Exception:
    _playwright_available = False

load_dotenv()

# Config
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
MAX_TOKENS_PER_CHUNK = int(os.getenv("MAX_TOKENS_PER_CHUNK", "500"))
TOP_K = int(os.getenv("TOP_K", "10"))
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
COLLECTION_NAME = os.getenv("MILVUS_COLLECTION", "html_chunks")

app = FastAPI(title="HTML Semantic Search (Milvus Lite)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "HTML Semantic Search (Milvus Lite) running. Use POST /search or /index or visit /docs."}

# Load embedding model once
logging.info(f"Loading embedding model: {MODEL_NAME} ...")
model = SentenceTransformer(MODEL_NAME)
logging.info("Model loaded.")

# Start Milvus Lite server automatically if available
def start_milvus_lite_if_available():
    try:
        import milvus_lite
        # milvus_lite.start() starts a lightweight milvus server bound to localhost:19530 by default
        print("Starting milvus-lite server...")
        milvus_lite.start()
        time.sleep(1.0)  # small delay for server to start
        print("milvus-lite started.")
    except Exception:
        # milvus_lite not installed or start failed — assume external Milvus available
        print("milvus-lite not started (not installed or failed). Assuming Milvus at localhost:19530.")

# Connect to Milvus (attempt to start milvus-lite first)
start_milvus_lite_if_available()
connections.connect(alias="default", host=MILVUS_HOST, port=MILVUS_PORT)
collection = None
try:
    collection = Collection(COLLECTION_NAME)
    print(f"Connected to Milvus collection '{COLLECTION_NAME}'.")
except Exception:
    # collection may not exist yet; user should run create_collection.py
    print(f"Collection '{COLLECTION_NAME}' not found. Run create_collection.py to create it.")

# Helpers
def normalize_vectors(v: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(v, axis=1, keepdims=True)
    norms[norms == 0.0] = 1e-8
    return v / norms

def fetch_with_playwright(url: str, timeout: int = 15000) -> str:
    if not _playwright_available:
        raise RuntimeError("Playwright not installed. Install with: pip install playwright && python -m playwright install")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=timeout)
        time.sleep(1.0)
        html = page.content()
        browser.close()
        return html

def fetch_url_text(url: str, timeout: int = 12, max_retries: int = 2, playwright_fallback=True) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": url,
    }
    session = requests.Session()
    retries = Retry(total=max_retries, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))
    try:
        resp = session.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except requests.HTTPError as http_err:
        status = getattr(http_err.response, "status_code", None)
        if status == 403 and playwright_fallback and _playwright_available:
            # try Playwright fallback
            try:
                return fetch_with_playwright(url)
            except Exception:
                # re-raise original http error
                raise http_err
        raise http_err
    except Exception:
        raise

def escape_milvus_string(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")

# Data models
class IndexInput(BaseModel):
    url: str

class SearchInput(BaseModel):
    url: str
    query: str

@app.post("/index")
async def index_url(payload: IndexInput):
    if not payload.url:
        raise HTTPException(status_code=400, detail="Missing 'url'")

    if collection is None:
        raise HTTPException(status_code=500, detail="Milvus collection not initialized. Run create_collection.py")

    try:
        raw_html = fetch_url_text(payload.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")

    text = clean_html(raw_html)
    chunks = chunk_by_tokens(text, max_tokens=MAX_TOKENS_PER_CHUNK)
    if not chunks:
        return {"url": payload.url, "chunks_indexed": 0}

    try:
        embeddings = model.encode(chunks, convert_to_numpy=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding error: {str(e)}")

    embeddings = embeddings.astype("float32")
    embeddings = normalize_vectors(embeddings)

    # Delete old entries for this URL to avoid duplicates
    try:
        expr = f"url == '{escape_milvus_string(payload.url)}'"
        collection.delete(expr)
    except Exception:
        pass

    url_list = [payload.url] * len(chunks)
    chunk_list = chunks
    emb_list = embeddings.tolist()
    collection.insert([url_list, chunk_list, emb_list])
    collection.flush()

    return {"url": payload.url, "chunks_indexed": len(chunks)}

@app.post("/search")
async def search(payload: SearchInput):
    if not payload.url or not payload.query:
        raise HTTPException(status_code=400, detail="Both 'url' and 'query' are required.")

    if collection is None:
        raise HTTPException(status_code=500, detail="Milvus collection not initialized. Run create_collection.py")

    try:
        raw_html = fetch_url_text(payload.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")

    text = clean_html(raw_html)
    chunks = chunk_by_tokens(text, max_tokens=MAX_TOKENS_PER_CHUNK)
    if not chunks:
        return JSONResponse(status_code=200, content={"results": []})

    try:
        embeddings = model.encode(chunks, convert_to_numpy=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding error: {str(e)}")

    embeddings = embeddings.astype("float32")
    embeddings = normalize_vectors(embeddings)

    # Delete old entries for this URL then insert new ones
    try:
        collection.delete(f"url == '{escape_milvus_string(payload.url)}'")
    except Exception:
        pass

    url_list = [payload.url] * len(chunks)
    chunk_list = chunks
    emb_list = embeddings.tolist()
    collection.insert([url_list, chunk_list, emb_list])
    collection.flush()

    try:
        q_vec = model.encode([payload.query], convert_to_numpy=True).astype("float32")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query embedding error: {str(e)}")
    q_vec = normalize_vectors(q_vec).tolist()

    search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
    limit = min(TOP_K, len(chunks))

    try:
        results = collection.search(
            data=q_vec,
            anns_field="embedding",
            param=search_params,
            limit=limit,
            output_fields=["chunk", "url"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Milvus search error: {str(e)}")

    out = []
    hits = results[0] if len(results) > 0 else []
    for hit in hits:
        chunk_text = hit.entity.get("chunk")
        url_val = hit.entity.get("url")
        out.append({"chunk": chunk_text, "url": url_val, "score": float(hit.distance)})

    out = sorted(out, key=lambda x: x["score"], reverse=True)
    return {"results": out}
