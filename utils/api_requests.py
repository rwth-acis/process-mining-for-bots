import requests as r
import pm4py
import pandas as pd
import json
from pm4py.objects.log.importer.xes import variants as xes_importer
import base64


bot_model_file_path = "./assets/models/test_bot_model.json"
event_log_file_path = "assets/event_logs/test_event_log.xes"

def fetch_bot_model(name , endpoint = "https://mobsos.tech4comp.dbis.rwth-aachen.de/SBFManager"):
    # fetches a bot model from the social bot manager. available at <base_url>/models/{name}
    print(f"Fetching bot model from {endpoint}/models/{name}")
    request = r.get(f"{endpoint}/models/{name}")
    if request.status_code == 200:
        return request.json()
    else:
        return None

def fetch_event_log(bot_name, url=None):
    if url is None:
        url = f"https://mobsos.tech4comp.dbis.rwth-aachen.de/event-log"
    # fetches an event log from the social bot manager. available at <base_url>/event_logs/{name}
    print(f"Fetching event log from {url}/bot/{bot_name}")
    response = r.get(f"{url}/bot/{bot_name}")
    # response is xml, use pm4py to parse it
    if response.status_code == 200:
        xml = response.content
        try:
            log = pm4py.convert_to_dataframe(xes_importer.iterparse.import_from_string(xml))
        except  Exception as e:
            print("Could not parse event log")
            print(e)
            return None
        if not "head" in dir(log):
            print("log is empty")
            return None
        log['time:timestamp'] = pd.to_datetime(log['time:timestamp']) # convert timestamp to datetime
        log =log[(log['EVENT'] == 'SERVICE_REQUEST') | (log['EVENT'] == 'USER_MESSAGE')] # drop bot messages
        log = log[(log['lifecycle:transition'] == 'complete') ] # only complete events
        return log

    else:
        print("Could not fetch event log, status code: ",response.status_code)
        return None
    
def get_default_event_log():
    log = pm4py.read_xes(event_log_file_path)
    # remove events lifecycle:transition=start
    log = log[(log['lifecycle:transition'] == 'complete') ]
    # remove bot messages
    log =log[(log['EVENT'] == 'SERVICE_REQUEST') | (log['EVENT'] == 'USER_MESSAGE')]
    return log
    

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
        

def fetch_success_model(endpoint, botName,bot_pw,group_id=None,service_id=None):
    if group_id is None:
        group_id = "343da947a6db1296fadb5eca3987bf71f2e36a6d088e224a006f4e20e6e7935bb0d5ce0c13ada9966228f86ea7cc2cf3a1435827a48329f46b0e3963213123e0"
    if service_id is None:
        service_id = "i5.las2peer.services.mensaService.MensaService"
    endpoint += group_id +"/"+ service_id
    headers = {'authorization': __getAuthorizationHeader(botName,bot_pw)}
    print(f"Fetching success model from {endpoint}")
    success_model_response = r.get(f"{endpoint}",headers=headers)
    return success_model_response.json()["xml"] if success_model_response.status_code == 200 else None


def __getAuthorizationHeader(user_name, pw):
    """
    Gets the authorization header for basic auth using useranme and password
    :param user_name: the username  
    :param pw: the password
    :return: the authorization header
    """
    return f"""Basic {base64.b64encode(f"{user_name}:{pw}".encode('utf-8')).decode('utf-8')}"""

def fetchL2PGroups(success_modeling_service_endpoint,user_name,pw):
    """
    Fetches all Las2peer groups of a user
    """
    success_modeling_service_endpoint += "/groups"
    response = r.get(success_modeling_service_endpoint,headers={'authorization': __getAuthorizationHeader(user_name,pw),
                                       'Content-Type': 'application/json'})
    return response.json() if response.status_code == 200 else None

def fetchL2PServices(endpoint = "https://mobsos.tech4comp.dbis.rwth-aachen.de/mobsos-success-modeling/apiv2/services"):
    """
    Fetches all Las2peer services available at the given endpoint
    """
    print(f"Fetching services from {endpoint}")
    response = r.get(endpoint)
    return response.json() if response.status_code == 200 else None