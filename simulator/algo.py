import copy

import networkx as nx
import numpy as np
from numba import jit
import matplotlib.pyplot as plt

import utils
import para

# Collection of sync algorithms
# sync_func(cur_error, cur_bound, cur_topo)
#   -> cur_error, cur_bound, sync_count:

def syncwise(rng, cur_error : np.ndarray, cur_bound : np.ndarray, cur_topo : nx.Graph, hop_error_bound : int,
             path_length_tracker, path_length_counter) -> tuple[list, list, int]:
    sync_count = 0
    #print(np.round(cur_bound,4))
    prev_error = cur_error
    prev_bound = cur_bound
    now_error = copy.deepcopy(cur_error)
    now_bound = copy.deepcopy(cur_bound)

    assert isinstance(cur_topo, nx.Graph)
    #print("In this time slice:")

    sync_record = []
    sync_record_str = ""
    for node in cur_topo.nodes():
        neighbors = utils.get_neighbors(cur_topo, node)
        if len(neighbors) == 0:
            continue
        neighbor_bounds = [prev_bound[neighbor] for neighbor in neighbors]
        #print(f"{neighbors=}")
        #print(f"{neighbor_bounds=}")
        chosen_neighbor, min_neighbor_bound = min(zip(neighbors, neighbor_bounds), key=lambda x: x[1])

        if prev_bound[node] > min_neighbor_bound + hop_error_bound:
            now_bound[node] = min_neighbor_bound + hop_error_bound
            now_error[node] = prev_error[chosen_neighbor] + para.get_hop_error(rng, hop_error_bound)
            sync_count += 1
            sync_record.append(chosen_neighbor)
            sync_record_str += f"{chosen_neighbor} -> {node}, "
            #print(f"Sync with {chosen_neighbor}, bound from {prev_bound[node]} to {now_bound[node]}")
            #print(f"Sync with {chosen_neighbor}, clk error from {prev_error[node]} to {now_error[node]}")
            path_length_tracker[node] = path_length_tracker[chosen_neighbor] + 1
            hop_count = path_length_tracker[node]
            if hop_count != 0: # skip inital phase
                path_length_counter[hop_count] += 1
        else:
            sync_record.append(9)
    #print(f"sync record={sync_record}")
    #print(np.round(prev_bound,0))
    #print(sync_record_str)
    #nx.draw(cur_topo, with_labels=True)
    #plt.show()
    return now_error, now_bound, sync_count

def dtp(rng, cur_error : np.ndarray, cur_bound : np.ndarray, cur_topo : nx.Graph, hop_error_bound : int) -> tuple[list, list, int]:
    sync_count = 0
    #print(f"{cur_bound=}")
    prev_error = cur_error
    prev_bound = cur_bound
    now_error = copy.deepcopy(cur_error)
    now_bound = copy.deepcopy(cur_bound)

    assert isinstance(cur_topo, nx.Graph)

    for node in cur_topo.nodes():
        neighbors = utils.get_neighbors(cur_topo, node)
        if len(neighbors) == 0:
            print(f"{node=} has no neighbors")
            continue
        neighbor_errors = [prev_error[neighbor] for neighbor in neighbors]

        now_error[node] = max(neighbor_errors) + para.get_hop_error(rng, hop_error_bound)
    
    # DTP does internal sync
    now_error = now_error - np.average(now_error)
    #print(now_error)

    return now_error, now_bound, sync_count

def graham(rng, cur_error : np.ndarray, cur_bound : np.ndarray, cur_topo : nx.Graph, hop_error_bound : int) -> tuple[list, list, int]:
    """Only sync with master"""
    sync_count = 0
    #print(f"{cur_bound=}")
    prev_error = cur_error
    prev_bound = cur_bound
    now_error = copy.deepcopy(cur_error)
    now_bound = copy.deepcopy(cur_bound)

    for node in cur_topo.nodes():
        neighbors = utils.get_neighbors(cur_topo, node)
        if 0 in neighbors:
            now_bound[node] = hop_error_bound
            now_error[node] = para.get_hop_error(rng, hop_error_bound)
            sync_count += 1

    return now_error, now_bound, sync_count
def spanning_tree(rng, cur_error : np.ndarray, cur_bound : np.ndarray, cur_topo : nx.Graph, hop_error_bound : int,
                  path_length_tracker, path_length_counter) -> tuple[list, list, int]:
    sync_count = 0
    #print(f"{cur_bound=}")
    prev_error = cur_error
    prev_bound = cur_bound
    now_error = copy.deepcopy(cur_error)
    now_bound = copy.deepcopy(cur_bound)

    bfs_tree = nx.bfs_tree(cur_topo, source=0)
    #pos = nx.spring_layout(bfs_tree)
    #nx.draw(bfs_tree, pos, with_labels=True)
    #plt.show()

    for src, dst in bfs_tree.edges():
        assert dst != 0, "Source node should not be synced."
        now_bound[dst] = prev_bound[src] + hop_error_bound
        now_error[dst] = prev_error[src] + para.get_hop_error(rng, hop_error_bound)
        #print(f"{src} with bound {prev_bound[src]} sync {dst} with bound {prev_bound[dst]}, new bound {now_bound[dst]}")
        #print(f"{src} with error {prev_error[src]} sync {dst} with error {prev_error[dst]}, new error {now_error[dst]}")
        sync_count += 1
        path_length_tracker[dst] = path_length_tracker[src] + 1
        hop_count = path_length_tracker[dst]
        if hop_count != 0:
            path_length_counter[hop_count] += 1
    
    #print(now_error[:10])
    #print(f"{hop_error_bound=}")
    return now_error, now_bound, sync_count

def firefly(rng : np.random.Generator, cur_error : np.ndarray, cur_bound : np.ndarray, cur_topo : nx.Graph, hop_error_bound : int) -> tuple[list, list, int]:
    """firefly algo, where sync with randomly picked nodes"""
    sync_count = 0
    
    prev_error = cur_error
    now_error = copy.deepcopy(cur_error)
    #now_bound = copy.deepcopy(cur_bound)
    now_bound = cur_bound # firefly has no bound

    assert isinstance(cur_topo, nx.Graph)

    all_shortest_paths = dict(nx.all_pairs_shortest_path_length(cur_topo))
    sum_hop_len = 0

    nb_link = len(utils.get_neighbors(cur_topo, 0))
    #nb_link = 20

    for node in cur_topo.nodes():
        # neighbors not used, only for get link number
        neighbors = rng.choice(list(cur_topo.nodes() - [node]), size=nb_link)
        #print(f"{neighbors=}")
        neighbor_errors = [prev_error[neighbor] for neighbor in neighbors]
        
        noise = 0
        for neighbor in neighbors:
            if neighbor not in all_shortest_paths[node].keys():
                # Not connected
                continue
            hop_length = all_shortest_paths[node][neighbor]
            sum_hop_len += hop_length
            #hop_length = max(hop_length, 50)
            #print(f"{hop_length=}")
            noise += sum([para.get_hop_error(rng, hop_error_bound) + para.get_path_asymmetry(rng)
                           for hop in range(hop_length)])
            #noise += para.get_hop_error(rng, hop_error_bound) * hop_length
        #print(f"sum {noise=}, avg {noise/len(neighbors)=}")
        #noises = [para.get_hop_error(rng, ) for neighbor in neighbors]
        now_error[node] = (sum(neighbor_errors) + noise) / len(neighbors)
        #print(f"Sync with {neighbors}, clk error from {prev_error[node]} to {now_error[node]}")

    # Cailibrate error viewing for the ease of debugging
    now_error = now_error - np.average(now_error)
    #print(f"{now_error=}")
    #avg_hop_len = sum_hop_len / len(cur_topo.nodes()) / len(utils.get_neighbors(cur_topo, node))
    #print(f"{avg_hop_len=}")

    return now_error, now_bound, sync_count

def firefly_optimized(rng : np.random.Generator, cur_error : np.ndarray, cur_bound : np.ndarray, cur_topo : nx.Graph, hop_error_bound : int) -> tuple[list, list, int]:
    """Applied firefly into rdcn, where only sync with direct neighbors"""
    sync_count = 0
    
    prev_error = cur_error
    #prev_bound = copy.deepcopy(cur_bound)
    now_error = copy.deepcopy(cur_error)
    #now_bound = copy.deepcopy(cur_bound)
    now_bound = cur_bound

    assert isinstance(cur_topo, nx.Graph)

    for node in cur_topo.nodes():
        neighbors = utils.get_neighbors(cur_topo, node)
        neighbor_errors = [prev_error[neighbor] for neighbor in neighbors]
        noises = [para.get_hop_error(rng, hop_error_bound)] * len(neighbors)
        now_error[node] = (sum(neighbor_errors) + sum(noises)) / len(neighbors)
        #print(f"Sync with {neighbors}, clk error from {prev_error[node]} to {now_error[node]}")

    # Cailibrate error viewing for the ease of debugging
    now_error = now_error - np.average(now_error)
    #print(f"{now_error=}")

    return now_error, now_bound, sync_count