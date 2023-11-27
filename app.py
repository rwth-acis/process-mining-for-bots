from dotenv import load_dotenv
from flask import Flask, request
import os
from utils.db.connection import get_connection
from utils import api_requests
from bot_blueprint import bot_resource
from flasgger import Swagger
from flask_cors import CORS
import logging

try:  # sometimes psutil is not working on M1 Macs
    import psutil

    parent_pid = os.getpid()
    parent_name = str(psutil.Process(parent_pid).name())
except psutil.NoSuchProcess:
    print("No such process")
    parent_name = "unknown"

# current directory
current_dir = os.path.dirname(os.path.realpath(__file__))
# load environment variables
load_dotenv(dotenv_path=current_dir+'/.env')

mysql_user = os.environ.get('MYSQL_USER', 'root')
mysql_password = os.environ.get('MYSQL_PASSWORD', 'root')
mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
mysql_events_db = os.environ.get('MYSQL_EVENTS_DB', 'LAS2PEERMON')
mysql_port = os.environ.get('MYSQL_PORT', '3306')

db_connection = get_connection(
    mysql_host, mysql_port, mysql_user, mysql_password, mysql_events_db)

app = Flask(__name__)
app.openai_key = os.environ.get('OPENAI_API_KEY', '123456')

# Define a logger
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.DEBUG, format=log_format, filename='app.log')
logger = logging.getLogger(__name__)

# add cors origin
CORS(app, resources={r"/*": {"origins": "http://localhost:8082"}}, origins="http://localhost:8082", supports_credentials=True,
     allow_headers=('Content-Type', 'Authorization', 'Access-Control-Allow-Origin', 'Access-Control-Allow-Headers', 'Access-Control-Allow-Methods'))

swagger = Swagger(app)

app.db_connection = db_connection
app.default_bot_pw = os.environ.get('DEFAULT_BOT_PASSWORD', '123456')
app.default_group_id = "343da947a6db1296fadb5eca3987bf71f2e36a6d088e224a006f4e20e6e7935bb0d5ce0c13ada9966228f86ea7cc2cf3a1435827a48329f46b0e3963213123e0"
app.default_service_id = "i5.las2peer.services.mensaService.MensaService"

app.swagger = swagger
app.logger = logger
app.register_blueprint(bot_resource, url_prefix='/bot')


@app.route("/services")
def getL2PServices():
    return api_requests.fetchL2PServices(request.args['services-endpoint'])


if __name__ == '__main__':
    app.run(debug=True, port=8088)
    file_handler = logging.FileHandler('app.log')
    file_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(file_handler)
