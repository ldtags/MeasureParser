from typing import Any

def queryfy(elements: list[str | int]) -> str:
    '''Generates a list that is understood by the SQL interpreter.'''

    query_list: str = '('
    length: int = len(elements)
    for i, element in enumerate(elements):
        match element:
            case str():
                query_list += '\"' + element + '\"'
            case int():
                query_list += str(element)
            case _:
                raise RuntimeError(f'Object type [{str(type(element))}]'
                                    ' is not supported by queryfy')

        if i != length - 1:
            query_list += ', '

    query_list += ')'
    return query_list


def listify(tuples: list[tuple[Any,]]) -> list[Any]:
    '''Generates a list of the first elements of each tuple in `tuples`.'''

    if type(tuples) is not list:
        return []

    if len(tuples) == 0:
        return []

    first = tuples[0]
    if type(first) is not tuple:
        return []

    if len(first) == 0:
        return []

    return [element[0] for element in tuples]
