import unittest

from context import utils


class TestSchemaValidation(unittest.TestCase):
    def test_validation(self) -> None:
        self.assertTrue(utils.is_etrm_measure('./resources/SWCR002.json'))
        self.assertFalse(utils.is_etrm_measure('./resources/schema/no_determ.json'))
        self.assertFalse(utils.is_etrm_measure('./resources/schema/no_sha_determ.json'))
        self.assertFalse(utils.is_etrm_measure('not a filepath'))
        