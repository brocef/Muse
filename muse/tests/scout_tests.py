from .. import scout
import unittest

class ScoutTests(unittest.TestCase):
    def test_import(self):
        self.assertIsNotNone(scout)

    def test_init(self):
        args = (None, 'SCT01', None, None, None, None, None)
        sct = scout.Scout(*args)
        self.assertIsNotNone(sct)

if __name__ == '__main__':
    unittest.main()
