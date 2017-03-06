from .. import conductor
import unittest

class ConductorTests(unittest.TestCase):
    def test_import(self):
        self.assertIsNotNone(conductor)

if __name__ == '__main__':
    unittest.main()
