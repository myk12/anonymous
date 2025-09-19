import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulator import Simulator
import topo, algo, para as para


def syncwise(nb_node, nb_link, sync_interval_ns, slice_duration_ns, d_bound=None, dv_bound=None, hop_error_bound=None,
             failed_node=[], failed_link=[]):
    sim = Simulator(
        name="syncwise",
        sync_algo=algo.syncwise,
        nb_node=nb_node,
        nb_link=nb_link,
        topo_func=topo.opera,
        #topo_func=topo.shale,
        drift_bound=d_bound,
        drift_variance_bound=dv_bound,
        hop_error_bound=hop_error_bound,
        sync_interval_ns=sync_interval_ns,
        slice_duration_ns=slice_duration_ns,
        offset_drift=True,
        failed_node=failed_node,
        failed_link=failed_link
    )

    return sim

def syncwise_skew(
        nb_node, nb_link, sync_interval_ns, slice_duration_ns, d_bound=None, dv_bound=None, hop_error_bound=None,
        topo_arg=None,topo_update_ts=None,
        failed_node=[], failed_link=[]):
    
    sim = Simulator(
        name="syncwise",
        sync_algo=algo.syncwise,
        nb_node=nb_node,
        nb_link=nb_link,
        topo_func=topo.opera_skew,
        topo_arg=topo_arg,
        topo_update_ts=topo_update_ts,
        #topo_func=topo.shale,
        drift_bound=d_bound,
        drift_variance_bound=dv_bound,
        hop_error_bound=hop_error_bound,
        sync_interval_ns=sync_interval_ns,
        slice_duration_ns=slice_duration_ns,
        offset_drift=True,
        failed_node=failed_node,
        failed_link=failed_link
    )

    return sim

if __name__ == "__main__":
    nb_node = 8
    nb_link = 2

    sim = syncwise(
        nb_node, nb_link, sync_interval_ns=100 * 1000, slice_duration_ns=100 * 1000,
        dv_bound = 500,
        hop_error_bound = 10
    )

    sim.run(iter=16)
    #import numpy as np
    #print(np.round(sim.get_error_bound(),4))
    #print(sim.get_error_bound(), sim.get_clock_errors())
