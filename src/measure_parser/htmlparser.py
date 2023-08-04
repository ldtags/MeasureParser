from html.parser import HTMLParser
from typing import Optional, TextIO
from spellchecker import SpellChecker
from objects import Characterization
import re

# Global Variables
spell = SpellChecker()

class CharacterizationParser(HTMLParser):
    def __init__(self,
                 characterization: Optional[Characterization] = None,
                 out: Optional[TextIO] = None,
                 tabs: int = 0):
        self.characterization: Optional[Characterization] \
            = characterization
        self.out: Optional[TextIO] = out
        self.tabs: str = '\t' * tabs
        self.__prev_tag: str = ''
        super().__init__()


    def set_characterization(self,
                             characterization: Characterization) -> None:
        self.characterization = characterization


    def parse(self) -> None:
        if self.characterization != None:
            self.feed(self.characterization.content)
        
        
    def parse(self,
              characterization: Characterization) -> None:
        self.characterization = characterization
        self.feed(self.characterization.content)


    def handle_data(self, data: str) -> None:
        pass


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


    def handle_starttag(self,
                        tag: str,
                        attrs: list[tuple[str, str | None]]) -> None:
        if not re.fullmatch('h[0-9]$', tag) == None:
            self.validate_header(tag)


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

    def handle_endtag(self, tag: str) -> None:
        pass