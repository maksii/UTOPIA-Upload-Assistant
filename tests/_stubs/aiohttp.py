class ClientSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def get(self, *_args, **_kwargs):
        return _FakeResponse()

    async def post(self, *_args, **_kwargs):
        return _FakeResponse()


class _FakeResponse:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def json(self):
        return {}

    async def text(self):
        return ""

    def raise_for_status(self) -> None:
        return None


class ClientTimeout:
    def __init__(self, *args, **kwargs) -> None:
        _ = (args, kwargs)
