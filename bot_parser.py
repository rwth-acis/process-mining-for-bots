import xml.etree.ElementTree as ET

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

class BotParser:
    instance = None
    l2pContext = None

    @staticmethod
    def get_instance():
        if BotParser.instance is None:
            BotParser.instance = BotParser()
        return BotParser.instance
    

    
    def bot_model_to_petri_net(self,json):
        """
        transform the bot model to a process model (petri net). For each node in the bot model, 
        we create a transition in the petri net. 
        For each outgoing edge in the bot model, we create an arc from the transition of the source node to the a place.
        For each incoming edge in the bot model, we create an arc from a place to the transition of the target node.
        If a node has multiple incoming edges, we create a place for each incoming edge. ((Need to verify))
        If a node has multiple outgoing edges, we create a place for each outgoing edge. ((Need to verify))
        :param json: the bot model in json format
        :return: the petri net in pnml format
        """

        nodes = json['nodes']
        edges = json['edges']

        root = ET.Element("pnml")
        net = ET.SubElement(root, "net")
        net.set("id", "net1")
        net.set("type", "http://www.pnml.org/version-2009/grammar/pnmlcoremodel")
        net_name = ET.SubElement(net, "name")
        net_name_text = ET.SubElement(net_name, "text")
        net_name_text.text = "Bot Model"
        net_page = ET.SubElement(net, "page")
        net_page.set("id", "n0")

        # create places similar to the alpha algorithm i.e. if A->B, A->C, then create a place p_((A), (B,C))
        
        # create the final marking
        final_markings = ET.SubElement(net, "finalmarkings")
        marking = ET.SubElement(final_markings, "marking")
        place = ET.SubElement(marking, "place")
        place.set("idref", "sink0")
        text = ET.SubElement(place, "text")
        text.text = "1"

        sink = create_place(net_page, "sink0")
        name = ET.SubElement(sink, "name")
        text = ET.SubElement(name, "text")
        text.text = "sink0"

        create_place(net_page, "initial_marking", True)

        for node_id,node in nodes.items(): 
            if node['type'] not in node_types_of_interest:
                continue

            if node['type'] == 'Incoming Message':
                intent_keyword = extract_intent_keyword(node_id,node,edges)
                create_transition(net_page, node_id, intent_keyword)

                # find the bot response
                # # comment out since the bot model does not have the bot response as separate node anymore
                # for attr in node['attributes']:
                #     if attr['name'] == 'Message':
                #         transition_bot_response = create_transition(net_page, intent_keyword+":response") 
                
            if node['type'] == 'Bot Action':
                function_name = extract_function_name(node)
                create_transition(net_page, node_id, function_name)


        out_degree = {} # out-degree of each node to find transitions with no outgoing edges which will later be connected to the sink
        
        for edge_id,edge in edges.items():
            if edge['type'] not in edge_types_of_interest:
                continue

            source = edge['source']
            target = edge['target']
            if edge['type'] in ['leadsTo','uses'] : # Incoming Message leadsTo other Incoming Message or uses Bot Action
                if source not in out_degree:
                    out_degree[source] = 0
                out_degree[source] += 1 # every time we have more than one outgoing edge, we produce more than one token (one for each place). Those tokens should also be consumed again at the end of the process

            if nodes[source]['type'] == 'Messenger':
                create_arc(net_page, edge_id, "initial_marking", target)
                continue

            if nodes[source]['type'] == 'Bot Action':
                create_arc(net_page, edge_id, source, target)
                continue

            # create a place between the source and target
            create_place(net_page, edge_id)
            # create an arc from the source to the place
            create_arc(net_page,f'${source}-->place', source, edge_id)
            # create an arc from the place to the target
            create_arc(net_page,f'place-->${target}', edge_id, target)

        # find nodes with no outgoing edges and connect them to the sink
        # TODO: this will not produce safe petri nets. Need to find a way to produce safe petri nets
        for node_id, node in nodes.items():
            if node['type'] in ['Incoming Message', 'Bot Action'] and node_id not in out_degree:
                create_arc(net_page, f'${node_id}-->sink0', node_id, 'sink0')

        tree = ET.ElementTree(root)
        return tree        


if __name__ == "__main__":
    # import test_model.json
    import json
    with open('test_model.json') as json_file:
        json = json.load(json_file)
    bot_parser = BotParser.get_instance()
    tree = bot_parser.bot_model_to_petri_net(json)
    tree.write("test_model_custom.pnml")
           # set <?xml version='1.0' encoding='UTF-8'?> as the first line of the pnml file
    with open("test_model_custom.pnml", 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write("<?xml version='1.0' encoding='UTF-8'?>\n" + content)

    
    