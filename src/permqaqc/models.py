from enum import Enum


class Severity(Enum):
    OPTIONAL = 'optional'
    MINOR = 'minor'
    CRITICAL = 'critical'


class FieldData:
    def __init__(self):
        self.data: list[tuple[str, Severity]] = []

    def add(self,
            description: str,
            severity: Severity=Severity.CRITICAL
           ) -> None:
        self.data.append((description, severity))

    def clear(self) -> None:
        self.data = []

    def get(self,
            severity: Severity | None=None
           ) -> list[tuple[str, Severity]]:
        data: list[tuple[str, Severity]] = []
        for entry in data:
            if severity is not None and entry[1] != severity:
                continue

            data.append(entry)
        return data
