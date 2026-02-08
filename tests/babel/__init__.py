class Locale:
    @classmethod
    def parse(cls, _value: str):
        return cls()

    def get_display_name(self, _locale: str) -> str:
        return ""
