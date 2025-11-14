// frontend/src/api.js
export async function searchUrl(url, query) {
  const res = await fetch("http://localhost:8000/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, query }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Request failed");
  }
  return res.json();
}
