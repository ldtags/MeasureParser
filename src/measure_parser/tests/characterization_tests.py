import unittest
from data.characterizations import ALL_CHARACTERIZATIONS
from htmlparser import CharacterizationParser as char_parser

class TestCharacterizationParsing(unittest.TestCase):
    def runTest(self):
        parser: char_parser = char_parser()
        

        