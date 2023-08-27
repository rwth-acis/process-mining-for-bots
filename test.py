import unittest
from bot_parser import get_bot_parser, BotParser

class TestBotParser(unittest.TestCase):
    def setUp(self):
        self.instance = get_bot_parser(self.bot_model)

    def test_get_bot_parser(self):
        bot_parser = get_bot_parser(self.bot_model)
        self.assertIsInstance(bot_parser, BotParser)

    def test_parse_to_petri_net(self):
        petri_net = self.instance.parse_to_petri_net()
        self.assertIsNotNone(petri_net)

    def test_parse_to_dfg(self):
        dfg = self.instance.parse_to_dfg()
        self.assertIsNotNone(dfg)