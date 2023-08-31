import pm4py
from pm4py.algo.conformance.alignments.petri_net.variants.discounted_a_star import Parameters

def custom_cost_function(x):
    print(x)
    return  list(map(lambda event: 1 , x))


def conformance( event_log, net, im, fm):
    fitness = pm4py.conformance.fitness_alignments(event_log,net,im,fm)
    precision=pm4py.conformance.precision_alignments(event_log,net,im,fm)
    return {
        "fitness":fitness,
        "precision":precision,
    }

def find_unfitting_traces(event_log, net, im, fm):
    from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments
    print(alignments.apply(event_log, net, im, fm,parameters={Parameters.PARAM_TRACE_COST_FUNCTION: custom_cost_function}))
    diagnostics = pm4py.conformance.conformance_diagnostics_alignments(event_log,net,im,fm)
    unfitting = list(trace for trace in diagnostics if trace['fitness'] < 1)
    return unfitting
