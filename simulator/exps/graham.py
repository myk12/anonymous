import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulator import Simulator
import topo, algo, para as para


def graham(nb_node, nb_link, sync_interval_ns, slice_duration_ns, d_bound=None, dv_bound=None, hop_error_bound=None):
    sim = Simulator(
        name="graham",
        sync_algo=algo.graham,
        nb_node=nb_node,
        nb_link=nb_link,
        topo_func=topo.opera,
        drift_bound=d_bound,
        drift_variance_bound=dv_bound,
        hop_error_bound=hop_error_bound,
        sync_interval_ns=sync_interval_ns,
        slice_duration_ns=slice_duration_ns,
        offset_drift=True,
    )

    return sim


if __name__ == "__main__":
    nb_node = 8
    nb_link = 2
    drift = para.gen_drift(nb_node)

    sim = graham(
        nb_node, nb_link, sync_interval_ns=10 * 1000, slice_duration_ns=10 * 1000
    )

    sim.run(time_ms=1)
    errs = sim.get_clock_errors()
    print(errs)
