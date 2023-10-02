from flask import Flask,request
import os
from utils.db.connection import get_connection
from utils import api_requests
from bot_blueprint import bot_resource
from flasgger import Swagger
from flask_cors import CORS
import logging

try: # sometimes psutil is not working on M1 Macs
    import psutil

    parent_pid = os.getpid()
    parent_name = str(psutil.Process(parent_pid).name())
except psutil.NoSuchProcess:
    print("No such process")
    parent_name = "unknown"


# current directory
current_dir = os.path.dirname(os.path.realpath(__file__))
# load environment variables
from dotenv import load_dotenv
load_dotenv(dotenv_path=current_dir+'/.env')

mysql_user = os.environ.get('MYSQL_USER', 'root')
mysql_password = os.environ.get('MYSQL_PASSWORD', 'root')
mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
mysql_events_db = os.environ.get('MYSQL_EVENTS_DB', 'LAS2PEERMON')
mysql_port = os.environ.get('MYSQL_PORT', '3306')

db_connection = get_connection(mysql_host,mysql_port, mysql_user, mysql_password, mysql_events_db)

app = Flask(__name__)
# Configure logging
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.DEBUG, format=log_format ,filename='app.log')

# Define a logger
logger = logging.getLogger(__name__)
origins = list(os.environ['CORS_ORIGIN'])  if 'CORS_ORIGIN' in os.environ else ['http://localhost:8082']
# add cors origin 
if 'DEVELOPMENT_MODE' in os.environ:
    CORS(app) 
else:
    CORS(app, origins=origins)
swagger = Swagger(app)
app.db_connection = db_connection
app.bot_manager_url = os.environ.get('SOCIAL_BOT_MANAGER_ENDPOINT', 'http://localhost:8080/SBFManager')
app.event_log_url = os.environ.get('EVENT_LOG_ENDPOINT', 'http://localhost:8087')
app.success_model_url = os.environ.get('SUCCESS_MODEL_ENDPOINT', 'http://localhost:8080/mobsos-success-modeling/apiv2')
app.default_bot_pw = os.environ.get('DEFAULT_BOT_PASSWORD', '123456')
app.contact_service_url = os.environ.get('CONTACT_SERVICE_URL', 'http://localhost:8080/contactservice')
app.swagger = swagger
app.register_blueprint(bot_resource, url_prefix='/bot')

@app.route('/')
def index():
    """
    A simple hello world endpoint
    ---
    responses:
      200:
        description: A simple hello world message
        schema:
          type: string
    """
    return 'Hello World!'

@app.route("/services")
def getL2PServices():
    return api_requests.fetchL2PServices(request.args['services-endpoint'])

if __name__ == '__main__':
    app.run(debug=True,port=8088)
    file_handler = logging.FileHandler('app.log')
    file_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(file_handler)
