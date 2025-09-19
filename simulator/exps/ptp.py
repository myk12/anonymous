import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulator import Simulator
import topo, algo, para as para


def ptp(nb_node, nb_link, sync_interval_ns, slice_duration_ns, d_bound=None, dv_bound=None, hop_error_bound=None):
    sim = Simulator(
        name="ptp",
        sync_algo=algo.spanning_tree,
        nb_node=nb_node,
        nb_link=nb_link,
        topo_func=topo.static_tree,
        drift_bound=d_bound,
        drift_variance_bound=dv_bound,
        hop_error_bound=hop_error_bound,
        sync_interval_ns=sync_interval_ns,
        slice_duration_ns=slice_duration_ns,
        offset_drift=False
    )

    return sim


if __name__ == "__main__":
    nb_node = 16
    nb_link = 4

    sim = ptp(nb_node, nb_link, sync_interval_ns=10 * 1000, slice_duration_ns=10 * 1000)

    sim.run(iter=10)
    print(sim.get_error_bound(), sim.get_clock_errors())
