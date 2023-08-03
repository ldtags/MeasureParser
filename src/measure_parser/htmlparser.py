from html.parser import HTMLParser
from typing import Optional, TextIO
from spellchecker import SpellChecker
from objects import Characterization
import re

spell = SpellChecker()

class CharacterizationParser(HTMLParser):
    def __init__(self,
                 characterization: Optional[Characterization]=None,
                 out: Optional[TextIO]=None):
        self.characterization: Optional[Characterization] \
            = characterization
        self.out: Optional[TextIO] = out
        self.header_stack: list[str] = []
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
                print(f'misspelled word - {word} should be {correct}',
                      file=self.out)


    def handle_starttag(self,
                        tag: str,
                        attrs: list[tuple[str, str | None]]) -> None:
        if re.fullmatch('^h[3-5]$', tag) == None:
            return None

        num_re: re.Pattern = re.compile('[^0-9]')
        h_level: int = int(num_re.sub('', tag))
        prev_level: int = 2
        if len(self.header_stack) != 0:
            prev_level = int(num_re.sub('', self.header_stack[-1]))

        if h_level - prev_level != 1:
            err_msg: str = '\tincorrect header '
            if self.characterization != None:
                err_msg += f'detected in {self.characterization.name} '
            err_msg += f'- expected h{prev_level + 1} but found h{h_level}'
            print(err_msg, file=self.out)

        self.header_stack.append(tag)


    def handle_endtag(self, tag: str) -> None:
        if re.fullmatch('^h[3-5]$', tag) == None:
            return None

        stack_tag: str = self.header_stack.pop()
        if stack_tag != tag:
            err_msg: str = '\tbad HTML formatting '
            if self.characterization != None:
                err_msg += f'detected in {self.characterization.name} '
            err_msg += f'- expected {stack_tag}, but found {tag}'
            print(err_msg, file=self.out)
            return None