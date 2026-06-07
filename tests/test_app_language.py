import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app_language import (
    build_prompt_filename,
    format_finish_code,
    get_chat_placeholder,
    get_finish_button_label,
    get_title,
    is_rtl_language,
    normalize_language,
)


def test_normalize_language_defaults_to_hebrew():
    assert normalize_language(None) == "he"
    assert normalize_language("") == "he"


@pytest.mark.parametrize("language", ["he", "HE", " en "])
def test_normalize_language_accepts_supported_values(language):
    assert normalize_language(language) in ("he", "en")


def test_normalize_language_rejects_unsupported_values():
    with pytest.raises(ValueError, match="Invalid 'language'"):
        normalize_language("fr")


def test_build_prompt_filename_uses_exact_language_case_name():
    assert build_prompt_filename(3, "he") == "he_case3.txt"
    assert build_prompt_filename(3, "en") == "en_case3.txt"


def test_language_direction_and_ui_strings():
    assert is_rtl_language("he") is True
    assert is_rtl_language("en") is False
    assert get_title("en", "female") == "Alex the Manager"
    assert get_chat_placeholder("en") == "Type your message here..."
    assert get_finish_button_label("en") == "End conversation"
    assert format_finish_code("en", "83651") == "Finish code: 83651"
