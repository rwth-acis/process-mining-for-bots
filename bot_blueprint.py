from flask import Blueprint, current_app, request, jsonify
from flasgger import swag_from
from utils.bot.parse_lib import get_parser, extract_state_label
from utils.api_requests import fetch_event_log, fetch_bot_model, fetch_success_model, fetchL2PGroups
from enhancement.main import repair_petri_net, enhance_bot_model, average_intent_confidence, case_durations
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.visualization.dfg import visualizer as dfg_visualizer
from pm4py.visualization.bpmn import visualizer as bpmn_visualizer
from pm4py.convert import convert_to_bpmn
from discovery.main import bot_statistics
from conformance.main import conformance
import utils.llm_interface as llm
import math

bot_resource = Blueprint('dynamic_resource', __name__)


@bot_resource.route('/<botName>/enhanced-model', methods=['GET', 'POST'])
@swag_from('enhanced-model.yml')
def enhanced_bot_model(botName):

    if 'event-log-url' not in request.args:
        return {
            "error": "event-log-url parameter is missing"
        }, 400
    event_log_url = request.args['event-log-url']
    res_format = request.args.get('format', 'json')

    if request.method == 'GET':
        if 'bot-manager-url' not in request.args:
            return {
                "error": "bot-manager-url parameter is missing"
            }, 400
        bot_manager_url = request.args['bot-manager-url']
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
    else:
        bot_model_json = request.get_json().get('bot-model', None)
        if bot_model_json is None:
            return {
                "error": "bot-model parameter is missing"
            }, 400

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

    try:
        bot_parser = get_parser(bot_model_json)
        bot_model_dfg, start_activities, end_activities, performance, frequency = enhance_bot_model(
            event_log, bot_parser)
        if res_format == 'svg':
            gviz = dfg_visualizer.apply(bot_model_dfg)
            return gviz.pipe(format='svg').decode('utf-8')

        return serialize_response(
            bot_model_dfg, bot_parser, start_activities, end_activities, performance, botName, frequency[0])
    except Exception as e:
        print(e)
        return {
            "error": "Could not enhance bot model"
        }, 500


@bot_resource.route('/<botName>/petri-net', methods=['GET', 'POST'])
def get_petri_net(botName):
    if request.method == 'GET':
        if 'bot-manager-url' not in request.args:
            return {
                "error": "bot-manager-url parameter is missing"
            }, 400
        bot_manager_url = request.args['bot-manager-url']
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
    else:
        try:
            data = request.get_json()
        except Exception as e:
            return jsonify(error=str(e)), 400
        bot_model_json = data.get('bot-model', None)
        if bot_model_json is None:
            return {
                "error": "bot-model parameter is missing"
            }, 400

    bot_parser = get_parser(bot_model_json)
    if request.args.get('enhance', 'false') == 'true':
        if 'event-log-url' not in request.args:
            return {
                "error": "event-log-url parameter is missing"
            }, 400

        event_log_url = request.args['event-log-url']
        try:
            event_log = fetch_event_log(botName, event_log_url)
            if event_log is None:
                print("Could not fetch event log")
                return {
                    "error": f"Could not fetch event log from {event_log_url}"
                }, 400

        except Exception as e:
            print(e)
            return {
                "error": f"Could not fetch event log from {event_log_url}, make sure the service is running and the bot name is correct"
            }, 400

    net, im, fm = bot_parser.to_petri_net()
    if request.args.get('enhance', 'false') == 'true':
        net, _, _ = repair_petri_net(event_log, net, im, fm)

    gviz = pn_visualizer.apply(
        net, im, fm, variant=pn_visualizer.Variants.PERFORMANCE)
    return gviz.pipe(format='svg').decode('utf-8')


@bot_resource.route('/<botName>/bpmn', methods=['GET', 'POST'])
def get_bpmn(botName):
    if request.method == 'GET':
        if 'bot-manager-url' not in request.args:
            return {
                "error": "bot-manager-url parameter is missing"
            }, 400
        bot_manager_url = request.args['bot-manager-url']
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
    else:
        bot_model_json = request.get_json().get('bot-model', None)
        if bot_model_json is None:
            return {
                "error": "bot-model parameter is missing"
            }, 400
    if 'event-log-url' not in request.args:
        return {
            "error": "event-log-url parameter is missing"
        }, 400

    event_log_url = request.args['event-log-url']
    bot_parser = get_parser(bot_model_json)
    if request.args.get('enhance', 'false') == 'true':
        try:
            event_log = fetch_event_log(botName, event_log_url)
            if event_log is None:
                print("Could not fetch event log")
                return {
                    "error": f"Could not fetch event log from {event_log_url}"
                }, 400

        except Exception as e:
            print(e)
            return {
                "error": f"Could not fetch event log from {event_log_url}, make sure the service is running and the bot name is correct"
            }, 400

    net, im, fm = bot_parser.to_petri_net()
    if request.args.get('enhance', 'false') == 'true':
        net, _, _ = repair_petri_net(event_log, net, im, fm)

    bpmn_graph = convert_to_bpmn(net, im, fm)
    gviz = bpmn_visualizer.apply(bpmn_graph)
    return gviz.pipe(format='svg').decode('utf-8')


@bot_resource.route('/<botName>/intent-confidence')
def get_intent_confidence(botName):
    return average_intent_confidence(botName, current_app.db_connection)


@bot_resource.route('/<botName>/case-durations')
def get_case_durations(botName):
    event_log_generator_url = request.args.get('event-log-url', None)
    if event_log_generator_url is None:
        return {
            "error": "event-log-generator-url parameter is missing"
        }, 400
    try:
        event_log = fetch_event_log(botName, event_log_generator_url)

    except Exception as e:
        print(e)
        return {
            "error": f"Could not fetch event log from {event_log_generator_url}, make sure the service is running and the bot name is correct"
        }, 500

    event_log = fetch_event_log(botName)
    return case_durations(event_log)


@bot_resource.route('/<botName>/success-model')
def get_success_model(botName):
    group_id = request.args.get('group-id', current_app.default_group_id)
    service_id = request.args.get('service-id', current_app.default_service_id)
    success_model_url = request.args.get("success-model-url", None)
    if success_model_url is None:
        return {
            "error": "success-model-url parameter is missing"
        }, 400

    return fetch_success_model(success_model_url, botName, current_app.default_bot_pw, service_id=service_id, group_id=group_id)


@bot_resource.route('/<botName>/statistics', methods=['GET', 'POST'])
def get_bot_statistics(botName):
    """
    Fetches the statistics of the bot 
    """
    event_log_generator_url = request.args.get('event-log-url', None)
    if event_log_generator_url is None:
        return {
            "error": "event-log-generator-url parameter is missing"
        }, 400
    try:
        event_log = fetch_event_log(botName, event_log_generator_url)

    except Exception as e:
        print(e)
        return {
            "error": f"Could not fetch event log from {event_log_generator_url}, make sure the service is running and the bot name is correct"
        }, 400
    statistics = bot_statistics(event_log)

    if request.method == 'GET' and 'bot-manager-url' in request.args:

        bot_manager_url = request.args['bot-manager-url']
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
    elif request.method == 'POST':
        bot_model_json = request.get_json().get('bot-model', None)
        if bot_model_json is None:
            return {
                "error": "bot-model parameter is missing"
            }, 400
        try:

            bot_parser = get_parser(bot_model_json)
            net, im, fm = bot_parser.to_petri_net()
            conformance_results = conformance(event_log, net, im, fm)
            statistics['conformance'] = conformance_results
        except Exception as e:
            print(e)
            statistics['conformance'] = None

    return statistics


@bot_resource.route('/<botName>/groups')
def get_groups(botName):
    """
    Fetches the groups that the bot is assigned to from the contact service
    """
    contact_service_url = request.args.get('contact-service-url', None)
    if contact_service_url is None:
        return {
            "error": "contact-service-url parameter is missing"
        }, 400
    return fetchL2PGroups(contact_service_url, botName, current_app.default_bot_pw)


def serialize_response(bot_model_dfg, bot_parser, start_activities, end_activities, performance, botName, frequency_dfg):
    added_edges = set()
    try:
        # serialize the bot model
        edges = []
        nodes = []
        avg_confidence_df = average_intent_confidence(
            botName, current_app.db_connection)
        avg_confidence = {}
        for _, row in avg_confidence_df.iterrows():
            if row['intentKeyword'] is not None:
                keyword = row['intentKeyword']
                keyword = keyword.replace('"', "")
                if keyword not in avg_confidence:
                    if row['averageConfidence'] == math.nan:
                        avg_confidence[keyword] = 0
                    else:
                        avg_confidence[keyword] = row['averageConfidence']
        for edge, frequency in bot_model_dfg.items():
            source_intent = bot_parser.id_name_map[edge[0]
                                                   ] if edge[0] in bot_parser.id_name_map else None
            target_intent = bot_parser.id_name_map[edge[1]
                                                   ] if edge[1] in bot_parser.id_name_map else None
            source_label = bot_parser.id_state_map[edge[0]
                                                   ] if edge[0] in bot_parser.id_state_map else None
            target_label = bot_parser.id_state_map[edge[1]
                                                   ] if edge[1] in bot_parser.id_state_map else None
            if (edge[0], edge[1]) in added_edges:
                continue
            edges.append({
                "source": edge[0],
                "target": edge[1],
                "performance": performance[(source_label, target_label)] if (source_label, target_label) in performance else None,
                "frequency": frequency_dfg[(source_label, target_label)] if (source_label, target_label) in frequency_dfg else None,
            })
            added_edges.add((edge[0], edge[1]))

            if edge[0] not in nodes:
                nodes.append({"id": edge[0], "label": source_intent,
                              "avg_confidence": avg_confidence[source_intent] if source_intent in avg_confidence else None})
            if edge[1] not in nodes:
                nodes.append({"id": edge[1], "label": target_intent,
                              "avg_confidence": avg_confidence[target_intent] if target_intent in avg_confidence else None})

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


@bot_resource.route('/<botName>/llm/dfg-improvements', methods=['POST'])
def get_improvements_for_dfg(botName):
    api_key = request.get_json().get('openai-key', None)
    api_key = current_app.openai_key if api_key == "evaluation-lakhoune" else api_key

    openai_model = request.get_json().get('openai-model', 'gpt-3.5-turbo-16k')
    if api_key is None:
        return {
            "error": "api_key parameter is missing"
        }, 400
    event_log_generator_url = request.args.get('event-log-url', None)
    if event_log_generator_url is None:
        return {
            "error": "event-log-url parameter is missing"
        }, 400
    event_log = fetch_event_log(botName, event_log_generator_url)
    prompt = llm.recommendations_from_event_log(event_log)
    # log the prompt
    current_app.logger.info(prompt)
    try:
        content = llm.send_prompt(prompt, api_key, openai_model)
        current_app.logger.info(content)
        return content
    except Exception as e:
        current_app.logger.error(e)
        return {
            "error": "Could not send prompt to OpenAI",
            "message": e
        }, e.status_code if hasattr(e, 'status_code') else 500


@bot_resource.route('/<botName>/llm/intent-improvements', methods=['POST'])
def get_improvements_for_intents(botName):
    api_key = request.get_json().get('openai-key', None)
    api_key = current_app.openai_key if api_key == "evaluation-lakhoune" else api_key

    openai_model = request.get_json().get('openai-model', 'gpt-3.5-turbo-16k')

    if api_key is None:
        return {
            "error": "api_key parameter is missing"
        }, 400
    average_intent_confidence_df = average_intent_confidence(
        botName, current_app.db_connection)
    prompt = llm.recommendations_for_intents(average_intent_confidence_df)
    current_app.logger.info(prompt)
    try:
        content = llm.send_prompt(prompt, api_key, openai_model)
        current_app.logger.info(content)
        return content
    except Exception as e:
        current_app.logger.error(e)
        return {
            "error": "Could not send prompt to OpenAI",
            "message": e
        }, e.status_code if hasattr(e, 'status_code') else 500


@bot_resource.route('/<botName>/llm/custom-prompt', methods=['POST'])
def get_custom_improvements(botName):
    average_intent_confidence_df = None
    event_log = None
    net = None
    initial_marking = None
    final_marking = None
    openai_model = request.get_json().get('openai-model', 'gpt-3.5-turbo-16k')
    api_key = request.get_json().get('openai-key', None)
    api_key = current_app.openai_key if api_key == "evaluation-lakhoune" else api_key

    if api_key is None:
        return {
            "error": "api_key parameter is missing"
        }, 400
    inputPrompt = request.get_json().get('inputPrompt', None)
    if inputPrompt is None:
        return {
            "error": "inputPrompt parameter is missing"
        }, 400
    if ("`botModel`" in inputPrompt):
        if 'bot-manager-url' not in request.args:
            return {
                "error": "bot-manager-url parameter is missing"
            }, 400
        bot_manager_url = request.args['bot-manager-url']
        try:
            bot_model_json = fetch_bot_model(botName, bot_manager_url)
        except Exception as e:
            print(e)
            return {
                "error": f"Could not fetch bot model from {bot_manager_url}, make sure the service is running and the bot name is correct"
            }, 500
        bot_parser = get_parser(bot_model_json)
        net, initial_marking, final_marking = bot_parser.to_petri_net()
    if ("`botIntents`" in inputPrompt):
        average_intent_confidence_df = average_intent_confidence(
            botName, current_app.db_connection)
    if ("`botLog`" in inputPrompt):
        event_log_generator_url = request.args.get('event-log-url', None)
        if event_log_generator_url is None:
            return {
                "error": "event-log-url parameter is missing"
            }, 400
        event_log = fetch_event_log(botName, event_log_generator_url)

    prompt = llm.custom_prompt(inputPrompt, average_intent_confidence_df,
                               event_log, net, initial_marking, final_marking)
    current_app.logger.info(prompt)
    try:
        content = llm.send_prompt(prompt, api_key, openai_model)
        current_app.logger.info(content)
        return content
    except Exception as e:
        current_app.logger.error(e)
        return {
            "error": "Could not send prompt to OpenAI",
            "message": e
        }, e.status_code if hasattr(e, 'status_code') else 500


@bot_resource.route('/<botName>/llm/describe', methods=['POST'])
def describe_bot_model(botName):
    api_key = request.get_json().get('openai-key', None)
    api_key = current_app.openai_key if api_key == "evaluation-lakhoune" else api_key
    openai_model = request.get_json().get('openai-model', 'gpt-3.5-turbo-16k')

    if api_key is None:
        return {
            "error": "api_key parameter is missing"
        }, 400
    try:
        bot_model_json = fetch_bot_model(
            botName, current_app.default_bot_manager_url)
        bot_parser = get_parser(bot_model_json)
        net, im, fm = bot_parser.to_petri_net()
        prompt = llm.describe_bot(net, im, fm)
        current_app.logger.info(prompt)
        content = llm.send_prompt(prompt, api_key, openai_model)
        current_app.logger.info(content)
        return content
    except Exception as e:
        print(e)
        return {
            "error": "Could not describe bot model",
            "message": e
        }, 500
