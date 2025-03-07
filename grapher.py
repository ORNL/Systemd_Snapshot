"""
grapher.py
Authors: Jason M. Carter, Mike Huettel
Date: December 2023
Version: 1.0

Licensed under the Apache License, Version 2.0 (the "License")
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Contributors:
    Oak Ridge National Laboratory

Description:  This is the main logic for the tool that creates the cytoscape graph. After the master 
    struct is built, systemd snapshot can run the graphing functions.  The graphing starts with the origin
    unit file ('default.target' by default) and searches through the master struct to find any and all 
    relationships that are created by that unit. It does this relationship mapping for each unit file 
    in the master struct.  For more information see doc strings.
"""

from collections import defaultdict

from element import ElementFactory, Element, Unit, Alias, Command, Executable, Library, String
from unit_file_lists import ms_only_keys



class Grapher:
    """Instances represent a single SystemD configuration inferred from static analysis of a filesystem

    Strategy:
    - Build a networkx graph with attributes as we parse the files generated by the static analysis tool.
    - Convert that graph into pandas dataframes.
    - Transfer the graph to Cytoscape using the py4cytoscape create from dataframe functions.

    There are more direct ways than the outline above; however, this provides us with a well-formed networkx
    graph, a pandas dataframe, and the ability to visualize it in Cytoscape.
    """
    # source and target are explicit
    EdgeFields = { 'interaction', 'subgraph', 'directed', 'edge_label_color', 'edge_line_type', 'source_arrow_shape', 'target_arrow_shape', 'edge_color' }

    # id is explicit
    VertexFields = { 'subgraph', 'node_label', 'node_label_color', 'node_label_width', 'node_fill_color', 'node_shape', 'node_height', 'node_width' }

    def __init__( self, system_name, log ):
        self.log = log
        self.system_name = system_name
        self.emap = dict()
        self.dset = set()
        self.G = None

        self.init_grapher()


    def init_grapher(self):
        """Import modules needed for graphing.
        
        Importing these conditionally allows us to run systemd snapshot and build a master
        struct on machines that don't have cytoscape or networkx installed without requiring each
        of those machines to install additional software.
        """
        global nx
        global p4c
        global pd

        import networkx as nx
        import py4cytoscape as p4c
        import pandas as pd                     # pandas dataframe for python cytoscape.
        
        return


    @staticmethod
    def make_edge_dataframe( G ):
        # pandas dataframe uses a dictionary of lists.
        edata = defaultdict(list)
        # for each edge
        for s, t, data in G.edges( data=True ):
            edata['source'].append( s )
            edata['target'].append( t )
            for field in Grapher.EdgeFields:
                if field in data:
                    edata[ field ].append( data[field] )
                else:
                    # must be here to meet the balanced dataframe requirement
                    edata[ field ].append( None )

        return pd.DataFrame( data = edata, columns = edata.keys() )

    @staticmethod
    def make_vertex_dataframe( G ):
        # pandas dataframe uses a dictionary of lists.
        vdata = defaultdict(list)
        # for each edge
        for v, data in G.nodes( data=True ):
            vdata['id'].append( v )
            for field in Grapher.VertexFields:
                if field in data:
                    vdata[ field ].append( data[field] )
                else:
                    # must be here to meet the balanced dataframe requirement
                    vdata[ field ].append( None )

        return pd.DataFrame( data = vdata, columns = vdata.keys() )

    def get_network_name( self ):
        """Uses only py4cytoscape"""
        # this still works and produces a list of all the network names in cytoscape.
        self.log.debug("Getting network name...")
        network_list = p4c.networks.get_network_list()
        nname = self.system_name
        i = 1
        # make names until you get something unique
        while ( nname in network_list ):
            nname = "{}.{}".format( self.system_name, i )
            i += 1
        self.system_name = nname
        self.log.debug("Finished getting network name: {}".format(self.system_name))
        return self.system_name

    def create_cytoscape_graph( self, master_struct, force = False ):
        """
        Args:
            master_struct:
            force:

        Returns:
            The networkx graph that was built and sent to cytoscape for rendering.
        """
        self.build( master_struct, force )
        edf = Grapher.make_edge_dataframe( self.G )
        vdf = Grapher.make_vertex_dataframe( self.G )

        gname = self.get_network_name()
        p4c.networks.create_network_from_data_frames( vdf, edf, title=gname )
        return self.G

    def transmit_to_cytoscape( self, G ):

        self.log.debug("Transmitting graph data to cytoscape...")
        edf = Grapher.make_edge_dataframe( G )
        vdf = Grapher.make_vertex_dataframe( G )
        gname = self.get_network_name()
        p4c.networks.create_network_from_data_frames( nodes=vdf, edges=edf, title=gname )
        self.log.debug("Finished transmitting graph data to cytoscape...")

    def multigraph_dump( self, G ):
        """Will dump the strange adjacency view of a MultiDiGraph from networkx
        
        TROUBLESHOOTING CODE.

        Args:
            G : the Multigraph
        """
        for uid, adj_udict in G.adj.items():
            print("vertex: {}".format( uid ))
            for vk, vv in G.nodes[ uid ].items():
                self.log.vdebug("\tv att: {} : {}".format( vk, vv ))

            print("\tAdjacency Information")

            for adj_vid, edge_key_dict  in adj_udict.items():

                # vertices adjacent to uid
                print("\tadj vertex: {}".format( adj_vid ))

                for uv_edge_id, edge_atts in edge_key_dict.items():

                    # u->v edge identifer because we could have mulitples
                    # and attributes
                    print("\t\tedge id: {} atts dict follows:".format( uv_edge_id ))
                    for att_key, att_value in edge_atts.items():
                        print("\t\t\t{}: {}".format( att_key, att_value ) )

    def build_tree( self, G, root, depth ):
        """Build and return a tree from G rooted at root that has maximum depth, depth.

        This is handy when you only want to investigate a small portion of the overall Systemd structure.
        Since it is hierarchical, the tree is a nice way to focus the lens to only those related items
        from that particular root.

        Args:
            G: A multigraph from which we want to extract a tree.
            root: the vertex identifier (a string pair) in G that will be the starting point for the tree.
            depth: how deep the tree will go (number of edges from root)

        Returns:
            A networkx tree graph WITH THE ATTRIBUTE from the original graph.

        Raises:
            Exception if the root node is NOT IN G.
            We could just return the empty graph, but that seems much less informative.
        """
        self.log.debug("Starting subtree build...")
        root_string = str(root)

        if root_string not in G:
            raise Exception( "Root: {} for tree is not in the systemd graph".format( root_string ))

        # The tree created here has the "skeleton" of what we need. It is incomplete because we are working
        # from a MultiDiGraph. In the graph we would like to derive from this tree there could be multiple
        # edges where this tree only has one. Also NetworkX DOES NOT transfer all the attributes we
        # have decorated our G with already; those need to be transfered.

        if depth > 0:
            T = nx.dfs_tree( G, source=str( root_string ), depth_limit=depth )
        else:
            # this will automagically search to the maximum depth it can.
            T = nx.dfs_tree( G, source=str( root_string ) )

        # T now has all the vertices and edges we want WITHOUT THE ATTRIBUTES and the possible extra edges.
        # G has all the attributes but doesn't know which ( V, E ) are in T.
        # Also, our output tree may have multiple edges between nodes, so we need another
        # MultiDiGraph

        Gp = nx.MultiDiGraph()
        for v in T:
            # T is a subgraph of G, so v can be assumed to be in G.
            Gp.add_node( v, **G.nodes[v] )

        for s, t in T.edges():
            # T is a subgraph of G, so s, t can be assumed to be in G.
            # We are transferring information from a MultiGraph, so we need to look at each possible
            # edge AND each of those edges may have a unique set of attributes. This loop transfers
            # those.
            for multi_edge_id, edge_atts in G.adj[s][t].items():
                Gp.add_edge( s, t, **edge_atts )
        
        self.log.debug("Finished subtree build...")
        return Gp

    def build( self, master_struct : dict, rebuild_graph = False ):
        """From a master file generated from the systemd_mapper tool (it is json), construct a new dictionary
        that we can use to construct an annotated graph.

        Args:
            master_struct: the data file with Systemd objects to use to build the graph.
            rebuild_graph: when True any existing graph will be replaced after rebuilding it.

        Returns:
            returned map: key -> xxx

        Raises:
        """
        self.log.debug("Building graph...")

        if not rebuild_graph and self.G:
            # if it is built and we don't want to force re-build, just return the previous built graph.
            return self.G

        self.G = nx.MultiDiGraph( name = 'systemd_graph' )

        # get this here, in case it is NOT the first item in the dictionary; we need it for 
        # certain elements. CAUTION: this path does NOT CURRENTLY end in /
        remote_path = master_struct['remote_path']

        efactory = ElementFactory( remote_path, self.log )

        for uid, data in master_struct.items():
            if uid in ms_only_keys:
                # this is a special object in the mapping that cannot be converted into an Element instance; skip it.
                continue

            if data['metadata']['file_type'] == 'dep_dir':
                # the dependency directory objects are not used because the SPECIFIC edge information is in the other
                # objects in the master structure.
                continue

            # The remaining objects in the master structure may produce a collection of Element instances we want to
            # add to the graph as vertices. 
            for e in efactory.make_element( uid, data, master_struct ):
                self.log.debug( "made element: {}".format( e.key() ))
                
                if repr(e) in self.G:
                    # This is troubleshooting code.
                    self.log.debug("The vertex: {} is already in the graph.".format( e.key() ))

                # Objects may produce vertices that have ALREADY BEEN ADDED to the
                # graph (see warnings above), that is fine: NetworkX will just update the attributes as needed.
                e.add_to_graph( self.G )

                # Each Element instance knows how to add edges to the graph; these are its children.
                # Vertices may be added here as well and their attributes later updated above.

                e.make_graph_edges( self.G )

        self.log.debug("Finished building graph...")
        return self.G
    
