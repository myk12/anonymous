import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulator import Simulator
import topo, algo, para as para
from utils import draw_cdf


def dtp(nb_node, nb_link, sync_interval_ns, slice_duration_ns, d_bound=None, dv_bound=None, hop_error_bound=None):
    sim = Simulator(
        name="dtp",
        sync_algo=algo.dtp,
        nb_node=nb_node,
        nb_link=nb_link,
        #topo_func=topo.opera,
        topo_func=topo.static_tree,
        #topo_func=topo.shale,
        drift_bound=d_bound,
        drift_variance_bound=dv_bound,
        hop_error_bound=hop_error_bound,
        sync_interval_ns=sync_interval_ns,
        slice_duration_ns=slice_duration_ns,
        offset_drift=False,
    )

    return sim

def dtp_adapted(nb_node, nb_link, sync_interval_ns, slice_duration_ns, dv_bound=None, hop_error_bound=None):
    sim = Simulator(
        name="dtp",
        sync_algo=algo.dtp,
        nb_node=nb_node,
        nb_link=nb_link,
        #topo_func=topo.opera,
        topo_func=topo.static_tree,
        #topo_func=topo.shale,
        drift_variance_bound=dv_bound,
        hop_error_bound=hop_error_bound,
        sync_interval_ns=sync_interval_ns,
        slice_duration_ns=slice_duration_ns,
        offset_drift=False,
    )

    return sim


if __name__ == "__main__":
    nb_node = 8
    nb_link = 2

    nb_node = 32
    nb_link = 4

    sim = dtp(
        nb_node, nb_link, sync_interval_ns=100 * 1000, slice_duration_ns=100 * 1000
    )

    sim.run(iter=100)
    import numpy as np
    print(np.round(sim.get_clock_errors(),2))
    draw_cdf({"dtp": sim.get_clock_errors()}, name="dtp")
    import matplotlib.pyplot as plt
    plt.show()
