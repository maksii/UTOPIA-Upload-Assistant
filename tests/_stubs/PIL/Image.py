class Image:
    def __init__(self, *args, **kwargs) -> None:
        _ = (args, kwargs)

    def save(self, *_args, **_kwargs) -> None:
        return None


def open(*_args, **_kwargs):
    return Image()
