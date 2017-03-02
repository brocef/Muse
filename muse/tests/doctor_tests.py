from .. import doctor
import unittest

class DoctorTests(unittest.TestCase):
    def test_import(self):
        self.assertIsNotNone(doctor)

    def test_init(self):
        args = (None, 'DOC01', None, None, None, None, None)
        doc = doctor.Doctor(*args)
        self.assertIsNotNone(doc)

if __name__ == '__main__':
    unittest.main()
