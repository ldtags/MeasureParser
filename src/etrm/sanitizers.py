import re
import logging

from src.etrm import patterns
from src.etrm.exceptions import (
    UnauthorizedError,
    ETRMConnectionError,
    ETRMRequestError
)


logger = logging.getLogger(__name__)


def sanitize_api_key(api_key: str) -> str:
    logger.info(f'Sanitizing API key: {api_key}')

    re_match = re.fullmatch(patterns.API_KEY, api_key)
    if re_match is None:
        err_msg = f'Invalid API key: {api_key}'
        logger.info(err_msg)
        raise UnauthorizedError(err_msg)

    token_type = 'Token'
    token = re_match.group(3)
    if not isinstance(token, str):
        err_msg = f'An error occurred while parsing API key'
        logger.warning(err_msg)
        raise ETRMConnectionError(err_msg)

    sanitized = f'{token_type} {token}'
    return sanitized


def sanitize_statewide_id(statewide_id: str) -> str:
    logger.info(f'Sanitizing statewide ID: {statewide_id}')

    re_match = re.search(patterns.STATEWIDE_WHITELIST, statewide_id)
    if re_match is not None:
        err_msg = f'Statewide ID {statewide_id} contains invalid characters'
        logger.info(err_msg)
        raise ETRMRequestError(err_msg)

    re_match = re.fullmatch(patterns.STWD_ID, statewide_id)
    if re_match is None:
        err_msg = f'Invalid statewide ID: {statewide_id}'
        logger.info(err_msg)
        raise ETRMRequestError(err_msg)

    stwd_id = re_match.group(1)
    if not isinstance(stwd_id, str):
        err_msg = 'An error occurred while parsing statewide ID'
        logger.warning(err_msg)
        raise ETRMConnectionError(err_msg)

    sanitized = stwd_id.upper()
    return sanitized


def sanitize_measure_id(measure_id: str) -> str:
    logger.info(f'Sanitizing measure ID: {measure_id}')

    re_match = re.search(patterns.VERSION_WHITELIST, measure_id)
    if re_match is not None:
        err_msg = f'Measure version {measure_id} contains invalid characters'
        logger.info(err_msg)
        raise ETRMRequestError(err_msg)

    re_match = re.fullmatch(patterns.VERSION_ID, measure_id)
    if re_match is None:
        err_msg = f'Invalid measure version: {measure_id}'
        logger.info(err_msg)
        raise ETRMRequestError(err_msg)

    measure_version = re_match.group(1)
    if not isinstance(measure_version, str):
        err_msg = 'An error occurred while parsing measure version'
        logger.warning(err_msg)
        raise ETRMConnectionError(err_msg)

    sanitized = measure_version.upper()
    return sanitized


def sanitize_reference(ref_id: str) -> str:
    logger.info(f'Sanitizing reference ID: {ref_id}')

    re_match = re.search(patterns.REFERENCE_WHITELIST, ref_id)
    if re_match is not None:
        err_msg = f'Reference ID {ref_id} contains invalid characters'
        logger.info(err_msg)
        raise ETRMRequestError(err_msg)

    sanitized = ref_id.upper()
    return sanitized


def sanitize_table_name(table_name: str) -> str:
    logger.info(f'Sanitizing value table name: {table_name}')

    re_match = re.search(patterns.TABLE_NAME_WHITELIST, table_name)
    if re_match is not None:
        err_msg = f'Table name {table_name} contains invalid characters'
        logger.info(err_msg)
        raise ETRMRequestError(err_msg)

    return table_name
