from flask import Flask
import os
from utils.db.connection import get_connection
from bot_blueprint import bot_resource
from flasgger import Swagger
from flask_cors import CORS
import logging

try:
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

mysql_user = os.environ['MYSQL_USER']
mysql_password = os.environ['MYSQL_PASSWORD']
mysql_host = os.environ['MYSQL_HOST']
mysql_events_db = os.environ['MYSQL_EVENTS_DB']
mysql_port = os.environ['MYSQL_PORT']

db_connection = get_connection(mysql_host,mysql_port, mysql_user, mysql_password, mysql_events_db)

app = Flask(__name__)
# Configure logging
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.DEBUG, format=log_format)

# Define a logger
logger = logging.getLogger(__name__)
origins = list(os.environ['CORS_ORIGIN'])  if 'CORS_ORIGIN' in os.environ else ['http://localhost:8082']
# add cors origin 
CORS(app, origins=origins) 
swagger = Swagger(app)
app.db_connection = db_connection
app.bot_manager_url = os.environ['SOCIAL_BOT_MANAGER_ENDPOINT']
app.event_log_url = os.environ['EVENT_LOG_ENDPOINT']
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

if __name__ == '__main__':
    app.run(debug=True,port=8088)
    file_handler = logging.FileHandler('app.log')
    file_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(file_handler)
