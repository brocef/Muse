from .. import caravan
import unittest

class CaravanTests(unittest.TestCase):
    def test_import(self):
        self.assertIsNotNone(caravan)

    def test_init(self):
        args = (None, 'CVN01', None, None, None, None, None)
        cvn = caravan.Caravan(*args)
        self.assertIsNotNone(cvn)

if __name__ == '__main__':
    unittest.main()
