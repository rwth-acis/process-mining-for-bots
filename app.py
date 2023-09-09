from flask import Flask
import os
from utils.db.connection import get_connection
from bot_blueprint import bot_resource
from flasgger import Swagger

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
swagger = Swagger(app)
app.db_connection = db_connection
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