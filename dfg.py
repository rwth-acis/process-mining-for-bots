import pandas as pd
import json

node_types_of_interest = ['Incoming Message', 'Bot Action']
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


def create_transition(parent_element, transition_id,transition_name="empty_intent"):
    """
    Creates a transition element in the PNML file
    :param parent_element: the parent element of the transition 
    :param transition_id: the id of the transition
    :return: the transition element
    
    :example:
    >>> transition = create_transition(net_page, "t1", "transition1")
    <transition id="t1">
        <name>
            <text>transition1</text>
        </name>
    </transition>
    """
    transition = ET.SubElement(parent_element, "transition")
    transition.set("id", transition_id)
    name = ET.SubElement(transition, "name")
    text = ET.SubElement(name, "text")
    text.text = transition_name
    if transition_name == "empty_intent":
        toolspecific = ET.SubElement(transition, "toolspecific")
        toolspecific.set("tool", "ProM")
        toolspecific.set("version", "6.4")
        toolspecific.set("activity", "$invisible$")
        toolspecific.set("localNodeID", transition_id)
    return transition

def create_place(parent_element, place_id, isInitialMarking = False):
    """
    Creates a place element in the PNML file
    :param parent_element: the parent element of the place
    :param place_id: the id of the place
    :param isInitialMarking: whether the place is an initial marking
    :return: the place element
    
    :example:
    >>> place = create_place(net_page, "id1")
    <place id="id1">
        <name>
            <text>id1</text>
        </name>
    </place>
    """
    place = ET.SubElement(parent_element, "place")
    place.set("id", place_id)
    name = ET.SubElement(place, "name")
    text = ET.SubElement(name, "text")
    text.text = place_id
    if isInitialMarking:
        initialMarking = ET.SubElement(place, "initialMarking")
        text = ET.SubElement(initialMarking, "text")
        text.text = "1"
    return place

def create_arc(parent_element, arc_id, source_id, target_id):
    """
    Creates an arc element in the PNML file
    :param parent_element: the parent element of the arc
    :param arc_id: the id of the arc
    :param source_id: the id of the source of the arc
    :param target_id: the id of the target of the arc
    :return: the arc element
    
    :example:
    >>> arc = create_arc(net_page, "a1", "t1", "p1")
    <arc id="a1" source="t1" target="p1">
    </arc>
    """
    arc = ET.SubElement(parent_element, "arc")
    arc.set("id", arc_id)
    arc.set("source", source_id)
    arc.set("target", target_id)
    return arc



if __name__ == "__main__":
    # import test_model.json
   

    # import test_model.json
    with open('test_model.json') as json_file:
        #load the json file
        json = json.load(json_file)

    # dependency matrix
    nodes = json['nodes']
    edges = json['edges']

    # create a dependency matrix as pandas dataframe 
    df = pd.DataFrame(columns = nodes.keys(), index = nodes.keys())

    for node_id in nodes.keys():
        if nodes[node_id]['type'] not in node_types_of_interest:
            continue
        df[node_id] = "#"
        df.loc[node_id] = "#" 

    # fill the upper right triangle of the dependency matrix
    #     -> means source_id depends on target_id
    #     || means source_id depends on target_id and target_id depends on source_id
    #     <- means target_id depends on source_id
    #     # means no dependency

    for edge in edges.values():
        if edge['type'] not in edge_types_of_interest:
                continue
        source_id = edge['source']
        target_id = edge['target']
        # get row and column index of the dependency matrix
        row_index = list(nodes.keys()).index(source_id)
        column_index = list(nodes.keys()).index(target_id)
        # fill the upper right triangle of the dependency matrix
        if row_index < column_index:
            if df.loc[source_id, target_id] == "#" and df.loc[target_id, source_id] == "#":
                df.loc[source_id, target_id] = "->"
            elif df.loc[target_id, source_id] == "->":
                df.loc[source_id, target_id] = "||"

    # fill the lower left triangle of the dependency matrix
    # will be symmetric to the upper right triangle
    for row_index in range(len(nodes.keys())):
        for column_index in range(len(nodes.keys())):
            if row_index < column_index:
                if df.iloc[row_index, column_index] == "->":
                    df.iloc[column_index, row_index] = "<-"
                else :
                    df.iloc[column_index, row_index] = df.iloc[row_index, column_index]
    
    # set of nodes that are not connected to any other node

    T_L = set()
    for node_id in nodes.keys():
        if nodes[node_id]['type'] not in node_types_of_interest:
            continue
        T_L.add(node_id)

    
        
    # print the dependency matrix
