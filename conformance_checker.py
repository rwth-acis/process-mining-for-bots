from bot_parser import to_petri_net
import json
import pm4py
import os
import requests
import xml.etree.ElementTree as ET

from db_utils import read_events_into_df, get_db_connection

# current directory
current_dir = os.path.dirname(os.path.realpath(__file__))
# load environment variables
from dotenv import load_dotenv
load_dotenv(dotenv_path=current_dir+'/.env')

bot_manager_endpoint = mysql_user = os.environ['SOCIAL_BOT_MANAGER_ENDPOINT']
mysql_user = os.environ['MYSQL_USER']
mysql_password = os.environ['MYSQL_PASSWORD']
mysql_host = os.environ['MYSQL_HOST']
events_database = os.environ['MYSQL_EVENTS_DB']
bots_database = os.environ['MYSQL_BOTS_DB']
mysql_port = os.environ['MYSQL_PORT']

db_connection_events = get_db_connection(mysql_host,mysql_port, mysql_user, mysql_password, events_database)
db_connection_bots = get_db_connection(mysql_host,mysql_port, mysql_user, mysql_password, bots_database)

bot_model_file_path = "./models/bot_model.json"
event_log_file_path = "event_logs/test_event_log.xes"
tmp_event_log_file_path = "event_logs/tmp_event_log.xes"


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

def fetch_bot_model(name):
    # fetches a bot model from the social bot manager. available at <base_url>/models/{name}
    request = requests.get(f"{bot_manager_endpoint}/models/{name}")
    if request.status_code == 200:
        return request.json()
    else:
        return None

def fetch_event_log(resource_id):
    # fetches an event log from the social bot manager. available at <base_url>/event_logs/{name}
    response = requests.get(f"https://mobsos.tech4comp.dbis.rwth-aachen.de/event-log/resource/{resource_id}")
    # response is xml, use pm4py to parse it
    if response.status_code == 200:
        xml = response.content
        root = ET.fromstring(xml)
        # write the xml to a file 
        with open(tmp_event_log_file_path, "wb") as f:
            f.write(xml)
        
        # read the file with pm4py and return the event log and delete the file
        return pm4py.read_xes(tmp_event_log_file_path), os.remove(tmp_event_log_file_path)
    else:
        print(response.status_code)
        return None

def get_bot_agentids(name):
    statement=f"SELECT REMARKS->>agentId FROM MESSAGE WHERE EVENT = 'SERVICE_CUSTOM_MESSAGE_3' AND REMARKS->>'botName' = '{name}' ORDER BY TIME_STAMP"
    return list(db_connection_events.execute(statement))

def conformance(name=None):
    bot_model=None
    if name==None:
        name = "MensaBot"
        bot_model=load_default_bot_model()
    else:
        bot_model=fetch_bot_model(name)
    
    if bot_model==None:
        raise ValueError(f"Bot model for {name} not found")
    botAgentIds=get_bot_agentids(name)
    if len(botAgentIds)==0:
        raise ValueError(f"Could not find any bot agent ids for {name}")
    event_log = read_events_into_df(db_connection_events,None,None,botAgentIds[0])
    net,im,fm= to_petri_net(bot_model)
    net=pm4py.reduce_petri_net_invisibles(net)
    diagnostics = pm4py.conformance.conformance_diagnostics_alignments(event_log,net,im,fm)
    fitness = pm4py.conformance.fitness_alignments(event_log,net,im,fm)
    precision=pm4py.conformance.precision_alignments(event_log,net,im,fm)
    variants=pm4py.stats.get_variants()
    return {
        "fitness":fitness,
        "precision":precision,
        "variants":variants,
        "diagnostics":diagnostics,
        "variants": variants
    }