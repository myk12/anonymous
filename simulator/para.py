import numpy as np
import matplotlib.pyplot as plt

drift_bound = 100
default_drift_variance_bound = 50
hop_error_bound = 5
#rng = np.random.default_rng(seed=42)  # set the seed

def get_hop_error(rng, hop_error_bound = hop_error_bound):
    err = rng.normal(loc=0.0, scale=hop_error_bound/3)
    return np.clip(err, -hop_error_bound, hop_error_bound)
    return err

def get_path_asymmetry(rng, asymmetry_bound = 10):
    # path asymmetry incurred when sync through multiple hops
    # +-20ns is the filterred value considering queuing and link length difference in DCNs
    err = rng.uniform(-asymmetry_bound, asymmetry_bound)
    return err
def get_runtime_drift_variance(rng, drift_variance_bound_list):
    runtime_drift_variance = np.array([rng.uniform(-bound, bound) for bound in drift_variance_bound_list])
    #runtime_drift_variance = np.array([rng.uniform(-bound*2, bound*0) for bound in drift_variance_bound_list])
    #runtime_drift_variance = np.array([rng.choice([-bound, bound, bound]) for bound in drift_variance_bound_list])
    #runtime_drift_variance = np.array([rng.normal(loc=0.0, scale=bound) for bound in drift_variance_bound_list])
    #print(f"{runtime_drift_variance=}")
    return runtime_drift_variance
def gen_normal_distribution(rng, nb_node, d, bound=200):
    """Generate gauss distribution and clip
    """
    #rng = np.random.default_rng(seed=42)  # set the seed
    arr = rng.normal(loc=0.0, scale=d/3, size=nb_node)
    #arr = np.clip(arr, -bound, bound)
    
    return arr
def gen_drift(rng, nb_node, drift_bound):
    """max 200ppm"""
    if drift_bound == None:
        drift_bound = 40
    drift = gen_normal_distribution(rng, nb_node=nb_node, d = drift_bound)
    drift[0] = 0
    return drift

def gen_drift_variance(rng, nb_node, dv_bound = None):
    """max 
    source: Graham, NSDI'22"""
    if dv_bound is None:
        dv_bound = default_drift_variance_bound
    dv = rng.uniform(0, dv_bound, size = nb_node)
    dv[0] = 0
    return dv

def gen_drift_variance_tree(rng, nb_node, dv_bound = None):
    """max 
    source: Graham, NSDI'22"""
    if dv_bound is None:
        dv_bound = default_drift_variance_bound
    dv = rng.uniform(0, dv_bound, size = nb_node)
    dv[1:] = np.sort(dv[1:])[::-1]
    dv[0] = 0
    #dv = np.abs(gen_normal_distribution(rng=rng, nb_node=nb_node, bound=dv_bound, three_d=dv_bound))
    #dv = dv_bound - dv
    #dv = np.array([dv_bound] * nb_node)
    return dv

def draw_drift_pdf_hist(drift):
    plt.hist(drift, bins = np.arange(-70,71,2), density=True,
             edgecolor='black')
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y * 100:.0f}%'))

    plt.tick_params(axis='both', which='major', labelsize=30)
    plt.xticks(range(-60,61,20))
    #plt.yticks(np.arange(0, 0.21, 0.05), size = 20)
    plt.xlim(-35, 35)
    #plt.ylim(0,0.21)
    plt.xlabel("Clock drift (ppm)", fontsize = 30)
    plt.ylabel("Probability Density", fontsize = 30)
    plt.subplots_adjust(bottom=0.21, left = 0.22, hspace = 0.0)
    plt.subplots_adjust(bottom=0.21, left = 0.19, hspace = 0.0)
    plt.grid()
    #plt.show()
    #plt.savefig(f"drifts/drift{drift_id}.pdf")
    plt.savefig(f"drift_pdf.pdf")
    #plt.clf()

if __name__ == "__main__":
    rng = np.random.default_rng(seed=42)
    drift = gen_drift(rng, 1024, 20)
    draw_drift_pdf_hist(drift)