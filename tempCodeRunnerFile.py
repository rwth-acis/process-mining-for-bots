

    # # replace the ids with the activity names
    # for node_id,node in nodes.items():
    #     if node['type'] not in node_types_of_interest:
    #         continue
    #     name = extract_activity_name(node_id,node,edges)
        
    #     for t in net.transitions:
    #         if node_id == t._Transition__label:
    #             if name == "empty_intent":
    #                 t._Transition__label = None
    #             else:
    #                 t._Transition__label = name
