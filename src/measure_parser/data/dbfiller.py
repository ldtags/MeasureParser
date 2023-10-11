import sqlite3
from sys import maxsize
from random import randint
from src.measure_parser.data.parameters import ALL_PARAMS
from src.measure_parser.data.permutations import ALL_PERMUTATIONS
from src.measure_parser.data.valuetables import (
    ALL_SHARED_TABLES,
    ALL_VALUE_TABLES
)
from src.measure_parser.data.characterizations import (
    ALL_CHARACTERIZATIONS
)

connection = sqlite3.connect('database.db')
cursor = connection.cursor()

def main():
    insert_parameters()
    insert_tables()
    insert_permutations()
    insert_characterizations()
    connection.commit()


def insert_parameters():
    data: list[tuple(str, str, str)] = []
    for i, key in enumerate(ALL_PARAMS.keys()):
        data.append((key, i, ALL_PARAMS[key]))

    if len(data) > 0:
        cursor.executemany(
            'INSERT INTO parameters (api_name, ord, criteria)'
                + 'VALUES (?, ?, ?)',
            data)


def insert_tables():
    data: list[tuple(str, str, str, str)] = []
    for i, key in enumerate(ALL_SHARED_TABLES.keys()):
        data.append((key, i, ALL_SHARED_TABLES[key], 1))

    buf: int = len(ALL_SHARED_TABLES)
    for i, key in enumerate(ALL_VALUE_TABLES.keys()):
        data.append((key, i + buf, ALL_VALUE_TABLES[key], 0))

    if len(data) > 0:
        cursor.executemany(
            'INSERT INTO tables (api_name, ord, criteria, shared)'
                + 'values (?, ?, ?, ?)',
            data)


def insert_permutations():
    perm_data: list[tuple[str, str, str, int]] = []
    permutations: list[tuple[str, dict]] = list(ALL_PERMUTATIONS.items())
    for permutation, perm_obj in permutations:
        verbose_name: str = perm_obj.get('verbose', None)
        if verbose_name == None:
            continue

        valid_name: str = perm_obj.get('validity', 'NULL')
        id: int = randint(1, maxsize)
        perm_data.append((permutation, verbose_name, valid_name, id))

        cond_data: list[tuple[str, int, str]] = []
        cond_names: list[tuple[str, str]] \
            = perm_obj.get('conditional', [])
        for name, criteria in cond_names:
            cond_data.append((name, id, criteria))
        if len(cond_data) > 0:
            cursor.executemany(
                'INSERT INTO conditional_names (name, id, criteria)'
                    + 'values (?, ?, ?)',
                cond_data)

    if len(perm_data) > 0:
        cursor.executemany(
        'INSERT INTO permutations'
            + '(reporting_name, verbose_name, valid_name, id)'
            + 'values (?, ?, ?, ?)',
        perm_data)
        pass
    else:
        print('oops')


def insert_characterizations():
    cursor.executemany(
        'INSERT INTO characterizations'
            + '(name) values (?)',
        list(map(lambda char: (char,), ALL_CHARACTERIZATIONS)))


if __name__ == '__main__':
    main()