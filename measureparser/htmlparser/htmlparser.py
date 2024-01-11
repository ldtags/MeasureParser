from bs4 import (
    BeautifulSoup,
    Tag,
    ResultSet,
    NavigableString
)

import re

from .embedded import (
    EmbeddedReference
)
import measureparser._dbservice as db
import measureparser._parserdata as pd
from measureparser.measure import (
    Characterization
)

class CharacterizationParser():
    '''A parser that validates data found in eTRM measure characterizations
    
    __init__(_data_dict, characterization)
        _data_dict (dict[str, CharacterizationData])
    '''

    def __init__(self,
                 _data_dict: dict[str, pd.CharacterizationData] | None = None,
                 characterization: Characterization | None = None):
        if _data_dict != None:
            self._data_dict = _data_dict
        else:
            self._data_dict = pd.characterization_dict()

        self.characterization = characterization
        self.data: pd.CharacterizationData | None = None

        if characterization != None:
            self.data = self._data_dict[characterization.name]

    def parse(self, characterization: Characterization | None = None) -> None:
        '''Validates the given characterization in accordance to the
            eTRM QA/QC
        '''
        if characterization != None:
            self.characterization = characterization
            self.data = self._data_dict.get(characterization.name)

        if self.characterization == None or self.data == None:
            return

        soup = BeautifulSoup(self.characterization.content, 'html.parser')
        self.validate_header_order(soup)
        self.validate_sentence_spacing(soup)
        self.validate_reference_tags(soup)

        name = self.characterization.name
        EMBEDDED_TABLE_MAP = db.get_embedded_table_map()
        if name in EMBEDDED_TABLE_MAP:
            self.validate_embedded_table(soup, EMBEDDED_TABLE_MAP[name])

        STATIC_TABLE_MAP = db.get_static_table_map()
        if name in STATIC_TABLE_MAP:
            self.validate_static_table(soup, STATIC_TABLE_MAP[name])

    def validate_header_order(self, soup: BeautifulSoup) -> None:
        '''Validates that all headers in the characterization follow
            the order of `h3 -> h4 -> h5`
        '''
        if self.data == None:
            return

        headers: ResultSet[Tag] = soup.find_all(r'^h[3-5]$')
        if headers == []:
            return

        initial = headers.pop(0)
        if initial.name != 'h3':
            self.data.initial_header = initial.name

        prev_level = int(re.sub(r'[^3-5]', '', initial.name))
        for header in headers:
            if header.name == 'h3':
                prev_level = 3
                continue

            cur_level = int(re.sub(r'[^3-5]', '', header.name))

            if (cur_level - prev_level) not in [0, 1]:
                self.data.invalid_headers.append(
                    pd.InvalidHeaderData(header.name, prev_level))
                continue

            prev_level = cur_level

    # searches for paragraphs by the <p> tag
    # splits sentences in those paragraphs by '.'
    # this also validates some reference tag spacing as a side effect
    def validate_sentence_spacing(self, soup: BeautifulSoup) -> None:
        '''Validates that all sentences are seperated by only one space'''
        if self.data == None:
            return

        paragraphs: ResultSet[Tag] = soup.find_all('p')
        for paragraph in paragraphs:
            text = paragraph.get_text()
            if text == '' or '.' not in text:
                continue

            sentences = text.split('.')
            if len(sentences) == 1:
                continue

            initial_sent = sentences.pop(0)
            spaces = _get_leading_spaces(initial_sent)
            if spaces > 0:
                self.data.sentences.append(
                    pd.SentenceSpacingData(leading=spaces,
                                           sentence=initial_sent,
                                           initial=True))

            for sentence in sentences:
                spacing_data = pd.SentenceSpacingData(sentence=sentence)
                leading_spaces = _get_leading_spaces(sentence)
                if leading_spaces != 1:
                    spacing_data.leading = leading_spaces

                trailing_spaces = _get_trailing_spaces(sentence)
                if trailing_spaces != 0:
                    spacing_data.trailing = trailing_spaces

                if not spacing_data.is_empty():
                    self.data.sentences.append(spacing_data)

    def validate_embedded_reference(self, reference_tag: Tag) -> None:
        pass

    def validate_reference_tags(self, soup: BeautifulSoup) -> None:
        '''Validates the spacing around reference tags and reference
            titles
        '''
        if self.data == None:
            return

        reference_tags: ResultSet[Tag] \
            = soup.find_all(attr={'data-etrmreference': True})
        for reference_tag in reference_tags:
            tag_data = pd.ReferenceTagData(
                spacing=validate_tag_spacing(reference_tag),
                title=validate_static_title(reference_tag))
            title = _get_static_title(reference_tag, clean=True)
            self.data.references.get(title).append(tag_data)

    def validate_embedded_calculation(self, soup: BeautifulSoup) -> None:
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

        embedded_name: str | None = _get_static_title(embedded_table_tag)
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


def validate_static_title(embedded_tag: Tag) -> pd.TitleData:
    '''Validates that `embedded_tag` has a nested title with no leading
        or trailing whitespace
    '''
    title_data = pd.TitleData()

    title = _get_static_title(embedded_tag)
    if title == None:
        title_data.missing = True
        return

    initial_spaces = _get_leading_spaces(title)
    if initial_spaces != 0:
        title_data.spacing.leading = initial_spaces
        pass

    trailing_spaces = _get_trailing_spaces(title)
    if trailing_spaces != 0:
        title_data.spacing.trailing = trailing_spaces
        pass

    return title_data


def validate_tag_spacing(tag: Tag,
                         leading: int = 0,
                         trailing: int = 0) -> pd.SpacingData:
    '''Validates that `tag` has `leading` and `trailing` whitespace'''
    spacing_data = pd.SpacingData()

    prev_text = _get_previous_text(tag)
    if prev_text != None:
        spaces = _get_trailing_spaces(prev_text)
        if spaces != leading:
            spacing_data.leading = spaces

    next_text = _get_following_text(tag)
    if next_text != None:
        spaces = _get_leading_spaces(next_text)
        if spaces != trailing:
            spacing_data.trailing = spaces

    return spacing_data


def _is_embedded_tag(tag: Tag) -> bool:
    return (tag.get('data-etrmreference') != None
        or tag.get('data-etrmvaluetable') != None
        or tag.get('data-etrmcalculation') != None)


def _get_static_title(tag: Tag, clean: bool = False) -> str | None:
    if not _is_embedded_tag(tag):
        return None

    if tag.contents == []:
        return None

    text = tag.get_text()
    if text == '':
        return None

    if clean:
        text = text.strip().upper()

    return text


def _get_previous_text(element: Tag) -> str | None:
    if element.previous_sibling == None:
        return None

    if isinstance(element.previous_sibling, NavigableString):
        return str(element.previous_sibling)

    prev_text = element.previous_sibling.get_text()
    if prev_text == '':
        return None
    return prev_text


def _get_following_text(element: Tag) -> str | None:
    if element.next_sibling == None:
        return None

    if isinstance(element.next_sibling, NavigableString):
        return str(element.next_sibling)

    next_text = element.next_sibling.get_text()
    if next_text == '':
        return None
    return next_text


def _get_leading_spaces(data: str) -> int:
    if not isinstance(data, str):
        return 0

    count = 0
    while data != '' and data[0] in ['\u00a0', ' ']:
        count += 1
        data = data[1:]
    return count


def _get_trailing_spaces(data: str) -> int:
    if not isinstance(data, str):
        return 0

    count = 0
    while data != '' and data[-1] in ['\u00a0', ' ']:
        count += 1
        data = data[:-1]
    return count