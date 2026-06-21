import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from case_file_loader import read_case_file_lines, resolve_case_file_path


def test_resolve_case_file_path_uses_language_case_filename(tmp_path):
    assert resolve_case_file_path(3, "en", tmp_path) == tmp_path / "en_case3.txt"


def test_read_case_file_lines_reads_utf8_and_preserves_line_splitting(tmp_path):
    case_file = tmp_path / "he_case2.txt"
    case_file.write_text("first line\nsecond line\nthird line", encoding="utf-8")

    assert read_case_file_lines(2, "he", tmp_path) == [
        "first line",
        "second line",
        "third line",
    ]


def test_read_case_file_lines_raises_clear_error_for_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="Expected case file not found"):
        read_case_file_lines(8, "en", tmp_path)
