import React, { useState } from "react";
import { searchUrl } from "./api";
import "./styles.css";

function escapeHtml(unsafe) {
  return unsafe
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

// return HTML string with <mark> wrapped around query matches (case-insensitive)
function highlightText(text, query) {
  if (!query) return escapeHtml(text);
  try {
    const escaped = escapeHtml(text);
    const q = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); // escape regex metachars
    const re = new RegExp(`(${q})`, "ig");
    return escaped.replace(re, '<mark class="hl">$1</mark>');
  } catch {
    return escapeHtml(text);
  }
}

export default function App() {
  const [url, setUrl] = useState("");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const onCopy = (text) => {
    navigator.clipboard?.writeText(text).then(() => {
      // tiny visual feedback could be added
    });
  };

  const onSearch = async () => {
    if (!url || !query) {
      alert("Please enter both URL and search query.");
      return;
    }
    setLoading(true);
    setResults([]);
    try {
      const data = await searchUrl(url, query);
      setResults(data.results || []);
      // scroll to results
      setTimeout(() => {
        const el = document.querySelector(".results");
        if (el) el.scrollIntoView({ behavior: "smooth" });
      }, 80);
    } catch (err) {
      console.error(err);
      alert("Search failed: " + (err.message || JSON.stringify(err)));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header className="hero">
        <div className="hero-inner">
          <h1>HTML Semantic Search</h1>
          <p className="subtitle">Enter a website URL and a search query — find the most relevant HTML chunks.</p>
        </div>
      </header>

      <main className="container">
        <div className="card form-card">
          <label className="label">Website URL</label>
          <input
            className="input"
            placeholder="https://example.com"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />

          <label className="label">Search Query</label>
          <input
            className="input"
            placeholder="e.g., camera"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") onSearch(); }}
          />

          <div className="controls">
            <button className="btn primary" onClick={onSearch} disabled={loading}>
              {loading ? <span className="spinner" /> : "Search"}
            </button>
            <button
              className="btn ghost"
              onClick={() => { setUrl(""); setQuery(""); setResults([]); }}
              disabled={loading}
            >
              Clear
            </button>
          </div>
        </div>

        <section className="results">
          {loading && <div className="loading-note">Searching — please wait...</div>}

          {!loading && results.length === 0 && (
            <div className="empty">No results yet — enter a URL and query and press Search.</div>
          )}

          <div className="grid">
            {results.map((r, idx) => (
              <article key={idx} className="result-card">
                <div className="result-head">
                  <div className="score-badge">Score: {r.score.toFixed(4)}</div>
                  <div className="actions">
                    <button title="Copy chunk" className="icon-btn" onClick={() => onCopy(r.chunk)}>Copy</button>
                  </div>
                </div>

                <div
                  className="chunk"
                  // chunk is sanitized and highlights are inserted by highlightText()
                  dangerouslySetInnerHTML={{ __html: highlightText(r.chunk, query) }}
                />
              </article>
            ))}
          </div>
        </section>
      </main>

      <footer className="footer">
        <div>Built with 💙 — Semantic search (FAISS + SentenceTransformers)</div>
      </footer>
    </div>
  );
}
