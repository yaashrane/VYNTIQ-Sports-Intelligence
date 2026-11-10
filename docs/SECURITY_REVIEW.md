# VYNTIQ — Security & Architectural Review

**Document ID:** VYNTIQ-SEC-001  
**Status:** APPROVED — RELEASE READY  
**Classification:** Internal Technical Architecture  
**Date:** 2026-11-08  

---

## 1. Overview & Threat Model

VYNTIQ is an analytical sports intelligence platform that processes athlete performance records, generates proprietary candidate rankings, and produces competition dossiers. 

The security architecture focuses on:
1. **Multi-Tenant Workspace Isolation (ADR-001):** Ensuring that proprietary shortlists, scout evaluations, notes, and workspace configurations cannot be accessed across organizational or tournament boundaries.
2. **Storage and Path Traversal Defenses:** Eliminating file injection and directory transversal during dataset upload and report download operations.
3. **Upload Pipeline Hardening:** Enforcing strict content inspection, size limits, and format gating.
4. **Information Disclosure Prevention:** Guaranteeing that unhandled exceptions and tracebacks do not leak internal system details, database schemas, or filesystem paths to end users or API consumers.

---

## 2. Multi-Tenant Workspace Isolation (ADR-001)

### 2.1 Workspace Boundary Enforcement
Every sensitive resource—including datasets, configurations, shortlists, candidate entries, and PDF reports—is bound to a foreign key `workspace_id`.

```python
# Enforcement pattern in ShortlistingService:
dataset_query = select(Dataset).where(Dataset.dataset_id == payload.dataset_id)
ds_res = await self.session.execute(dataset_query)
dataset = ds_res.scalars().first()
if dataset and dataset.workspace_id and dataset.workspace_id != workspace_id:
    raise WorkspaceException(
        f"Dataset '{payload.dataset_id}' belongs to workspace '{dataset.workspace_id}' "
        f"and cannot be accessed by '{workspace_id}'."
    )
```

### 2.2 Shortlist and Report Scoping
- All candidate queries filter explicitly by `workspace_id`.
- Report download endpoints verify that the requested `report_id` belongs to the `workspace_id` in the URL path; requests targeting reports from other workspaces return `HTTP 404 EntityNotFoundException`.

---

## 3. Storage & Path Traversal Prevention

### 3.1 Filename Sanitization
User-supplied filenames (e.g., CSV filenames or custom export titles) are never used directly as filesystem paths.

```python
# ReportStorageService path safety implementation:
def _sanitize_filename(self, filename: str) -> str:
    # Strip path separators and non-standard characters
    clean = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', os.path.basename(filename))
    return clean.strip('._') or "unnamed_report"
```

### 3.2 Canonical Path Traversal Verification
All generated file paths are strictly resolved against `settings.STORAGE_PATH`:
- If `os.path.commonpath([resolved_path, allowed_dir]) != allowed_dir`, an immediate `ValidationException` is raised.
- Relative navigation characters (`..`, `~`, `/`, `\`) are neutralized by `os.path.basename` extraction prior to filesystem operations.

*Automated test:* `backend/tests/test_reporting_and_export.py::test_file_naming_safety_and_path_traversal_prevention` **PASSED**.

---

## 4. Dataset Ingestion & Upload Security

### 4.1 File Size Gating
- Maximum upload size is strictly capped at **100 MB** (`settings.MAX_UPLOAD_SIZE_MB = 100`).
- Stream length is validated chunk-by-chunk during upload processing. Files exceeding the limit are immediately aborted with `HTTP 413 Payload Too Large` without filling disk storage.

### 4.2 MIME & Extension Validation
- Uploaded files must match approved formats: `.csv` (`text/csv`, `application/vnd.ms-excel`) or `.json` (`application/json`).
- Executable files (`.exe`, `.sh`, `.bat`, `.py`) and unknown binary blobs are rejected at upload validation before parsing.

### 4.3 Content Disinfection & Cryptographic Fingerprinting
- Every uploaded dataset receives a computed SHA-256 hash at upload time.
- The raw byte stream is stored immutably; data parsing occurs in memory using isolated Pandas/Pydantic parsers.
- No dynamic code execution (`eval()`, `exec()`, or pickle serialization) is used anywhere in the ingestion pipeline.

---

## 5. Error Shielding & Information Disclosure

### 5.1 Global Exception Handlers
VYNTIQ implements custom exception handlers for:
- `AppException` (Domain errors: `EntityNotFoundException`, `ValidationException`, `ConflictException`, `WorkspaceException`).
- `RequestValidationError` (Pydantic schema validation failures).
- `Exception` (Unhandled internal server errors).

### 5.2 Stack Trace Leakage Prevention
In production (`ENVIRONMENT = "production"`), any unhandled error logs the full traceback internally using structured JSON logging with a unique correlation `request_id`, but returns a sanitised client response:

```json
{
  "code": "INTERNAL_SERVER_ERROR",
  "message": "An unexpected internal server error occurred. Please contact system support.",
  "request_id": "req_84f93b1e"
}
```

*Automated test:* `backend/tests/test_errors.py::test_unhandled_exception_does_not_leak_traceback` **PASSED**.

---

## 6. Audit Trail & Immutability

### 6.1 Shortlist Audit Logs
- Every generated shortlist creates an immutable `ShortlistAuditLog` entry detailing:
  - Generating user or system identity.
  - Snapshot timestamp.
  - Total candidates evaluated, eligible count, and excluded count.
  - Full configuration parameters used during generation.

### 6.2 Analytics Immutability
- Scout reviews (`APPROVED`, `REJECTED`, `NEEDS_REVIEW`) and scout notes are stored on the candidate linkage table (`shortlist_candidates`).
- The underlying performance metrics, evaluation profiles, and VOR scores are strictly read-only and immutable.

---

## 7. Security Audit Matrix

| Audit Item | Mechanism | Implementation | Test Status |
|:---|:---|:---|:---|
| Multi-tenant Workspace Isolation | Tenant boundary validation | `ShortlistingService`, `WorkspaceRepo` | Verified |
| Path Traversal Defenses | Filename sanitization, canonical path check | `ReportStorageService` | Verified |
| Upload Size Limits | Chunk-level size monitoring (100MB) | `DatasetService.upload_dataset` | Verified |
| Malformed File Protection | Pydantic schema validation & quarantine | `DatasetValidator` | Verified |
| Traceback Shielding | Custom FastAPI error handlers | `backend/app/main.py` | Verified |
| Score Tampering | Immutable scoring runs & read-only profiles | `ScoringEngine`, `ShortlistingService` | Verified |

