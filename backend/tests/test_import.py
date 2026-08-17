import io
import openpyxl
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def get_auth_header(email="importuser@example.com"):
    boot = client.post("/api/v1/auth/admin/bootstrap", json={
        "bootstrap_key": settings.ADMIN_BOOTSTRAP_SECRET,
        "full_name": "Import Admin User",
        "email": email,
        "password": "Password123!"
    })
    if boot.status_code in (200, 201):
        token = boot.json()["access_token"]
    else:
        login = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"})
        token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_csv_import_preview_and_confirm():
    headers = get_auth_header("csvuser@example.com")

    csv_content = (
        "HR Name,Company Name,Phone,Email,Designation\n"
        "Priya Sharma,Infosys,+91 9876543210,priya@infosys.com,Senior Recruiter\n"
        "Rahul Patil,TCS,+91 9999911111,rahul@tcs.com,Talent Acquisition\n"
    )

    files = {"file": ("contacts.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}

    # 1. Preview
    preview_res = client.post("/api/v1/import/preview", files=files, headers=headers)
    assert preview_res.status_code == 200
    preview_data = preview_res.json()
    assert preview_data["total_rows"] == 2
    assert preview_data["summary_stats"]["new_count"] == 2

    file_token = preview_data["file_name"]
    mapping = preview_data["suggested_mappings"]

    # 2. Confirm
    confirm_res = client.post("/api/v1/import/confirm", json={
        "file_token": file_token,
        "sheet_name": "Sheet1",
        "mapping": mapping,
        "duplicate_handling": "SKIP"
    }, headers=headers)

    assert confirm_res.status_code == 200
    result = confirm_res.json()
    assert result["success"] is True
    assert result["imported_contacts_count"] == 2
    assert result["imported_companies_count"] == 2

    # 3. Verify contacts exist in DB via API
    list_res = client.get("/api/v1/contacts", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 2

def test_multisheet_xlsx_and_variant_headers():
    headers = get_auth_header("xlsxuser@example.com")

    # Create workbook with 2 sheets
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "HR Contacts"
    ws1.append(["HR Name", "Company Name", "Designation", "Phone Number", "Email ID", "Location", "Notes"])
    ws1.append(["Anita Desai", "Wipro", "Lead Recruiter", "9876500001", "anita@wipro.com", "Bangalore", "Great contact"])

    ws2 = wb.create_sheet(title="Variant Headers Test")
    ws2.append(["Contact Person", "Employer", "Job Title", "Mobile", "E-mail", "City", "Remarks"])
    ws2.append(["Suresh Kumar", "Accenture", "TA Manager", "9876500002", "suresh@accenture.com", "Hyderabad", "Variant test"])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    # 1. Preview Sheet 1
    files1 = {"file": ("test_multisheet.xlsx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    prev1 = client.post("/api/v1/import/preview?import_type=HR_CONTACTS", files=files1, headers=headers)
    assert prev1.status_code == 200
    data1 = prev1.json()
    assert data1["sheets"] == ["HR Contacts", "Variant Headers Test"]
    assert data1["selected_sheet"] == "HR Contacts"
    assert data1["suggested_mappings"]["HR Name"] == "name"
    assert data1["suggested_mappings"]["Company Name"] == "company_name"

    # 2. Preview Sheet 2
    files2 = {"file": ("test_multisheet.xlsx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    prev2 = client.post("/api/v1/import/preview?import_type=HR_CONTACTS&sheet_name=Variant%20Headers%20Test", files=files2, headers=headers)
    assert prev2.status_code == 200
    data2 = prev2.json()
    assert data2["selected_sheet"] == "Variant Headers Test"
    assert data2["suggested_mappings"]["Contact Person"] == "name"
    assert data2["suggested_mappings"]["Employer"] == "company_name"
    assert data2["suggested_mappings"]["Mobile"] == "phone"
    assert data2["suggested_mappings"]["E-mail"] == "email"

def test_duplicate_detection_and_missing_optional_fields():
    headers = get_auth_header("dupuser@example.com")

    # Seed an existing contact first
    csv_content1 = (
        "HR Name,Company Name,Phone,Email\n"
        "Rajesh V,HCL,+91 9900011122,rajesh@hcl.com\n"
    )
    files1 = {"file": ("seed.csv", io.BytesIO(csv_content1.encode("utf-8")), "text/csv")}
    p1 = client.post("/api/v1/import/preview", files=files1, headers=headers).json()
    client.post("/api/v1/import/confirm", json={
        "file_token": p1["file_name"],
        "mapping": p1["suggested_mappings"],
        "duplicate_handling": "SKIP"
    }, headers=headers)

    # Now upload file with exact duplicate email and optional missing fields
    csv_content2 = (
        "HR Name,Company Name,Phone,Email,Designation\n"
        "Rajesh V,HCL,+91 9900011122,rajesh@hcl.com,Senior TA\n"
        "New Contact,HCL,,newcontact@hcl.com,\n"  # Missing phone and designation
    )
    files2 = {"file": ("test_dup.csv", io.BytesIO(csv_content2.encode("utf-8")), "text/csv")}
    p2_res = client.post("/api/v1/import/preview", files=files2, headers=headers)
    assert p2_res.status_code == 200
    p2 = p2_res.json()
    assert p2["summary_stats"]["exact_duplicates"] == 1
    assert p2["summary_stats"]["new_count"] == 1

def test_empty_workbook_structured_error():
    headers = get_auth_header("erruser@example.com")

    csv_content = ""
    files = {"file": ("empty.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    res = client.post("/api/v1/import/preview", files=files, headers=headers)
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert "empty" in detail.lower() or "readable" in detail.lower()

def test_ambiguous_header_detection():
    headers = get_auth_header("ambiguser@example.com")
    csv_content = "Name,Contact,Details\nJohn Doe,1234567890,Some note\n"
    files = {"file": ("ambig.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    res = client.post("/api/v1/import/preview", files=files, headers=headers)
    assert res.status_code == 200
    data = res.json()
    mappings = {m["source_header"]: m for m in data["column_mappings"]}
    assert mappings["Name"]["confidence"] == "AMBIGUOUS"
    assert mappings["Contact"]["confidence"] == "AMBIGUOUS"

def test_unsupported_file_extension_structured_error():
    headers = get_auth_header("badext@example.com")
    files = {"file": ("data.txt", io.BytesIO(b"hello world"), "text/plain")}
    res = client.post("/api/v1/import/preview", files=files, headers=headers)
    assert res.status_code == 400
    assert "Unsupported file format" in res.json()["detail"]

def test_actual_56_records_workbook_file(reset_db_schema):
    import os
    file_path = r"C:\Users\vinay\Downloads\NxtMov_HR_Contacts_Test_56.xlsx"
    if os.path.exists(file_path):
        headers = get_auth_header("wb56user@example.com")
        with open(file_path, "rb") as f:
            files = {"file": ("NxtMov_HR_Contacts_Test_56.xlsx", f.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        res1 = client.post("/api/v1/import/preview?import_type=HR_CONTACTS", files=files, headers=headers)
        assert res1.status_code == 200
        d1 = res1.json()
        assert d1["total_rows"] == 56
        assert d1["selected_sheet"] == "HR Contacts"

        # Preview Sheet 2
        with open(file_path, "rb") as f:
            files2 = {"file": ("NxtMov_HR_Contacts_Test_56.xlsx", f.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        res2 = client.post("/api/v1/import/preview?import_type=HR_CONTACTS&sheet_name=Variant%20Headers%20Test", files=files2, headers=headers)
        assert res2.status_code == 200
        d2 = res2.json()
        assert d2["selected_sheet"] == "Variant Headers Test"
        assert d2["suggested_mappings"]["Contact Person"] == "name"
        assert d2["suggested_mappings"]["Employer"] == "company_name"

