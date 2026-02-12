class _Scraper:
    def get(self, *_args, **_kwargs):
        return _FakeResponse()

    def post(self, *_args, **_kwargs):
        return _FakeResponse()


class _FakeResponse:
    def __init__(self) -> None:
        self.status_code = 200
        self.text = ""


def create_scraper(*_args, **_kwargs):
    return _Scraper()
