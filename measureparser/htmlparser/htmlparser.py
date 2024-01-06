from bs4 import (
    BeautifulSoup,
    Tag,
    ResultSet,
    NavigableString
)

import measureparser._dbservice as db
from measureparser._parserdata import CharacterizationData
from measureparser.measure import (
    Characterization
)

class CharacterizationParser():
    def __init__(self, data: CharacterizationData):
        self.data = data


    def parse(self, characterization: Characterization) -> None:
        soup = BeautifulSoup(characterization.content, 'html.parser')

        name = characterization.name
        _EMBEDDED_MAP = db.get_embedded_table_map()
        if name in _EMBEDDED_MAP:
            self.validate_embedded_table(soup, _EMBEDDED_MAP[name])

        _STATIC_MAP = db.get_static_table_map()
        if name in _STATIC_MAP:
            self.validate_static_table(soup, _STATIC_MAP[name])

        self.validate_reference_spacing()


    def validate_reference_spacing(self, soup: BeautifulSoup) -> None:
        reference_tags: ResultSet[Tag] \
            = soup.find_all('span', attr={'data-etrmreference': True})
        for reference_tag in reference_tags:
            prev_element = reference_tag.previous_sibling
            if not isinstance(prev_element, NavigableString):
                continue

            trailing_spaces = _get_trailing_spaces(prev_element)
            if trailing_spaces != 0:
                # there are extra spaces behind the reference tag
                pass

            title = _get_title(reference_tag)
            if title == None:
                # reference tag is formatted incorrectly
                return

            initial_spaces = _get_initial_spaces(title)
            if initial_spaces != 0:
                # there are extra spaces in front of the reference tag
                return



    def validate_header_order(self, soup: BeautifulSoup) -> None:
        pass

    
    def validate_embedded_calculation(self, soup: BeautifulSoup) -> None:
        pass

    
    def validate_embedded_reference(self, soup: BeautifulSoup) -> None:
        pass


    def validate_embedded_table(self,
                                soup: BeautifulSoup,
                                table_name: str) -> None:
        embedded_table_tags: ResultSet[Tag] \
            = soup.find_all('div', attrs={'data-etrmvaluetable': True})
        if embedded_table_tags == []:
            # no embedded value tables exist
            return

        try:
            embedded_table_tags[1]
            # there exists multiple embedded tables within the characterization
            return
        except IndexError:
            pass

        embedded_table_tag: Tag = embedded_table_tags[0]

        embedded_name: str | None = _get_title(embedded_table_tag)
        if embedded_name == None:
            # embedded table is formatted incorrectly
            return

        if embedded_name != table_name:
            # embedded name is incorrect
            return


    def validate_static_table(self,
                              soup: BeautifulSoup,
                              table_name: str) -> None:
        table_header: Tag | None = None
        headers: list[Tag] = soup.find_all('h6')
        for header in headers:
            if table_name in header.descendants:
                table_header = header
                break
        if table_header == None:
            # static table header does not exist
            return

        static_table: Tag | None = table_header.next_sibling
        if static_table == None:
            # static table is either misplaced or does not exist
            return

        if static_table.name != 'table':
            # static table either does not immediately follow the header or does not exist
            return


def _get_title(element: Tag) -> NavigableString | None:
    if element.contents == []:
        return None

    span = element.contents[0]
    if not isinstance(span, Tag) or span.name != 'span':
        return None

    if span.contents == []:
        return None

    title = span.contents[0]
    if not isinstance(title, NavigableString):
        return None

    return title


def _get_initial_spaces(data: str) -> int:
    count = 0
    while data != '' and data[0] == ' ':
        count += 1
        data = data[1:]
    return count


def _get_trailing_spaces(data: str) -> int:
    count = 0
    while data != '' and data[-1] == ' ':
        count += 1
        data = data[:-1]
    return count