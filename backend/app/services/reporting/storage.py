"""Safe file naming, directory persistence, and SHA-256 integrity calculation for PDF exports."""

import hashlib
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from backend.app.core.config import get_settings


class ReportStorage:
    """Manages secure on-disk persistence of compiled PDF documents."""

    def __init__(self, base_dir: str | None = None) -> None:
        settings = get_settings()
        self.base_dir = Path(base_dir or settings.REPORTS_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def generate_safe_filename(
        self, report_type: str, context_id: str | None = None
    ) -> str:
        """Construct an audit-friendly, sanitized filename without exposing filesystem paths.
        
        Example: VYNTIQ_INDIVIDUAL_PLAYER_P_001_20261108_143000.pdf
        """
        # Sanitize report type and context id to alphanumerics, underscores, and hyphens only
        clean_type = re.sub(r"[^A-Za-z0-9_]", "_", str(report_type).upper())
        clean_id = (
            re.sub(r"[^A-Za-z0-9_-]", "_", str(context_id))
            if context_id
            else "GENERAL"
        )
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"VYNTIQ_{clean_type}_{clean_id}_{timestamp}.pdf"

    def get_file_path(self, filename: str) -> Path:
        """Resolve a filename to a secured, canonical path strictly inside the reports directory.
        
        Prevents directory traversal attacks by verifying the resolved path starts with base_dir.
        """
        # Strip any leading slashes or directories from the filename
        safe_name = os.path.basename(filename)
        resolved = (self.base_dir / safe_name).resolve()

        if not str(resolved).startswith(str(self.base_dir.resolve())):
            raise ValueError(f"Path traversal detected for filename '{filename}'.")

        return resolved

    def compute_sha256(self, file_path: Path) -> str:
        """Calculate the SHA-256 cryptographic digest of a generated PDF file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def get_file_size(self, file_path: Path) -> int:
        """Return the size in bytes of a persisted file."""
        return file_path.stat().st_size
