from .. import config
import unittest

class ConfigTests(unittest.TestCase):
    def test_import(self):
        self.assertIsNotNone(config)

if __name__ == '__main__':
    unittest.main()
