from pathlib import Path

import pytest
from openpyxl import Workbook

from src.exceptions import InvalidInputError
from src.services.spreadsheet import read_people

FIXTURE = Path(__file__).parent.parent / "fixtures" / "challenge.xlsx"
HEADER = [
    "First Name",
    "Last Name ",
    "Company Name",
    "Role in Company",
    "Address",
    "Email",
    "Phone Number",
]


def _write(tmp_path: Path, rows: list[list[object]]) -> Path:
    workbook = Workbook()
    for row in rows:
        workbook.active.append(row)
    path = tmp_path / "planilha.xlsx"
    workbook.save(path)
    return path


def test_reads_the_official_challenge_file():
    people = read_people(FIXTURE)
    assert len(people) == 10
    assert people[0].first_name == "John"
    assert people[0].last_name == "Smith"
    assert people[0].phone == "40716543298"


def test_header_with_trailing_spaces_and_other_order(tmp_path):
    header = list(reversed(HEADER))
    row = list(reversed(["Ana", "Lima", "ACME", "Dev", "Rua 1", "ana@acme.com", 11999990000]))
    people = read_people(_write(tmp_path, [header, row]))
    assert people[0].first_name == "Ana"
    assert people[0].phone == "11999990000"


def test_skips_blank_rows(tmp_path):
    row = ["Ana", "Lima", "ACME", "Dev", "Rua 1", "ana@acme.com", "1199"]
    people = read_people(_write(tmp_path, [HEADER, row, [None] * 7, row]))
    assert len(people) == 2


def test_missing_column_raises(tmp_path):
    with pytest.raises(InvalidInputError, match="phone"):
        read_people(_write(tmp_path, [HEADER[:-1], ["a"] * 6]))


def test_invalid_email_raises_with_line_number(tmp_path):
    row = ["Ana", "Lima", "ACME", "Dev", "Rua 1", "sem-arroba", "1199"]
    with pytest.raises(InvalidInputError, match="Linha 2"):
        read_people(_write(tmp_path, [HEADER, row]))
