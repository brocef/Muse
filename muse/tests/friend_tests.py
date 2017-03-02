from .. import friend
import unittest

class FriendTests(unittest.TestCase):
    def test_import(self):
        self.assertIsNotNone(friend)

    def test_init(self):
        args = (None, 'FND01', None, None, None, None, None)
        fnd = friend.Friend(*args)
        self.assertIsNotNone(fnd)

if __name__ == '__main__':
    unittest.main()
