import pm4py
import uuid
import pandas as pd
import itertools
import uuid
import numpy as np
from pm4py.statistics.traces.generic.log import case_statistics
from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments_algorithm
from pm4py.algo.conformance.alignments.petri_net.variants.state_equation_a_star import Parameters

bot_model_json_path = "./assets/models/test_bot_model.json"


def enhance_bot_model(event_log, bot_parser):
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
    dfg = repair_bot_model(event_log, dfg, bot_parser)  # repair the dfg
    dfg = add_edge_frequency(event_log, dfg, start_activities,
                             end_activities, bot_parser)  # add the edge frequency
    performance = pm4py.discovery.discover_performance_dfg(event_log)
    # replace NaN values with None 
    performance = __replace_nan_with_null(performance)
    return dfg, start_activities, end_activities, performance


def repair_bot_model(event_log, bot_model_dfg, bot_parser):
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
    net, im, fm = bot_parser.to_petri_net()
    alignments = list(a['alignment'] for a in pm4py.conformance.conformance_diagnostics_alignments(
        event_log, net, im, fm))

    for alignment in alignments:
        log_moves = list(move[0] for move in alignment if move[0] != ">>")
        # search for this trace in the event_log
        trace_in_log = _find_trace_in_log(log_moves, event_log)
        trace_in_log['in-service-context'] = trace_in_log['in-service-context'].fillna(
            False)

        tmp = None
        anchor = None
        # iterate over the trace and find subprocesses that are in the service context
        for _, row in trace_in_log.iterrows():
            if tmp != None and row["in-service-context"] == True:
                # create a path tmp->row['concept:name']
                new_id = str(uuid.uuid4())
                bot_parser.add_id(new_id, row['concept:name'])
                bot_model_dfg[(anchor['id'], new_id)] = 1
                tmp = {'name': row['concept:name'], 'id': new_id}
            elif tmp != None and row["in-service-context"] == False:
                # create a path tmp->anchor
                bot_model_dfg[(tmp['id'], anchor['id'])] = 1
                anchor = None
                tmp = None
            if row['EVENT'] == "SERVICE_REQUEST":
                anchor = {'name': row['concept:name'], 'id': bot_parser.get_node_id_by_name(
                    row['concept:name'])}  # defines the (potential) start of a subprocess
                tmp = anchor.copy()
    return bot_model_dfg


def add_edge_frequency(event_log, bot_model_dfg, start_act, end_act, bot_parser):
    net, im, fm = bot_parser.to_petri_net(bot_model_dfg, start_act, end_act)
    alignments_results = alignments_algorithm.apply(event_log, net, im, fm, {
                                                  Parameters.PARAM_ALIGNMENT_RESULT_IS_SYNC_PROD_AWARE: True})
    variants = pm4py.stats.get_variants_as_tuples(event_log)
    for alignment in list(diagnostic['alignment'] for diagnostic in alignments_results):
        log_trace = tuple(log_move[0] for model_move,
                          log_move in alignment if log_move[0] != ">>")
        # model_trace = tuple(
        #     log_move[1] for model_move, log_move in alignment if model_move[1] != ">>") # for debugging
        # count the number of times this trace is in the log
        log_trace_count = variants[log_trace]

        for ((source, align_source), (target, align_target)) in itertools.pairwise(alignment):
            if (source[1] == ">>"):
                source_id = str(uuid.uuid4())
                bot_parser.id_name_map[source_id] = align_source[0]
            else:
                source_id = source[1].split("_")[0]
            if (target[1] == ">>"):
                target_id = str(uuid.uuid4())
                bot_parser.id_name_map[target_id] = align_target[0]
            else:
                target_id = target[1].split("_")[0]
            if (source_id, target_id) in bot_model_dfg:
                bot_model_dfg[(source_id, target_id)] += log_trace_count
            else:
                bot_model_dfg[(source_id, target_id)] = log_trace_count

    return bot_model_dfg


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
    print(filtered_log)


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


# Call the get_cases_description function

# import pm4py.objects.petri_net.utils.align_utils as align_utils

# def my_reconstruct_alignment(state, visited, queued, traversed, ret_tuple_as_trans_desc=True, lp_solved=0):
#     alignment = list()
#     if state.p is not None and state.t is not None:
#         parent = state.p
#         if ret_tuple_as_trans_desc:
#             alignment = [(state.t.name, state.t.label)]
#             while parent.p is not None:
#                 alignment = [(parent.t.name, parent.t.label)] + alignment
#                 parent = parent.p
#         else:
#             alignment = [state.t.label]
#             while parent.p is not None:
#                 alignment = [parent.t.label] + alignment
#                 parent = parent.p
#     return {'alignment': alignment, 'cost': state.g, 'visited_states': visited, 'queued_states': queued,
#             'traversed_arcs': traversed, 'lp_solved': lp_solved}

# align_utils.__reconstruct_alignment = my_reconstruct_alignment

# import utils.requests as r
# import utils.bot.parser as p
# log = r.get_default_event_log()
# bot_model =  r.load_default_bot_model()
# bot_parser = p.get_parser(bot_model)
# net, im, fm = bot_parser.to_petri_net()
# bot_model_dfg = bot_parser.get_dfg()[0]
# res = add_edge_frequency(log, bot_model_dfg,bot_parser)
# print(res)

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