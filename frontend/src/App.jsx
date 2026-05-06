import { useMemo, useRef, useState } from 'react'
import * as XLSX from 'xlsx'
import './App.css'

const API_BASE = 'https://invoice-backend.tienloc.org'

function exportToExcel({ results, columns, summary }) {
  const headers = ['S/N', 'File', ...columns.map(c => c.name), 'Notes']
  const rows = results.map((r, i) => {
    const row = {
      'S/N': i + 1,
      'File': r.filename,
    }
    for (const c of columns) {
      const v = r.data?.[c.name]
      row[c.name] = (v === null || v === undefined || v === '') ? '' : v
    }
    row['Notes'] = r.error
      ? `ERROR: ${r.error}`
      : (r.missing && r.missing.length ? `Missing: ${r.missing.join(', ')}` : '')
    return row
  })

  const wb = XLSX.utils.book_new()
  const ws = XLSX.utils.json_to_sheet(rows, { header: headers })

  // Auto-size columns
  ws['!cols'] = headers.map(h => {
    const maxLen = Math.max(
      h.length,
      ...rows.map(r => String(r[h] ?? '').length),
    )
    return { wch: Math.min(Math.max(maxLen + 2, 8), 60) }
  })

  XLSX.utils.book_append_sheet(wb, ws, 'Invoices')

  // Summary sheet
  const counts = summary?.missing_data_counts || {}
  const flagged = summary?.files_with_missing_data || []
  const summaryRows = [
    { Metric: 'Total invoices processed', Value: summary?.total ?? 0 },
    { Metric: 'Successfully extracted',   Value: summary?.successful ?? 0 },
    { Metric: 'Failed',                   Value: summary?.failed ?? 0 },
    { Metric: 'Files with missing fields', Value: flagged.length },
    { Metric: '', Value: '' },
    { Metric: 'Missing field totals', Value: '' },
    ...columns
      .filter(c => counts[c.name])
      .map(c => ({ Metric: `  ${c.name}`, Value: `missing in ${counts[c.name]} of ${summary?.total ?? 0}` })),
    { Metric: '', Value: '' },
    { Metric: 'Per-file flags', Value: '' },
    ...flagged.map(f => ({
      Metric: `  ${f.filename}`,
      Value: `${f.reason || 'missing'}: ${f.missing.join(', ')}`,
    })),
  ]
  const ws2 = XLSX.utils.json_to_sheet(summaryRows, { header: ['Metric', 'Value'] })
  ws2['!cols'] = [{ wch: 36 }, { wch: 60 }]
  XLSX.utils.book_append_sheet(wb, ws2, 'Summary')

  const today = new Date().toISOString().slice(0, 10)
  XLSX.writeFile(wb, `invoice-registry-${today}.xlsx`)
}

const TYPES = ['string', 'number', 'date', 'boolean']

const DEFAULT_COLUMNS = [
  { name: 'project_code',       description: 'Internal project code referenced on the invoice (e.g. Q/26/1010)', type: 'string' },
  { name: 'supplier_name',      description: 'Name of the supplier / vendor issuing the invoice', type: 'string' },
  { name: 'invoice_number',     description: 'Invoice number / invoice reference', type: 'string' },
  { name: 'invoice_date',       description: 'Date the invoice was issued', type: 'date' },
  { name: 'po_number',          description: 'Purchase Order number referenced on the invoice', type: 'string' },
  { name: 'do_number',          description: 'Delivery Order number referenced on the invoice', type: 'string' },
  { name: 'description',        description: 'Description of items / works billed (concise summary)', type: 'string' },
  { name: 'amount_before_gst',  description: 'Subtotal amount before GST / tax', type: 'number' },
  { name: 'gst_percent',        description: 'GST / tax percentage applied (e.g. 9 for 9%)', type: 'number' },
  { name: 'gst_amount',         description: 'GST / tax amount in currency', type: 'number' },
  { name: 'total_amount',       description: 'Final invoice total amount including GST', type: 'number' },
  { name: 'currency',           description: 'Currency code, e.g. SGD, USD, EUR', type: 'string' },
  { name: 'payment_terms',      description: 'Payment terms, e.g. 30D, Net 30, COD', type: 'string' },
  { name: 'cost_code',          description: 'Cost code or trade category, e.g. Electrical, Mechanical', type: 'string' },
]

function ColumnEditor({ columns, setColumns }) {
  const update = (i, patch) => {
    setColumns(cols => cols.map((c, idx) => (idx === i ? { ...c, ...patch } : c)))
  }
  const remove = i => setColumns(cols => cols.filter((_, idx) => idx !== i))
  const add = () => setColumns(cols => [...cols, { name: '', description: '', type: 'string' }])

  return (
    <div className="section">
      <div className="section-head">
        <span className="step-pill">Step 1</span>
        <h2>Define the columns to extract</h2>
      </div>
      <p className="help">
        Tell the model exactly what to pull out of each invoice. Missing fields will be left blank and flagged in the summary.
      </p>
      <div className="col-row">
        <div className="head">Field name</div>
        <div className="head">Description (helps the model)</div>
        <div className="head">Type</div>
        <div></div>
      </div>
      {columns.map((c, i) => (
        <div className="col-row" key={i}>
          <input
            placeholder="e.g. invoice_number"
            value={c.name}
            onChange={e => update(i, { name: e.target.value })}
          />
          <input
            placeholder="What this field means on the invoice"
            value={c.description}
            onChange={e => update(i, { description: e.target.value })}
          />
          <select value={c.type} onChange={e => update(i, { type: e.target.value })}>
            {TYPES.map(t => <option key={t}>{t}</option>)}
          </select>
          <button className="icon-btn" title="Remove" onClick={() => remove(i)}>×</button>
        </div>
      ))}
      <button className="btn-ghost" onClick={add}>+ Add column</button>
    </div>
  )
}

function FileUploader({ files, setFiles }) {
  const inputRef = useRef(null)
  const [drag, setDrag] = useState(false)

  const accept = (incoming) => {
    const arr = Array.from(incoming).filter(f => {
      const n = f.name.toLowerCase()
      return n.endsWith('.pdf') || n.endsWith('.zip')
    })
    setFiles(prev => {
      const existing = new Set(prev.map(f => f.name + f.size))
      const merged = [...prev]
      for (const f of arr) {
        if (!existing.has(f.name + f.size)) merged.push(f)
      }
      return merged
    })
  }

  const onDrop = e => {
    e.preventDefault()
    setDrag(false)
    accept(e.dataTransfer.files)
  }

  return (
    <div className="section">
      <div className="section-head">
        <span className="step-pill">Step 2</span>
        <h2>Upload invoices</h2>
      </div>
      <p className="help">Drop individual PDFs, multiple PDFs, or a single ZIP file containing PDFs.</p>
      <div
        className={`dropzone${drag ? ' drag' : ''}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setDrag(true) }}
        onDragLeave={() => setDrag(false)}
        onDrop={onDrop}
      >
        <div className="dz-icon">↑</div>
        <p className="dz-title">Click to select or drag files here</p>
        <p className="dz-sub">.pdf or .zip — multiple files allowed</p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.zip,application/pdf,application/zip"
          style={{ display: 'none' }}
          onChange={e => accept(e.target.files)}
        />
      </div>
      {files.length > 0 && (
        <div className="file-list">
          {files.map((f, i) => (
            <span className="file-chip" key={f.name + i}>
              {f.name}
              <button onClick={() => setFiles(prev => prev.filter((_, idx) => idx !== i))}>×</button>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function Summary({ summary, columns }) {
  const counts = summary.missing_data_counts || {}
  const flagged = summary.files_with_missing_data || []
  return (
    <div className="section">
      <div className="section-head">
        <span className="step-pill">Summary</span>
        <h2>Extraction overview</h2>
      </div>
      <div className="summary-grid">
        <div className="stat"><div className="v">{summary.total}</div><div className="l">Invoices processed</div></div>
        <div className="stat ok"><div className="v">{summary.successful}</div><div className="l">Extracted</div></div>
        <div className={`stat ${summary.failed ? 'danger' : ''}`}>
          <div className="v">{summary.failed}</div><div className="l">Failed</div>
        </div>
        <div className={`stat ${flagged.length ? 'warn' : ''}`}>
          <div className="v">{flagged.length}</div><div className="l">Files with missing fields</div>
        </div>
      </div>

      {Object.keys(counts).length > 0 && (
        <>
          <p className="help" style={{ marginTop: 6 }}>Missing field totals across all invoices:</p>
          <ul className="flag-list">
            {columns.map(c => counts[c.name]
              ? <li key={c.name}><code>{c.name}</code> — missing in {counts[c.name]} of {summary.total}</li>
              : null
            )}
          </ul>
        </>
      )}

      {flagged.length > 0 && (
        <>
          <p className="help" style={{ marginTop: 12 }}>Per-file flags:</p>
          <ul className="flag-list">
            {flagged.map((f, i) => (
              <li key={i}>
                <strong style={{ color: 'var(--text)' }}>{f.filename}</strong>
                {' — '}
                {f.reason || 'missing'}: {f.missing.map(m => <code key={m} style={{ marginRight: 4 }}>{m}</code>)}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}

function ResultsTable({ results, columns, summary }) {
  if (!results.length) return null
  return (
    <div className="section">
      <div className="section-head" style={{ justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
          <span className="step-pill">Results</span>
          <h2>Extracted data</h2>
        </div>
        <button
          className="btn-ghost"
          onClick={() => exportToExcel({ results, columns, summary })}
          title="Download as .xlsx"
        >
          ↓ Export to Excel
        </button>
      </div>
      <div className="table-wrap">
        <table className="results">
          <thead>
            <tr>
              <th>S/N</th>
              <th>File</th>
              {columns.map(c => <th key={c.name}>{c.name}</th>)}
            </tr>
          </thead>
          <tbody>
            {results.map((r, i) => (
              <tr key={i}>
                <td className="sn-cell">{i + 1}</td>
                <td className="filename-cell">
                  {r.filename}
                  {r.error && <div className="error-cell" style={{ fontSize: 11, marginTop: 2 }}>{r.error}</div>}
                </td>
                {columns.map(c => {
                  const v = r.data?.[c.name]
                  if (v === null || v === undefined || v === '') {
                    return <td key={c.name} className="missing">— missing —</td>
                  }
                  return <td key={c.name}>{typeof v === 'object' ? JSON.stringify(v) : String(v)}</td>
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function App() {
  const [columns, setColumns] = useState(DEFAULT_COLUMNS)
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [response, setResponse] = useState(null)

  const validColumns = useMemo(
    () => columns.filter(c => c.name.trim()).map(c => ({ ...c, name: c.name.trim() })),
    [columns]
  )

  const canSubmit = files.length > 0 && validColumns.length > 0 && !loading

  const submit = async () => {
    setLoading(true)
    setError(null)
    setResponse(null)
    try {
      const fd = new FormData()
      for (const f of files) fd.append('files', f)
      fd.append('columns', JSON.stringify(validColumns))
      const res = await fetch(`${API_BASE}/api/extract`, { method: 'POST', body: fd })
      if (!res.ok) {
        const t = await res.text()
        throw new Error(t || `HTTP ${res.status}`)
      }
      const data = await res.json()
      setResponse(data)
    } catch (e) {
      setError(e.message || String(e))
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setFiles([])
    setResponse(null)
    setError(null)
  }

  return (
    <div className="app">
      <div className="app-header">
        <div className="app-logo">AI</div>
        <div>
          <h1>Invoice Registry</h1>
          <p className="sub">Upload invoices from any provider — define your columns once, get a clean table back.</p>
        </div>
      </div>

      <ColumnEditor columns={columns} setColumns={setColumns} />
      <FileUploader files={files} setFiles={setFiles} />

      <div className="section">
        <div className="actions">
          <button className="btn" disabled={!canSubmit} onClick={submit}>
            {loading && <span className="spinner" />}
            {loading ? 'Extracting…' : `Extract ${files.length} file${files.length === 1 ? '' : 's'}`}
          </button>
          {(response || error) && (
            <button className="btn-ghost" onClick={reset}>Clear results</button>
          )}
          {!validColumns.length && <span className="help" style={{ margin: 0 }}>Define at least one column.</span>}
        </div>
        {error && <div className="error">{error}</div>}
      </div>

      {response && (
        <>
          <Summary summary={response.summary} columns={response.columns} />
          <ResultsTable results={response.results} columns={response.columns} summary={response.summary} />
        </>
      )}
    </div>
  )
}
