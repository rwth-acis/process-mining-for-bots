import pm4py

def conformance( event_log, net, im, fm):
    fitness = pm4py.conformance.fitness_alignments(event_log,net,im,fm)
    precision=pm4py.conformance.precision_alignments(event_log,net,im,fm)
    return {
        "fitness":fitness,
        "precision":precision,
    }

def find_unfitting_traces(event_log, net, im, fm):
    diagnostics = pm4py.conformance.conformance_diagnostics_alignments(event_log,net,im,fm)
    unfitting = list(trace for trace in diagnostics if trace['fitness'] < 1)
    return unfitting
