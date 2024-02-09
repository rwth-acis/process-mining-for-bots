import pm4py
    
def discover_petri_net(event_log,algorithm="inductive"):
    """
    discover a petri net from an event log

    Parameters
    ----------
    event_log : pm4py event log
        event log to discover the petri net from
    algorithm : str, optional
        algorithm to use for petri net discovery. The default is "inductive".

    Returns
    -------
    petri_net : pm4py petri net
        discovered petri net
    im : initial marking
        initial marking of the petri net
    fm : final marking
        final marking of the petri net
    """
    if algorithm == "inductive":
        return pm4py.discover_petri_net_inductive(event_log)
    elif algorithm == "heuristic":
        return pm4py.discover_petri_net_heuristics(event_log)
    elif algorithm == "ilp":
        return pm4py.discover_petri_net_ilp(event_log)
    else:
        return pm4py.discover_petri_net_alpha(event_log)
    
def discover_dfg(event_log):
    """
    discover a direct follow graph from an event log

    Parameters
    ----------
    event_log : pm4py event log
        event log to discover the dfg from

    Returns
    -------
    dfg : pm4py dfg
        discovered dfg
    start_activities : list
        list of start activities
    end_activities : list
        list of end activities
    """
    return pm4py.discover_dfg(event_log)

def discover_process_tree(event_log):
    """
    discover a process tree from an event log

    Parameters
    ----------
    event_log : pm4py event log
        event log to discover the process tree from

    Returns
    -------
    process_tree : pm4py process tree
        discovered process tree
    """
    return pm4py.discover_process_tree_inductive(event_log)

def discover_bpmn(event_log):
    """
    discover a bpmn from an event log

    Returns
    -------
    bpmn : pm4py bpmn
        discovered bpmn
    """
    return pm4py.discover_bpmn_inductive(event_log)

def bot_statistics(event_log):
    stats = dict()
    if (event_log is None):
        return stats
    stats['numberOfConversations'] = event_log.groupby('case:concept:name').ngroups
    stats['numberOfStates'] = event_log['concept:name'].nunique()
    stats['numberOfUsers'] = event_log['user'].nunique()
    stats['averageConversationLength'] = event_log.groupby(
        'case:concept:name').size().mean()
    stats['averageConversationDuration'] = event_log.groupby(
        'case:concept:name')['time:timestamp'].apply(lambda x: x.max() - x.min()).mean().total_seconds()
    return stats