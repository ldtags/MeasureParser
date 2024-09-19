from enum import Enum


class Severity(Enum):
    OPTIONAL = 'optional'
    MINOR = 'minor'
    CRITICAL = 'critical'


class DataEntry:
    def __init__(self,
                 description: str,
                 severity: Severity=Severity.CRITICAL,
                 y: int | None=None):
        self.description = description
        self.severity = severity
        self.y = y

    def __str__(self) -> str:
        rep = f'{self.severity.name}'
        if self.y is not None:
            rep += f' ({self.y + 2})'
        rep += f': {self.description}'
        return rep


class FieldData:
    def __init__(self, columns: list[str]):
        self.data: dict[str, list[DataEntry]] = {}
        for column in columns:
            self.data[column] = []

    def __getitem__(self, column: str) -> list[DataEntry]:
        return self.data[column]

    def __str__(self) -> str:
        rep = ''
        for key, entries in self.data.items():
            rep += f'{key}:\n'
            for entry in entries:
                rep += f'\t{entry}\n'
            if entries == []:
                rep += '\tNo issues\n'
            rep += '\n'
        return rep

    def clear(self) -> None:
        self.data.clear()

    def add(self,
            column: str,
            description: str,
            severity: Severity=Severity.CRITICAL,
            y: int | None=None
           ) -> None:
        self.data[column].append(
            DataEntry(
                description=description,
                severity=severity,
                y=y
            )
        )

    def get(self,
            column: str | None=None,
            severity: Severity | None=None,
            y: int | None=None
           ) -> list[DataEntry]:
        if column is not None:
            entries = self.data[column]
        else:
            entries = [item for row in self.data.values() for item in row]

        return list(
            filter(
                lambda entry: (
                    (severity is None or entry.severity == severity)
                        and (y is None or entry.y == y)
                ),
                entries
            )
        )
