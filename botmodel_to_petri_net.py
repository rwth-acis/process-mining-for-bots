import pandas as pd
import json
from pm4py.algo.discovery.alpha.algorithm import apply_dfg
from pm4py.write import write_pnml
from pm4py .convert import convert_to_petri_net
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

if __name__ == "__main__":
    # import test_model.json
   

    # import test_model.json
    with open(file_name) as json_file:
        #load the json file
        json = json.load(json_file)

    # dependency matrix
    nodes = json['nodes']
    edges = json['edges']

    node_renames = {} # in case of duplicate activity names, rename the node to avoid loops in the petri net that are not loops in the bot model
    rename_count = {} # shows for each renaming how many times it has been done

    start_activities = set()

    dfg = {}
    for edge in edges.values():
        if edge['type'] not in edge_types_of_interest:
                continue
        source_id = edge['source']
        target_id = edge['target']
        
        if nodes[source_id]['type'] not in node_types_of_interest or nodes[target_id]['type'] not in node_types_of_interest:
            continue

        if nodes[source_id]['type'] == 'Messenger':
            start_activities.add(extract_activity_name(target_id,nodes[target_id],edges))
            continue

        source_name = extract_activity_name(source_id,nodes[source_id],edges)
        target_name = extract_activity_name(target_id,nodes[target_id],edges)

        if source_name == target_name and source_id != target_id:
            if rename_count.get(source_name) is None:
                rename_count[source_name] = 1
            else:
                rename_count[source_name] += 1
            target_name = target_name + "_" + str(rename_count[source_name])
            node_renames[target_id] = target_name
    
        print(source_name, target_name)

        if (source_name,target_name) not in dfg:
            dfg[(source_name,target_name)] = 0
        dfg[(source_name,target_name)] += 1

   

    end_activities = set()
    # find end activities which are nodes with no outgoing edge
    for node_id,node in nodes.items():
        if node['type'] not in node_types_of_interest:
            continue
        has_outgoing_edge = False
        for edge in edges.values():
            if edge['source'] == node_id and edge['type'] in edge_types_of_interest:
                has_outgoing_edge = True
                break
        if not has_outgoing_edge:
            name = extract_activity_name(node_id,node,edges)
            if node_renames.get(node_id) is not None:
                name = node_renames[node_id] 
            end_activities.add(name)
    print(start_activities)
    print(end_activities)
        
    
    net, im,fm = convert_to_petri_net(dfg,start_activities,end_activities)

    write_pnml(net, im,fm,"test_model.pnml")
    
