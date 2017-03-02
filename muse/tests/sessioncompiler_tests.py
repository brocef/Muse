from .. import sessioncompiler
import unittest

class SessionCompilerTests(unittest.TestCase):
    def test_import(self):
        self.assertIsNotNone(sessioncompiler)

    def test_init(self):
        sc = sessioncompiler.SessionCompiler(None)
        self.assertIsNotNone(sc)

if __name__ == '__main__':
    unittest.main()
