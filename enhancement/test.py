import unittest
import json
import os
import pm4py
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from enhancement.main import add_edge_frequency,add_edge_performance
from utils.bot.parse_lib import get_parser, BotParser



def get_bot_model_json(rel_path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, rel_path), 'r', encoding='UTF-8') as f:
        return json.load(f)


def get_event_log(rel_path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return pm4py.read_xes(os.path.join(current_dir, rel_path))


class TestBotParser(unittest.TestCase):
    def setUp(self):
        self.bot_model = None
        self.instance = None

    def test_frequency_dfg(self):
        self.bot_model = get_bot_model_json('assets/alignment-test.json')
        event_log = get_event_log('assets/test.xes')
        self.instance = get_parser(self.bot_model)
        self.assertIsInstance(self.instance, BotParser)
        dfg, start,end = self.instance.get_dfg()
        result_dfg = add_edge_frequency(event_log=event_log, dfg=dfg,start_act=start,end_act=end,bot_parser=self.instance)
        self.assertEqual(len(result_dfg.keys()), 2)
        self.assertEqual(result_dfg[('a', 'a2')], 1)
        self.assertEqual(result_dfg[('a2', 'e')], 1)

    def test_performance_dfg(self):
        self.bot_model = get_bot_model_json('assets/alignment-test.json')
        event_log = get_event_log('assets/test.xes')
        self.instance = get_parser(self.bot_model)
        self.assertIsInstance(self.instance, BotParser)
        dfg, start,end = self.instance.get_dfg()
        result_dfg = add_edge_performance(event_log=event_log, dfg=dfg,start_act=start,end_act=end,bot_parser=self.instance)
        self.assertEqual(len(result_dfg.keys()), 2)
        self.assertEqual(result_dfg[('a', 'a2')], 65)
        self.assertEqual(result_dfg[('a2', 'e')], 30)




if __name__ == '__main__':
    unittest.main()
