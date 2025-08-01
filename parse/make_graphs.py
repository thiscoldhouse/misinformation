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
        

def make_network_graph():
    make_graph(nodes, edges, 1)
    make_graph(nodes_with_dave, edges_with_dave, 2)    
    plt.show()


def make_graphs_no_dave(degrees=1):
    tainted_papers = ['mediabiasfactcheck.com']
    nodes = nodes_with_dave
    edges = edges_with_dave
    for i in range(degrees):
        remove_is = []
        print(f'Round {i}: tainted papers: {len(tainted_papers)}')
        for i, edge_pair in enumerate(edges):
            if edge_pair[0] in tainted_papers:
                tainted_papers.append(edge_pair[1])
            elif edge_pair[1] in tainted_papers:
                tainted_papers.append(edge_pair[0])
            else:
                continue

            remove_is.append(i)
        for i in sorted(remove_is, key=lambda i: i * -1):
            # order matters in list index iteration.
            # Start from the end
            edges.pop(i)
        for paper in tainted_papers:
            try:
                nodes.remove(paper)
            except ValueError:
                pass
    
    make_graph(nodes, edges)
    plt.show()

# def make_graphs_2_degree(degrees=2):
#     nodes = nodes_with_dave
#     edges = edges_with_dave

#     for edge_pair in edges:
        
    
#     make_graph(nodes, edges)
#     plt.show()
    
    
make_graphs_no_dave()
