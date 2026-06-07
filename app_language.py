SUPPORTED_LANGUAGES = ("he", "en")
DEFAULT_LANGUAGE = "he"


def normalize_language(value: str | None) -> str:
    language = (value or DEFAULT_LANGUAGE).strip().lower()
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError("Invalid 'language'. Use he or en.")
    return language


def build_prompt_filename(case_id: int, language: str) -> str:
    return f"{normalize_language(language)}_case{case_id}.txt"


def is_rtl_language(language: str) -> bool:
    return normalize_language(language) == "he"


def get_title(language: str, alex_gender: str) -> str:
    if normalize_language(language) == "en":
        return "Alex the Manager"
    return "אלכס המנהל" if alex_gender == "male" else "אלכס המנהלת"


def get_chat_placeholder(language: str) -> str:
    if normalize_language(language) == "en":
        return "Type your message here..."
    return "הקלד/י את ההודעה כאן..."


def get_finish_button_label(language: str) -> str:
    if normalize_language(language) == "en":
        return "End conversation"
    return "סיים שיחה"


def format_finish_code(language: str, finish_code: str) -> str:
    if normalize_language(language) == "en":
        return f"Finish code: {finish_code}"
    return f"קוד סיום: {finish_code}"
