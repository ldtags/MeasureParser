import re
import time
import logging
import requests
import http.client as httpc
from typing import TypeVar, Callable, overload

from src.etrm import utils, sanitizers, lookups
from src.etrm.models import (
    MeasuresResponse,
    MeasureVersionsResponse,
    Measure,
    Reference,
    SharedLookupRef,
    SharedValueTable,
    PermutationsTable
)
from src.etrm.exceptions import (
    ETRMError,
    ETRMResponseError,
    ETRMRequestError,
    ETRMConnectionError
)


logger = logging.getLogger(__name__)


PROD_API = 'https://www.caetrm.com/api/v1'
STAGE_API = 'https://stage.caetrm.com/api/v1'


_T = TypeVar('_T')
_DEC_TYPE = Callable[..., _T | None]
def etrm_cache_request(func: _DEC_TYPE) -> _DEC_TYPE:
    """Decorator for eTRM cache request methods.

    Adds additional functionality that should be consistent with
    every eTRM cache request method.    
    """

    def wrapper(*args, **kwargs) -> _T | None:
        value = func(*args, **kwargs)
        if value is not None:
            logger.info('Cache HIT')
        else:
            logger.info('Cache MISS')
        return value
    return wrapper


class ETRMCache:
    """Cache for eTRM API response data

    Used to decrease eTRM API connection layer latency on repeat calls
    """

    def __init__(self):
        self.id_cache: list[str] = []
        self.__id_count: int = -1
        self.uc_id_caches: dict[str, list[str]] = {}
        self.__uc_id_counts: dict[str, int] = {}
        self.version_cache: dict[str, list[str]] = {}
        self.measure_cache: dict[str, Measure] = {}
        self.references: dict[str, Reference] = {}
        self.shared_value_tables: dict[str, SharedValueTable] = {}

    @etrm_cache_request
    def get_ids(self,
                offset: int,
                limit: int,
                use_category: str | None=None
               ) -> tuple[list[str], int] | None:
        if use_category != None:
            try:
                id_cache = self.uc_id_caches[use_category]
                count = self.__uc_id_counts[use_category]
            except KeyError:
                return None
        else:
            id_cache = self.id_cache
            count = self.__id_count

        try:
            cached_ids = id_cache[offset:offset + limit]
            if len(cached_ids) == limit and all(cached_ids):
                return (cached_ids, count)
        except IndexError:
            return None
        return None

    def add_ids(self,
                measure_ids: list[str],
                offset: int,
                limit: int,
                count: int,
                use_category: str | None=None):
        if use_category != None:
            try:
                id_cache = self.uc_id_caches[use_category]
            except KeyError:
                self.uc_id_caches[use_category] = []
                id_cache = self.uc_id_caches[use_category]
            self.__uc_id_counts[use_category] = count
        else:
            id_cache = self.id_cache
            self.__id_count = count

        cache_len = len(id_cache)
        if offset == cache_len:
            id_cache.extend(measure_ids)
        elif offset > cache_len:
            id_cache.extend([''] * (offset - cache_len))
            id_cache.extend(measure_ids)
        elif offset + limit > cache_len:
            new_ids = measure_ids[cache_len - offset:limit]
            for i in range(offset, cache_len):
                if id_cache[i] == '':
                    id_cache[i] = measure_ids[i - offset]
            id_cache.extend(new_ids)

    @etrm_cache_request
    def get_versions(self, measure_id: str) -> list[str] | None:
        return self.version_cache.get(measure_id, None)

    def add_versions(self, measure_id: str, versions: list[str]):
        self.version_cache[measure_id] = versions

    @etrm_cache_request
    def get_measure(self, version_id: str) -> Measure | None:
        return self.measure_cache.get(version_id, None)

    def add_measure(self, measure: Measure):
        self.measure_cache[measure.version_id] = measure

    @etrm_cache_request
    def get_reference(self, ref_id: str) -> Reference | None:
        return self.references.get(ref_id, None)

    def add_reference(self, ref_id: str, reference: Reference):
        self.references[ref_id] = reference

    @etrm_cache_request
    def get_shared_value_table(self,
                               table_name: str,
                               version: str
                              ) -> SharedValueTable | None:
        return self.shared_value_tables.get(f'{table_name}-{version}', None)

    def add_shared_value_table(self,
                               table_name: str,
                               version: str,
                               value_table: SharedValueTable):
        self.shared_value_tables[f'{table_name}-{version}'] = value_table


class ETRMConnection:
    """eTRM API connection layer"""

    def __init__(self, auth_token: str, stage: bool=False):
        self.auth_token = sanitizers.sanitize_api_key(auth_token)
        self.api = STAGE_API if stage else PROD_API
        self.headers = {
            'Authorization': auth_token
        }
        self.cache = ETRMCache()

    def extract_id(self, url: str) -> str | None:
        URL_RE = re.compile(f'{self.api}/measures/([a-zA-Z0-9]+)/')
        re_match = re.search(URL_RE, url)
        if len(re_match.groups()) != 1:
            return None

        id_group = re_match.group(1)
        if not isinstance(id_group, str):
            return None

        return id_group

    def get(self,
            endpoint: str,
            headers: dict[str, str] | None=None,
            params: dict[str, str] | None=None,
            stream: bool=True,
            **kwargs
           ) -> requests.Response:
        _endpoint = endpoint.replace(self.api, '')
        if not _endpoint.startswith('/'):
            _endpoint = '/' + _endpoint

        if not _endpoint.endswith('/'):
            _endpoint += '/'

        req_headers: dict[str, str] = {**self.headers}
        if headers != None:
            req_headers |= headers

        _url = f'{self.api}{_endpoint}'
        logger.info(f'Making request to {_url}')
        for i in range(4):
            try:
                response = requests.get(_url,
                                        params=params,
                                        headers=req_headers,
                                        stream=stream,
                                        **kwargs)
                logger.info(f'Request complete: {response.status_code}')
                break
            except httpc.IncompleteRead:
                logger.info('Request failed')
                if i == 3:
                    raise
                time.sleep(i)
                logger.info('Trying again...')
            except requests.exceptions.ConnectionError as err:
                raise ConnectionError() from err

        match response.status_code:
            case 200:
                return response
            case status:
                msg = response.content.decode()
                raise ETRMResponseError(message=msg, status=status)

    def get_measure(self, measure_id: str) -> Measure:
        logger.info(f'Retrieving measure: {measure_id}')

        sanitized_id = sanitizers.sanitize_measure_id(measure_id)
        cached_measure = self.cache.get_measure(sanitized_id)
        if cached_measure != None:
            return cached_measure

        statewide_id, version_id = sanitized_id.split('-', 1)
        response = self.get(f'/measures/{statewide_id}/{version_id}')
        measure = Measure(response.json(), source='etrm')
        self.cache.add_measure(measure)
        return measure

    def get_measure_ids(self,
                        offset: int=0,
                        limit: int=25,
                        use_category: str | None=None
                       ) -> tuple[list[str], int]:
        logger.info(f'Retrieving measure IDs')

        if offset < 0:
            raise ETRMRequestError(
                f'Invalid offset: {offset} must be a non-negative integer'
            )

        if limit < 0:
            raise ETRMRequestError(
                f'Invalid limit: {limit} must be a non-negative integer'
            )

        if use_category is not None:
            try:
                lookups.USE_CATEGORIES[use_category]
            except KeyError:
                keys = lookups.USE_CATEGORIES.keys()
                raise ETRMRequestError(
                    f'Invalid use category: {use_category} must be one of'
                    f' [{",".join(keys)}]'
                )

        cache_response = self.cache.get_ids(offset, limit, use_category)
        if cache_response is not None:
            return cache_response

        params = {
            'offset': str(offset),
            'limit': str(limit)
        }

        if use_category is not None:
            params['use_category'] = use_category

        response = self.get('/measures', params=params)
        response_body = MeasuresResponse(response.json())
        statewide_ids: list[str] = []
        for result in response_body.results:
            statewide_id = self.extract_id(result.url)
            sanitized_id = sanitizers.sanitize_statewide_id(statewide_id)
            statewide_ids.append(sanitized_id)

        count = response_body.count
        self.cache.add_ids(
            measure_ids=statewide_ids,
            offset=offset,
            limit=limit,
            count=count,
            use_category=use_category
        )
        return (statewide_ids, count)

    def get_all_measure_ids(self, use_category: str | None=None) -> list[str]:
        logger.info('Retrieving all measure ids')

        _, count = self.get_measure_ids(use_category=use_category)
        measure_ids, _ = self.get_measure_ids(
            offset=0,
            limit=count,
            use_category=use_category
        )
        return measure_ids

    def get_measure_versions(self, statewide_id: str) -> list[str]:
        logger.info(f'Retrieving versions of measure {statewide_id}')

        statewide_id = sanitizers.sanitize_statewide_id(statewide_id)
        cached_versions = self.cache.get_versions(statewide_id)
        if cached_versions is not None:
            return list(reversed(cached_versions))

        response = self.get(f'/measures/{statewide_id}/')
        response_body = MeasureVersionsResponse(response.json())
        measure_versions: list[str] = []
        for version_info in response_body.versions:
            sanitized_id = sanitizers.sanitize_measure_id(version_info.version)
            measure_versions.append(sanitized_id)

        self.cache.add_versions(statewide_id, measure_versions)
        return list(reversed(measure_versions))

    def get_reference(self, ref_id: str) -> Reference:
        logger.info(f'Retrieving reference {ref_id}')

        sanitized_ref = sanitizers.sanitize_reference(ref_id)
        cached_ref = self.cache.get_reference(sanitized_ref)
        if cached_ref is not None:
            return cached_ref

        response = self.get(f'/references/{sanitized_ref}/')
        reference = Reference(response.json())
        self.cache.add_reference(sanitized_ref, reference)
        return reference

    @overload
    def get_shared_value_table(self,
                               lookup_ref: SharedLookupRef
                              ) -> SharedValueTable:
        ...

    @overload
    def get_shared_value_table(self,
                               table_name: str,
                               version: str | int
                              ) -> SharedValueTable:
        ...

    def get_shared_value_table(self, *args) -> SharedValueTable:
        def parse_args() -> tuple[str, str, str]:
            if len(args) == 1:
                if not isinstance(args[0], SharedLookupRef):
                    raise ETRMRequestError(f'unknown overload args: {args}')
                table_name = args[0].name
                version = args[0].version
                url = args[0].url
            elif len(args) == 2:
                if not (isinstance(args[0], str)
                            and isinstance(args[1], str | int)):
                    raise ETRMRequestError(f'unknown overload args: {args}')
                table_name = args[0]
                version = f'{args[1]:03d}'
                url = f'/shared-value-tables/{table_name}/{version}'
            else:
                raise ETRMRequestError('missing required parameters')
            return table_name, version, url

        table_name, version, url = parse_args()

        logger.info(f'Retrieving shared value table {table_name}')

        sanitized_name = sanitizers.sanitize_table_name(table_name)
        cached_table = self.cache.get_shared_value_table(
            sanitized_name,
            version
        )
        if cached_table is not None:
            return cached_table

        response = self.get(url)
        value_table = SharedValueTable(response.json())
        self.cache.add_shared_value_table(sanitized_name, version, value_table)
        return value_table

    @overload
    def get_permutations(self, measure: Measure) -> PermutationsTable:
        ...

    @overload
    def get_permutations(self, measure_id: str) -> PermutationsTable:
        ...

    @overload
    def get_permutations(self,
                         statewide_id: str,
                         version: str
                        ) -> PermutationsTable:
        ...

    def get_permutations(self, *args) -> PermutationsTable:
        def parse_args() -> tuple[str, str]:
            arg_len = len(args)
            if arg_len == 1:
                if isinstance(args[0], str):
                    measure_id = args[0]
                elif isinstance(args[0], Measure):
                    measure_id = args[0].version_id
                else:
                    raise ETRMError(
                        f'Unsupported single arg type: {type(args[0])}'
                    )
                split_id = measure_id.split('-', 1)
                if len(split_id) != 2:
                    raise ETRMConnectionError(
                        f'Invalid measure id: {measure_id}'
                    )
                statewide_id = split_id[0]
                version = split_id[1]
            if arg_len == 2:
                statewide_id = args[0]
                if not isinstance(statewide_id, str):
                    raise ETRMRequestError(
                        'Invalid arg type: statewide_id must be a str object'
                    )
                version = args[1]
                if not isinstance(version, str):
                    raise ETRMRequestError(
                        'Invalid arg type: version_id must be a str object'
                    )
            else:
                raise ETRMRequestError(
                    f'Expected 1 or 2 args, but got {arg_len}'
                )
            return (statewide_id, version)

        statewide_id, version = parse_args()

        logger.info(
            f'Retrieving permutations of measure {statewide_id}-{version}'
        )

        statewide_id = sanitizers.sanitize_statewide_id(statewide_id)
        url = f'/measures/{statewide_id}/{version}/permutations'
        permutations_table: PermutationsTable | None = None
        while url is not None:
            response = self.get(url, stream=False)
            table = PermutationsTable(response.json())
            if table.links.next is not None:
                prev_url = utils.parse_url(url)
                prev_offset = prev_url.query.get('offset', '')
                parsed_url = utils.parse_url(table.links.next)
                url_offset = parsed_url.query.get('offset', '')
                if prev_offset == url_offset:
                    break
            if permutations_table is None:
                permutations_table = table
            else:
                permutations_table.join(table)
            url = table.links.next
        return permutations_table
