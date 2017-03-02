from .. import agent
import unittest

class AgentTests(unittest.TestCase):
    def test_import(self):
        self.assertIsNotNone(agent)

    def test_init(self):
        args = (None, 'AGT01', None, None, None, None, None)
        agt = agent.Agent(*args)
        self.assertIsNotNone(agt)

if __name__ == '__main__':
    unittest.main()
