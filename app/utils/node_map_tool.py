import numpy as np
import pandas as pd
from collections import deque


def section_sequence(network_df, source_node):
    # Create a dictionary to store the graph
    graph = {}

    section = network_df['section'].values
    start = network_df['start'].values
    end = network_df['end'].values

    for sec, s, e in zip(section, start, end):

        if s not in graph:
            graph[s] = []
        if e not in graph:
            graph[e] = []
        graph[s].append((e, sec))
        graph[e].append((s, sec))

    # Initialize the queue for BFS with the start node
    queue = deque([(source_node, 0)])

    # Initialize visited nodes set and the result list
    visited = set()
    sequence = [0] * len(section)
    further_node = [''] * len(section)

    while queue:
        current_node, level = queue.popleft()
        # Mark the current node as visited
        if current_node not in visited:
            visited.add(current_node)
            for neighbor, section_id in graph.get(current_node, []):
                # If the neighbor has not been visited and is not an open section
                if neighbor not in visited :
                    for idx, sec in enumerate(section):
                        if sec == section_id:
                            sequence[idx] = level + 1
                            further_node[idx] = neighbor
                    queue.append((neighbor, level + 1))

    sequence = np.array(sequence)

    return sequence, further_node


def get_downstream_nodes(network_df, start_node):

    downstream_nodes = [start_node]

    is_connected = ((network_df['start'] == start_node) | (network_df['end'] == start_node))
    to_process = network_df[is_connected]['section'].tolist()
    is_in_to_process = network_df['section'].isin(to_process)
    next_sequence = network_df.loc[is_in_to_process, 'sequence'].max()
    is_next_sequence = (network_df['sequence'] == next_sequence)

    to_process = network_df[is_connected & is_next_sequence]['section'].tolist()

    while to_process:
        current_section = to_process[-1]

        sequence = network_df.loc[network_df['section'] == current_section, 'sequence'].values[0]
        further_node = network_df.loc[network_df['section'] == current_section, 'further_node'].values[0]

        downstream_nodes.append(further_node)

        network_df = network_df[network_df['section'] != current_section]

        is_next = network_df['sequence'] > sequence

        connected_mask = (((network_df['start'] == further_node) |
                           (network_df['end'] == further_node)) & is_next)

        connected_df = network_df.loc[connected_mask, 'section']
        connected_list = connected_df.values.tolist()

        to_process += connected_list

        to_process.remove(current_section)

    return downstream_nodes


def set_downstream_dict(node_list, network_df):
    downstream_dict = {}

    for n in node_list:
        downstream_nodes = get_downstream_nodes(network_df, start_node=n)

        downstream_dict[n] = downstream_nodes

    return downstream_dict


def dict_to_table(node_list, downstream_dict):

    downstream_nodes_table = pd.DataFrame(0, index=node_list, columns=node_list)

    for node, dowstream_nodes in downstream_dict.items():
        for dn in dowstream_nodes:
            if dn in downstream_nodes_table.index:
                downstream_nodes_table.at[dn, node] = 1

    return downstream_nodes_table


def run_nm_analysis(files, path_to_save):
    """
    :param files: Network, Source, limit and open file
    :type files: dict of Path
    :param path_to_save: Path to the generated files directory
    :type files: Path
    """
    path_to_save = path_to_save/'node_map.csv'

    network_df = pd.read_csv(files["network_file"])
    source_nodes = pd.read_csv(files["source_file"])['source'].tolist()
    open_sections = pd.read_csv(files["open_file"])['section'].tolist()

    network_df = network_df[~network_df['section'].isin(open_sections)]

    # Set a list of the nodes
    selected_columns = network_df[['start', 'end']]  # Select the desired columns
    node_list = selected_columns.values.flatten().tolist() # Flatten the DataFrame and convert to a list
    node_list = list(set(node_list))

    s_list = []
    fn_list = []
    for s in source_nodes:
        sequence, further_node = section_sequence(network_df, s)
        s_list.append(sequence)
        fn_list.append(further_node)

    size = len(sequence)

    sequence = []
    further_node = []

    for idx in range(size):

        for s, fn in zip(s_list, fn_list):
            if s[idx] > 0 :
                s_val = s[idx]
                fn_val = fn[idx]
                break

        sequence.append(s_val)
        further_node.append(fn_val)

    network_df['sequence'] = sequence
    network_df['further_node'] = further_node

    downstream_dict = set_downstream_dict(node_list=node_list, network_df=network_df)

    downstream_nodes_table = dict_to_table(node_list=node_list, downstream_dict=downstream_dict)
    downstream_nodes_table.to_csv(path_to_save)

    return path_to_save


