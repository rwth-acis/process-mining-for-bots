import pm4py
import uuid
import pandas as pd
import itertools
import uuid
import statistics
import numpy as np
from pm4py.statistics.traces.generic.log import case_statistics
from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments_algorithm
from pm4py.algo.conformance.alignments.petri_net.variants.state_equation_a_star import Parameters
from process_model_repair_algorithm import repair_process_model

bot_model_json_path = "./assets/models/test_bot_model.json"


def enhance_bot_model(event_log, bot_parser, repair=False):
    """
    Enhance the bot model using the event log.
    We assume that the bot model is incomplete 
    as it does not contain subprocesses which are logged when 
    the bot is communicating with an external service.
    We say that the bot is in the service context in that case.
    The event log contains the information whether we are in a service context as an additional attribute.
    :param event_log: event log
    :param bot_model_dfg: bot model as a DFG
    :return: enhanced bot model
    """
    dfg, start_activities, end_activities = bot_parser.get_dfg()  # initial dfg
    net, im, fm = bot_parser.to_petri_net()
    if repair == True:
        net, _, _ = repair_petri_net(event_log, net, im, fm)  # repair the dfg
    frequency_dfg = add_edge_frequency(event_log, dfg, start_activities,
                                       end_activities, bot_parser)  # add the edge frequency
    performance_dfg = add_edge_performance(
        event_log, dfg, start_activities, end_act=end_activities,bot_parser=bot_parser)  # add the edge performance
    # performance = pm4py.discovery.discover_performance_dfg(event_log)
    # frequency = pm4py.discovery.discover_dfg(event_log)
    # replace NaN values with None
    # performance = __replace_nan_with_null(performance[0])
    return dfg, start_activities, end_activities, frequency_dfg, performance_dfg


def repair_petri_net(event_log, net, im, fm):
    """
    Repair the bot model using the event log.
    We assume that the bot model is incomplete 
    as it does not contain subprocesses which are logged when 
    the bot is communicating with an external service.
    We say that the bot is in the service context in that case.
    The event log contains the information whether we are in a service context as an additional attribute.
    :param event_log: event log
    :param bot_model_dfg: bot model as a DFG
    :return: enhanced bot model
    """
    net, _, _ = repair_process_model(net, im, fm, event_log)
    net = pm4py.reduce_petri_net_invisibles(net)
    net, im, fm = pm4py.reduce_petri_net_implicit_places(net, im, fm)
    # for some very weird reasons the repair function swaps the initial and final places. As a workaround we return the final marking as the initial marking and vice versa
    return net, fm, im


def add_edge_frequency(event_log, dfg, start_act, end_act, bot_parser):
    """
    Add the edge frequency to the bot model
    :param event_log: event log
    :param bot_model_dfg: bot model as a DFG
    :param start_act: start activities
    :param end_act: end activities
    :param bot_parser: bot parser
    :return: bot model with edge frequency
    """
    frequency_dfg = dfg.copy()
    net, im, fm = bot_parser.to_petri_net(frequency_dfg, start_act, end_act)
    alignments_results = alignments_algorithm.apply(event_log, net, im, fm, {
        Parameters.PARAM_ALIGNMENT_RESULT_IS_SYNC_PROD_AWARE: True})
    variants = pm4py.stats.get_variants_as_tuples(event_log)
    new_nodes = dict()  # nodes that are added to the bot model
    for alignment in list(diagnostic['alignment'] for diagnostic in alignments_results):
        log_trace = tuple(log_move[0] for model_move,
                          log_move in alignment if log_move[0] != ">>")  # trace as it is in the log
        # model_trace = tuple(
        #     log_move[1] for model_move, log_move in alignment if model_move[1] != ">>") # for debugging
        log_trace_count = variants[log_trace]
        potential_start_activities = set()
        potential_end_activities = set()

        for ((source, align_source), (target, align_target)) in itertools.pairwise(alignment):
            if (source[1] == ">>"):
                if align_source[0] in new_nodes.keys():
                    source_id = new_nodes[align_source[0]]
                else:
                    source_id = str(uuid.uuid4())
                    new_nodes[align_source[0]] = source_id
                    bot_parser.id_name_map[source_id] = align_source[0]
            else:
                source_id = source[1].split("_")[0]
            if (target[1] == ">>"):
                if align_target[0] in new_nodes.keys():
                    target_id = new_nodes[align_target[0]]
                else:
                    target_id = str(uuid.uuid4())
                    new_nodes[align_target[0]] = target_id
                    bot_parser.id_name_map[target_id] = align_target[0]
            else:
                target_id = target[1].split("_")[0]

            if (source_id, target_id) in frequency_dfg:
                frequency_dfg[(source_id, target_id)] += log_trace_count
            else:
                potential_start_activities.add(source_id)
                potential_end_activities.add(target_id)
                frequency_dfg[(source_id, target_id)] = log_trace_count

        for potential_start_activity in potential_start_activities:
            # check if the potential start activity has no incoming edge
            has_incoming_edge = False
            for _, target in frequency_dfg.keys():
                if target == potential_start_activity:
                    has_incoming_edge = True
                    break
            if not has_incoming_edge and potential_start_activity not in start_act:
                start_act.add(potential_start_activity)
        for potential_end_activity in potential_end_activities:
            # check if the potential end activity has no outgoing edge
            has_outgoing_edge = False
            for source, _ in frequency_dfg.keys():
                if source == potential_end_activity:
                    has_outgoing_edge = True
                    break
            if not has_outgoing_edge and potential_end_activity not in end_act:
                end_act.add(potential_end_activity)
    return frequency_dfg


def add_edge_performance(event_log, dfg, start_act, end_act, bot_parser):
    """
    Add the edge performance to the bot model
    :param event_log: event log
    :param bot_model_dfg: bot model as a DFG
    :param start_act: start activities
    :param end_act: end activities
    :param bot_parser: bot parser
    :return: bot model with edge frequency
    """
    performance_dfg = dfg.copy()
    net, im, fm = bot_parser.to_petri_net(performance_dfg, start_act, end_act)
    alignments_results = alignments_algorithm.apply(event_log, net, im, fm, {
        Parameters.PARAM_ALIGNMENT_RESULT_IS_SYNC_PROD_AWARE: True})
    variants = pm4py.stats.get_variants_as_tuples(event_log)
    new_nodes = dict()  # nodes that are added to the bot model
    for alignment in list(diagnostic['alignment'] for diagnostic in alignments_results):
        log_trace = tuple(log_move[0] for model_move,
                          log_move in alignment if log_move[0] != ">>")  # trace as it is in the log
        model_trace = tuple(
            log_move[1] for model_move, log_move in alignment if model_move[1] != ">>")  # for debugging
        performance = _average_performance_of_trace(
            log_trace, event_log, alignment)
        potential_start_activities = set()
        potential_end_activities = set()

        for ((source, align_source), (target, align_target)) in itertools.pairwise(alignment):
            if (source[1] == ">>"):
                if align_source[0] in new_nodes.keys():
                    source_id = new_nodes[align_source[0]]
                else:
                    source_id = str(uuid.uuid4())
                    new_nodes[align_source[0]] = source_id
                    bot_parser.id_name_map[source_id] = align_source[0]
            else:
                source_id = source[1].split("_")[0]
            if (target[1] == ">>"):
                if align_target[0] in new_nodes.keys():
                    target_id = new_nodes[align_target[0]]
                else:
                    target_id = str(uuid.uuid4())
                    new_nodes[align_target[0]] = target_id
                    bot_parser.id_name_map[target_id] = align_target[0]
            else:
                target_id = target[1].split("_")[0]

            if (source_id, target_id) in performance_dfg and performance_dfg[(source_id, target_id)] != 0:
                 performance_dfg[(source_id, target_id)] = statistics.mean([
                     performance_dfg[(source_id, target_id)], performance[(source_id, target_id)]]) if (source_id, target_id) in performance else performance_dfg[(source_id, target_id)]
            else:
                potential_start_activities.add(source_id)
                potential_end_activities.add(target_id)
                performance_dfg[(source_id, target_id)
                                ] = performance[(source_id, target_id)] if (source_id, target_id) in performance else 0

        for potential_start_activity in potential_start_activities:
            # check if the potential start activity has no incoming edge
            has_incoming_edge = False
            for _, target in performance_dfg.keys():
                if target == potential_start_activity:
                    has_incoming_edge = True
                    break
            if not has_incoming_edge and potential_start_activity not in start_act:
                start_act.add(potential_start_activity)
        for potential_end_activity in potential_end_activities:
            # check if the potential end activity has no outgoing edge
            has_outgoing_edge = False
            for source, _ in performance_dfg.keys():
                if source == potential_end_activity:
                    has_outgoing_edge = True
                    break
            if not has_outgoing_edge and potential_end_activity not in end_act:
                end_act.add(potential_end_activity)
    return performance_dfg


def _average_performance_of_trace(log_trace, event_log, alignment):
    """
    gets the average performance of a trace in the event log. For each edge in the trace, we get the average duration
    """
    cases = pm4py.filtering.filter_variants(event_log, [log_trace])
    durations = dict()
    for case in cases.groupby("case:concept:name"):
        case = case[1]
        for i in range(0, len(case) - 1):
            edge = (case.iloc[i]["concept:name"],
                    case.iloc[i + 1]["concept:name"])
            corresponding_model_ids = tuple(map(lambda x: x.split(
                "_")[0], (alignment[i][0][1], alignment[i+1][0][1])))
            if corresponding_model_ids is None:
                corresponding_model_ids = edge
            if corresponding_model_ids in durations:
                statistics.mean(
                    [durations[corresponding_model_ids], (
                        (case.iloc[i + 1]["time:timestamp"] - case.iloc[i]["time:timestamp"]).total_seconds())])
            else:
                durations[corresponding_model_ids] = (
                    (case.iloc[i + 1]["time:timestamp"] - case.iloc[i]["time:timestamp"]).total_seconds())
    return durations


def _find_trace_in_log(log_moves, log):
    """
    Find a trace in the event log
    :param log_moves: moves of the trace
    :param log: event log
    :return: trace
    """
    log = log.copy()
    # iterate over cases
    for case in log.groupby("case:concept:name"):
        # check if the case contains the moves
        if (set(log_moves).issubset(set(case[1]["concept:name"].values))):
            return case[1]
    return None


def _closest_aligned_trace(alignment, ):
    """
    Find the closest aligned trace in the event log
    :param alignment: alignment
    :param log: event log
    :return: trace
    """
    log = log.copy()
    log_moves = tuple(move[0] for move in alignment if move[0] != ">>")
    filtered_log = pm4py.filtering.filter_variants(log, [log_moves])


def average_intent_confidence(botName, connection):
    """
    Get the confidence of the intents in the bot model
    :param botName: bot name
    :param connection: database connection
    :return: confidence of intents
    """
    statement = "SELECT json_extract(REMARKS, '$.intent.intentKeyword') AS intentKeyword, AVG(json_extract(REMARKS, '$.intent.confidence')) AS averageConfidence FROM MESSAGE WHERE json_extract(REMARKS, '$.botName') = %s  GROUP BY intentKeyword;"
    df = pd.read_sql(statement, con=connection, params=(botName,))
    return df


def case_durations(log, ids=None):
    """
    Get the throughput times of the bot model
    :param botName: bot name
    :param log: event log
    :return: throughput times
    """
    stats = case_statistics.get_cases_description(log)
    if ids is None:
        ids = log["case:concept:name"].unique()

    traces = log.groupby("case:concept:name").agg(
        {'concept:name': lambda x: list(x), 'case:concept:name': 'first'})
    # add the traces to the case stats
    for case_id, trace in traces.iterrows():
        if case_id in ids:
            stats[case_id]['trace'] = trace['concept:name']
    return stats


def __replace_nan_with_null(obj):
    """
    Replace NaN values with null
    :param obj: dictionary
    :return: dictionary
    """
    # Recursively replace nan values with null
    def replace_nan(obj):
        if isinstance(obj, dict):
            return {k: replace_nan(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_nan(v) for v in obj]
        elif isinstance(obj, float) and np.isnan(obj):
            return None
        else:
            return obj

    # Replace nan values with null
    obj = replace_nan(obj)

    return obj


def get_alignment_for_variant(variant, alignments_results):
    """
    Get the alignment for a variant
    :param variant: variant
    :param alignments_results: alignments results
    :return: alignment
    """
    for alignment in alignments_results:
        log_trace = tuple(label_align[0] for model_move,
                          label_align in alignment['alignment'] if label_align[0] != ">>")
        if log_trace == variant:
            return alignment
    return None


# # debug
# import sys
# import os

# # Add parent folder to Python path
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# # Rest of your code
# from utils.bot.parse_lib import get_parser
# from utils.api_requests import load_default_bot_model,get_default_event_log
# if __name__ == "__main__":

#     event_log = get_default_event_log()
#     # test if time:timestamp is a datetime
#     # make time:timestamp to datetime
#     event_log['time:timestamp'] = pd.to_datetime(event_log['time:timestamp'],utc=True)
#     bot_model_json = load_default_bot_model()
#     bot_parser = get_parser(bot_model_json)
#     dfg,start,end, p = enhance_bot_model(event_log,bot_parser)
#     pm4py.view_dfg(dfg, start_activities=start, end_activities=end)
#     # pm4py.view_petri_net(net,im,fm)


# def repair_bot_model(event_log, bot_parser, bot_model_dfg, start_activities, end_activities):
#     """
#     Enhance the bot model using the event log.
#     We assume that the bot model is incomplete
#     as it does not contain subprocesses which are logged when
#     the bot is communicating with an external service.
#     We say that the bot is in the service context in that case.
#     The event log contains the information whether we are in a service context as an additional attribute.
#     :param event_log: event log
#     :param bot_parser: bot parser
#     :param bot_model_dfg: bot model as a DFG
#     :param start_activities: start activities
#     :param end_activities: end activities
#     :return: enhanced bot model
#     """
#     net, im, fm = bot_parser.to_petri_net(bot_model_dfg, start_activities, end_activities)
#     alignments = list(a['alignment'] for a in pm4py.conformance.conformance_diagnostics_alignments(
#         event_log, net, im, fm))

#     for alignment in alignments:
#         log_moves = list(move[0] for move in alignment if move[0] != ">>")
#         # search for this trace in the event_log
#         trace_in_log = _find_trace_in_log(log_moves, event_log)
#         trace_in_log['in-service-context'] = trace_in_log['in-service-context'].fillna(
#             False)

#         tmp = None
#         anchor = None
#         potential_start_activities = set()
#         potential_end_activities = set()

#         # iterate over the trace and find subprocesses that are in the service context
#         for _, row in trace_in_log.iterrows():
#             if tmp != None and row["in-service-context"] == True:
#                 # extend the chain with tmp->row['concept:name']
#                 new_id = str(uuid.uuid4())
#                 bot_parser.add_name(new_id, row['concept:name'])
#                 bot_model_dfg[(anchor['id'], new_id)] = 0
#                 potential_start_activities.add(anchor['id'])
#                 tmp = {'name': row['concept:name'], 'id': new_id}
#             elif tmp != None and row["in-service-context"] == False:
#                 # create a path back to anchor
#                 bot_model_dfg[(tmp['id'], anchor['id'])] = 0
#                 anchor = None
#                 tmp = None

#             if row['EVENT'] == "SERVICE_REQUEST":
#                 anchor = {'name': row['concept:name'], 'id': bot_parser.get_node_id_by_name(
#                     row['concept:name'])}  # defines the (potential) start of a subprocess

#                 tmp = anchor.copy()
#             if tmp!= None:
#                 potential_end_activities.add(tmp['id'])

#         for potential_start_activity in potential_start_activities:
#             # check if the potential start activity has no incoming edge
#             has_incoming_edge = False
#             for _, target in bot_model_dfg.keys():
#                 if target == potential_start_activity:
#                     has_incoming_edge = True
#                     break
#             if not has_incoming_edge and potential_start_activity not in start_activities:
#                 start_activities.add(potential_start_activity)
#         for potential_end_activity in potential_end_activities:
#             # check if the potential end activity has no outgoing edge
#             has_outgoing_edge = False
#             for source, _ in bot_model_dfg.keys():
#                 if source == potential_end_activity:
#                     has_outgoing_edge = True
#                     break
#             if not has_outgoing_edge and potential_end_activity not in end_activities:
#                 end_activities.add(potential_end_activity)

#     return bot_model_dfg, start_activities, end_activities
