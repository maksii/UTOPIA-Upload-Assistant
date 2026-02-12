class LoginFailure(Exception):
    pass


class ClientException(Exception):
    pass


class Intents:
    @classmethod
    def default(cls):
        return cls()


class Client:
    def __init__(self, *args, **kwargs) -> None:
        _ = (args, kwargs)

    async def close(self) -> None:
        return None


class Message:
    pass


class AppInfo:
    pass


class _ABC:
    class Messageable:
        pass


abc = _ABC()

__version__ = "0.0"
