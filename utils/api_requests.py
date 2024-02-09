import requests as r
import pm4py
import pandas as pd
import json
from pm4py.objects.log.importer.xes import variants as xes_importer
import base64


bot_model_file_path = "./assets/models/test_bot_model.json"
event_log_file_path = "assets/event_logs/demo.xes"


def fetch_bot_model(name, endpoint="https://mobsos.tech4comp.dbis.rwth-aachen.de/SBFManager"):
    # fetches a bot model from the social bot manager. available at <base_url>/models/{name}
    request = r.get(f"{endpoint}/models/{name}")
    if request.status_code == 200:
        return request.json()
    else:
        return None


def fetch_event_log(bot_name, url=None,botManagerUrl = None):
    if url is None:
        url = f"https://mobsos.tech4comp.dbis.rwth-aachen.de/event-log"
    if botManagerUrl is None:
        botManagerUrl = f"https://mobsos.tech4comp.dbis.rwth-aachen.de/SBFManager"
    endpoint = f"{url}/bot/{bot_name}?bot-manager-url={botManagerUrl}"
    print(f"Fetching event log from {endpoint}")
    response = r.get(endpoint)
    # response is xml, use pm4py to parse it
    if response.status_code == 200:
        xml = response.content
        try:
            log = pm4py.convert_to_dataframe(
                xes_importer.iterparse.import_from_string(xml))
        except Exception as e:
            print("Could not parse event log")
            print(e)
            return None
        if not "head" in dir(log):
            print("log is empty")
            return None
        log['time:timestamp'] = pd.to_datetime(
            log['time:timestamp'])  # convert timestamp to datetime
        log = log[(log['EVENT_TYPE'] == 'SERVICE_REQUEST') | (
            log['EVENT_TYPE'] == 'USER_MESSAGE')]  # drop bot messages
        # only complete events
        log = log[(log['lifecycle:transition'] == 'complete')]
        return log

    else:
        print("Could not fetch event log, status code: ", response.status_code, response.content)
        return None


def get_default_event_log():
    log = pm4py.read_xes(event_log_file_path)
    # remove events lifecycle:transition=start
    log = log[(log['lifecycle:transition'] == 'complete')]
    # remove bot messages
    log = log[(log['EVENT_TYPE'] == 'SERVICE_REQUEST')
              | (log['EVENT_TYPE'] == 'USER_MESSAGE')]
    # convert timestamp to datetime
    log['time:timestamp'] = pd.to_datetime(log['time:timestamp'])
    return log


def load_default_bot_model():
    with open(bot_model_file_path) as json_file:
        # load the json file
        bot_model = json.load(json_file)
        return bot_model


def load_bot_model(path=None):
    if path is None:
        return load_default_bot_model()
    else:
        with open(path) as json_file:
            # load the json file
            bot_model = json.load(json_file)
            return bot_model


def fetch_success_model(endpoint, botName, bot_pw, group_id=None, service_id=None):
    if group_id is None:
        group_id = "343da947a6db1296fadb5eca3987bf71f2e36a6d088e224a006f4e20e6e7935bb0d5ce0c13ada9966228f86ea7cc2cf3a1435827a48329f46b0e3963213123e0"
    if service_id is None:
        service_id = "i5.las2peer.services.mensaService.MensaService"
    endpoint += "/models/" + group_id + "/" + service_id
    headers = {'authorization': __getAuthorizationHeader(botName, bot_pw)}
    print(f"Fetching success model from {endpoint}")
    try:
        success_model_response = r.get(f"{endpoint}", headers=headers)
        return success_model_response.json()["xml"] if success_model_response.status_code == 200 else None
    except Exception as e:
        print("Could not fetch success model")
        print(e)
        return None


def __getAuthorizationHeader(user_name, pw):
    """
    Gets the authorization header for basic auth using useranme and password
    :param user_name: the username  
    :param pw: the password
    :return: the authorization header
    """
    return f"""Basic {base64.b64encode(f"{user_name}:{pw}".encode('utf-8')).decode('utf-8')}"""


def fetchL2PGroups(success_modeling_service_endpoint, user_name, pw):
    """
    Fetches all Las2peer groups of a user
    """
    success_modeling_service_endpoint += "/groups"
    print(f"Fetching groups from {success_modeling_service_endpoint}")
    response = r.get(success_modeling_service_endpoint, headers={'authorization': __getAuthorizationHeader(user_name, pw),
                                                                 'Content-Type': 'application/json'})
    return response.json() if response.status_code == 200 else None


def fetchL2PServices(endpoint="https://mobsos.tech4comp.dbis.rwth-aachen.de/mobsos-success-modeling/apiv2/services"):
    """
    Fetches all Las2peer services available at the given endpoint
    """
    print(f"Fetching services from {endpoint}")
    response = r.get(endpoint)
    return response.json() if response.status_code == 200 else None


def fetchVisualization(endpoint, username, password, SQLQuery, vizFormat="CSV"):
    """
    Fetches the visualization data from the given endpoint
    """
    if endpoint is None:
        endpoint = "https://mobsos.tech4comp.dbis.rwth-aachen.de/QVS"
    endpoint += f"/query/visualize?format={vizFormat}"
    print(f"Fetching visualization data from {endpoint}")
    body = {
        'dbkey': 'las2peermon',
        'query': SQLQuery,
    }
    response = r.post(endpoint, data=json.dumps(body), headers={'authorization': __getAuthorizationHeader(
        username, password), 'Content-Type': 'application/json'})
    return response.content if response.status_code < 300 else None


# print(fetchVisualization(None, "MensaBot", "actingAgent",
#       "SELECT REMARKS->\"$.url\" as url , AVG(REMARKS->\"$.duration\") as duration FROM LAS2PEERMON.MESSAGE WHERE EVENT = 'SERVICE_CUSTOM_MESSAGE_40' AND REMARKS->\"$.duration\"<300 GROUP BY  REMARKS->\"$.url\" ", "GOOGLEBARCHART"))

# CSV: { ID: 0, STRING: 'csv' },
# JSON: { ID: 1, STRING: 'JSON' },
# HTMLTABLE: { ID: 2, STRING: 'htmltable' },
# XML: { ID: 3, STRING: 'xml' },
# GOOGLEPIECHART: { ID: 4, STRING: 'googlepiechart' },
# GOOGLEBARCHART: { ID: 5, STRING: 'googlebarchart' },
# GOOGLELINECHART: { ID: 6, STRING: 'googlelinechart' },
# GOOGLETIMELINECHART: { ID: 7, STRING: 'googletimelinechart' },
# GOOGLERADARCHART: { ID: 8, STRING: 'googleradarchart' },
# GOOGLETABLE: { ID: 9, STRING: 'googletable' },
