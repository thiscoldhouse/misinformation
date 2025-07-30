import json
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from tabulate import tabulate


nodes = None
edges = None
edges_with_dave = None
with open('data-for-network.json', 'r+') as f:
    data = json.loads(f.read())
    nodes = data['nodes']
    edges = data['edges']
    nodes_with_dave = nodes[:]
    nodes_with_dave.append('mediabiasfactcheck.com')
    edges_with_dave = data['edges_with_dave']
    edges_with_dave.extend(data['edges'])


def make_tables():
    def make_counts(nodes, edges):
        counts = []
        for node in nodes:
            count = 0
            for edge in edges:
                if node == edge[0] or node==edge[1]:
                    count += 1
            counts.append(count)
            print(counts)
        return counts

    
    df1 = pd.DataFrame()
    df1['papers (no dave)'] = nodes
    df1['count (no dave)'] = make_counts(nodes, edges)
    df2 = pd.DataFrame()
    df2['papers (with dave)'] = nodes_with_dave
    df2['count (with dave)'] = make_counts(nodes_with_dave,
                                          edges_with_dave)
    print(tabulate(
        df1.sort_values(
            by=['count (no dave)'], ascending=False
        )[:10],
        headers='keys',
        tablefmt='psql'        
    ))
    print(tabulate(
        df2.sort_values(
            by=['count (with dave)'], ascending=False
        )[:10],
        headers='keys',
        tablefmt='psql'
        
    ))
    
make_tables()

def make_network_graph():
    def make_graph(nodes, edges, fignumber=1):    
        plt.figure(fignumber)
        G = nx.DiGraph()
        for node in nodes:
            G.add_node(node[:15])
        for edge in edges:
            edge = (e[0:15] for e in edge)
            G.add_edge(*edge)

        G.remove_nodes_from(list(nx.isolates(G)))
        node_sizes = [100 * G.degree(n) for n in G.nodes()]
        node_colors = [G.degree(n) for n in G.nodes()]

        pos = nx.spring_layout(G, k=0.15, iterations=20)
        nx.draw(
            G, pos,
            with_labels=True,
            node_size=node_sizes,
            node_color=node_colors,
            cmap=plt.cm.viridis,
            edge_color='gray',
            linewidths=0.5,
            font_size=4
        )

    make_graph(nodes, edges, 1)
    make_graph(nodes_with_dave, edges_with_dave, 2)    
    plt.show()
    
make_network_graph()
