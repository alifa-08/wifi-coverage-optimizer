"""
College USN and Batch Validation Service
-----------------------------------------
Parses, validates, and standardizes college University Seat Numbers (USNs).

Format specification:
  Example: ENG23CS0518
    - ENG : 3-letter institution / college prefix
    - 23  : 2-digit admission / batch year -> 2023
    - CS  : 2-letter academic department code
    - 0518: 3 to 5 digit student sequence / roll number

Department mappings and batch year limits are configurable.
Demo accounts (e.g., DEMO-USN-CSE01) are explicitly detected and labelled.
"""

import re
from datetime import datetime
from typing import Dict, Any, Optional

# Supported academic departments (Configurable dictionary)
DEFAULT_DEPARTMENT_MAP = {
    "CS": "Computer Science Core",
    "CT": "Cybersecurity",
    "IT": "Information Technology",
    "IS": "Information Science & Engineering",
    "EC": "Electronics & Communication",
    "ME": "Mechanical Engineering",
    "AI": "Artificial Intelligence & Data Science",
    "DS": "Data Science",
    "EE": "Electrical & Electronics Engineering",
    "CV": "Civil Engineering",
}

# Regex for standard college USN: 3 letters + 2 digits + 2 letters + 3-5 digits
USN_STANDARD_REGEX = re.compile(r"^([A-Za-z]{3})(\d{2})([A-Za-z]{2})(\d{3,5})$")

# Demo USN format: DEMO-USN-xxx or DEMO-xxx
DEMO_USN_REGEX = re.compile(r"^DEMO(?:-USN)?-([A-Za-z0-9]+)$", re.IGNORECASE)


class UsnParseResult:
    """Structured result of USN parsing and validation."""
    def __init__(
        self,
        is_valid: bool,
        normalized_usn: str,
        institution_prefix: Optional[str] = None,
        batch_year: Optional[int] = None,
        department_code: Optional[str] = None,
        department_name: Optional[str] = None,
        student_sequence: Optional[str] = None,
        is_demo: bool = False,
        error_message: Optional[str] = None
    ):
        self.is_valid = is_valid
        self.normalized_usn = normalized_usn
        self.institution_prefix = institution_prefix
        self.batch_year = batch_year
        self.department_code = department_code
        self.department_name = department_name
        self.student_sequence = student_sequence
        self.is_demo = is_demo
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "normalized_usn": self.normalized_usn,
            "institution_prefix": self.institution_prefix,
            "batch_year": self.batch_year,
            "department_code": self.department_code,
            "department_name": self.department_name,
            "student_sequence": self.student_sequence,
            "is_demo": self.is_demo,
            "error_message": self.error_message
        }


def parse_and_validate_usn(
    usn: str,
    department_map: Optional[Dict[str, str]] = None,
    min_year: int = 2018,
    max_future_years: int = 2
) -> UsnParseResult:
    """
    Parses and thoroughly validates a College USN.

    1. Trims whitespace and normalizes to uppercase.
    2. Identifies demo test accounts (clearly labelled).
    3. Extracts institution code, batch year (e.g. 23 -> 2023), department code, and roll sequence.
    4. Validates batch year against realistic campus window (configurable min_year to current + max_future_years).
    5. Validates department against recognized college branches.
    """
    if not usn or not usn.strip():
        return UsnParseResult(
            is_valid=False,
            normalized_usn="",
            error_message="USN cannot be empty."
        )

    clean_usn = usn.strip().upper()
    dept_map = department_map or DEFAULT_DEPARTMENT_MAP

    # Check for demo accounts
    demo_match = DEMO_USN_REGEX.match(clean_usn)
    if demo_match or "DEMO" in clean_usn:
        # Determine department hint if available
        dept_name = "Computer Science Core (Demo)"
        dept_code = "CS"
        if "IT" in clean_usn:
            dept_name = "Information Technology (Demo)"
            dept_code = "IT"
        elif "ECE" in clean_usn or "EC" in clean_usn:
            dept_name = "Electronics & Communication (Demo)"
            dept_code = "EC"
        elif "ME" in clean_usn:
            dept_name = "Mechanical Engineering (Demo)"
            dept_code = "ME"

        return UsnParseResult(
            is_valid=True,
            normalized_usn=clean_usn,
            institution_prefix="DEMO",
            batch_year=2023,
            department_code=dept_code,
            department_name=dept_name,
            student_sequence=demo_match.group(1) if demo_match else "001",
            is_demo=True,
            error_message=None
        )

    # Standard College USN Match
    match = USN_STANDARD_REGEX.match(clean_usn)
    if not match:
        return UsnParseResult(
            is_valid=False,
            normalized_usn=clean_usn,
            error_message="Invalid USN structure. Expected format: 3-letter prefix + 2-digit batch year + 2-letter department + 3-5 digits (e.g., ENG23CS0518, ENG23CT0112)."
        )

    prefix, year_str, dept_code, seq = match.groups()

    # Calculate full 4-digit batch year
    two_digit_year = int(year_str)
    full_batch_year = 2000 + two_digit_year

    current_year = datetime.now().year
    max_allowed_year = current_year + max_future_years

    if full_batch_year < min_year or full_batch_year > max_allowed_year:
        return UsnParseResult(
            is_valid=False,
            normalized_usn=clean_usn,
            institution_prefix=prefix,
            batch_year=full_batch_year,
            department_code=dept_code,
            student_sequence=seq,
            error_message=f"Invalid batch year {full_batch_year}. Accepted admission batches: {min_year} to {max_allowed_year}."
        )

    # Validate department code
    if dept_code not in dept_map:
        valid_depts = ", ".join(dept_map.keys())
        return UsnParseResult(
            is_valid=False,
            normalized_usn=clean_usn,
            institution_prefix=prefix,
            batch_year=full_batch_year,
            department_code=dept_code,
            student_sequence=seq,
            error_message=f"Unrecognized department code '{dept_code}'. Supported branches: {valid_depts}."
        )

    department_name = dept_map[dept_code]

    return UsnParseResult(
        is_valid=True,
        normalized_usn=clean_usn,
        institution_prefix=prefix,
        batch_year=full_batch_year,
        department_code=dept_code,
        department_name=department_name,
        student_sequence=seq,
        is_demo=False,
        error_message=None
    )


def determine_academic_year(batch_year: int) -> str:
    """
    Estimates current academic year based on admission batch year.
    E.g. in 2026:
      - 2026 batch -> 1st Year
      - 2025 batch -> 2nd Year
      - 2024 batch -> 3rd Year
      - 2023 batch -> 4th Year / Final Year
      - <= 2022 batch -> Alumni / Extended
    """
    current_year = datetime.now().year
    diff = current_year - batch_year
    if diff <= 0:
        return "1st Year"
    elif diff == 1:
        return "2nd Year"
    elif diff == 2:
        return "3rd Year"
    elif diff == 3:
        return "4th Year / Final Year"
    else:
        return f"Batch {batch_year} (Senior/Alumni)"
