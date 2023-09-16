from flask import Blueprint, current_app, request
from flasgger import Swagger, swag_from
from utils.bot.parser import get_parser
from utils.requests import fetch_event_log, fetch_bot_model
from enhancement.main import enhance_bot_model, average_intent_confidence, case_durations
import pm4py

bot_resource = Blueprint('dynamic_resource', __name__)


@bot_resource.route('/<botName>/enhanced-model')
@swag_from('enhanced-model.yml')
def enhanced_bot_model(botName):
    # check if ?url=<url> is set
    if 'bot-manager-url' in request.args:
        bot_manager_url = request.args['bot-manager-url']
    else:
        bot_manager_url = current_app.bot_manager_url

    if 'event-log-url' in request.args:
        event_log_url = request.args['event-log-url']
    else:
        event_log_url = current_app.event_log_url
    try:
        bot_model_json = fetch_bot_model(botName, bot_manager_url)
    except Exception as e:
        print(e)
        return {
            "error": f"Could not fetch bot model from {bot_manager_url}, make sure the service is running and the bot name is correct"
        }, 500

    if bot_model_json is None:
        print("Could not fetch bot model")
        return {
            "error": f"Could not fetch bot model from {bot_manager_url}"
        }, 500
    bot_parser = get_parser(bot_model_json)
    event_log = fetch_event_log(botName, event_log_url)
    bot_model_dfg, start_activities, end_activities, performance = enhance_bot_model(
        event_log, bot_parser)
    # serialize the bot model
    edges = []
    nodes = []
    avg_confidence_df = average_intent_confidence(
        botName, current_app.db_connection)
    avg_confidence = {}
    for _, row in avg_confidence_df.iterrows():
        avg_confidence[row['intentKeyword']] = row['averageConfidence']

    
    for edge in bot_model_dfg.keys():
        source_label = bot_parser.id_name_map[edge[0]]
        target_label = bot_parser.id_name_map[edge[1]]
        edges.append({
            "source": edge[0],
            "target": edge[1],
            "performance": performance[(source_label, target_label)] if (source_label, target_label) in performance else None
        })

        if edge[0] not in nodes:
            nodes.append({"id": edge[0], "label": source_label,
                         "avg_confidence": avg_confidence[source_label] if source_label in avg_confidence else None})
        if edge[1] not in nodes:
            nodes.append({"id": edge[1], "label": target_label,
                         "avg_confidence": avg_confidence[target_label] if target_label in avg_confidence else None})

    res = {
        "graph": {
            "nodes": nodes,
            "edges": edges
        },
        "start_activities": list(start_activities),
        "end_activities": list(end_activities),
        "confidence": avg_confidence
    }
    print("sending response", res)
    return res


@bot_resource.route('/<botName>/intent-confidence')
def get_intent_confidence(botName):
    return average_intent_confidence(botName, current_app.db_connection)


@bot_resource.route('/<botName>/case-durations')
def get_case_durations(botName):
    event_log = fetch_event_log(botName)
    return case_durations(event_log)
