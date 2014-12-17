import itertools
import networkx as nx
import matplotlib.pyplot as plt

def state_to_str(state, maxheight):
    state_chr = ['-' for _ in xrange(maxheight)]
    for pos in state:
        state_chr[pos] = 'x'
    state_str = ''.join(state_chr)
    return state_str

def juggling_graph(nballs, maxheight):
    assert(nballs <= maxheight)
    G = nx.DiGraph()
    for state in itertools.combinations(range(maxheight), nballs):
        G.add_node(state_to_str(state, maxheight))
    for state in itertools.combinations(range(maxheight), nballs):
        node_from = state_to_str(state, maxheight)
        if state[0] == 0:
            for h in xrange(1, maxheight + 1):
                if h in state:
                    continue
                state_to = [k - 1 for k in state[1:]] + [h - 1]
                node_to = state_to_str(state_to, maxheight)
                G.add_edge(node_from, node_to, height=h)
        else:
            node_to = state_to_str([k - 1 for k in state], maxheight)
            G.add_edge(node_from, node_to, height=0)
    return G

def show_juggling_graph(G):
    plt.title("Juggling 4 balls at most 7 units high")
    pos = nx.spring_layout(G, iterations=200, scale=2.0)
    node_colors = [nx.degree(G).values()]
    edge_colors = [edge[2]['height'] for edge in G.edges(data=True)]
    nx.draw(G, pos, 
        node_color=node_colors, edge_color=edge_colors, node_size=1800, node_shape='o',
        width=2.0, edge_cmap=plt.cm.cool, cmap=plt.cm.winter, with_labels=True,
        font_color='white', font_size=12)
    plt.show()

G = juggling_graph(nballs=4, maxheight=7)
print(G.number_of_nodes(), G.number_of_edges())
degree_sequence = sorted(nx.degree(G).values(), reverse=True)
from collections import Counter
cnt = Counter(degree_sequence)
print(cnt)
show_juggling_graph(G)
