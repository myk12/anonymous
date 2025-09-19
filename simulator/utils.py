import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

def get_cur_topo(cur_time_ns, slice_duration_ns, topo) -> nx.Graph:
    nb_slice = len(topo.keys())
    cur_slice = (cur_time_ns // slice_duration_ns) % nb_slice
    #print(f"{cur_slice=}")
    return topo[cur_slice]

def get_neighbors(graph : nx.Graph, node : int) -> list[int]:
    return list(graph.neighbors(node))


##### draw

color_map = {
    "syncwise"            :   '#DC3220',
    "graham"          :   '#994F00',
    "firefly_adapted"   :   "#D35FB7",
    "firefly"   :   "#D35FB7",
    "ptp":   '#0C7BDC',
    "dtp"           :   '#40B0A6',
    "dtp_adapted"   :   '#40B0A6',
}

name_map = {
    #"syncwise"            :   'Our Solution',
    "syncwise"            :   'SyncWise (RDCN)',
    "graham"          :   'Graham (Adapted to RDCN)', #'Graham\n(Adapted)',
    "firefly"   :   'Firefly (Static DCN)', #'Firefly\n(on Static)',
    "ptp" :   'Sundial (Static DCN)', #'Sundial\n(on Static)',
    "dtp" :  'DTP (Static DCN)', #'DTP\n(on Static)',
    #"dtp_adapted" :  'DTP\n(Adapted)',

    'syncwise[1]'            :   'SyncWise[1]',
}

def gen_label(name, value):
    if name == "syncwise":
        return f"SyncWise ({value}ns)"
        #return f"Our Solution ({value}ns)"
    if name == "graham":
        return f"Graham ({value}ns)\n(Adapted)"
        return f"Graham ({value}ns)\n(Adapted)"
    if name == "firefly":
        return f"Firefly ({value}ns)\n(on Static)"
        return f"Firefly ({value}ns)\n(on Static)"
    if name == "ptp":
        return f"Sundial ({value}ns)\n(on Static)"
        return f"Sundial ({value}ns)\n(on Static)"
    if name == "dtp":
        return f"DTP ({value}ns) (on Static)"
        return f"DTP ({value}ns)\n(on Static)"
    print(f"name {name} not found.")
def draw_cdf(data_dict, name):
    """
    Draw CDF from a dictionary where key is the legend and value is the data.
    All CDF lines are plotted in one matplotlib figure.
    
    Parameters:
    data_dict (dict): A dictionary where keys are legend labels and values are data arrays
    """
    #plt.figure(figsize=(10, 6))
    
    for label, data in data_dict.items():
        #print(f"{label=}\n{data=}")
        data = np.array(data).ravel()  # Return a flatten view
        data = np.abs(data)

        threshold = np.percentile(data, 99)
        print(f"{label} 99 tail value is {threshold}")

        threshold = np.percentile(data, 99.99)
        print(f"{label} 99.99 tail value is {threshold}")

        threshold = np.percentile(data, 100)
        print(f"{label} 100 tail value is {threshold}")
        data = np.clip(data, 0, threshold)

        cnt, b_cnt = np.histogram(data, bins=10000)
        pdf = cnt/sum(cnt)
        cdf = np.cumsum(pdf)
        
        plt.plot(b_cnt[1:], cdf,
                 color = color_map[label],
                 linestyle='-',
                 linewidth=5.0,
                 #label=label
                 #label=f"{name_map[label]} ({threshold:.1f})"
                 label=gen_label(label, int(threshold))
                 )

        plt.axvline(x=threshold, ymin=0, ymax=1,
                    color = color_map[label],
                    linestyle="--", 
                    linewidth=5.0,
                    #label=f"{label} (99.9%={threshold:.2f})"
                    #label=f"{name_map[label]} ({threshold:.1f})"
                    )

    font_size = 22
    #plt.ylim((0,0.999))
    plt.ylim((0,1))
    plt.xlim((0,130))
    plt.xticks(size = font_size)
    #plt.yticks([0,0.25,0.5,0.75,0.999], labels = ["0","0.25","0.5", "0.75",".999"], size = font_size)
    plt.yticks([0.25,0.5,0.75,1], size = font_size)
    
    """
    plt.legend(
        fontsize = font_size-4,
        loc="right",
        )
    """
    plt.xlabel("Clock Error (ns)", fontsize=font_size)
    plt.ylabel("CDF", fontsize=font_size)
    plt.grid(True)
    plt.subplots_adjust(bottom=0.15, left = 0.19, right=0.97, top = 0.95, hspace = 0.0)
    plt.show()
    #print(f"Save fig at {name}")
    #plt.savefig(f"{name}.pdf")

def draw_cdf_failure(data_dict, name):
    """
    Draw CDF from a dictionary where key is the legend and value is the data.
    All CDF lines are plotted in one matplotlib figure.
    
    Parameters:
    data_dict (dict): A dictionary where keys are legend labels and values are data arrays
    """
    #plt.figure(figsize=(10, 6))
    
    for label, data in data_dict.items():
        #print(f"{label=}\n{data=}")
        data = np.array(data).ravel()  # Return a flatten view
        data = np.abs(data)

        threshold = np.percentile(data, 99)
        print(f"{label} 99 tail value is {threshold}")

        threshold = np.percentile(data, 99.99)
        print(f"{label} 99.99 tail value is {threshold}")

        threshold = np.percentile(data, 100)
        print(f"{label} 100 tail value is {threshold}")
        data = np.clip(data, 0, threshold)

        cnt, b_cnt = np.histogram(data, bins=10000)
        pdf = cnt/sum(cnt)
        cdf = np.cumsum(pdf)
        
        plt.plot(b_cnt[1:], cdf,
                 #color = color_map[label],
                 linestyle='-',
                 linewidth=5.0,
                 #label=label
                 #label=f"{name_map[label]} ({threshold:.1f})"
                 #label=gen_label(label, int(threshold))
                 label=label
                 )

        plt.axvline(x=threshold, ymin=0, ymax=1,
                    #color = color_map[label],
                    linestyle="--", 
                    linewidth=5.0,
                    #label=f"{label} (99.9%={threshold:.2f})"
                    #label=f"{name_map[label]} ({threshold:.1f})"
                    )

    font_size = 22
    #plt.ylim((0,0.999))
    plt.ylim((0,1))
    plt.xlim((0,130))
    plt.xticks(size = font_size)
    #plt.yticks([0,0.25,0.5,0.75,0.999], labels = ["0","0.25","0.5", "0.75",".999"], size = font_size)
    plt.yticks([0.25,0.5,0.75,1], size = font_size)
    
    plt.legend(
        fontsize = font_size-4,
        loc="right",
        )
    plt.xlabel("Error Bound (ns)", fontsize=font_size)
    plt.ylabel("CDF", fontsize=font_size)
    plt.grid(True)
    plt.subplots_adjust(bottom=0.15, left = 0.19, right=0.97, top = 0.95, hspace = 0.0)
    #plt.show()
    print(f"Save fig at {name}")
    plt.savefig(f"{name}.pdf")

def draw_cdf_skew(data_dict, name):
    """
    Draw CDF from a dictionary where key is the legend and value is the data.
    All CDF lines are plotted in one matplotlib figure.
    
    Parameters:
    data_dict (dict): A dictionary where keys are legend labels and values are data arrays
    """
    #plt.figure(figsize=(10, 6))
    color_list = ["red", "blue", "green", "orange", "purple", "brown", "pink", "gray", "olive", "cyan"]
    
    for id, (label, data) in enumerate(data_dict.items()):
        #print(f"{label=}\n{data=}")
        data = np.array(data).ravel()  # Return a flatten view
        data = np.abs(data)

        threshold = np.percentile(data, 100)
        print(f"{label} 100 tail value is {threshold}")
        data = np.clip(data, 0, threshold)

        cnt, b_cnt = np.histogram(data, bins=10000)
        pdf = cnt/sum(cnt)
        cdf = np.cumsum(pdf)
        
        plt.plot(b_cnt[1:], cdf,
                 color = color_list[id],
                 linestyle='-',
                 linewidth=3.0,
                 #label=label
                 #label=f"{name_map[label]} ({threshold:.1f})"
                 label=f"{label} ({threshold:.1f})",
                 #label=label
                 )
        
        plt.axvline(x=threshold, ymin=0, ymax=1,
                    color = color_list[id],
                    linestyle="--", 
                    linewidth=3.0,
                    #label=f"{label} (99.9%={threshold:.2f})"
                    #label=f"{name_map[label]} ({threshold:.1f})"
                    )
        

    font_size = 22
    #plt.ylim((0,0.999))
    plt.ylim((0,1))
    plt.xlim((5,30))
    plt.xticks(size = font_size)
    #plt.yticks([0,0.25,0.5,0.75,0.999], labels = ["0","0.25","0.5", "0.75",".999"], size = font_size)
    plt.yticks([0.25,0.5,0.75,1], size = font_size)
    
    plt.legend(
        fontsize = font_size-4,
        loc="right",
        )
    plt.xlabel("Error Bound (ns)", fontsize=font_size)
    plt.ylabel("CDF", fontsize=font_size)
    plt.grid(True)
    plt.subplots_adjust(bottom=0.15, left = 0.19, right=0.97, top = 0.95, hspace = 0.0)
    #plt.show()
    print(f"Save fig at {name}")
    plt.savefig(f"{name}.pdf")

def draw_tail_trend(data_dict : dict[str, int], x, x_label, y_label, x_ticks=None, name=None):
    """
    Draw the trend of error tail
    """
    for label, tail in data_dict.items():
        tail = np.abs(tail)
        print(label, tail)
        plt.plot(
            x,
            tail,
            label = name_map[label],
            marker = 'o',
            markersize = 12,
            linewidth = 5.0,
            alpha = 0.8,
            color = color_map[label],
        )

    font_size = 22
    #plt.xlim((0,52))
    plt.ylim((1,180))
    if x_ticks is None:
        x_ticks = x
    plt.xticks(x_ticks, size = font_size)
    plt.yticks(size = font_size)
    plt.xlabel(x_label, fontsize=font_size)
    plt.ylabel(y_label, fontsize=font_size)
    #plt.legend(fontsize = font_size-4)
    plt.grid(True)
    plt.subplots_adjust(bottom=0.17, left = 0.17, right=0.95, top = 0.95, hspace = 0.0)
    #plt.show()
    if name is None:
        name = x_label
    #plt.show()
    plt.savefig(f"{name}.pdf")



    # Extract legend handles and labels
    handles, labels = plt.gca().get_legend_handles_labels()

    # --- create a new figure only for legend ---
    fig_legend = plt.figure()
    fig_legend.legend(
        handles,
        labels,
        loc="center",
        ncol=len(labels),     # all in one row
        frameon=False,        # no box around legend
    )

    # Remove axes completely
    fig_legend.gca().axis("off")

    # Save to file (vector-friendly for papers)
    fig_legend.savefig("legend.pdf", bbox_inches="tight")
    plt.close(fig_legend)

def draw_tail_trend_failure(data_dict : dict[str, int], x, x_label, y_label, x_ticks=None, name=None):
    """
    Draw the trend of error tail
    """
    for label, tail in data_dict.items():
        tail = np.abs(tail)
        print(label, tail)
        plt.plot(
            x,
            tail,
            label = label,
            marker = 'o',
            markersize = 12,
            linewidth = 5.0,
            alpha = 0.8,
            #color = color_map[label],
        )

    font_size = 22
    #plt.xlim((0,52))
    plt.ylim((15,40))
    if x_ticks is None:
        x_ticks = x
    x_ticks_in_percentage = [f"{tick}%" for tick in x_ticks]
    plt.xticks(x_ticks,x_ticks_in_percentage, size = font_size)
    plt.yticks(range(15,41,5), size = font_size)
    plt.xlabel(x_label, fontsize=font_size)
    plt.ylabel(y_label, fontsize=font_size)
    plt.legend(fontsize = font_size, loc="upper center")
    plt.grid(True)
    plt.subplots_adjust(bottom=0.17, left = 0.17, right=0.95, top = 0.95, hspace = 0.0)
    #plt.show()
    if name is None:
        name = x_label
    #plt.show()
    plt.savefig(f"failure.pdf")
def draw_error_scatter(data_dict : dict[str, np.ndarray]):
    """
    Draw scatter figure from a 2D array where x-axis is the first-dimension 
    and y-axis plot each data point of the second-dimension.
    
    Parameters:
    data (array-like): A 2D array where the first dimension represents x-axis values
                      and the second dimension represents y-axis values
    """

    for label, data in data_dict.items():
        #print(f"{label=}\n{data=}")
        data = np.abs(data)

        iters, nb_nodes = data.shape
        x = [i for i in range(iters) for _ in range(nb_nodes)]
        #print(x)

        plt.scatter(x, data.ravel(), label = label, #color=color_map[label],
                    #alpha=0.5, 
                    edgecolors='none')
    

    font_size = 22
    #plt.xlim((25,200))
    #plt.ylim((15,25))
    plt.xticks(size = font_size)
    plt.yticks(size = font_size)
    #plt.legend(fontsize = font_size-4)
    plt.xlabel("Sync Iteration", fontsize=font_size)
    plt.ylabel("Error Bound (ns)", fontsize=font_size)
    plt.grid(True)
    plt.subplots_adjust(bottom=0.15, left = 0.17, right=0.95, top = 0.95, hspace = 0.0)
    #plt.savefig(f"periodic_bound.pdf")
    plt.show()

def draw_error_scatter_topology_change(data_dict : dict[str, np.ndarray]):
    """
    Draw scatter figure from a 2D array where x-axis is the first-dimension 
    and y-axis plot each data point of the second-dimension.
    
    Parameters:
    data (array-like): A 2D array where the first dimension represents x-axis values
                      and the second dimension represents y-axis values
    """

    for label, data in data_dict.items():
        #print(f"{label=}\n{data=}")
        data = np.abs(data)
        #data = np.sort(data)[-30:]

        iters, nb_nodes = data.shape

        x_vals = []
        y_vals = []
        
        for i in range(iters):
            # take the top 10 values for this row
            top10 = np.sort(data[i])[-10:]
            
            x_vals.extend([i] * len(top10))   # repeat iteration index
            y_vals.extend(top10)              # corresponding values

        #x = [i for i in range(iters) for _ in range(nb_nodes)]
        #print(x)

        plt.scatter(x_vals, y_vals, 
                    #label = label, #color=color_map[label],
                    #alpha=0.5, 
                    edgecolors='none')
    
    plt.axvline(x=100, ymin=0, ymax=1,
                    linestyle="--", 
                    linewidth=3.0,
                    color="olive",
                    label=f"Topology Change"
                    )
    
    plt.axhline(y=21.5, xmin=0, xmax=0.43,
                    linestyle="--", 
                    linewidth=3.0,
                    color="red",
                    label=f"Old Error Bound"
                    )
    
    plt.axhline(y=22.3, xmin=0.53, xmax=1,
                    linestyle="--", 
                    linewidth=3.0,
                    color="brown",
                    label=f"New Error Bound"
                    )
    
    font_size = 22
    plt.xticks(range(0,200,40),size = font_size)
    plt.yticks(size = font_size)
    plt.xlim((25,200))
    plt.ylim((14,28))
    plt.legend(fontsize = font_size-4)
    plt.xlabel("Sync Interval", fontsize=font_size)
    plt.ylabel("Error Bound (ns)", fontsize=font_size)
    plt.grid(True)
    plt.subplots_adjust(bottom=0.15, left = 0.17, right=0.95, top = 0.95, hspace = 0.0)
    plt.savefig(f"bound_changes.pdf")
    #plt.show()

def draw_hop_count_cdf(hop_count_dict):

    color_list = ["#D55E00","#E69F00","#56B4E9","#009E73","#0072B2","#990000"]
    hop_limit = 5

    for id, (name, hop_ctr) in enumerate(hop_count_dict.items()):
        hop_ctr = {k: v for k, v in hop_ctr.items() if v > 0}
        hops = np.array(sorted(hop_ctr.keys()))
        counter = np.array([hop_ctr[k] for k in hops])
        cumsum = np.cumsum(counter)
        cdf = cumsum / cumsum[-1]
        
        if name == "Sundial":
            plt.plot(hops, cdf,
                linewidth=3.0,
                label=f"Sundial",
                color=color_list[id],
                marker='d',
                markersize=13
                )
        else:
            plt.plot(hops, cdf,
                    linewidth=3.0,
                    label=f"{int(name/1000)}µs",
                    color=color_list[id],
                    marker='d',
                    markersize=13
                    )
    font_size=22
    plt.xticks(range(1,1+hop_limit),size = font_size)
    plt.yticks([0.25,0.5,0.75,1], size = font_size)
    #plt.ylim((0,1))
    #plt.xlim((0,130))
    plt.xlabel("Clock Propagation Path Length", fontsize=font_size)
    plt.ylabel("CDF", fontsize=font_size)
    plt.legend(fontsize = font_size-4)
    plt.grid(True)
    plt.subplots_adjust(bottom=0.15, left = 0.19, right=0.97, top = 0.95, hspace = 0.0)
    plt.savefig("hop_count.pdf")
    #plt.show()

def check_converge(bounds):
    print(f"{len(bounds)} iter.")
    conv_flag = False
    for id1 in range(len(bounds)):
        for id2 in range(id1):
            if (bounds[id1] == bounds[id2]).all():
                print(f"Iter {id1} same as {id2}")
                return True
                conv_flag = True
    return conv_flag

