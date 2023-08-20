import requests
import xml.etree.ElementTree as ET
import pm4py
import os
import pandas as pd
import json

bot_model_file_path = "./models/test_bot_model.json"
event_log_file_path = "event_logs/test_event_log.xes"

def fetch_bot_model(name , endpoint):
    # fetches a bot model from the social bot manager. available at <base_url>/models/{name}
    print(f"Fetching bot model from {endpoint}/models/{name}")
    request = requests.get(f"{endpoint}/models/{name}")
    if request.status_code == 200:
        return request.json()
    else:
        return None

def fetch_event_log(bot_name, url=None):
    tmp_event_log_file_path = "event_logs/tmp_event_log.xes"

    if url is None:
        url = f"https://mobsos.tech4comp.dbis.rwth-aachen.de/event-log"
    # fetches an event log from the social bot manager. available at <base_url>/event_logs/{name}
    print(f"Fetching event log from {url}/bot/{bot_name}")
    response = requests.get(f"{url}/bot/{bot_name}")
    # response is xml, use pm4py to parse it
    if response.status_code == 200:
        xml = response.content
        ET.fromstring(xml)
        # write the xml to a file 
        with open(tmp_event_log_file_path, "wb") as f:
            f.write(xml)
        
        # read the file with pm4py and return the event log and delete the file
        log = pm4py.read_xes(tmp_event_log_file_path)
        os.remove(tmp_event_log_file_path)
        if not "head" in dir(log):
            print("Could not fetch event log")
            return None
        log['time:timestamp'] = pd.to_datetime(log['time:timestamp']) # convert timestamp to datetime
        log =log[(log['EVENT'] == 'SERVICE_REQUEST') | (log['EVENT'] == 'USER_MESSAGE')] # drop bot messages
        log = log[(log['lifecycle:transition'] == 'complete') ] # only complete events
        return log

    else:
        print(response.status_code)
        return None
    

def load_default_bot_model():
    with open(bot_model_file_path) as json_file:
            #load the json file
        bot_model = json.load(json_file)
        return bot_model
    
def load_bot_model(path=None):
    if path is None:
        return load_default_bot_model()
    else:
        with open(path) as json_file:
            #load the json file
            bot_model = json.load(json_file)
            return bot_model