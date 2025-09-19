import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulator import Simulator
import topo, algo, para as para

from utils import draw_cdf


def firefly(nb_node, nb_link, sync_interval_ns, slice_duration_ns, d_bound=None, dv_bound=None, hop_error_bound=None):
    sim = Simulator(
        name="firefly",
        sync_algo=algo.firefly,
        #sync_algo=algo.firefly_optimized,
        nb_node=nb_node,
        nb_link=nb_link,
        #topo_func=topo.opera,
        topo_func=topo.static_tree,
        drift_bound=d_bound,
        drift_variance_bound=dv_bound,
        hop_error_bound=hop_error_bound,
        sync_interval_ns=sync_interval_ns,
        slice_duration_ns=slice_duration_ns,
        offset_drift=True
    )

    return sim

def firefly_adapted(nb_node, nb_link, sync_interval_ns, slice_duration_ns, dv_bound=None, hop_error_bound=None):
    sim = Simulator(
        name="firefly_adapted",
        #sync_algo=algo.firefly,
        sync_algo=algo.firefly_optimized,
        nb_node=nb_node,
        nb_link=nb_link,
        topo_func=topo.opera,
        #topo_func=topo.static_tree,
        drift_variance_bound=dv_bound,
        hop_error_bound=hop_error_bound,
        sync_interval_ns=sync_interval_ns,
        slice_duration_ns=slice_duration_ns,
        offset_drift=True
    )

    return sim

if __name__ == "__main__":
    nb_node = 8
    nb_link = 2

    sim = firefly(
        nb_node, nb_link, sync_interval_ns=100 * 1000, slice_duration_ns=100 * 1000,
        dv_bound = 0, hop_error_bound=0
    )

    sim.run(iter=100)
    errs = {}
    errs['firefly'] = sim.get_clock_errors(start_record_from=50)

    draw_cdf(errs)
