import pm4py
from utils.api_requests import fetch_event_log


def custom_trace_cost_function(log):
    """
    Defines a custom cost function for the discounted A* algorithm
    the cost function works similar to the default one, but if the log move 
    has the in-service-context attribute set to true, the cost is 0 instead of 1
    """
    df = log.copy()[['in-service-context','concept:name']]
    cost = {}
    for activity in df['concept:name'].unique():
        if activity in cost:
            continue
        if df[df['concept:name'] == activity]['in-service-context'].values[0] == "true":
            cost[activity] = 0
    return cost


def conformance( event_log, net, im, fm):
    try:
        fitness = pm4py.conformance.fitness_alignments(event_log, net, im, fm)
    except:
        fitness = None
    try:
        precision = pm4py.conformance.precision_alignments(
            event_log, net, im, fm)
    except:
        precision = None
    return {
        "fitness":fitness,
        "precision":precision,
    }

def find_unfitting_traces(event_log, net, im, fm):
    diagnostics = pm4py.conformance.conformance_diagnostics_alignments(event_log,net,im,fm)
    unfitting = list(trace for trace in diagnostics if trace['fitness'] < 1)
    return unfitting


def trace_is_fitting(trace, net, im, fm):
    from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments
    return alignments.apply_trace(trace, net, im, fm)['fitness'] == 1

