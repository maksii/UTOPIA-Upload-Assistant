class AccessDenied(Exception):
    pass


class NoSuchProcess(Exception):
    pass


class Process:
    def __init__(self, _pid: int | None = None) -> None:
        _ = _pid

    def children(self, recursive: bool = True):
        _ = recursive
        return []

    def terminate(self) -> None:
        return None

    def kill(self) -> None:
        return None


def process_iter(_attrs=None):
    return []


def wait_procs(_procs, timeout: float | None = None):
    _ = timeout
    return [], []
