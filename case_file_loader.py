from pathlib import Path
from typing import List

from app_language import build_prompt_filename


DEFAULT_CASE_FILES_DIR = Path(__file__).resolve().parent / "case_files"


def resolve_case_file_path(
    case_id: int,
    language: str,
    case_files_dir: Path | str = DEFAULT_CASE_FILES_DIR,
) -> Path:
    filename = build_prompt_filename(case_id, language)
    return Path(case_files_dir) / filename


def read_case_file_lines(
    case_id: int,
    language: str,
    case_files_dir: Path | str = DEFAULT_CASE_FILES_DIR,
) -> List[str]:
    case_path = resolve_case_file_path(case_id, language, case_files_dir)
    if not case_path.is_file():
        raise FileNotFoundError(
            f"Expected case file not found: {case_path}. "
            f"Add {case_path.name} under {Path(case_files_dir)}."
        )
    return case_path.read_text(encoding="utf-8").splitlines()
