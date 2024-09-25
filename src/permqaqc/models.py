import re
import os
import json
from enum import Enum

import src.etrm.constants as cnst


class Severity(Enum):
    OPTIONAL = 'optional'
    SEMI_MINOR = 'semi_minor'
    MINOR = 'minor'
    SEMI_CRITICAL = 'semi_critical'
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

    def to_json(self, file_path: str, overwrite: bool=True) -> str:
        if file_path.rsplit('.')[-1] != 'json':
            raise RuntimeError('File path must specify a JSON file')
            
        if os.path.exists(file_path) and not overwrite:
            raise RuntimeError(f'Cannot overwrite {file_path}')

        json_dict: dict[str, dict[str, list[int]]] = {}
        for column, entries in self.data.items():
            column_dict: dict[str, list[int]] = {}
            for entry in entries:
                y = entry.y + 2 if entry.y is not None else 0
                try:
                    column_dict[entry.severity.name].append(y)
                except KeyError:
                    column_dict[entry.severity.name] = [y]
            json_dict[column] = column_dict

        with open(file_path, 'w+') as fp:
            json.dump(json_dict, fp)

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

    def get_error_map(self, column: str) -> dict[Severity, list[int]]:
        try:
            if column == cnst.ETP_FLAG:
                key = cnst.ETP_FLAG
                for col_key in self.data.keys():
                    if re.fullmatch(r'^ETP Flag.*$', col_key):
                        key = col_key
            else:
                key = column
            entries = self.data[key]
        except KeyError:
            raise RuntimeError(f'No column named {column} exists')

        error_map = {
            Severity.MINOR: [],
            Severity.OPTIONAL: [],
            Severity.CRITICAL: []
        }

        for entry in entries:
            error_map[entry.severity].append(entry.y)

        return error_map

    def get(self,
            column: str | None=None,
            severity: Severity | None=None,
            y: int | list[int] | None=None
           ) -> list[DataEntry]:
        if column is not None:
            entries = self.data[column]
        else:
            entries = [item for row in self.data.values() for item in row]

        return list(
            filter(
                lambda entry: (
                    (severity is None or entry.severity == severity)
                        and (
                            (
                                entry.y == y
                            ) if isinstance(y, int)
                            else (
                                entry.y in y
                            ) if isinstance(y, list)
                            else True
                        )
                ),
                entries
            )
        )
