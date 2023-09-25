import unittest
from utils.bot.parse_lib import get_parser, BotParser
import json
import os


def get_bot_model_json(rel_path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, rel_path), 'r', encoding='UTF-8') as f:
        return json.load(f)


class TestBotParser(unittest.TestCase):
    def setUp(self):
        self.bot_model = None
        self.instance = None

    def test_get_bot_parser(self):
        self.bot_model = get_bot_model_json('assets/sequential_path_model.json')
        self.instance = get_parser(self.bot_model)
        self.assertIsInstance(self.instance, BotParser)

    def test_incomplete_bot_model(self):
        with self.assertRaises(Exception) as context:
            self.instance = BotParser({})
            # check if exception "Invalid bot model" is raised
            self.assertTrue('Invalid bot model' in context.exception)

    def test_no_bot_node(self):
        with self.assertRaises(Exception) as context:
            self.instance = BotParser({'nodes': {}, 'edges': {}})
            # check if exception "No bot node found in bot model" is raised
            self.assertTrue(
                'Bot name not found in bot model' in context.exception)

    def test_messenger_node_missing(self):
        with self.assertRaises(Exception) as context:
            self.instance = BotParser({'nodes': {'bot': {
                "type": "Bot",
                "attributes": {
                    "a": {
                        "id": "a[name]",
                        "name": "Name",
                        "value": {
                            "id": "a[name]",
                            "name": "Name",
                            "value": "Bot"
                        }
                    }
                }
            }}, 'edges': {}})
            self.assertTrue(
                'Messenger node not found in bot model' in context.exception)

    def test_parse_to_dfg(self):
        # minimal bot model with a single conversation edge
        seq_json = get_bot_model_json('assets/sequential_path_model.json')
        self.instance = BotParser(seq_json)
        dfg, start, end = self.instance.get_dfg()
        self.assertIsNotNone(dfg)
        self.assertEqual(start, {'A'})
        self.assertEqual(end, {'B'})
        self.assertEqual(dfg, {('A', 'B'): 0})

    def test_parse_to_dfg_with_single_node(self):
        # bot model with a single incoming message node
        model = get_bot_model_json('assets/single_conversation_node.json')
        self.instance = BotParser(model)
        dfg, start, end = self.instance.get_dfg()
        self.assertIsNotNone(dfg)
        self.assertEqual(start, {'A'})
        self.assertEqual(end, {"empty_intent"})
        self.assertEqual(dfg, {('A', "empty_intent"): 0})


if __name__ == '__main__':
    unittest.main()
