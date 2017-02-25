from .. import scout
import unittest

class ScoutTests(unittest.TestCase):
    def test_init(self):
        self.assertIsNotNone(scout)

if __name__ == '__main__':
    unittest.main()
