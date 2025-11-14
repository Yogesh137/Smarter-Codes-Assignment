# Smarter.Codes — HTML Semantic Search (React + FastAPI + FAISS)

## Overview
A single-page React app where a user enters a website URL and a search query. The backend downloads the page, cleans & chunks HTML into ~500-token segments, embeds text with `sentence-transformers`, builds a FAISS index in-memory, and returns the top-10 semantically relevant chunks.

This implementation uses FAISS (local in-memory) — so no Docker, no external vector DB is required.

---

## Prerequisites
- Node.js (v16+ recommended) and npm
- Python 3.9+ (3.10+ recommended)
- Git (optional)
- (Optional) Virtualenv for Python

---

## Project structure
