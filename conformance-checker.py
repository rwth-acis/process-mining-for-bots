from bot_parser import to_petri_net
import json
import pm4py


bot_model_file_path = "./models/bot_model.json"
event_log_file_path = "event_logs/test_event_log.xes"

with open(bot_model_file_path) as json_file:
        #load the json file
    bot_model = json.load(json_file)

    net,im,fm = to_petri_net(bot_model)
    event_log = pm4py.read_xes(event_log_file_path)

    diagnostics = pm4py.fitness_token_based_replay(event_log,net,im,fm)
    print(diagnostics)
    print(diagnostics['log_fitness'])
