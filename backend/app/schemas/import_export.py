from typing import Dict, List, Any, Optional
from pydantic import BaseModel

class ColumnMappingInfo(BaseModel):
    source_header: str
    target_field: str
    confidence: str  # "HIGH", "AMBIGUOUS", "UNMAPPED"
    reason: Optional[str] = None

class ImportPreviewRow(BaseModel):
    row_number: int
    name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    notes: Optional[str] = None
    skills: Optional[str] = None
    experience_years: Optional[float] = None
    status_flag: str  # "NEW", "EXACT_DUPLICATE", "POSSIBLE_DUPLICATE", "INVALID"
    duplicate_reason: Optional[str] = None
    issue_details: Optional[str] = None

class ImportPreviewResponse(BaseModel):
    file_name: str
    original_filename: str
    file_size_bytes: int
    import_type: str = "HR_CONTACTS"  # "HR_CONTACTS" or "CANDIDATES"
    total_rows: int
    selected_sheet: str
    sheets: List[str]
    detected_headers: List[str]
    column_mappings: List[ColumnMappingInfo]
    suggested_mappings: Dict[str, str]
    preview_rows: List[ImportPreviewRow]
    summary_stats: Dict[str, int]

class ImportConfirmRequest(BaseModel):
    file_token: str
    import_type: str = "HR_CONTACTS"  # "HR_CONTACTS" or "CANDIDATES"
    sheet_name: str = "Sheet1"
    mapping: Dict[str, str]
    duplicate_handling: str = "SKIP"  # "SKIP", "UPDATE", "IMPORT_ALL"

class ImportResultResponse(BaseModel):
    success: bool
    imported_contacts_count: int = 0
    imported_companies_count: int = 0
    reused_companies_count: int = 0
    imported_candidates_count: int = 0
    updated_records_count: int = 0
    skipped_duplicates_count: int = 0
    invalid_rows_count: int = 0
    errors_count: int = 0
    message: str

