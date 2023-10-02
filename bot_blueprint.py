from flask import Blueprint, current_app, request
from flasgger import swag_from
from utils.bot.parse_lib import get_parser
from utils.api_requests import fetch_event_log, fetch_bot_model, fetch_success_model, fetchL2PGroups
from enhancement.main import repair_petri_net, enhance_bot_model, average_intent_confidence, case_durations
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.visualization.dfg import visualizer as dfg_visualizer
import math

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
    res_format = request.args.get('format', 'json')
    try:
        bot_model_json = fetch_bot_model(botName, bot_manager_url)
        if bot_model_json is None:
            print(f"Could not fetch bot model from {bot_manager_url}")
            return {
                "error": f"Could not fetch bot model from {bot_manager_url}"
            }, 500
    except Exception as e:
        print(e)
        return {
            "error": f"Could not fetch bot model from {bot_manager_url}, make sure the service is running and the bot name is correct"
        }, 500

    try:

        event_log = fetch_event_log(botName, event_log_url)
        if event_log is None:
            print(f"Could not fetch event log from {event_log_url}")
            return {
                "error": f"Could not fetch event log from {event_log_url}"
            }, 500
    except Exception as e:
        print(e)
        return {
            "error": f"Could not fetch event log from {event_log_url}, make sure the service is running and the bot name is correct"
        }, 500

    bot_parser = get_parser(bot_model_json)

    bot_model_dfg, start_activities, end_activities, performance = enhance_bot_model(
        event_log, bot_parser)
    if res_format == 'svg':
        gviz = dfg_visualizer.apply(bot_model_dfg)
        return gviz.pipe(format='svg').decode('utf-8')

    return serialize_response(
        bot_model_dfg, bot_parser, start_activities, end_activities, performance, botName)


@bot_resource.route('/<botName>/petri-net')
def get_petri_net(botName):
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
    net,im,fm =  bot_parser.to_petri_net()
    net, im, fm = repair_petri_net(event_log,net,im,fm)
    gviz = pn_visualizer.apply(
        net, im, fm, variant=pn_visualizer.Variants.PERFORMANCE)
    return gviz.pipe(format='svg').decode('utf-8')


@bot_resource.route('/<botName>/intent-confidence')
def get_intent_confidence(botName):
    return average_intent_confidence(botName, current_app.db_connection)


@bot_resource.route('/<botName>/case-durations')
def get_case_durations(botName):
    event_log = fetch_event_log(botName)
    return case_durations(event_log)


@bot_resource.route('/<botName>/success-model')
def get_success_model(botName):
    group_id = request.args.get('group-id', current_app.default_group_id)
    service_id = request.args.get('service-id', current_app.default_service_id)
    return fetch_success_model(current_app.success_model_url, botName, current_app.default_bot_pw, group_id, service_id)


@bot_resource.route('/<botName>/groups')
def get_groups(botName):
    """
    Fetches the groups that the bot is assigned to from the contact service
    """
    return fetchL2PGroups(current_app.contact_service_url, botName, current_app.default_bot_pw)

def serialize_response( bot_model_dfg, bot_parser, start_activities, end_activities, performance, botName):
    try:
    # serialize the bot model
        edges = []
        nodes = []
        avg_confidence_df = average_intent_confidence(
            botName, current_app.db_connection)
        avg_confidence = {}
        for _, row in avg_confidence_df.iterrows():
            if row['intentKeyword'] in avg_confidence:
                avg_confidence[row['intentKeyword']
                            ] = row['averageConfidence'] if row['averageConfidence'] != math.nan else 0
        for edge in bot_model_dfg.keys():
            source_label = bot_parser.id_name_map[edge[0]] if edge[0] in bot_parser.id_name_map else edge[0]
            target_label = bot_parser.id_name_map[edge[1]] if edge[1] in bot_parser.id_name_map else edge[1]
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
            "confidence": avg_confidence,
            "names": bot_parser.id_name_map
        }

        return res
    except Exception as e:
        print("Exception: ", e)
        return None