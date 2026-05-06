# AI Invoice Registry

FastAPI + React (Vite) app that extracts structured data from a batch of invoice PDFs using OpenAI `gpt-4o-mini`. The user defines the columns up front; the table is filled in automatically and missing fields are flagged in the summary.

## Layout

```
backend/    FastAPI app (PDF text extraction + OpenAI call)
frontend/   React + Vite UI
```

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env       # then put your real key in .env
# OPENAI_API_KEY=sk-...

uvicorn main:app --reload --port 8000
```

Health check: <http://localhost:8000/api/health>

### Endpoint

`POST /api/extract` — multipart form data:
- `files`: one or more `.pdf` and/or a single `.zip` containing PDFs
- `columns`: JSON string, e.g.
  ```json
  [
    {"name": "invoice_number", "description": "Unique invoice id", "type": "string"},
    {"name": "total_amount",   "description": "Grand total",       "type": "number"}
  ]
  ```

Response:
```json
{
  "columns": [...],
  "results": [
    { "filename": "acme-001.pdf", "data": {"invoice_number": "A-001", "total_amount": 230.00}, "missing": [], "error": null }
  ],
  "summary": {
    "total": 12,
    "successful": 11,
    "failed": 1,
    "missing_data_counts": {"currency": 3},
    "files_with_missing_data": [{"filename": "x.pdf", "missing": ["currency"], "reason": "Field(s) absent from invoice"}]
  }
}
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Then open <http://localhost:5173>. The Vite dev server proxies `/api/*` to the backend on port 8000, so just keep both processes running.

## Notes

- Text-based PDFs only (uses `pdfplumber`). Scanned/image-only PDFs return an error per-file with the reason `No selectable text found in PDF (may be a scanned image)` — add an OCR step (e.g. `pytesseract`) if you need to handle those.
- Missing/null values are normalized server-side ("N/A", "-", "null", empty string → `null`) and reported in `summary.missing_data_counts` and `summary.files_with_missing_data`.
- Model: `gpt-4o-mini`, `temperature=0`, `response_format=json_object` for stable structured output.
