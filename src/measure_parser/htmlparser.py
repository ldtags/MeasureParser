from html.parser import HTMLParser
from typing import Optional, TextIO
from spellchecker import SpellChecker
from objects import Characterization
import re

# Global Variables
spell = SpellChecker()

class CharacterizationParser(HTMLParser):
    """The parser for measure characterization HTML
    
    Attributes:
        characterization (Optional[Characterization]): an object
            containing the name and HTML of a characterization
        out (Optional[TextIO]): a file stream for the log file
        tabs (str): the amount of tabs that will precede any log output
        __prev_tag (str): the HTML tag that was previously encountered
        __prev_data (str): the data that was previously encountered
    """

    def __init__(self,
                 characterization: Optional[Characterization] = None,
                 out: Optional[TextIO] = None,
                 tabs: int = 0):
        self.characterization: Optional[Characterization] \
            = characterization
        self.out: Optional[TextIO] = out
        self.tabs: str = '\t' * tabs
        self.__prev_tag: str = ''
        self.__prev_data: str = ''
        super().__init__()

    # sets the objects @characterization to the input @characterization
    #
    # Parameters:
    #   characterization (Characterization): characterization to be parsed
    def set_characterization(self,
                             characterization: Characterization) -> None:
        self.characterization = characterization

    # parses the objects @characterization
    def parse(self) -> None:
        if self.characterization != None:
            self.feed(self.characterization.content)

    # parses the input @characterization
    #
    # Parameters:
    #   characterization (Characterization): characterization to be parsed
    def parse(self,
              characterization: Characterization) -> None:
        self.feed(characterization.content)

    # determines how any data found in the HTML will be handled
    #
    # Parameters:
    #   data (str): the text contained by the tags
    def handle_data(self, data: str) -> None:
        if data == '\n':
            return

        self.__prev_data = data
        self.validate_punctuation_spacing(data)

    # checks the spaces that occur after a sentence
    #
    # Parameters:
    #   data (str): the text to be validated
    def validate_punctuation_spacing(self, data: str) -> None:
        sentences: list[str] = data.split('.')
        if len(sentences) <= 1:
            return

        for sentence in sentences:
            extra_spaces: int = self.__get_start_spaces(sentence)
            if extra_spaces > 1:
                print(self.tabs
                        + 'extra space(s) detected after punctuation',
                      f'in {self.characterization.name} -',
                      f'{extra_spaces - 1}',
                      file=self.out)

    # determines how many spaces occur at the beginning of @data
    #
    # Parameters:
    #   data (str): the string getting checked for spaces
    #
    # Returns:
    #   int: the amount of spaces that occur at the beginning of @data
    def __get_start_spaces(self, data: str) -> int:
        count: int = 0
        while len(data) > 0 and data[0] == ' ':
            count += 1
            data = data[1:]
        return count


    def spell_check(self, words: list[str]) -> None:
        # regex: re.Pattern = re.compile('[^a-zA-Z]')
        spell.word_frequency.load_words(
            ['IWF', 'IMEF', 'kWh', 'MEF', 'high-efficiency']
        )
        for word in words:
            correct: str = spell.correction(word)
            if correct != None:
                print(self.tabs
                        + f'misspelled word - {word} should be {correct}',
                      file=self.out)

    # determines what happens when a starting tag is detected
    #
    # Parameters:
    #   tag (str): the type of tag encountered
    #   attrs (list[tuple[str, str | None]]): the list of tag attributes
    def handle_starttag(self,
                        tag: str,
                        attrs: list[tuple[str, str | None]]) -> None:
        if not re.fullmatch('h[0-9]$', tag) == None:
            self.validate_header(tag)

        self.check_ref_spacing(attrs)

    # validates that all references have only one space before them
    #
    # Parameters:
    #   attrs (list[tuple[str, str | None]]): the list of tag attributes
    def check_ref_spacing(self,
                          attrs: list[tuple[str, str | None]]) -> None:
        for attr, value in attrs:
            if (attr == 'data-etrmreference'
                    and self.__prev_data.endswith(' ')):
                extra_spaces: int \
                    = self.__get_end_spaces(self.__prev_data)
                print(self.tabs
                        + 'extra space(s) detected before a reference',
                      f'in {self.characterization.name} - {extra_spaces}',
                      file=self.out)

    # determines how many spaces occur at the end of @data
    #
    # Parameters:
    #   data (str): the string getting checked for spaces
    #
    # Returns:
    #   int: the amount of spaces that occur at the end of @data
    def __get_end_spaces(self, data: str) -> int:
        count: int = 0
        while data.endswith(' '):
            data = data[:-1]
            count += 1
        return count

    # validates that @tag follows the h3 -> h4 -> h5 header precedence
    #
    # Parameters:
    #   tag (str): the header that was detected
    #
    # Returns:
    #   bool: True if the header is valid, False otherwise
    def validate_header(self, tag: str) -> bool:
        if re.fullmatch('^h[3-5]$', tag) == None:
            print(self.tabs + 'invalid header in',
                  f'{self.characterization.name} - {tag}',
                  file=self.out)
            return False

        if tag == 'h3':
            self.__prev_tag = tag
            return True

        if self.__prev_tag == '':
            print(self.tabs + 'incorrect initial header in',
                  f'{self.characterization.name} -',
                  f'expected h3, but detected {tag}',
                  file=self.out)
            return False

        level_re: re.Pattern = re.compile('[^3-5]')
        prev_level: int = int(level_re.sub('', self.__prev_tag))
        cur_level: int = int(level_re.sub('', tag))
        if (cur_level - prev_level) in [0, 1]:
            self.__prev_tag = tag
            return True

        print(self.tabs + 'incorrect header in',
              f'{self.characterization.name} -',
              f'expected h{prev_level} or h{prev_level + 1},',
              f'but detected {tag}',
              file=self.out)
        return False

    # determines what happens when an end tag is detected
    #
    # Parameters:
    #   tag (str): the type of tag encountered
    def handle_endtag(self, tag: str) -> None:
        pass