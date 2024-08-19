#!/usr/bin/env python3

import networkx as nx

nodes = [
        ( 1, { 'name':'a' } ),
        ( 2, { 'name':'b' } ),
        ( 3, { 'name':'c' } ),
        ( 4, { 'name':'d' } ),
        ( 5, { 'name':'e' } ),
        ( 6, { 'name':'f' } ),
        ( 7, { 'name':'g' } ),
        ( 8, { 'name':'h' } ),
        ( 9, { 'name':'i' } ),
        ( 10, { 'name':'j' } ),
        ( 11, { 'name':'k' } )
        ]

edges = [
    (1,2,{ 'att':1.0} ),
    (2,3,{ 'att':2.0} ),
    (2,1,{ 'att':2.5} ),
    (3,5,{ 'att':3.5} ),
    (4,5,{ 'att':2.2} ),
    (5,6,{ 'att':3.3} ),
    (6,7,{ 'att':4.5} ),
    (7,8,{ 'att':6.7} ),
    (8,9,{ 'att':1.3} ),
    (9,10,{ 'att':1.4} ),
    (9,11,{ 'att':1.8} )
    ]

def f( item ):
    return (item[0] == 1 or item[1] == 1)

G = nx.DiGraph()

new_edges = filter( f, edges )
print( list(new_edges) )
S = set([ 8, 9 ] )
print( list( filter( lambda x : x[0] == 1 or x[1] == 1 or x[0] in S, edges ) ) )

# for n in nodes:
#     G.add_node( n[0], **n[1] )
# 
# for e in edges:
#     G.add_edge( e[0], e[1], **e[2] ) 
# 
# print("{}".format( G.adj ))
# 
# for v, data in G.nodes( data=True ):
#     print("{} : {}".format( v, data ))
# 
# for s, t, data in G.edges( data=True ):
#     print("( {}, {} ): {}".format( s, t, data ))
# 
# 
# print("Tree ====")
# 
# T = nx.dfs_tree( G, source=1 )
# 
# T.update( edges = ..., nodes = ... )
# 
# for v in T:
#     T.add_node( v, **G.nodes[v] )
# 
# for s, t in T.edges():
#     T.add_edge( s, t, **G.edges[s,t] )
# 
# 
# 
# for v, data in T.nodes( data=True ):
#     print("{} : {}".format( v, data ))
# 
# for s, t, data in T.edges( data=True ):
#     print("( {}, {} ): {}".format( s, t, data ))
# 
