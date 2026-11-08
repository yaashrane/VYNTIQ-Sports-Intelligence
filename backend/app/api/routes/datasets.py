"""API endpoints for dataset ingestion, inspection, validation, and persistence."""

from typing import Annotated
from fastapi import APIRouter, Depends, File, Header, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.dependencies import get_current_workspace_id, get_db
from backend.app.schemas.dataset import (
    DatasetUploadResponse,
    InspectionReport,
    PersistenceResponse,
    ValidationReport,
    ValidationRequest,
    ValidationSummary,
)
from backend.app.services.ingestion.pipeline import IngestionPipelineService
from backend.app.services.ingestion.uploader import DatasetUploader

router = APIRouter(prefix="/datasets", tags=["Datasets & Ingestion"])


@router.post(
    "/upload",
    response_model=DatasetUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Raw Cricket Dataset",
    description="Accepts a raw CSV or JSON dataset, calculates SHA-256 hash, and stores raw file safely.",
)
async def upload_dataset(
    file: Annotated[UploadFile, File(description="CSV or JSON raw cricket dataset file")],
    session: Annotated[AsyncSession, Depends(get_db)],
    workspace_id: Annotated[str | None, Depends(get_current_workspace_id)] = None,
) -> DatasetUploadResponse:
    """Upload and securely register a raw cricket dataset."""
    uploader = DatasetUploader(session)
    dataset = await uploader.save_uploaded_file(
        file=file,
        workspace_id=workspace_id,
        origin_type="COMPETITION_SANDBOX" if workspace_id else "CANONICAL_HISTORICAL",
    )

    file_size = 0
    try:
        from pathlib import Path
        file_size = Path(dataset.storage_path).stat().st_size
    except Exception:
        pass

    return DatasetUploadResponse(
        dataset_id=dataset.dataset_id,
        filename=dataset.source_filename,
        file_format=dataset.file_format,
        file_size_bytes=file_size,
        status=dataset.status,
        message="Dataset uploaded successfully and ready for structural inspection.",
    )


@router.get(
    "/{dataset_id}/inspection",
    response_model=InspectionReport,
    status_code=status.HTTP_200_OK,
    summary="Inspect Dataset Schema & Headers",
    description="Inspects columns, infers data types, and suggests canonical field mappings without altering records.",
)
async def inspect_dataset(
    dataset_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> InspectionReport:
    """Inspect dataset columns and detect schema mappings."""
    service = IngestionPipelineService(session)
    return await service.inspect_dataset(dataset_id)


@router.post(
    "/{dataset_id}/validate",
    response_model=ValidationReport,
    status_code=status.HTTP_200_OK,
    summary="Validate Dataset & Log Quarantine",
    description="Runs two-tiered structural and cricket domain validation, isolating invalid records.",
)
async def validate_dataset(
    dataset_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: ValidationRequest | None = None,
) -> ValidationReport:
    """Validate dataset records and generate data quality report."""
    service = IngestionPipelineService(session)
    custom_mapping = payload.column_mapping if payload else None
    return await service.validate_dataset(dataset_id=dataset_id, custom_mapping=custom_mapping)


@router.get(
    "/{dataset_id}/status",
    response_model=dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Get Ingestion Processing Status",
    description="Returns the current lifecycle state of the dataset (PENDING, VALIDATED, PERSISTED, etc.).",
)
async def get_dataset_status(
    dataset_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    """Return dataset processing status."""
    service = IngestionPipelineService(session)
    dataset = await service.get_dataset_or_404(dataset_id)
    return {
        "dataset_id": dataset.dataset_id,
        "status": dataset.status,
        "origin_type": dataset.origin_type,
        "workspace_id": dataset.workspace_id or "CANONICAL_GLOBAL",
    }


@router.get(
    "/{dataset_id}/report",
    response_model=ValidationReport,
    status_code=status.HTTP_200_OK,
    summary="Get Data Quality Validation Report",
    description="Returns the complete quality report, record counts, and quarantined issue diagnostics.",
)
async def get_dataset_report(
    dataset_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ValidationReport:
    """Retrieve full validation report."""
    service = IngestionPipelineService(session)
    return await service.get_validation_report(dataset_id)


@router.post(
    "/{dataset_id}/persist",
    response_model=PersistenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Persist Validated Records to Database",
    description="Atomically commits valid delivery records, matches, and players into canonical relational tables.",
)
async def persist_dataset(
    dataset_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: ValidationRequest | None = None,
) -> PersistenceResponse:
    """Persist validated dataset into database."""
    service = IngestionPipelineService(session)
    custom_mapping = payload.column_mapping if payload else None
    return await service.persist_dataset(dataset_id=dataset_id, custom_mapping=custom_mapping)
