from pm4py.convert import convert_to_petri_net

bot_parsers = {}  # map of botParser instances for each bot

def get_bot_parser(bot_model):
    """
    Gets a bot parser instance for a bot model
    :param bot_model: the bot model
    :return: the bot parser instance
    """
    for node_id, node in bot_model['nodes'].items():
        if node['type'] == "Bot":
            bot_id = node_id
            break

    if bot_id is None:
        raise Exception("No bot node found in bot model")

    if bot_id not in bot_parsers:
        bot_parsers[bot_id] = BotParser(bot_model)
    return bot_parsers[bot_id]


class BotParser:
    """
    This class provides methods to parse a bot model to a petri net and a dfg.
    """

    def __init__(self, bot_model):
        self.bot_model = bot_model
        self.idNameMap = {}  # for each node id of interest, store a name representative of the node
        self.node_types_of_interest = [
            'Incoming Message', 'Bot Action', 'Messenger']
        self.edge_types_of_interest = ['leadsTo', 'uses', 'generates']
        self.nodes = bot_model['nodes']
        self.edges = bot_model['edges']
        
        for node_id, node in bot_model['nodes'].items():
            if node['type'] not in self.node_types_of_interest:
                continue
            name = extract_activity_name(
                node_id, node, bot_model['edges'])
            self.idNameMap[node_id] = name

    def to_petri_net(self,dfg =None, start_activities=None, end_activities=None):
        """
        Converts a dfg to a petri net with initial and final markings
        :param dfg: the dfg of the bot model (optional) if not provided, it is computed from the bot model
        :param start_activities: the start activities of the bot model (optional) if not provided, it is computed from the bot model
        :param end_activities: the end activities of the bot model (optional) if not provided, it is computed from the bot model 
        :return: the petri net with initial and final markings

        :example:
        >>> petri_net,im,fm = to_petri_net(json)
        """
        if(dfg is None):
            dfg, start_activities, end_activities = self.to_dfg()

        net, im, fm = convert_to_petri_net(
            dfg, start_activities, end_activities)
        # from pm4py.objects.petri_net.utils.check_soundness import check_easy_soundness_net_in_fin_marking
        # check_easy_soundness_net_in_fin_marking(net, im, fm)

        return self.rename_labels(net, im, fm)

    

    def to_dfg(self):
        """
        Converts a bot model to a direct follow graph (dfg)
        :param json: the bot model
        :return: the dfg, the start activities and the end activities
        """

        edges = self.edges.copy() # copy the edges since we need to remove some of them 
        
        start_activities = set()
        end_activities = set()
        dfg = {}

        edges_to_remove = set()
        # find patterns of the form A -> Bot Action and A -> Incoming Message and replace them with A -> Bot Action -> Incoming Message
        # The reason for doing this is the pattern A -> Bot Action -> Incoming Message is semantically more meaningful because it shows that
        # the Bot Action is triggered by the Incoming Message and the next Incoming Message is only handled after the Bot Action is finished.
        for edge_id, edge in self.edges.items():
            if edge['type'] == 'uses' and self.nodes[edge['target']]['type'] == 'Bot Action':  # A -> Bot Action
                source_id = edge['source']
                target_id = edge['target']
                if (source_id, target_id) not in dfg:
                    dfg[(source_id, target_id)] = 0
                dfg[(source_id, target_id)] += 1
                # remove the uses edge since we have already handled it
                edges_to_remove.add(edge_id)

                for edge2_id, edge2 in self.edges.items():
                    # A -> Incoming Message
                    if edge2['type'] == 'leadsTo' and edge2['source'] == edge['source']:

                        # create Bot Action -> Incoming Message
                        source_id = edge['target']  # Bot Action
                        target_id = edge2['target']  # Incoming Message

                        if (source_id, target_id) not in dfg:
                            dfg[(source_id, target_id)] = 0
                        dfg[(source_id, target_id)] += 1
                        # remove the leadsTo edge
                        # remove the leadsTo edge since it is now replaced by Bot Action -> Incoming Message
                        edges_to_remove.add(edge2_id)

        # remove all edges that are were replaced
        for edge_id in edges_to_remove:
            edges.pop(edge_id)

        # now build dfg from the remaining edges
        for edge in edges.values():
            if edge['type'] not in self.edge_types_of_interest:
                continue

            source_id = edge['source']
            target_id = edge['target']

            # nodes connected to the messenger are start activities
            if self.nodes[source_id]['type'] == 'Messenger':
                start_activities.add(source_id)
            if self.nodes[source_id]['type'] not in self.node_types_of_interest or self.nodes[target_id]['type'] not in self.node_types_of_interest:
                continue

            if (source_id, target_id) not in dfg:
                dfg[(source_id, target_id)] = 0
            dfg[(source_id, target_id)] += 1

        # find end activities which are nodes with no outgoing edge
        for node_id, node in self.nodes.items():
            if node['type'] not in self.node_types_of_interest:
                continue
            has_outgoing_edge = False
            for source, _ in dfg.keys():
                if source == node_id and edge['type'] in self.edge_types_of_interest:
                    has_outgoing_edge = True
                    break
            if not has_outgoing_edge:
                # also check whether the node is in the dfg, if not it is a start activity and an end activity
                if node_id in start_activities and (node_id, _) not in dfg:
                    dfg[("None", node_id)] = 0
                end_activities.add(node_id)
        return dfg, start_activities, end_activities


    def get_node_id_by_name(self, name):
        """
        Gets the id of a node by its name
        :param name: the name of the node
        :param nodes: the nodes of the bot model
        :return: the id of the node

        :example:
        >>> node_id = get_node_id_by_name("n1")
        """
        for node_id, node_name in self.idNameMap.items():
            if node_name == name:
                return node_id
        return None
    
    def rename_labels(self, net, im, fm):
        # replace the ids with the activity names
        for node_id, node in self.nodes.items():
            if node['type'] not in self.node_types_of_interest:
                continue
            name = self.idNameMap[node_id]

            for t in net.transitions:
                if node_id == t._Transition__label:
                    if name == "empty_intent" or name == "empty_activity":
                        t._Transition__label = None
                    else:
                        t._Transition__label = name
        return net, im, fm




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


def extract_intent_keyword(node_id, node, edges):
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
            intent_keyword = attr['value']['value']
            if intent_keyword != "" and intent_keyword is not None:
                return intent_keyword

        # sometimes the intent keyword is empty and stored in the ingoing edge of the node instead
        for edge in edges.values():
            if edge['target'] == node_id:
                intent_keyword = edge['label']['value']['value']
                if intent_keyword != "" and intent_keyword is not None:
                    return intent_keyword
    return "empty_intent"


def extract_activity_name(node_id, node, edges):
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
        return extract_intent_keyword(node_id, node, edges)
    elif node['type'] == 'Bot Action':
        return extract_function_name(node)
    return "empty_activity"
