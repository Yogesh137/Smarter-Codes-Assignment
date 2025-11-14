# Semantic Search Application

A full-stack web application that performs semantic search on any website using AI-powered vector embeddings.

## Features

- 🔍 Semantic search using sentence transformers
- 🎯 Top 10 relevant content matches
- 📊 Relevance scoring
- 🚀 Fast and efficient vector search with MILVUS
- 💅 Clean, modern UI with React

## Tech Stack

**Backend:**
- FastAPI (Python)
- MILVUS (Vector Database)
- Sentence Transformers (all-MiniLM-L6-v2)
- BeautifulSoup4 (HTML Parsing)

**Frontend:**
- React
- Tailwind CSS
- Lucide Icons

---

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

---

## Installation & Setup

### Backend Setup

1. **Create a project directory:**

2. **Create virtual environment:**
```bash
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Create main.py** and paste the backend code

5. **Run the backend server:**
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Create React app:**
```bash
cd ..
npx create-react-app frontend
cd frontend
```

2. **Install dependencies:**
```bash
npm install lucide-react
```

3. **Setup Tailwind CSS:**
```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

4. **Configure Tailwind** - Update `tailwind.config.js`:
```javascript
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

5. **Update `src/index.css`:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

6. **Replace `src/App.js`** with the frontend React code

7. **Run the frontend:**
```bash
npm start
```

The app will open at `http://localhost:3000`

---

## Usage

1. Start the backend server (port 8000)
2. Start the frontend (port 3000)
3. Enter a website URL (e.g., `https://en.wikipedia.org/wiki/Artificial_intelligence`)
4. Enter your search query (e.g., "machine learning applications")
5. Click "Search" to get the top 10 relevant matches

---

## API Endpoints

### `POST /search`
Performs semantic search on a website.

**Request Body:**
```json
{
  "url": "https://example.com",
  "query": "your search query"
}
```

**Response:**
```json
[
  {
    "content": "Text chunk content...",
    "relevance_score": 0.8543,
    "chunk_id": 0
  }
]
```

### `GET /`
Health check endpoint

### `GET /health`
Returns API status

---

## How It Works

1. **Fetch HTML**: Downloads the webpage content
2. **Parse & Clean**: Removes scripts, styles, and extracts text
3. **Tokenize**: Splits content into 500-token chunks
4. **Embed**: Converts chunks to vector embeddings using Sentence Transformers
5. **Index**: Stores embeddings in ChromaDB vector database
6. **Search**: Converts query to embedding and finds similar chunks
7. **Rank**: Returns top 10 matches sorted by relevance


---

## Future Improvements

- Add URL validation and error handling
- Implement caching for repeated searches
- Add pagination for results
- Support for JavaScript-rendered pages
- Export results to PDF/CSV
- User authentication
- Search history

---
