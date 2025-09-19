# Generate topology schedule

import networkx as nx
import matplotlib.pyplot as plt
import math
import numpy as np
import itertools
import random

"""
Circuit:
[time_slice, node1, node2, port1, port2]
"""

def generate_topo(nb_nodes, circuits) -> dict[int,nx.Graph]:
    """
    Generate topologies (in networkx graph) based on given circuits

    Args:
        nb_nodes: number of nodes
        circuits: [node1, port1, node2, port2, time_slice], or a nx.Graph

    Returns:
        bool: the dictionary of topologies with key of time slices.
            If it is a static topology, there is only one key
    """

    # Static topology. Only one time slice
    if isinstance(circuits, nx.Graph):
        #nx.draw(circuits, with_labels=True)
        plt.show()
        return {0: circuits}

    slice_to_topo = {}

    for (time_slice, node1, node2, port1, port2) in circuits:
        
        if time_slice not in slice_to_topo.keys():
            # Fill missing time slices
            for added_time_slice in range(time_slice+1):
                if added_time_slice not in slice_to_topo.keys():
                    slice_to_topo[added_time_slice] = nx.Graph()
                    slice_to_topo[added_time_slice].add_nodes_from(list(range(nb_nodes)))

        slice_to_topo[time_slice].add_edge(node1, node2, port1=port1, port2=port2)

    #draw_topo(slice_to_topo)

    return slice_to_topo

def static_tree(rng, nb_node, nb_link) -> nx.Graph:
    """Create a tree"""
    tree = nx.full_rary_tree(r=nb_link, n=nb_node)
    #mapping = {0: 'temp', nb_node-1: 0,}
    #tree = nx.relabel_nodes(tree, mapping)
    #mapping = {'temp': nb_node-1}
    #tree = nx.relabel_nodes(tree, mapping)
    #nx.draw(tree, with_labels=True)
    #plt.show()
    return tree
    #return nx.balanced_tree(nb_node, nb_link)

def clos(nb_node, nb_link) -> nx.Graph:
    pass
def flat(nb_node, nb_link) -> nx.Graph:
    assert nb_node > 1
    return nx.star_graph(n=nb_node-1)
    
def round_robin(nb_node=None, nb_link=1, nodes=None, port1=0, port2=0, self_loop=False) -> list:
    """
    Create a round-robin topology with the circle method. Assume one upper link per node.
    Args:
        nb_node: Number of nodes
        nodes: If not specified, create node list based on the number of nodes.
                Otherwise create round-robin within given nodes.
        port1: The port src node uses to connect. 0 by default
        port2: The port dst node uses to connect. 0 by default
        self_loop: Whether to add loop-back time slice.
    Returns:
        A list of circuits.
    """

    if nb_link != 1:
        raise ValueError("Round robin only supports one upper link."
        "For multi-link round robin, please refer to use Opera.")
    
    if nodes is None:
        assert nb_node is not None, "Need either nb_node or node"
        nodes = list(range(nb_node))
    else:
        nb_node = len(nodes)
        if isinstance(nodes, np.ndarray):
            nodes = nodes.tolist()

    #assert nb_node % 2 == 0, "Round-robin needs number of nodes to be even."
    if nb_node % 2 == 1:
        nb_node = nb_node + 1
        nodes.append(-1) # -1 indicate dummy node

    circuits = []

    for slice_id in range(nb_node - 1):
        for i in range(nb_node // 2):
            if nodes[i] == -1 or nodes[-i-1] == -1:
                # does not connect dummy node
                continue
            circuits.append(
                [slice_id, nodes[i], nodes[-i-1], port1, port2]
            )
        nodes.insert(1, nodes.pop(-1))

    # Add a loop-back time slice for being the building block of more complex topology
    if self_loop == True:
        for node_id in range(nb_node):
            circuits.append(
                [nb_node-1, nodes[node_id], nodes[node_id], port1, port2]
            )

    return circuits

def opera(rng, nb_node, nb_link, nodes = None):
    """
    Opera topology support multiple upper links per node.
    In (nb_node / nb_link) time slices, each link of every node connects (nb_node / nb_link) number of nodes
    We connect ports with the same index together.
    """

    # First we generate a basic round robin that each node connects every other node.
    base_circuits = round_robin(nb_node = nb_node, nodes = nodes, self_loop=True)
    # e.g. 4 nodes, 2 links
    # slice0: 0(p0) <-> 3(p0), 1(p0) <-> 2(p0)
    # slice1: 0(p0) <-> 2(p0), 1(p0) <-> 3(p0)
    # slice2: 0(p0) <-> 1(p0), 2(p0) <-> 3(p0)
    # slice3: self loop

    # Randomize topo by shuffling topologies to different time slices
    base_circuits = topo_randomize_ts(rng, base_circuits)

    # To connect all nodes in nb_node / nb_link time slice, we merge time slices, as well as connections,
    # with the ratio of nb_link. The connections in (nb_link) time slices are achieved by nb_link links at one time slice.
    # With two upper links, we map old_ts to new_ts by (2n -> n), (2n+1 -> n)
    # With three upper links, we map old_ts to new_ts by (3n -> n), (3n+1 -> n), (3n+2 -> n)

    merged_circuit = []
    for ts, node1, node2, port1, port2 in base_circuits:
        port_id = ts % nb_link
        merged_circuit.append([ts//nb_link, node1, node2, port_id, port_id])
    # e.g. 4 nodes, 2 links
    # slice0: 0(p0) <-> 3(p0), 0(p1) <-> 2(p1), 1(p0) <-> 2(p0), 1(p1) <-> 3(p1)
    # slice1: 0(p0) <-> 1(p0), 0&1 (p1)   loop, 2(p0) <-> 3(p0), 2&3 (p1)   loop

    offset_circuits = merged_circuit
    #offset_circuits = port_offset(merged_circuit)
    #offset_circuits = merged_circuit

    return offset_circuits

def opera_skew(rng, nb_node, nb_link, skew_ratio, nodes = None):
    """
    Opera topology support multiple upper links per node.
    In (nb_node / nb_link) time slices, each link of every node connects (nb_node / nb_link) number of nodes
    We connect ports with the same index together.
    """

    # First we generate a basic round robin that each node connects every other node.
    base_circuits = round_robin(nb_node = nb_node, nodes = nodes, self_loop=True)
    # e.g. 4 nodes, 2 links
    # slice0: 0(p0) <-> 3(p0), 1(p0) <-> 2(p0)
    # slice1: 0(p0) <-> 2(p0), 1(p0) <-> 3(p0)
    # slice2: 0(p0) <-> 1(p0), 2(p0) <-> 3(p0)
    # slice3: self loop

    # Randomize topo by shuffling topologies to different time slices
    #topo_randomize_ts(base_circuits)

    # To connect all nodes in nb_node / nb_link time slice, we merge time slices, as well as connections,
    # with the ratio of nb_link. The connections in (nb_link) time slices are achieved by nb_link links at one time slice.
    # With two upper links, we map old_ts to new_ts by (2n -> n), (2n+1 -> n)
    # With three upper links, we map old_ts to new_ts by (3n -> n), (3n+1 -> n), (3n+2 -> n)

    merged_circuit = []
    for ts, node1, node2, port1, port2 in base_circuits:
        port_id = ts % nb_link
        merged_circuit.append([ts//nb_link, node1, node2, port_id, port_id])
    # e.g. 4 nodes, 2 links
    # slice0: 0(p0) <-> 3(p0), 0(p1) <-> 2(p1), 1(p0) <-> 2(p0), 1(p1) <-> 3(p1)
    # slice1: 0(p0) <-> 1(p0), 0&1 (p1)   loop, 2(p0) <-> 3(p0), 2&3 (p1)   loop

    skew_circuit = make_topo_skew(merged_circuit, skew_ratio)
    if skew_ratio > 0:
        assert len(merged_circuit) != len(skew_circuit)

    return skew_circuit

def shale(nb_node, h, nodes = None):
    """
    We assume num of links == h, so rr in different dimension doesn't influence each other.
    """
    if nodes is None:
        nodes = list(range(nb_node))
    else:
        nb_node = len(nodes)

    root = int(math.pow(nb_node, 1/h))
    assert root ** h == nb_node, "number of nodes need to be the power of h"

    # Reshape nodes into an h-dimensional cube
    nodes = np.array(nodes).reshape([root] * h)

    circuits = []
    for pos in range(h):
        for base_indices in itertools.product(range(root), repeat=h-1):
            # base indices are (0,0), (0,1), (1,0), (1,1)
            indices = base_indices[:pos] + (slice(None),) + base_indices[pos:]
            # indices are (:,0,0), (:,0,1), (:,1,0), (:,1,1), (0,:,0), (0,:,1), (1,:,0)....
            circuits.extend(round_robin(nodes=nodes[indices], port1=pos, port2=pos))

    return circuits

def topo_randomize_ts(rng, circuits : list):
    """
    Randomize connection order (time_slice -> connections mapping) for circuits.
    """
    circuits.sort(key = lambda x: x[4])
    #print(circuits)

    ts_set = set()
    for ts, node1, node2, port1, port2 in circuits:
        ts_set.add(ts)

    time_slices = sorted(list(ts_set))
    shuffled = time_slices.copy()
    rng.shuffle(shuffled)

    shuffled_circuits = []
    for ts, node1, node2, port1, port2 in circuits:
        shuffled_circuits.append([shuffled[ts], node1, node2, port1, port2])

    # Sort based on time slice
    shuffled_circuits.sort(key = lambda x: x[0])
    #print(shuffled_circuits)

    return shuffled_circuits

def make_topo_skew(circuits : list, skew_ratio):
    """
    Duplicate the first half of the circuits skew_ratio times
    """
    circuits.sort(key = lambda x: x[4])
    #print(circuits)

    ts_set = set()
    for ts, node1, node2, port1, port2 in circuits:
        ts_set.add(ts)

    skew_circuits = []
    for ts, node1, node2, port1, port2 in circuits:
        skew_circuits.append([ts, node1, node2, port1, port2])
        if ts < len(ts_set) // 2:
            for i in range(1, skew_ratio+1):
                skew_circuits.append([ts + (len(ts_set)//2) * i, node1, node2, port1, port2])

    # Sort based on time slice
    skew_circuits.sort(key = lambda x: x[0])

    return skew_circuits

def port_offset(circuits : list):
    """
    Helper function to transform the circuits to reconfigure topology one port per time slice.
    New nb_time_slice = old nb_time_slice * nb_links
    """

    nb_time_slice = get_nb_time_slice_from_circuits(circuits)
    nb_links = get_nb_links_from_circuits(circuits)

    offset_circuits = []
    for ts, node1, node2, port1, port2 in circuits:
        assert port1 == port2, "To enable port offset, port id should be the same for both side."
        new_ts_start = ts * nb_links + port1
        new_ts_end = (ts+1) * nb_links + port1
        for new_ts in range(new_ts_start, new_ts_end):
            offset_circuits.append([
                new_ts % (nb_time_slice * nb_links), node1, node2, port1, port2
            ])
    
    return offset_circuits

def get_nb_time_slice_from_circuits(circuits : list):
    """
    Helper function
    Args:
        A list of circuits
    Returns:
        The number of time slices
    """
    max_ts = 0
    for ts, node1, node2, port1, port2 in circuits:
        if ts > max_ts:
            max_ts = ts
    return max_ts + 1

def get_nb_links_from_circuits(circuits : list):
    """
    Helper function
    Args:
        A list of circuits
    Returns:
        The number of links
    """
    max_port = 0
    for ts, node1, node2, port1, port2 in circuits:
        if port1 > max_port:
            max_port = port1
        if port2 > max_port:
            max_port = port2
    return max_port + 1

def compute_skewness(slice_to_topo):
    data = {}
    for ts, topo in slice_to_topo.items():
        for node1, node2 in topo.edges():
            node1, node2 = sorted([node1, node2])
            if (node1, node2) not in data.keys():
                data[(node1, node2)] = 1
            else:
                data[(node1, node2)] += 1

    from scipy.stats import skew
    v = list(data.values())
    print(f"{v=}")
    print(skew(v))

def draw_topo(slice_to_topo):
    nb_time_slices = len(slice_to_topo)
    pos = nx.circular_layout(sorted(slice_to_topo[0].nodes))
    fig, axs = plt.subplots(1, nb_time_slices)

    if nb_time_slices == 1:
        axs = [axs]

    for time_slice, ax in enumerate(axs):
        nx.draw(slice_to_topo[time_slice],
                ax = ax,
                pos = pos,
                with_labels=True,
                node_color="#6A9FB5",
                font_color="white")
        ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
        ax.axis('on')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"slice={time_slice}")
    
    fig.set_size_inches(3 * nb_time_slices, 3)
    plt.show()

    return 