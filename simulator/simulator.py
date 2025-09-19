import copy

import numpy as np
#from numba import jit

import topo, para
import utils

class Simulator:

    def __init__(
            self,
            name,
            sync_algo,
            nb_node, 
            nb_link, 
            topo_func, 
            drift_variance_bound : int, 
            drift_bound : int,
            topo_arg = None,
            topo_update_ts = None,
            hop_error_bound = None,
            hop_error_d = None,
            sync_interval_ns = 1,
            slice_duration_ns = 1,
            offset_drift = True,
            failed_node = [],
            failed_link = []
    ):
        
        self.rng = np.random.default_rng(seed=42)  # set the seed

        self.name = name
        self.sync_algo = sync_algo
        self.nb_node = nb_node
        self.nb_link = nb_link
        if topo_arg is not None:
            self.first_topo, self.second_topo = topo_arg
            self.topo = topo.generate_topo(nb_node, topo_func(rng=self.rng, nb_node=nb_node, nb_link=nb_link, skew_ratio=self.first_topo))
        else:
            self.topo = topo.generate_topo(nb_node, topo_func(rng=self.rng, nb_node=nb_node, nb_link=nb_link))
        
        #topo.compute_skewness(self.topo)

        self.topo_func = topo_func
        self.drift_rate = para.gen_drift(self.rng, nb_node, drift_bound)
        if self.name == "ptp":
            self.drift_variance_bound = para.gen_drift_variance_tree(self.rng, nb_node, drift_variance_bound)
        else:
            self.drift_variance_bound = para.gen_drift_variance(self.rng, nb_node, drift_variance_bound)
        self.sync_interval_ns = sync_interval_ns
        self.slice_duration_ns = slice_duration_ns
        if hop_error_bound is None:
            self.hop_error_bound = 5
        else:
            self.hop_error_bound = hop_error_bound
        self.hop_error_d = hop_error_d
        self.offset_drift = offset_drift

        self.nodes = self.topo[0].nodes()
        self.cur_error = np.array([0] + [1e3] * (nb_node-1)) # current clock error of nodes 
        self.cur_bound = np.array([0] + [1e3] * (nb_node-1))  # current clock error bound of nodes 
        self.path_length_counter = {node: 0 for node in self.nodes}
        self.path_length_tracker = {node: 0 for node in self.nodes}
        #self.cur_error = np.array([0] * (nb_node)) # current clock error of nodes 
        #self.cur_bound = np.array([0] * (nb_node))  # current clock error bound of nodes 
        self.errors = []
        self.bounds = []
        self.failed_node = failed_node # ids of failed nodes
        self.failed_link = []
        self.topo_update_ts = topo_update_ts

        if failed_link: # Generate topology for the given number of failed links
            nb_ts = len(self.topo.keys())
            for ts, cur_topo in self.topo.items():
                edges_to_be_removed = self.rng.choice(cur_topo.edges(), size=int(failed_link/nb_ts))
                #print(f"{list(cur_topo.edges())=}")
                #print(f"{edges_to_be_removed=}")
                self.failed_link.extend(edges_to_be_removed)

        
    def __str__(self):
        return f"{self.name} {self.sync_algo.__name__} {self.topo[0].number_of_nodes()} {self.topo[0].number_of_edges()}" \
        f" {self.drift_rate[:5]} {self.drift_variance_bound[:5]} {self.sync_interval_ns} {self.slice_duration_ns}"
    def get_runtime_drift_variance(self):
        return para.get_runtime_drift_variance(self.rng, self.drift_variance_bound)
    #@jit(forceobj=True, looplift=True)
    def run(self, iter):
        """Run simulator for a period of time

        Args:
            iter: Sync iterations"""

        cur_time_ns = 0
        while cur_time_ns < iter * self.sync_interval_ns:
            # for exp of changing topology during operation
            if self.topo_update_ts is not None and (cur_time_ns // self.sync_interval_ns == self.topo_update_ts):
                print(f"change topo at ts {self.topo_update_ts}")
                self.topo = topo.generate_topo(self.nb_node, self.topo_func(self.rng, self.nb_node, self.nb_link, self.second_topo))

            cur_topo = utils.get_cur_topo(
                        cur_time_ns, 
                        slice_duration_ns=self.slice_duration_ns, 
                        topo=self.topo
                        )
            
            if self.failed_node:
                assert len(self.failed_link) == 0, "Only one type of failure at a time"
                assert len(cur_topo.nodes()) == self.nb_node, "Original topo has been modified"
                cur_topo = cur_topo.copy()
                cur_topo.remove_nodes_from(self.failed_node)

            elif self.failed_link:
                print(f"{self.failed_link=}")
                cur_topo = cur_topo.copy()
                cur_topo.remove_edges_from(self.failed_link)

            # Sync. Update errors and bounds
            if self.name == "syncwise" or self.name == "ptp" :
                self.cur_error, self.cur_bound, sync_count = \
                    self.sync_algo(
                        rng = self.rng, 
                        cur_error = self.cur_error, 
                        cur_bound = self.cur_bound, 
                        cur_topo = cur_topo,
                        hop_error_bound = self.hop_error_bound,
                        #hop_error_d = self.hop_error_d,
                        path_length_tracker = self.path_length_tracker,
                        path_length_counter = self.path_length_counter
                    )
            else:
                self.cur_error, self.cur_bound, sync_count = \
                    self.sync_algo(
                        rng = self.rng, 
                        cur_error = self.cur_error, 
                        cur_bound = self.cur_bound, 
                        cur_topo = cur_topo,
                        hop_error_bound = self.hop_error_bound,
                    )

            if self.offset_drift:
                #print(f"drift variance increase {self.get_runtime_drift_variance()[:20] * self.sync_interval_ns / 1e6}")
                self.cur_error = self.cur_error + self.get_runtime_drift_variance() * self.sync_interval_ns / 1e6
                self.cur_bound = self.cur_bound + self.drift_variance_bound * self.sync_interval_ns / 1e6
                if self.name != "firefly" and self.name != "dtp": # firefly and dtp use internal error
                    self.cur_error[0] = 0
                    self.cur_bound[0] = 0
            else:
                self.cur_error = self.cur_error + (self.drift_rate + self.get_runtime_drift_variance()) * self.sync_interval_ns / 1e6
                self.cur_bound = self.cur_bound + (self.drift_rate + self.drift_variance_bound) * self.sync_interval_ns / 1e6
                if self.name != "firefly" and self.name != "dtp": # firefly use internal error
                    self.cur_error[0] = 0
                    self.cur_bound[0] = 0
                
            # Record error
            if self.failed_node:
                # don't add failed node error into account
                counted_err = np.delete(copy.deepcopy(self.cur_error), self.failed_node)
                counted_bound = np.delete(copy.deepcopy(self.cur_bound), self.failed_node)
                self.errors.append(counted_err)
                self.bounds.append(counted_bound)
            else:
                self.errors.append(copy.deepcopy(self.cur_error))
                self.bounds.append(copy.deepcopy(self.cur_bound))
            

            # Time procede
            cur_time_ns += self.sync_interval_ns
        #print(f"{self.path_length_counter=}")
        print(f"{self.name} sync ctr: {sync_count}")
    
    def get_clock_errors(self, start_record_from=0) -> list:       
        if self.name == 'firefly':
            return self.get_internal_clock_errors(start_record_from) 
        return np.abs(self.errors[start_record_from:])
    
    def get_internal_clock_errors(self, start_record_from=0) -> list:
        internal_err = [errs - np.average(errs) for errs in self.errors[start_record_from:]]
        return np.abs(internal_err)
    def get_error_bound(self, start_record_from=0) -> list:
        return self.bounds[start_record_from:]