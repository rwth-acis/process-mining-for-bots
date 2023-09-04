import pm4py
import os

# current directory
current_dir = os.path.dirname(os.path.realpath(__file__))
# load environment variables
from dotenv import load_dotenv
load_dotenv(dotenv_path=current_dir+'/.env')

api_key = os.environ['OPENAI_API_KEY']

def send_prompt(prompt):
    return pm4py.llm.openai_query(prompt, api_key=api_key, openai_model="gpt-3.5-turbo")

def describe_bot_model(bot_model):
    """
    Describe a bot model using GPT-3
    :param bot_model: the bot model
    :return: the description
    """
    

