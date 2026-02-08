def ask_yes_no(_prompt: str, default: bool = False) -> bool:
    return default


def ask_string(_prompt: str) -> str:
    return ""


def error(_message: str) -> None:
    return None


def info(_message: str) -> None:
    return None


def info_progress(_message: str, _current: int, _total: int) -> None:
    return None


def ask_choice(_prompt: str, choices: list[str]):
    return choices[0] if choices else ""


def select_choices(_prompt: str, choices: list[str]):
    _ = (_prompt, choices)
    return []


red = object()


def setup(*_args, **_kwargs) -> None:
    return None
