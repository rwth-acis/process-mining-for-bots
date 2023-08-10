import pandas as pd
import json
from pm4py.algo.discovery.alpha.algorithm import apply_dfg
from pm4py.write import write_pnml
from pm4py .convert import convert_to_petri_net
from pm4py import view_petri_net
file_name = "model_test.json"
node_types_of_interest = ['Incoming Message', 'Bot Action', 'Messenger']
edge_types_of_interest = ['leadsTo','uses','generates']

def extract_function_name(node):
    """
    Extracts the function name from the node
    :param node: the node
    :return: the function name

    :example:
    >>> function_name = extract_function_name(node)
    """
    for attr in node['attributes'].values():
        if attr['name'] == 'Function Name':
            return attr['value']['value']

def extract_intent_keyword(node_id,node,edges):
    """
    Extracts the intent keyword from the node. If the intent keyword is empty, it is extracted from the ingoing edge of the node instead.
    :param node_id: the id of the node
    :param node: the node
    :param edges: the edges of the bot model
    :return: the intent keyword

    :example:
    >>> intent_keyword = extract_intent_keyword("n1", node, edges)
    """
    intent_keyword = None
    # find the intent keyword
    for attr in node['attributes'].values():
        if attr['name'] == 'Intent Keyword':
            intent_keyword=attr['value']['value']
            if intent_keyword != "" and intent_keyword is not None:
                return intent_keyword
    
        # sometimes the intent keyword is empty and stored in the ingoing edge of the node instead
        for edge in edges.values():
            if edge['target'] == node_id:
                intent_keyword = edge['label']['value']['value']
                if intent_keyword != "" and intent_keyword is not None:
                    return intent_keyword
    return "empty_intent"

def extract_activity_name(node_id,node,edges):
    """
    Extracts the activity name from the node. If the activity name is empty, it is extracted from the ingoing edge of the node instead.
    :param node_id: the id of the node
    :param node: the node
    :param edges: the edges of the bot model
    :return: the activity name

    :example:
    >>> activity_name = extract_activity_name("n1", node, edges)
    """
    if node['type'] == 'Incoming Message':
        return extract_intent_keyword(node_id,node,edges)
    elif node['type'] == 'Bot Action':
        return extract_function_name(node)
    return "empty_activity"

def to_petri_net(json):
    """
    Converts a bot model to a petri net
    :param json: the bot model
    :return: the petri net with initial and final markings
    
    :example:
    >>> petri_net,im,fm = to_petri_net(json)
    """
    # dependency matrix
    nodes = json['nodes']
    edges = json['edges']

    original_edges = edges.copy()


    known_node_names = {} # used to check for duplicate activity names
    rename_count = {} # used to rename duplicate activity names

    start_activities = set()

    dfg = {}

    edges_to_remove = set()

    # find patterns of the form A -> Bot Action and A -> Incoming Message and replace them with A -> Bot Action -> Incoming Message
    for edge_id,edge in edges.items():
        if edge['type'] == 'uses' and nodes[edge['target']]['type'] == 'Bot Action': # A -> Bot Action
            source_id = edge['source']
            target_id = edge['target']
            if (source_id,target_id) not in dfg: # if the edge is not in the dfg, add it
                dfg[(source_id,target_id)] = 0
            dfg[(source_id,target_id)] += 1
            edges_to_remove.add(edge_id)
            
            for edge2_id,edge2 in edges.items():
                if edge2['type'] == 'leadsTo' and edge2['source'] == edge['source']: # A -> Incoming Message
                    
                    # create Bot Action -> Incoming Message
                    source_id = edge['target'] # Bot Action
                    target_id = edge2['target'] # Incoming Message
                    
                    if (source_id,target_id) not in dfg:
                        dfg[(source_id,target_id)] = 0
                    dfg[(source_id,target_id)] += 1
                    # remove the leadsTo edge
                    edges_to_remove.add(edge2_id)

    # remove all edges that are leadsTo and are connected to the source of the uses edge
    for edge_id in edges_to_remove:
        edges.pop(edge_id)

    
    for edge in edges.values():
        if edge['type'] not in edge_types_of_interest:
                continue
        source_id = edge['source']
        target_id = edge['target']
        
        if nodes[source_id]['type'] not in node_types_of_interest or nodes[target_id]['type'] not in node_types_of_interest:
            continue

        if nodes[source_id]['type'] == 'Messenger':
            start_activities.add(target_id)
            continue

    
        if (source_id,target_id) not in dfg:
            dfg[(source_id,target_id)] = 0
        dfg[(source_id,target_id)] += 1

   

    end_activities = set()
    # find end activities which are nodes with no outgoing edge
    for node_id,node in nodes.items():
        if node['type'] not in node_types_of_interest:
            continue
        has_outgoing_edge = False
        for source,target in dfg.keys():
            if source == node_id and edge['type'] in edge_types_of_interest:
                has_outgoing_edge = True
                break
        if not has_outgoing_edge:
            end_activities.add(node_id)
        
    net, im,fm = convert_to_petri_net(dfg,start_activities,end_activities)


    # replace the ids with the activity names
    for node_id,node in nodes.items():
        if node['type'] not in node_types_of_interest:
            continue
        name = extract_activity_name(node_id,node,original_edges)
        
        for t in net.transitions:
            if node_id == t._Transition__label:
                if name == "empty_intent":
                    t._Transition__label = None
                else:
                    t._Transition__label = name
    
    return net,im,fm



if __name__ == "__main__":
    # import test_model.json
   

    # import test_model.json
    with open(file_name) as json_file:
        #load the json file
        json = json.load(json_file)

    net,im,fm = to_petri_net(json)

    view_petri_net(net, im, fm)
    write_pnml(net, im,fm,"test_model.pnml")
    
