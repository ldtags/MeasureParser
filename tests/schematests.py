import unittest
from measureparser.utils import is_etrm_measure

class TestSchemaValidation(unittest.TestCase):
    def test_validation(self) -> None:
        self.assertTrue(is_etrm_measure('./resources/SWCR002.json'))
        self.assertFalse(is_etrm_measure('./resources/schema/no_determ.json'))
        self.assertFalse(is_etrm_measure('./resources/schema/no_sha_determ.json'))
        self.assertFalse(is_etrm_measure('not a filepath'))
        