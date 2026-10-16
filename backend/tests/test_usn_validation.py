import pytest
from app.services.usn_service import parse_and_validate_usn, determine_academic_year

def test_valid_usn_parsing_cs_2023():
    res = parse_and_validate_usn("ENG23CS0518")
    assert res.is_valid is True
    assert res.normalized_usn == "ENG23CS0518"
    assert res.institution_prefix == "ENG"
    assert res.batch_year == 2023
    assert res.department_code == "CS"
    assert res.department_name == "Computer Science Core"
    assert res.student_sequence == "0518"
    assert res.is_demo is False
    assert res.error_message is None

def test_valid_usn_parsing_ct_2023():
    res = parse_and_validate_usn("ENG23CT0112")
    assert res.is_valid is True
    assert res.batch_year == 2023
    assert res.department_code == "CT"
    assert res.department_name == "Cybersecurity"
    assert res.student_sequence == "0112"

def test_valid_usn_parsing_2024_batch():
    res_cs = parse_and_validate_usn("eng24cs0518")  # Case insensitive
    assert res_cs.is_valid is True
    assert res_cs.normalized_usn == "ENG24CS0518"
    assert res_cs.batch_year == 2024
    assert res_cs.department_code == "CS"

    res_ct = parse_and_validate_usn("ENG24CT0112")
    assert res_ct.is_valid is True
    assert res_ct.batch_year == 2024
    assert res_ct.department_code == "CT"

def test_future_batch_configurable():
    # 2025 and 2026 batches should be valid dynamically
    res_25 = parse_and_validate_usn("ENG25CS0001")
    assert res_25.is_valid is True
    assert res_25.batch_year == 2025

def test_invalid_usn_structures():
    # Bad length / characters
    assert parse_and_validate_usn("INVALID").is_valid is False
    assert parse_and_validate_usn("").is_valid is False
    assert parse_and_validate_usn("123456").is_valid is False
    assert parse_and_validate_usn("ENG23CS").is_valid is False  # Missing sequence
    assert parse_and_validate_usn("ENG23CS0518X").is_valid is False  # Trailing letter

def test_invalid_department_code():
    res = parse_and_validate_usn("ENG23ZZ0518")
    assert res.is_valid is False
    assert "Unrecognized department code" in res.error_message

def test_invalid_batch_year_out_of_range():
    # Year 2010 is out of bounds (min_year=2018)
    res = parse_and_validate_usn("ENG10CS0518")
    assert res.is_valid is False
    assert "Invalid batch year 2010" in res.error_message

def test_demo_usn_detection():
    res = parse_and_validate_usn("DEMO-USN-CSE01")
    assert res.is_valid is True
    assert res.is_demo is True
    assert res.department_code == "CS"
    assert "Demo" in res.department_name

    res_it = parse_and_validate_usn("DEMO-IT-02")
    assert res_it.is_valid is True
    assert res_it.is_demo is True

def test_determine_academic_year():
    # Assuming current year 2026
    assert "1st Year" in determine_academic_year(2026)
    assert "2nd Year" in determine_academic_year(2025)
    assert "3rd Year" in determine_academic_year(2024)
    assert "4th Year" in determine_academic_year(2023)
