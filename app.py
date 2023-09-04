from flask import Flask
import os
from db_utils import get_db_connection
from enhancement import enhance_bot_model,get_intent_confidence
from bot_parser import get_bot_parser, BotParser
from utilities import fetch_event_log,fetch_bot_model

try:
    import psutil

    parent_pid = os.getpid()
    parent_name = str(psutil.Process(parent_pid).name())
except psutil.NoSuchProcess:
    print("No such process")
    parent_name = "unknown"
import pm4py


# current directory
current_dir = os.path.dirname(os.path.realpath(__file__))
# load environment variables
from dotenv import load_dotenv
load_dotenv(dotenv_path=current_dir+'/.env')

mysql_user = os.environ['MYSQL_USER']
mysql_password = os.environ['MYSQL_PASSWORD']
mysql_host = os.environ['MYSQL_HOST']
mysql_db = os.environ['MYSQL_DB']
mysql_port = os.environ['MYSQL_PORT']

db_connection = get_db_connection(mysql_host,mysql_port, mysql_user, mysql_password, mysql_db)


app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello, World!'

@app.route('/<botName>/enhanced-bot-model')
def enhanced_bot_model(botName):
    bot_model_json = fetch_bot_model(botName)
    bot_parser = get_bot_parser(bot_model_json)
    event_log = fetch_event_log(botName)
    bot_model_dfg, start_activities, end_activities = bot_parser.get_dfg()
    bot_model_dfg = enhance_bot_model(event_log, bot_model_dfg,bot_parser)
    intent_confidence = get_intent_confidence(botName,db_connection)
    return {
        "dfg":{
            "graph":bot_model_dfg,
            "start_activities":start_activities,
            "end_activities":end_activities
        },
        "intent_confidence": intent_confidence
    }


if __name__ == '__main__':
    app.run(debug=True)