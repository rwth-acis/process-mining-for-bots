from flask import Blueprint,current_app
from utils.bot.parser import get_parser
from utils.requests import fetch_event_log,fetch_bot_model
from enhancement.main import enhance_bot_model,intent_confidence,case_durations

bot_resource = Blueprint('dynamic_resource', __name__)

@bot_resource.route('/<botName>/enhanced-bot-model')
def enhanced_bot_model(botName):
    bot_model_json = fetch_bot_model(botName)
    bot_parser = get_parser(bot_model_json)
    event_log = fetch_event_log(botName)
    bot_model_dfg, start_activities, end_activities = bot_parser.get_dfg()
    bot_model_dfg = enhance_bot_model(event_log, bot_model_dfg,bot_parser)
    return {
        
            "graph":bot_model_dfg,
            "start_activities":start_activities,
            "end_activities":end_activities
    }

@bot_resource.route('/<botName>/intent-confidence')
def get_intent_confidence(botName):
    return intent_confidence(botName,current_app.db_connection)

@bot_resource.route('/<botName>/case-durations')
def get_case_durations(botName):
    event_log = fetch_event_log(botName)
    return case_durations(event_log)