from __future__ import annotations

from typing import Any, Callable


class Response:
    def __init__(
        self,
        response: Any = None,
        status: int = 200,
        headers: dict[str, str] | None = None,
        mimetype: str | None = None,
    ) -> None:
        self.response = response if response is not None else []
        self.status_code = status
        self.headers = headers or {}
        self.mimetype = mimetype


def jsonify(payload: Any, *args: Any, **kwargs: Any) -> dict[str, Any]:
    _ = (args, kwargs)
    return {"json": payload}


def render_template(*_args: Any, **_kwargs: Any) -> str:
    return ""


class _Request:
    def __init__(self) -> None:
        self.json: dict[str, Any] | None = None
        self.method = "GET"
        self.path = "/"
        self.authorization = None


request = _Request()


class Flask:
    def __init__(self, _name: str) -> None:
        self._before_request: list[Callable[[], Any]] = []

    def route(self, _rule: str, methods: list[str] | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        _ = methods

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return decorator

    def before_request(self, func: Callable[..., Any]) -> Callable[..., Any]:
        self._before_request.append(func)
        return func

    def errorhandler(self, _code: int) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return decorator
