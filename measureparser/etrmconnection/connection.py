from contextlib import contextmanager
from typing import Generator

import psycopg as pg
from psycopg.rows import dict_row

from .models import (
    Measure
)


def add_criteria(query: str, criteria: str) -> str:
    query = query.strip()
    if 'WHERE' in query:
        query += ' AND '
    else:
        query += ' WHERE '
    query += criteria.strip()
    return query


class ETRMConnection:
    def __init__(self, filename: str, section: str):
        from . import config
        self.connection: pg.Connection = pg.connect(**config(filename, section))

    def commit(self) -> None:
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def cursor(self, *args, **kwargs) -> pg.Cursor:
        return self.connection.cursor(*args, **kwargs)

    def execute(
        self,
        query: str,
        params: str | None=None,
        *,
        prepare: bool | None=None,
        binary: bool=False
    ) -> pg.Cursor:
        '''Execute a query and return a cursor to read its results.'''
        return self.connection.execute(query, params, prepare=prepare, binary=binary)

    def get_measure(
        self,
        id: str | None=None,
        version_id: str | None=None,
        name: str | None=None
    ) -> Measure | None:
        '''Returns a measure associated with the provided constraints.
        
        In the case that multiple measures match the provided constraints,
        only the first is returned.
        '''

        query = 'SELECT * FROM measures'

        if id != None:
            query = add_criteria(query, f'MeasureID = {id}')

        if version_id != None:
            query = add_criteria(query, f'\"MeasureVersionID\" = \'{version_id}\'')

        if name != None:
            query = add_criteria(query, f'MeasureName = {name}')

        query += ' ORDER BY pk ASC'

        with self.cursor(row_factory=dict_row) as cursor:
            response: dict | None = cursor.execute(query).fetchone()
            if response == None:
                return None
            return Measure(response)

    def get_measures(self, limit: int=-1) -> list[Measure]:
        query = 'SELECT * FROM measures ORDER BY pk ASC'
        if limit > -1:
            query += f' LIMIT {limit}'
        with self.cursor(row_factory=dict_row) as cursor:
            response: list[dict] = cursor.execute(query).fetchall()
            return list(map(lambda row: Measure(row), response))


@contextmanager
def etrm_connection(
    filename='database.ini',
    section='postgresql'
) -> Generator[ETRMConnection, None, None]:
    '''Establishes a connection to the eTRM PostgreSQL database.
    
    Typical usage:
        `with etrm_connection() as conn:`
            `conn.<pre-built query method>()`\n
            `conn.execute(<query>)`\n
            `conn.execute(<query>, <params>)`
    '''

    try:
        connection = ETRMConnection(filename, section)
    except Exception | pg.DatabaseError as err:
        raise err

    try:
        yield connection
    finally:
        connection.commit()
        connection.close()
