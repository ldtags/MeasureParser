from __future__ import annotations
import os
import csv
import math
import pandas as pd
import datetime as dt
import statistics as st
import unicodedata as ud
from enum import Enum
from typing import Literal, Any, overload
from pandas import DataFrame, Series

from src.etrm import utils
from src.utils import getc, JSONObject
from src.exceptions import RequiredContentError
from src.etrm.exceptions import (
    ETRMResponseError,
    ETRMConnectionError,
    ETRMError
)


ETRM_URL = 'https://www.caetrm.com'


class PermutationsTable:
    reporting_baselines = {
        'PEDR_1': 'UnitkW1stBaseline',
        'PEDR_2': 'UnitkW2ndBaseline',
        'ES_1': 'UnitkWh1stBaseline',
        'ES_2': 'UnitkWh2ndBaseline',
        'GS_1': 'UnitTherm1stBaseline',
        'GS_2': 'UnitTherm2ndBaseline',
        'MTC_1': 'UnitMeaCost1stBaseline',
        'MTC_2': 'UnitMeaCost2ndBaseline'
    }

    verbose_baselines = {
        'PEDR_1': 'First Baseline - Peak Electric Demand Reduction',
        'PEDR_2': 'Second Baseline - Peak Electric Demand Reduction',
        'ES_1': 'First Baseline - Electric Savings',
        'ES_2': 'Second Baseline - Electric Savings',
        'GS_1': 'First Baseline - Gas Savings',
        'GS_2': 'Second Baseline - Gas Savings',
        'MTC_1': 'Measure Total Cost 1st Baseline',
        'MTC_2': 'Measure Total Cost 2nd Baseline'
    }

    @overload
    def __init__(self, csv_path: str):
        ...

    @overload
    def __init__(self, res_json: dict[str, Any]):
        ...

    def __init__(self, _input: dict[str, Any] | str):
        if isinstance(_input, str):
            self.__csv_init(_input)
        elif isinstance(_input, dict):
            self.__json_init(_input)
        else:
            raise ETRMConnectionError(
                'Invalid input type: cannot build permutations table from'
                f' input of type {type(_input)}'
            )

        self.data = DataFrame(
            data=self.results,
            columns=self.headers
        )

        columns = [list(col) for col in zip(*self.results)]
        data: dict[str, list[str | float | None]] = {}
        for x, header in enumerate(self.headers):
            data[header] = columns[x]
        self.data = DataFrame(data)

    def __getitem__(self, header: str) -> Series:
        try:
            return self.data[header]
        except KeyError as err:
            raise ETRMConnectionError(
                f'Permutation column {header} not found'
            ) from err

    def __eq__(self, other) -> bool:
        if not isinstance(other, PermutationsTable):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    class _Links:
        def __init__(self, links: dict[str, str | None] | None=None):
            if links is None:
                links = {}

            self.next = links.get('next', None)
            self.previous = links.get('previous', None)

    def __csv_init(self, csv_path: str) -> None:
        if not os.path.exists(csv_path):
            raise ETRMConnectionError(
                f'Invalid file path: {csv_path} does not exist'
            )

        if not os.path.isfile(csv_path):
            raise ETRMConnectionError(
                f'Invalid file path: {csv_path} is a folder, not a csv file'
            )

        _, ext = os.path.splitext(csv_path)
        if not ext == 'csv':
            raise ETRMConnectionError(
                f'Invalid file path: {csv_path} is a {ext} file, not a csv'
                ' file'
            )

        self.headers: list[str] = []
        self.results: list[list[str]] = []
        with open(csv_path) as fp:
            csv_reader = csv.reader(fp)
            self.headers.extend(next(csv_reader))
            for line in csv_reader:
                self.results.append(line)
        self.count = len(self.results)
        self.links = self._Links()
        self.baselines = self.verbose_baselines

    def __json_init(self, _json: dict[str, Any]) -> None:
        self.json = _json
        try:
            self.count = getc(_json, 'count', int)
            self.links = getc(_json, 'links', self._Links)
            self.headers = getc(_json, 'headers', list[str])
            self.results = getc(
                _json,
                'results',
                list[list[str | float | None]]
            )
        except IndexError:
            raise ETRMResponseError()
        self.baselines = self.reporting_baselines

    def join(self, table: PermutationsTable) -> None:
        if table.count == 0:
            return

        if self.headers != table.headers:
            raise ETRMResponseError()

        self.results.extend(table.results)

    def get_baseline_avg(self,
                         baseline: str,
                         *mat_labels: str,
                         negate: bool=False
                        ) -> float | None:
        column = self.baselines.get(baseline)
        if column is None:
            raise ETRMError(f'Unknown baseline: {baseline}')

        if mat_labels != ():
            if negate:
                df = self.data.loc[
                    ~self.data['MeasAppType'].isin([*mat_labels])
                ]
            else:
                df = self.data.loc[
                    self.data['MeasAppType'].isin([*mat_labels])
                ]
        else:
            df = self.data

        if df.empty:
            return None

        avg = df[column].mean()
        if math.isnan(avg):
            return 0

        return avg

    def get_standard_costs(self) -> tuple[float, float, float]:
        """Returns a three-tuple of the (Peak Electric Demand Reduction,
        Electric Savings, Gas Savings) standard costs.

        The standard costs are either:
            First Baseline  (NC or NR)
            Second Baseline (AR)
            None            (other)
        """

        pedr_vals: list[float] = []
        pedr = self.get_baseline_avg('PEDR_1', 'NC', 'NR')
        if pedr is not None:
            pedr_vals.append(pedr)

        pedr = self.get_baseline_avg('PEDR_2', 'AR')
        if pedr is not None:
            pedr_vals.append(pedr)

        if len(pedr_vals) == 0:
            pedr = 0.0
        else:
            pedr = st.fmean(pedr_vals)

        es_vals: list[float] = []
        es = self.get_baseline_avg('ES_1', 'NC', 'NR')
        if es is not None:
            es_vals.append(es)

        es = self.get_baseline_avg('ES_2', 'AR')
        if es is not None:
            es_vals.append(es)

        if len(es_vals) == 0:
            es = 0.0
        else:
            es = st.fmean(es_vals)

        gs_vals: list[float] = []
        gs = self.get_baseline_avg('GS_1', 'NC', 'NR')
        if gs is not None:
            gs_vals.append(gs)

        gs = self.get_baseline_avg('GS_2', 'AR')
        if gs is not None:
            gs_vals.append(gs)

        if len(gs_vals) == 0:
            gs = 0.0
        else:
            gs = st.fmean(gs_vals)

        return (pedr, es, gs)


    def get_pre_existing_costs(self) -> tuple[float, float, float]:
        """Returns a three-tuple of the (Peak Electric Demand Reduction,
        Electric Savings, Gas Savings) pre-existing costs.

        The pre-existing costs are either:
            None            (NC or NR)
            First Baseline  (other)
        """

        pedr = self.get_baseline_avg('PEDR_1', 'NC', 'NR', negate=True) or 0.0
        es = self.get_baseline_avg('ES_1', 'NC', 'NR', negate=True) or 0.0
        gs = self.get_baseline_avg('GS_1', 'NC', 'NR', negate=True) or 0.0
        return (pedr, es, gs)

    def get_incremental_cost(self) -> float:
        """Returns the incremental cost of the measure.
        
        The incremental cost is either:
            Measure Total Cost 1st Baseline (NC or NR)
            Measure Total Cost 2nd Baseline (AR)
            None                            (other)
        """

        mtc_1 = self.get_baseline_avg('MTC_1', 'NC', 'NR')
        mtc_2 = self.get_baseline_avg('MTC_2', 'AR')

        if mtc_1 is None and mtc_2 is None:
            return 0.0

        if mtc_1 is None:
            return mtc_2

        if mtc_2 is None:
            return mtc_1

        return st.fmean([mtc_1, mtc_2])

    def get_total_cost(self) -> float:
        """Returns the total cost of the measure.
        
        The total cost is either:
            None                            (NC or NR)
            Measure Total Cost 1st Baseline (other)
        """

        return self.get_baseline_avg('MTC_1', 'NC', 'NR', negate=True) or 0.0


class MeasureInfo:
    def __init__(self, res_json: dict[str, Any]):
        try:
            self.name = getc(res_json, 'name', str)
            self.url = getc(res_json, 'url', str)
        except IndexError:
            raise ETRMResponseError()

    def __eq__(self, other) -> bool:
        if not isinstance(other, MeasureInfo):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


class MeasuresResponse:
    def __init__(self, res_json: dict[str, Any]):
        try:
            self.count = getc(res_json, 'count', int)
            self.next = getc(res_json, 'next', str)
            self.previous = getc(res_json, 'previous', str)
            self.results = getc(res_json, 'results', list[MeasureInfo])
        except IndexError:
            raise ETRMResponseError()

    def __eq__(self, other) -> bool:
        if not isinstance(other, MeasuresResponse):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


class MeasureVersionInfo:
    def __init__(self, res_json: dict[str, Any]):
        try:
            self.version = getc(res_json, 'version', str)
            self.status = getc(res_json, 'status', str)
            self.change_description = getc(res_json, 'change_description', str)
            self.owner = getc(res_json, 'owner', str)
            self.is_published = getc(res_json, 'is_published', str)
            self.date_committed = getc(res_json, 'date_committed', str)
            self.url = getc(res_json, 'url', str)
        except IndexError:
            raise ETRMResponseError('malformed measure version info')

    def __eq__(self, other) -> bool:
        if not isinstance(other, MeasureVersionInfo):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


class MeasureVersionsResponse:
    def __init__(self, res_json: dict[str, Any]):
        try:
            self.statewide_measure_id = getc(res_json,
                                             'statewide_measure_id',
                                             str)
            self.use_category = getc(res_json, 'use_category', str)
            self.versions = getc(res_json,
                                 'versions',
                                 list[MeasureVersionInfo])
        except IndexError:
            raise ETRMResponseError('malformed measure versions response')

    def __eq__(self, other) -> bool:
        if not isinstance(other, MeasureVersionsResponse):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


class Reference:
    def __init__(self, res_json: dict[str, Any]):
        self.json = res_json
        try:
            self.reference_code = getc(res_json, 'reference_code', str)
            self.reference_citation = getc(res_json, 'reference_citation', str)
            self.source_reference = getc(
                res_json,
                'source_reference',
                str | None
            )
            self.source_url = getc(res_json, 'source_url', str | None)
            self.reference_location = getc(
                res_json,
                'reference_location',
                str | None
            )
            self.reference_type = getc(res_json, 'reference_type', str)
            self.publication_title = getc(
                res_json,
                'publication_title',
                str | None
            )
            self.lead_author = getc(res_json, 'lead_author', str | None)
            self.lead_author_org = getc(
                res_json,
                'lead_author_org',
                str | None
            )
            self.sponsor_org = getc(res_json, 'sponsor_org', str | None)
            self.source_document = getc(res_json, 'source_document', str)
        except IndexError:
            raise ETRMResponseError()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Reference):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


class Permutation:
    """Class representation of a measure permutation."""

    def __init__(self,
                 reporting_name: str,
                 mapped_name: str | None,
                 derivation: str = 'mapped'):
        self.reporting_name = reporting_name
        self.mapped_name = mapped_name
        self.derivation = derivation


class Characterization:
    """Class representation of a characterization."""

    def __init__(self, name: str, content: str):
        self.name = name
        self.content = content


class Version:
    def __init__(self, res_json: dict[str, Any]):
        try:
            version_string = getc(res_json, 'version_string', str)
        except IndexError:
            raise ETRMResponseError()
        try:
            self.table_name, self.version = version_string.split('-', 1)
        except ValueError:
            raise ETRMResponseError(f'{version_string} is not'
                                    ' properly formatted')

    def __eq__(self, other) -> bool:
        if not isinstance(other, Version):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


class SharedDeterminantRef:
    def __init__(self, res_json: dict[str, Any]):
        try:
            self.order = getc(res_json, 'order', int)
            _version = getc(res_json, 'version', Version)
            self.name = _version.table_name
            self.version = _version.version
            self.active_labels = getc(res_json, 'active_labels', list[str])
            self.url = getc(res_json, 'url', str)
        except IndexError:
            raise ETRMResponseError()

    def __eq__(self, other) -> bool:
        if not isinstance(other, SharedDeterminantRef):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


class Label:
    def __init__(self, res_json: dict[str, Any]):
        try:
            self.name = getc(res_json, 'name', str)
            self.api_name = getc(res_json, 'api_name', str)
            self.active = getc(res_json, 'active', str)
            self.description = getc(res_json, 'description', str)
        except IndexError:
            raise ETRMResponseError()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Label):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


class Determinant:
    def __init__(self, res_json: dict[str, Any]):
        try:
            self.name = getc(res_json, 'name', str)
            self.api_name = getc(res_json, 'api_name', str)
            self.labels = getc(res_json, 'labels', list[Label])
            self.description = getc(res_json, 'description', str)
            self.order = getc(res_json, 'order', int)
            self.reference_refs = getc(res_json, 'reference_refs', list[str])
        except IndexError:
            raise ETRMResponseError()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Determinant):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


class SharedLookupRef:
    def __init__(self, res_json: dict[str, Any]):
        try:
            self.order = getc(res_json, 'order', int)
            _version = getc(res_json, 'version', Version)
            self.name = _version.table_name
            self.version = _version.version
            self.url = getc(res_json, 'url', str)
        except IndexError:
            raise ETRMResponseError()

    def __eq__(self, other) -> bool:
        if not isinstance(other, SharedLookupRef):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


class Column:
    def __init__(self, res_json: dict[str, Any]):
        try:
            self.name = getc(res_json, 'name', str)
            self.api_name = getc(res_json, 'api_name', str)
            self.unit = getc(res_json, 'unit', str)
            try:
                self.reference_refs = getc(res_json,
                                           'reference_refs',
                                           list[str])
            except TypeError:
                self.reference_refs = getc(res_json, 'references', list[str])
        except IndexError:
            raise ETRMResponseError()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Column):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


class ValueTable:
    def __init__(self, res_json: dict[str, Any]):
        try:
            self.name = getc(res_json, 'name', str)
            self.api_name = getc(res_json, 'api_name', str)
            self.type = getc(res_json, 'type', str)
            self.description = getc(res_json, 'description', str)
            self.order = getc(res_json, 'order', int)
            self.determinants = getc(res_json, 'determinants', list[str])
            self.columns = getc(res_json, 'columns', list[Column])
            self.values = getc(res_json, 'values', list[list[str | None]])
            self.reference_refs = getc(res_json, 'reference_refs', list[str])
        except IndexError:
            raise ETRMResponseError()

    def __eq__(self, other) -> bool:
        if not isinstance(other, ValueTable):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def get_column(self, api_name: str) -> Column | None:
        for column in self.columns:
            if column.api_name.lower() == api_name.lower():
                return column
        return None

    def contains_column(self, api_name: str) -> bool:
        for column in self.columns:
            if column.api_name.lower() == api_name.lower():
                return True
        return False


class SharedValueTable:
    def __init__(self, res_json: dict[str, Any]):
        self.json = res_json
        try:
            self.name = getc(res_json, 'name', str)
            self.api_name = getc(res_json, 'api_name', str)
            self.parameters = getc(res_json, 'parameters', list[str])
            self.columns = getc(res_json, 'columns', list[Column])
            self.values = getc(res_json,
                               'values',
                               list[list[str | float | None]])
            self.references = getc(res_json, 'references', list[str])
            self.version = getc(res_json, 'version', str)
            self.status = getc(res_json, 'status', str)
            self.change_description = getc(res_json, 'change_description', str)
            self.owner = getc(res_json, 'owner', str)
            self.is_published = getc(res_json, 'is_published', bool)
            self.committed_date = getc(res_json, 'committed_date', str)
            self.last_updated_date = getc(res_json, 'last_updated_date', str)
            self.type = getc(res_json, 'type', str)
            self.versions_url = getc(res_json, 'versions_url', str)
            self.url = getc(res_json, 'url', str)

            headers = [
                *self.parameters,
                *[col.api_name for col in self.columns]
            ]

            self.data: dict[str, dict[str, list[str | float | None]]] = {}
            for row in self.values:
                eul_id = str(row[0])
                id_map = self.data.get(eul_id, {})
                for i, item in enumerate(row[1:], 1):
                    mapped_list = id_map.get(headers[i], [])
                    mapped_list.append(item)
                    id_map[headers[i]] = mapped_list
                self.data[eul_id] = id_map

        except IndexError:
            raise ETRMResponseError()

    def __eq__(self, other) -> bool:
        if not isinstance(other, SharedValueTable):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


class Calculation:
    def __init__(self, res_json: dict[str, Any]):
        try:
            self.name = getc(res_json, 'name', str)
            self.api_name = getc(res_json, 'api_name', str)
            self.order = getc(res_json, 'order', int)
            self.unit = getc(res_json, 'unit', str)
            self.determinants = getc(res_json, 'determinants', list[str])
            self.values = getc(res_json, 'values', list[list[str]])
            self.reference_refs = getc(res_json, 'reference_refs', list[str])
        except IndexError:
            raise ETRMResponseError()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Calculation):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


class ExclusionTable:
    def __init__(self, res_json: dict[str, Any]):
        try:
            self.name = getc(res_json, 'name', str)
            self.api_name = getc(res_json, 'api_name', str)
            self.order = getc(res_json, 'order', int)
            self.determinants = getc(res_json, 'determinants', list[str])
            self.values = getc(res_json, 'values', list[tuple[str, str, bool]])
            self.reference_refs = getc(res_json, 'reference_refs', list[str])
        except IndexError:
            raise ETRMResponseError()

    def __eq__(self, other) -> bool:
        if not isinstance(other, ExclusionTable):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


class Measure(JSONObject):
    def __init__(self,
                 res_json: dict[str, Any],
                 source: Literal['etrm', 'json'],
                 char_names: list[str],
                 perm_names: list[str] | None=None):
        """Initializes a new eTRM measure object.

        Measures can be generated from two sources:
            1. eTRM measure JSON files
            2. The eTRM API

        If the measure is generated from a JSON file:
            - The measure will contain permutation mappings

        If the measure is generated from an eTRM API response:
            - The measure object will not contain any permutation mappings.
            Instead, permutations must be acquired from another eTRM API call.
        """

        JSONObject.__init__(self, res_json)

        self.source = source
        if source == 'etrm':
            self.__etrm_init()
        elif source == 'json':
            self.__json_init()
        else:
            raise ETRMError(f'Invalid source type: {source}')

        try:
            self.determinants = self.get('determinants', list[Determinant])
            self.shared_determinant_refs = self.get(
                'shared_determinant_refs',
                list[SharedDeterminantRef]
            )
            self.shared_lookup_refs = self.get(
                'shared_lookup_refs',
                list[SharedLookupRef]
            )
            self.value_tables = self.get('value_tables', list[ValueTable])
            self.calculations = self.get('calculations', list[Calculation])
            self.exclusion_tables = self.get(
                'exclusion_tables',
                list[ExclusionTable]
            )
        except IndexError:
            raise ETRMError()

        id_path = '/'.join(self.version_id.split('-'))
        self.link = f'{ETRM_URL}/measure/{id_path}'

        self.characterizations = self.__get_characterizations(char_names)
        self.permutations = self.__get_permutations(perm_names or [])

        self._determinant_map: dict[str, Determinant] = {}
        for determinant in self.determinants:
            self._determinant_map[determinant.api_name.lower()] = determinant
            self._determinant_map[determinant.name.lower()] = determinant

        self._shared_det_ref_map: dict[str, SharedDeterminantRef] = {}
        for ref in self.shared_determinant_refs:
            self._shared_det_ref_map[ref.name.lower()] = ref

        self._shared_lookup_ref_map: dict[str, SharedLookupRef] = {}
        for ref in self.shared_lookup_refs:
            self._shared_lookup_ref_map[ref.name.lower()] = ref

        self._value_table_map: dict[str, ValueTable] = {}
        for table in self.value_tables:
            self._value_table_map[table.api_name.lower()] = table
            self._value_table_map[table.name.lower()] = table

        self._calculation_map: dict[str, Calculation] = {}
        for calculation in self.calculations:
            self._calculation_map[calculation.api_name.lower()] = calculation
            self._calculation_map[calculation.name.lower()] = calculation

        self._exclusion_table_map: dict[str, ExclusionTable] = {}
        for table in self.exclusion_tables:
            self._exclusion_table_map[table.api_name.lower()] = table
            self._exclusion_table_map[table.name.lower()] = table

        self._characterization_map: dict[str, Characterization] = {}
        for characterization in self.characterizations:
            key = characterization.name.lower()
            self._characterization_map[key] = characterization
        del key

        self._permutation_map: dict[str, Permutation] = {}
        for permutation in self.permutations:
            key = permutation.reporting_name.lower()
            self._permutation_map[key] = permutation
        del key

    def __eq__(self, other) -> bool:
        if not isinstance(other, Measure):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __etrm_init(self) -> None:
        try:
            self.owner = self.get('owner', str)
            self.statewide_id = self.get('statewide_measure_id', str)
            self.version_id = self.get('full_version_id', str)
            self.name = self.get('name', str)
            self.use_category = self.get('use_category', str)
            self.pa_lead = self.get('pa_lead', str)
            self.start_date = self.get('effective_start_date', str)
            self.end_date = self.get('sunset_date', str | None)
            self.status = self.get('status', str)
            self.is_published = self.get('is_published', bool)
            self.permutation_method = self.get('permutation_method', int)
            self.workpaper_cover_sheet = self.get(
                'workpaper_cover_sheet',
                str
            )
            self.characterization_source_file = self.get(
                'characterization_source_file',
                str | None
            )
            self.date_committed = self.get('date_committed', str)
            self.change_description = self.get('change_description', str)
            self.permutations_url = self.get('permutations_url', str)
            self.property_data_url = self.get('property_data_url', str)
        except IndexError as err:
            raise ETRMResponseError from err

    def __json_init(self) -> None:
        try:
            self.owner = self.get('owned_by_user', str)
            self.statewide_id = self.get('MeasureID', str)
            self.version_id = self.get('MeasureVersionID', str)
            self.name = self.get('MeasureName', str)
            self.use_category = self.get('UseCategory', str)
            self.pa_lead = self.get('PALead', str)
            self.start_date = self.get('StartDate', str)
            self.end_date = self.get('EndDate', str | None)
            self.status = self.get('Status', str)
            self.is_published = None
            self.permutation_method = None
            self.workpaper_cover_sheet = None
            self.characterization_source_file = None
            self.date_committed = None
            self.change_description = None
            self.permutations_url = None
            self.property_data_url = None
        except IndexError as err:
            raise ETRMResponseError from err

    @property
    def start_date_time(self) -> dt.date:
        return utils.to_date(self.start_date)

    @property
    def end_date_time(self) -> dt.date | None:
        if self.end_date is None:
            return None

        return utils.to_date(self.end_date)

    def __get_characterizations(self,
                                names: list[str]
                               ) -> list[Characterization]:
        characterizations: list[str] = []
        for name in names:
            try:
                raw_content = self.get(name, str)
            except IndexError:
                continue

            content = ud.normalize('NFKD', raw_content)
            characterizations.append(Characterization(name, content))

        return characterizations

    def __get_permutations(self, names: list[str]) -> list[Permutation]:
        if self.source != 'json':
            return []

        permutations: list[Permutation] = []
        for name in names:
            try:
                mapped_value = self.get(name, str)
            except IndexError:
                continue

            permutations.append(Permutation(name, mapped_value))

        return permutations

    def get_determinant(self, name: str) -> Determinant | None:
        return self._determinant_map.get(name.lower())

    def contains_determinant(self, name: str) -> bool:
        return self.get_determinant(name) is not None

    def get_shared_parameter(self, name: str) -> SharedDeterminantRef | None:
        return self._shared_det_ref_map.get(name.lower())

    def get_shared_parameters(self,
                              names: list[str]
                             ) -> list[SharedDeterminantRef]:
        """Returns a list of shared determinant references associated
        with the shared determinant names in `names`.
        """

        refs: list[SharedDeterminantRef] = []
        for name in names:
            ref = self.get_shared_parameter(name)
            if ref is not None:
                refs.append(ref)
        return refs

    def contains_parameter(self, name: str) -> bool:
        return self.get_shared_parameter(name) is not None
    
    @overload
    def get_value_table(self, name: str) -> ValueTable | None:
        ...

    @overload
    def get_value_table(self, *names: str) -> ValueTable | None:
        ...

    def get_value_table(self, *names: str) -> ValueTable | None:
        """Returns the value table associated with the first name
        in `names` that has an associated value table.

        Returns `None` if no name has an associated value table.
        """

        for name in names:
            table = self._value_table_map.get(name.lower())
            if table is not None:
                return table
        return None

    def get_value_tables(self, names: list[str]) -> list[ValueTable]:
        """Returns a list of value tables associated with the non-shared
        value table names in `names`.
        """

        tables: list[ValueTable] = []
        for name in names:
            table = self.get_value_table(name)
            if table is not None:
                tables.append(table)
        return tables

    def contains_value_table(self, name: str) -> bool:
        return self.get_value_table(name) is not None

    def get_shared_lookup(self, name: str) -> SharedLookupRef | None:
        return self._shared_lookup_ref_map.get(name.lower())

    def get_shared_lookups(self, names: list[str]) -> list[SharedLookupRef]:
        """Returns a list of shared lookup references associated with the
        shared value table names in `names`.
        """

        refs: list[SharedLookupRef] = []
        for name in names:
            ref = self.get_shared_lookup(name)
            if ref is not None:
                refs.append(ref)
        return refs

    def contains_shared_table(self, name: str) -> bool:
        return self.get_shared_lookup(name) is not None

    def contains_table(self, name: str) -> bool:
        if self.contains_value_table(name):
            return True

        if self.contains_shared_table(name):
            return True

        return False

    def get_calculation(self, name: str) -> Calculation | None:
        return self._calculation_map.get(name.lower())

    def contains_calculation(self, name: str) -> bool:
        return self.get_calculation(name) is not None

    def get_exclusion_table(self, name: str) -> ExclusionTable | None:
        return self._exclusion_table_map.get(name.lower())

    def contains_exclusion_table(self, name: str) -> bool:
        return self.get_exclusion_table(name) is not None

    def get_permutation(self, name: str) -> Permutation | None:
        return self._permutation_map.get(name.lower())

    def contains_permutation(self, name: str) -> bool:
        return self.get_permutation(name) is not None

    def get_characterization(self, name: str) -> Characterization | None:
        return self._characterization_map.get(name.lower())

    def contains_characterization(self, name: str) -> bool:
        return self.get_characterization(name) is not None

    def contains_mat_label(self, *labels: str) -> bool:
        mat = self.get_shared_parameter('MeasAppType')
        if mat is None:
            raise RequiredContentError(name='Measure Application Type')

        return set(labels).issubset(mat.active_labels)

    def is_deer(self) -> bool:
        version = self.get_shared_parameter('version')
        if version is None:
            raise RequiredContentError(name='Version')

        return 'DEER' in version.active_labels

    def is_wen(self) -> bool:
        wen_param = self.get_shared_parameter('waterMeasureType')
        wen_table = self.get_shared_lookup('waterEnergyIntensity')
        if wen_param is not None and wen_table is not None:
            return True

        if wen_param is None and wen_table is None:
            return False

        if wen_param is None:
            raise RequiredContentError('WEN measure detected, but missing'
                                       ' a Water Energy Intensity value table')

        if wen_table is None:
            raise RequiredContentError('WEN measure detected, but missing'
                                       ' a Water Energy Intensity parameter')

        return False

    def is_deemed(self) -> bool:
        delivery_table = self.get_shared_parameter('DelivType')
        if delivery_table is None:
            raise RequiredContentError(name='Delivery Type')

        labels = delivery_table.active_labels
        return (
            'DnDeemDI' in labels
                or set(['DnDeemed', 'UpDeemed']).issubset(labels)
        )

    def is_fuel_sub(self) -> bool:
        mat = self.get_shared_parameter('MeasImpactType')
        if mat is None:
            raise RequiredContentError(name='Measure Impact Type')

        return 'FuelSub' in mat.active_labels

    def is_sector_default(self) -> bool:
        sector = self.get_shared_parameter('Sector')
        if sector is None:
            raise RequiredContentError(name='Sector')

        ntg_id = self.get_shared_parameter('NTGID')
        if ntg_id is None:
            raise RequiredContentError(name='Net to Gross Ratio ID')

        sectors = list(
            map(
                lambda sector: sector + '-Default',
                sector.active_labels
            )
        )

        for sector in sectors:
            for _id in ntg_id.active_labels:
                if sector in _id:
                    return True
        return False

    def requires_ntg_version(self) -> bool:
        ntg_id = self.get_shared_parameter('NTGID')
        if ntg_id == None:
            raise RequiredContentError(name='Net to Gross Ratio ID')

        for label in ntg_id.active_labels:
            match label:
                case ('Res-Default>2yrs'
                        | 'Com-Default>2yrs'
                        | 'Ind-Default>2yrs'
                        | 'Agric-Default>2yrs'):
                    continue
                case _:
                    return True
        return False

    def requires_upstream_flag(self) -> bool:
        delivery_type = self.get_shared_parameter('DelivType')
        if delivery_type == None:
            raise RequiredContentError(name='Delivery Type')

        if len(delivery_type.active_labels) < 2:
            return False

        return 'UpDeemed' in delivery_type.active_labels

    def is_res_default(self) -> bool:
        ntg_id = self.get_shared_parameter('NTGID')
        if ntg_id == None:
            raise RequiredContentError(name='Net to Gross Ratio ID')

        return 'Res-Default>2yrs' in ntg_id.active_labels

    def is_nonres_default(self) -> bool:
        ntg_id = self.get_shared_parameter('NTGID')
        if ntg_id == None:
            raise RequiredContentError(name='Net to Gross Ratio ID')

        for label in ntg_id.active_labels:
            match label:
                case ('Com-Default>2yrs'
                        | 'Ind-Default>2yrs'
                        | 'Agric-Default>2yrs'):
                    return True
                case _:
                    continue
        return False

    def is_GSIA_default(self) -> bool:
        gsia = self.get_shared_parameter('GSIAID')
        if gsia == None:
            raise RequiredContentError(name='GSIA ID')

        return 'Def-GSIA' in gsia.active_labels

    def is_interactive(self) -> bool:
        lighting_type = self.get_shared_parameter('LightingType')
        interactive_effect_app = self.get_value_table('IEApplicability')
        commercial_effects = self.get_shared_lookup('commercialInteractiveEffects')
        residential_effects = self.get_shared_lookup('residentialInteractiveEffects')

        if lighting_type or (commercial_effects or residential_effects):
            return True
        # elif (lighting_type or (commercial_effects or residential_effects)
        #       or interactive_effect_app):
        #     raise MeasureFormatError(
        #         'Missing required information for interactive effects')

        return False

    def get_criteria(self) -> list[str]:
        criteria: list[str] = ['REQ']

        if self.is_deer():
            criteria.append('DEER')

        if self.is_GSIA_default():
            criteria.append('DEF_GSIA')
        else:
            criteria.append('GSIA')

        if self.is_wen():
            criteria.append('WEN')

        if self.is_fuel_sub():
            criteria.append('FUEL')

        if self.is_interactive():
            criteria.append('INTER')

        if self.is_res_default():
            criteria.append('RES_DEF')

        if self.is_nonres_default():
            criteria.append('RES_NDEF')

        if not ('RES-DEF' in criteria or 'RES-NDEF' in criteria):
            criteria.append('RES')

        mat_labels = self.get_shared_parameter('MeasAppType').active_labels
        if 'AR' in mat_labels or 'AOE' in mat_labels:
            criteria.append('MAT_ARAOE')

        if 'NC' in mat_labels or 'NR' in mat_labels:
            criteria.append('MAT_NCNR')
            if 'AR' in mat_labels or 'AOE' in mat_labels:
                criteria.append('MAT_NCNR_ARAOE')

        if self.requires_ntg_version():
            criteria.append('NTG')

        if self.requires_upstream_flag():
            criteria.append('DEEM')

        if self.contains_value_table('emergingTech'):
            criteria.append('ET')

        return criteria

    def get_table_column_criteria(self) -> list[str]:
        criteria: list[str] = []

        mat = self.get_shared_parameter('MeasAppType')
        if 'AR' in mat.active_labels:
            criteria.append('AR_MAT')
            if len(mat.active_labels) > 2:
                criteria.append('AR_M_MAT')

        deliv = self.get_shared_parameter('DelivType')
        if 'UpDeemed' in deliv.active_labels:
            if len(deliv.active_labels) > 2:
                criteria.append('UD_M_DT')

        return criteria

    def get_permutation_criteria(self) -> list[str]:
        criteria: list[str] = []

        mat = self.get_shared_parameter('MeasAppType')
        if 'AR' in mat.active_labels:
            criteria.append('AR_MAT')
            if len(mat.active_labels) == 1:
                criteria.append('O_AR_MAT')
            else:
                criteria.append('M_AR_MAT')
        else:
            criteria.append('N_AR_MAT')

        if 'AOE' in mat.active_labels:
            criteria.append('AOE_MAT')
        else:
            criteria.append('N_AOE_MAT')

        if 'AR' in mat.active_labels and 'AOE' in mat.active_labels:
            criteria.append('AR_AOE_MAT')
            if len(mat.active_labels) == 2:
                criteria.append('O_AR_AOE_MAT')
            else:
                criteria.append('M_AR_AOE_MAT')
        else:
            criteria.append('N_AR_AOE_MAT')

        if self.is_GSIA_default():
            criteria.append('DEF_GSIA')

        criteria.append('PK_DMND')
        criteria.append('ELCT_SVG')
        criteria.append('GAS_SVG')
        criteria.append('FBLC') # maybe in costs value table? ask chau

    @staticmethod
    def sorting_key(measure: Measure) -> int:
        return utils.version_key(measure.version_id)
