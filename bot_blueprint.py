from flask import Blueprint,current_app
from flasgger import Swagger, swag_from
from utils.bot.parser import get_parser
from utils.requests import fetch_event_log,fetch_bot_model
from enhancement.main import enhance_bot_model,intent_confidence,case_durations

bot_resource = Blueprint('dynamic_resource', __name__)


@bot_resource.route('/<botName>/enhanced-model')
@swag_from('enhanced-model.yml')
def enhanced_bot_model(botName):
    bot_model_json = fetch_bot_model(botName)
    if bot_model_json is None:
        print("Could not fetch bot model")
        return {
            "error":"Could not fetch bot model"
        }
    bot_parser = get_parser(bot_model_json)
    event_log = fetch_event_log(botName)
    bot_model_dfg, start_activities, end_activities = bot_parser.get_dfg()
    bot_model_dfg = enhance_bot_model(event_log, bot_model_dfg,bot_parser)
    print("Enhanced bot model",bot_model_dfg)
    # serialize the bot model
    edges = []
    nodes = []
    for edge in bot_model_dfg.keys():
        edges.append({
            "source":edge[0],
            "target":edge[1],
            "value":bot_model_dfg[edge]
        })
        if edge[0] not in nodes:
            nodes.append(edge[0])
        if edge[1] not in nodes:
            nodes.append(edge[1])
    
    return {
        
            "graph": {
                "nodes": nodes,
                "edges": edges
            },
            "start_activities":list(start_activities),
            "end_activities":list(end_activities)
    }

@bot_resource.route('/<botName>/intent-confidence')
def get_intent_confidence(botName):
    return intent_confidence(botName,current_app.db_connection)

@bot_resource.route('/<botName>/case-durations')
def get_case_durations(botName):
    event_log = fetch_event_log(botName)
    return case_durations(event_log)