# ArticleHelper

ArticleHelper is a local paper-reading agent. It accepts one PDF at a time, parses the paper, splits it into cited chunks, builds optional embeddings with Qwen-compatible APIs, and lets the user discuss the paper through a web interface.

The project currently focuses on a single-paper reading workflow:

```text
Upload PDF
-> parse pages
-> detect sections
-> split chunks
-> store pages/chunks/embeddings in SQLite
-> retrieve evidence
-> answer with citations
```

## Current Features

- PDF upload through `POST /api/papers/upload`
- PDF text extraction with PyMuPDF
- Page-level text storage
- Basic language detection
- Title guessing from the first pages
- Standard section detection, including Abstract, Introduction, Methods, Experiments, Results, Discussion, Conclusion, Limitations, and References
- Chunking by detected section with overlap handling
- SQLite persistence for papers, pages, chunks, chat messages, and chunk embeddings
- Local lexical retrieval as a fallback search path
- Qwen-compatible LLM client for chat completion
- Qwen-compatible embedding client for text embeddings
- Vector retrieval with cosine similarity over stored chunk embeddings
- Hybrid retrieval: vector search first, lexical search fallback
- Evidence-grounded chat responses with citations
- Static frontend served by FastAPI
- Minimal web UI for uploading PDFs, asking questions, using quick prompts, and viewing citations
- Unit and integration tests for each backend module

## Project Structure

```text
ArticleViewer/
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |   |-- chat.py
|   |   |   |-- papers.py
|   |   |-- core/
|   |   |   |-- config.py
|   |   |-- models/
|   |   |   |-- api.py
|   |   |   |-- domain.py
|   |   |-- services/
|   |   |   |-- chat_agent.py
|   |   |   |-- chunker.py
|   |   |   |-- paper_parser.py
|   |   |   |-- paper_pipeline.py
|   |   |   |-- qwen_client.py
|   |   |   |-- retrieval_service.py
|   |   |   |-- section_detector.py
|   |   |   |-- summary_service.py
|   |   |   |-- vector_retrieval_service.py
|   |   |-- storage/
|   |   |   |-- database.py
|   |   |-- main.py
|   |-- tests/
|   |-- requirements.txt
|-- frontend/
|   |-- index.html
|   |-- styles.css
|   |-- app.js
|-- data/
|   |-- uploads/
|   |-- sqlite/
|   |-- indexes/
|-- config.example.txt
|-- config.txt
|-- README.md
```

`config.txt`, `data/`, caches, local databases, and uploaded papers are ignored by Git.

## Configuration

Create a local `config.txt` in the repository root. Do not commit this file.

```txt
embedding_model = "text-embedding-v4"
llm_model = "qwen3.6-plus"
api_key = "your-api-key"
api_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
```

`api_base_url` is optional. If omitted, the backend uses:

```text
https://dashscope.aliyuncs.com/compatible-mode/v1
```

Environment variables can override `config.txt`:

```text
ARTICLEVIEWER_CONFIG_PATH
ARTICLEVIEWER_DATA_DIR
ARTICLEVIEWER_DB_PATH
ARTICLEVIEWER_UPLOAD_DIR
ARTICLEVIEWER_INDEX_DIR
ARTICLEVIEWER_API_BASE_URL
ARTICLEVIEWER_API_KEY
ARTICLEVIEWER_EMBEDDING_MODEL
ARTICLEVIEWER_LLM_MODEL
```

The config parser supports UTF-8 files with or without BOM.

## Installation

From the repository root:

```powershell
cd backend
python -m pip install -r requirements.txt
```

## Run Locally

```powershell
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/
```

Health check:

```text
http://127.0.0.1:8000/api/health
```

## API

### Health

```http
GET /api/health
```

Response:

```json
{
  "status": "ok"
}
```

### Upload Paper

```http
POST /api/papers/upload
```

Form field:

```text
file: PDF
```

Response:

```json
{
  "paper_id": "uuid",
  "status": "ready",
  "title": "Detected title",
  "language": "en"
}
```

During upload, the backend:

1. Saves the PDF under `data/uploads/`
2. Extracts page text with PyMuPDF
3. Stores page records
4. Detects sections
5. Builds chunks
6. Stores chunks
7. Generates and stores embeddings when embedding config is available
8. Marks the paper as `ready`

### Paper Status

```http
GET /api/papers/{paper_id}/status
```

### Page Text

```http
GET /api/papers/{paper_id}/pages/{page_number}
```

### Chat

```http
POST /api/papers/{paper_id}/chat
```

Request:

```json
{
  "message": "这篇文章的主要贡献是什么？",
  "selected_text": null,
  "current_page": null
}
```

Response:

```json
{
  "answer": "回答内容",
  "citations": [
    {
      "chunk_id": "paper-id-chunk-0000",
      "section": "Abstract",
      "page_start": 1,
      "page_end": 1
    }
  ]
}
```

## Retrieval and Answering

The chat flow currently works as follows:

```text
User question
-> load chunks
-> load stored embeddings
-> try vector retrieval with query embedding
-> fallback to lexical retrieval if needed
-> send retrieved evidence to the LLM
-> return answer plus citations
```

If no LLM configuration is available, the backend returns an extractive evidence answer instead of a generated answer.

If the embedding API fails during chat, the backend falls back to lexical retrieval.

## Testing

Run all tests:

```powershell
cd backend
python -m pytest -q
```

Run compile check:

```powershell
cd backend
python -m compileall app tests
```

Current test coverage includes:

- Package import smoke test
- Config parsing, including UTF-8 BOM handling
- SQLite CRUD for papers, pages, chunks, embeddings, and messages
- PDF parser text normalization and error paths
- Section detection
- Chunking
- Lexical retrieval
- Qwen-compatible chat and embedding client payloads
- Summary extraction
- Chat agent behavior
- Vector embedding creation and cosine retrieval
- Hybrid retrieval fallback
- End-to-end PDF ingestion with generated test PDFs
- FastAPI health endpoint
- Static frontend serving

## Current Limitations

- OCR for scanned PDFs is not implemented yet.
- PDF layout handling is basic; complex two-column layouts, tables, formulas, and figure content may need improved extraction.
- The frontend does not yet include a PDF.js reader or citation-to-page navigation.
- Embeddings are stored in SQLite JSON for MVP simplicity. A dedicated vector database can be added later.
- Upload currently performs parsing and embedding synchronously.

## Suggested Next Modules

1. Add PDF.js reader with page rendering.
2. Add citation click-to-page behavior.
3. Move upload processing into background jobs.
4. Add OCR fallback for scanned PDFs.
5. Add structured paper cards for contribution, method, experiments, results, and limitations.
6. Add streaming chat responses.
7. Add a dedicated vector store such as FAISS, Chroma, Qdrant, or Milvus.

## Git Workflow

The repository is connected to:

```text
https://github.com/ShuchenLee/ArticleHelper.git
```

Each completed module should be:

```powershell
python -m pytest -q
git add .
git commit -m "Short module summary"
git push
```
