import io
import json
import os
import zipfile
from typing import List, Optional

import pdfplumber
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="AI Invoice Registry")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000", "http://127.0.0.1:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o-mini"


class Column(BaseModel):
    name: str
    description: Optional[str] = ""
    type: Optional[str] = "string"


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    parts: List[str] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
    return "\n".join(parts)


def collect_pdfs(files: List[UploadFile], contents: List[bytes]):
    pdfs: List[tuple[str, bytes]] = []
    for upload, raw in zip(files, contents):
        name = upload.filename or "unknown"
        lower = name.lower()
        if lower.endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                    for member in zf.namelist():
                        if member.lower().endswith(".pdf") and not member.startswith("__MACOSX"):
                            pdfs.append((os.path.basename(member) or member, zf.read(member)))
            except zipfile.BadZipFile:
                continue
        elif lower.endswith(".pdf"):
            pdfs.append((name, raw))
    return pdfs


def build_prompt(columns: List[dict], invoice_text: str) -> str:
    lines = []
    for c in columns:
        t = c.get("type") or "string"
        desc = c.get("description") or ""
        lines.append(f'- "{c["name"]}" (type: {t}): {desc}')
    cols_block = "\n".join(lines)
    return f"""You are extracting structured data from a single invoice. Invoices may come from different providers and use different layouts.

Extract these fields and return them in a JSON object using the EXACT keys shown:
{cols_block}

Rules:
- If a field is not clearly present in the invoice, set its value to null. Do not guess.
- Preserve numbers as numbers when the type is number/integer/float. Otherwise use strings.
- For dates, use ISO 8601 (YYYY-MM-DD) when possible.
- Return ONLY the JSON object — no commentary.

Invoice text:
\"\"\"
{invoice_text}
\"\"\"
"""


def extract_with_openai(text: str, columns: List[dict]) -> dict:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a precise invoice data extraction assistant. Return only valid JSON with the requested keys.",
            },
            {"role": "user", "content": build_prompt(columns, text)},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return json.loads(response.choices[0].message.content)


def normalize_value(value):
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        if s == "" or s.lower() in {"null", "n/a", "na", "none", "-"}:
            return None
        return s
    return value


@app.get("/api/health")
def health():
    return {"ok": True, "model": MODEL}


@app.post("/api/extract")
async def extract_invoices(
    files: List[UploadFile] = File(...),
    columns: str = Form(...),
):
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(500, "OPENAI_API_KEY is not configured on the server.")

    try:
        cols = json.loads(columns)
        if not isinstance(cols, list) or not cols:
            raise ValueError
        for c in cols:
            if "name" not in c or not c["name"]:
                raise ValueError
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(400, "`columns` must be a non-empty JSON array of {name, description?, type?}.")

    contents = [await f.read() for f in files]
    pdfs = collect_pdfs(files, contents)

    if not pdfs:
        raise HTTPException(400, "No PDF files found in the upload.")

    results = []
    missing_counts: dict[str, int] = {}
    files_with_missing = []
    successful = 0
    failed = 0

    for filename, pdf_bytes in pdfs:
        row = {"filename": filename, "data": {c["name"]: None for c in cols}, "missing": [], "error": None}
        try:
            text = extract_text_from_pdf(pdf_bytes)
            if not text.strip():
                row["missing"] = [c["name"] for c in cols]
                row["error"] = "No selectable text found in PDF (may be a scanned image)."
                results.append(row)
                failed += 1
                files_with_missing.append({"filename": filename, "missing": row["missing"], "reason": row["error"]})
                for c in cols:
                    missing_counts[c["name"]] = missing_counts.get(c["name"], 0) + 1
                continue

            raw = extract_with_openai(text, cols)
            normalized = {}
            missing = []
            for c in cols:
                v = normalize_value(raw.get(c["name"]))
                normalized[c["name"]] = v
                if v is None:
                    missing.append(c["name"])
                    missing_counts[c["name"]] = missing_counts.get(c["name"], 0) + 1

            row["data"] = normalized
            row["missing"] = missing
            results.append(row)
            successful += 1
            if missing:
                files_with_missing.append({"filename": filename, "missing": missing, "reason": "Field(s) absent from invoice"})

        except Exception as e:  # noqa: BLE001
            row["missing"] = [c["name"] for c in cols]
            row["error"] = f"{type(e).__name__}: {e}"
            results.append(row)
            failed += 1

    summary = {
        "total": len(pdfs),
        "successful": successful,
        "failed": failed,
        "missing_data_counts": missing_counts,
        "files_with_missing_data": files_with_missing,
    }

    return {"columns": cols, "results": results, "summary": summary}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)
