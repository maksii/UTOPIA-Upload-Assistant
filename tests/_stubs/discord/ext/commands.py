class Bot:
    def __init__(self, *args, **kwargs) -> None:
        _ = (args, kwargs)

    async def close(self) -> None:
        return None


class CommandError(Exception):
    pass
