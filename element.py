"""
element.py
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

Description:  This module parses a master struct to create a graph of all unit files and 
    symbolic links found.  Since dependency directories have all items within them recorded 
    individually, the dependency directory entries are ignored.
"""

import re

from pathlib import Path

import colors
import unit_file_lists

class ElementFactory:
    """A class whose instances construct Element instances for use in graphing Systemd
    data.
    """

    def __init__( self, remote_path, log ):
        """ElementFactory Constructor. These are used as nodes in a networkx graph that 
        can be rendered in Cytoscape.

        Primarily I am doing this so I don't have to continually specify the remote path.
        There may be other reasons later.

        Args:
            remote_path: the filesystem prefix path TO THE FIRMWARE root directory
            log: logger for messages.
        """
        self.remote_path = remote_path
        self.log = log

    def make_element( self, uid, data, master_struct ):
        """Make elements (derived from systemd artifacts) that can act as graph nodes.
    
        We use the term Element because these items could be converted into nodes or edges.

        This is a generator because multiple elements can be created from a single unit
        file.

        Args:
            uid: The master structure dictionary key that is associated with data
            data: The data dictionary that is associated with uid.
            master_struct: dictionary used for libs, files, and strings for elements
        
        Yields:
           Instances of Element type: Alias, DropInFile, Unit, Exec, Directory 

        Raises:
            ValueError: if the file_type in the data['metadata'] dictionary is not 
                        one of sym_link, unit_file, dep_dir
        """
        ftype = data['metadata']['file_type']
    
        if ftype == 'sym_link':
            yield Alias( uid, data, self.log )
    
        elif ftype == 'unit_file':
            # Split out two different items in the graph from a element file type:
            # 1. DropIn "conf" files
            # 2. Systemd Element files
            p = Path( uid )
    
            # p is a file so look at the parent directory suffix.
            if p.parent.suffix == '.d':
                # p is a file, p.parent is the directory, and p.parent.suffix allows us to detect
                # whether this is a Drop In path.
                elt = DropInFile( uid, data, self.remote_path, master_struct, self.log )
                yield elt

            else:
                # p is a unit file that possibly contains directives for working with service processes.
                elt = Unit( uid, data, self.remote_path, master_struct, self.log )
                yield elt

            # This is ugly and probably should be refactored with a more elegant solution.
            for command in elt.get_children():
                # Unit children are Commands
                yield command
                for executables in command.get_children():
                    # Command children are Executables
                    yield executables
                    for libs_and_strings in executables.get_children():
                        # Executable children are Libraries and Strings
                        yield libs_and_strings
    
        elif ftype == 'dep_dir':
            # dependency directory information is not needed during graph construction; the dependencies
            # will be derived from the Systemd directives.
            return
    
        else:
            raise ValueError('element file type: {} is not recognized'.format( ftype ) )

class Element:
    """Instances are single elements in a Systemd graph; this is the base class for all elements in a graph.

    Elements are uniquely identified by a pair of strings: ( id, type ) where
        id: the unit name, directory path, library name, other string
        type: one of { ELEMENT, DIRECTORY, ALIAS, LIBRARY, UNIT, EXEC.*, EXECUTABLE, DROPIN, STRING.* }
        
    This key is used for dictionaries, node identifiers, etc.

    We can look up Elements in a dictionary by their key: ( id, type ) pairs. They have hashcodes and equals methods.
    """
    TypeKey = 'ELEMENT'
    EdgeDirectives = unit_file_lists.unit_dependency_opts
    EdgeDirectives.append( 'OnFailure' )

    @staticmethod
    def get_default_vertex_attrs( subgraph, node_label ):
        """Return a dictionary containing the default Cytoscape vertex attributes

        The following attributes (keys in the attrs dict) on vertices are passthrough: 
        the values assigned here are used directly to determine the formatting of the graph.
        The Cytoscape properties are the SAME NAME BUT CAPITALIZED.

        node_fill_color,
        node_label,
        node_label_width,
        node_shape,
        node_height,
        node_width

        Args:
            subgraph:
            node_label:

        Returns:
            A dictonary containing the attributes for this vertex; the keys are special.
        """
        attrs = {}

        attrs['subgraph'] = subgraph
        attrs['node_label'] = node_label
        attrs['node_label_color'] = colors.basic_colors['black']
        attrs['node_label_width'] = Element.get_label_width( node_label )
        attrs['node_fill_color'] = colors.light_colors['blue']
        attrs['node_shape'] = 'ROUND_RECTANGLE'
        attrs['node_height'] = Element.get_node_height( node_label )
        attrs['node_width'] = Element.get_node_width( node_label )

        return attrs

    @staticmethod
    def get_default_edge_attrs( subgraph, edge_label ):
        """Return a dictionary containing the default Cytoscape edge attributes

        The following attributes (keys in the attrs dict) on edges are passthrough: 
        the values assigned here are used directly to determine the formatting of the graph.
        The Cytoscape properties are the SAME NAME BUT CAPITALIZED.

        edge_line_type,
        source_arrow_shape,
        target_arrow_shape

        Args:
            subgraph:
            edge_label:

        Returns:
            A dictonary containing the attributes for this edge; the keys are special.
        """
        attrs = {}

        attrs['interaction'] = edge_label
        attrs['subgraph'] = subgraph
        attrs['directed'] = True
        attrs['edge_label_color'] = colors.basic_colors['black']
        attrs['source_arrow_shape'] = 'NONE'
        attrs['target_arrow_shape'] = 'DELTA'   # this is more arrow-like.
        attrs['edge_line_type'] = 'SOLID'
        attrs['edge_color'] = colors.basic_colors['black']

        return attrs

    @staticmethod
    def get_label_width( label_string ):
        """Compute the width of the label based on the string it will contain.

        Args:
            label_string: the string to use to size the node

        Returns:
            The label width as a float
        """
        width = len( label_string ) * 5.0
        if width < 100.0:
            return 100.0
        elif width > 300.0:
            return 300.0
        return width

    @staticmethod
    def get_node_height( label_string ):
        """Compute the size of the graph node based on the string it will contain.

        Args:
            label_string: the string to use to size the node

        Returns:
            The height as a float
        """
        height = 15.0 * len( label_string )/50.0
        if height < 30.0:
            return 30.0
        return height

    @staticmethod
    def get_node_width( label_string ):
        """Compute the size of the graph node based on the string it will contain.

        Args:
            label_string: the string to use to size the node

        Returns:
            The width as a float
        """
        width = len( label_string ) * 5.0
        if width < 100.0:
            return 100.0
        elif width > 300.0:
            return 300.0
        return width

    def __init__( self, uid, data, log ):
        """Constructor for an element

        Args:
            uid: unique identifier for this Element
            data: the object that describes this element, e.g., the Systemd Directives.
            log: logger for tracing and errors.

        """
        self.log = log

        # Elements are uniquely identified by their UID name (could be a unit name or path) and a type.
        self._key = ( uid, Element.TypeKey )

        # Data derived by our tools.
        self.metadata = {}

        if 'metadata' in data:
            self.metadata = data['metadata']

        # Options and directives provided in Systemd Unit files.
        # this could be the empty dictionary.
        self.properties = { k : data[k] for k in set( data.keys() ) - { 'metadata' } }

        # The set of Element instances that are direct children of this Element.
        self._children = set()

    def id( self ):
        """Return the ID portion of this Element's key

        Returns:
            A string; this is usually a path or the name of a unit file.
        """
        return self._key[0]

    def get_type( self ):
        """Return the TYPE portion of this Element's key

        Returns:
            A string; this is a standardized string, e.g., UNIT, that identifies the type of Element.
        """
        return self._key[1]

    def add_to_graph( self, G ):
        """An interface definition: Add this Element instance to graph G

        Args:
            G: the graph to add this Element to.
        """
        pass

    def get_children_keys( self ):
        """Return this Element's children as a set of id pairs: ( string id, element type ).

        NOTE: If the get_children method does not return a list of Element instances, this needs to
        be OVERRIDDEN to provide the correct information (i.e., a pair for instances does not have
        a key() method.

        Returns:
            A set of pairs of strings; these pairs are expected to be valid keys that can map to 
            instances of Element.
        """
        return { c.key() for c in self.get_children() }

    def get_children( self ):
        """Return this Element's children as a set of Element instances.

        This is meant to be overridden to fill up the children instance variable.

        Returns:
            The set of children of this Element as Element instances. The directed relationship is ( Element, child )
        """
        return self._children

    def key( self ):
        """Get this Element's key; once set this should be immutable.

        Returns:
            A pair of strings; this should not change once set.
        """
        return self._key

    def __str__( self ):
        """Get the string representation of this Element

        Returns:
            A string that represents this element; the type is written first.
        """
        return "{}: {}".format( self.get_type(), self.id() )

    def __repr__( self ):
        """Get the object representation of this Element

        Returns:
            The repr of the key pair: ( string, string ) that uniquely identifies this Element
        """
        return repr( self._key )

    def __hash__( self ):
        """Return the hashcode for this Element

        Returns:
            The hashcode for this Element is the hashcode of its key pair.
        """
        return hash( self.key() )

    def __eq__( self, other ):
        """Equals predicate.

        Returns:
            True if this Element is equivalent to other; False otherwise.
        """
        if isinstance( other, Element ):
            return self.key() == other.key()

        return NotImplemented

    def get_data( self, key ):
        """In this Master Structure's metadata mapping, get the object that key maps to.

        Args:
            key: the name of the metadata field to return.

        Returns:
            The object key maps to in the Element's metadata field, or None if the key is
            not in the metadata.
        """
        try:
            return self.metadata[ key ]
        except KeyError as error:
            self.log.warning("Key: {} not in the metadata of this unit.".format( key ))
            return None

    def set_data( self, key, value ):
        """In this Master Structure's metadata mapping, set the key -> value mapping.

        Args:
            key: the name of the metadata field to set.
            value: the value that key maps to.

        Returns:
            Nothing.
        """
        if key not in self.metadata:
            self.metadata[ key ] = value
        elif isinstance( self.metadata[ key ], list ):
            self.metadata[ key ].append( value )
        else:
            self.log.warning("Replacing metadata[ {} ] = {} with {}".format( key, self.metadata[key], value ))
            self.metadata[ key ] = value

    def has_property( self, prop ):
        """Predicate that indicates whether a certain property name is in this element's properties dictionary.

        Args:
            prop: the property string name to look up.

        Returns:
            True: this dict has that key; False otherwise.
        """
        return prop in self.properties

    def get_property( self, prop ):
        """In this Master Structure's mappings, get the object that key maps to; these are Systemd Directives.

        Args:
            key: the name of the Directive to return.

        Returns:
            The object key maps to in the Element's Systemd Directives, or None if the key is
            not in the metadata.
        """
        try:
            return self.properties[ prop ]
        except (IndexError, KeyError) as error:
            self.log.warning("Property Key: {} not in the properties of this unit.".format( prop ))
            return None

class Alias( Element ):
    """A symbolic link to a unit file. The term Alias is used in Systemd documentation.""" 
    TypeKey = 'ALIAS'

    @staticmethod
    def vertex_attrs( node_label ):
        """Return a dictionary containing the Alias Cytoscape vertex attributes

        Args:
            node_label:

        Returns:
            A dictonary containing the attributes for this vertex; the keys are special.
        """
        # sets subgraph, node_label, node_label_width, node_height, node_width
        attrs = Element.get_default_vertex_attrs( Alias.TypeKey, node_label )

        # set the specifics for node_label_color, node_fill_color, node_shape
        # attrs['node_label_color'] = colors.basic_colors['white']
        attrs['node_fill_color']  = colors.element_fill_colors[Alias.TypeKey]
        attrs['node_shape']       = 'ROUND_RECTANGLE'

        return attrs

    @staticmethod
    def edge_attrs( edge_label=None ):
        """Return a dictionary containing the Alias Cytoscape edge attributes

        Args:
            edge_label:

        Returns:
            A dictonary containing the attributes for this edge; the keys are special.
        """
        if not edge_label:
            edge_label = Alias.TypeKey

        attrs = Element.get_default_edge_attrs( Alias.TypeKey, edge_label )

        # set the specifics for edge_label_color, edge_line_type, edge_color
        attrs['edge_line_type']     = 'EQUAL_DASH'
        attrs['edge_color']         = colors.purple_colors['dark']

        return attrs

    def __init__( self, uid, data, log ):
        """Constructor for an Alias Element

        Args:
            uid: the unique identifier string.
            data: the dictionary from master structure that contains Alias information.
            log: logger for messaging.
        """
        super().__init__( uid, data, log )
        self._key = ( self.id(), Alias.TypeKey )

        self.source = self.id()
        self.target = "{}{}".format( self.get_data( 'sym_link_target_path' ), self.get_data( 'sym_link_target_unit' ) )

    def get_vertex_attrs( self ):
        """Return a dictionary containing the Alias Cytoscape vertex attributes

        Returns:
            A dictonary containing the attributes for this vertex; the keys are special.
        """
        return Alias.vertex_attrs( self.id() )

    def get_edge_attrs( self, edge_label ):
        """Return a dictionary containing the edge Cytoscape edge attributes

        Args:
            edge_label:

        Returns:
            A dictonary containing the attributes for this edge; the keys are special.
        """
        return Alias.edge_attrs( edge_label )

    def get_children_keys( self ):
        """For an Alias, the children and NOT Element INSTANCES, so we just return the list of pairs of strings."""
        if not self._children:
            self.get_children()

        return self._children

    def get_children( self ):
        if not self._children:
            self._children.add( ( self.get_data('sym_link_target_unit'), 'UNIT' ) )
        return self._children

    def add_to_graph( self, G ):
        """Add this Element instance to graph G

        Args:
            G: the graph to add this Element to.
        """
        G.add_node( repr(self), **Alias.vertex_attrs( self.id() ) )

    def make_graph_edges( self, G ):
        for c in self.get_children_keys():
            G.add_edge( repr(self), repr(c), **Alias.edge_attrs( Alias.TypeKey ) )

class Unit( Element ):
    """A systemd unit file; Unit Elements are NOT uniquely identified by full path."""
    TypeKey = 'UNIT'
    TemplateMatcher = re.compile( '^\S+@\S+\.\S+$' )

    @staticmethod
    def vertex_attrs( node_label ):
        """Return a dictionary containing the Unit Cytoscape vertex attributes

        Args:
            node_label:

        Returns:
            A dictonary containing the attributes for this vertex; the keys are special.
        """
        # sets subgraph, node_label, node_label_width, node_height, node_width
        attrs = Element.get_default_vertex_attrs( Unit.TypeKey, node_label )

        # set the specifics for node_label_color, node_fill_color, node_shape
        attrs['node_label_color'] = colors.basic_colors['white']
        attrs['node_fill_color']  = colors.element_fill_colors[Unit.TypeKey]
        attrs['node_shape']       = 'RECTANGLE'

        return attrs

    @staticmethod
    def edge_attrs( edge_label ):
        """Return a dictionary containing the edge Cytoscape edge attributes
        Args:
            edge_label:

        Returns:
            A dictonary containing the attributes for this edge; the keys are special.
        """
        # sets directed, subgraph, interaction are set here
        attrs = Element.get_default_edge_attrs( Unit.TypeKey, edge_label )

        attrs['edge_line_type']     = 'SOLID'
        attrs['edge_color']         = colors.green_colors['dark']

        return attrs


    def __init__( self, path, data, remote_path, master_struct, log ):
        """
        Args:
            path: The unit file's path
            data: The master structure data dictionary.
            remote_path: the base path on this filesystem to the firmware image;
                needed to file and process any executables within the firmware.
            log: message logger.
        """
        super().__init__( path, data, log )

        self.remote_path = remote_path
        self.master_struct = master_struct

        # for files, the uid is just their unit name.
        self._key = ( Path( path ).name, Unit.TypeKey )

    def get_vertex_attrs( self ):
        """Return a dictionary containing the Unit Cytoscape vertex attributes

        Returns:
            A dictonary containing the attributes for this vertex; the keys are special.
        """
        return Unit.vertex_attrs( self.id() )

    def get_edge_attrs( self, edge_label ):
        """Return a dictionary containing the Unit Cytoscape edge attributes

        Args:
            edge_label:

        Returns:
            A dictonary containing the attributes for this edge; the keys are special.
        """
        return Unit.edge_attrs( edge_label )

    def get_children( self ):
        """Get the set of "direct" children for this Unit. These are Command Element instances.

        Returns:
            the set of Unit children that are associated with Commands that are executed.
        """
        if not self._children:
            # the child set is empty.
            for exec_directive in Command.Directives:
                if self.has_property( exec_directive ):
                    # this unit contains an "Exec" directive; these will be constructed as distinct nodes.
                    # each execfile can perform multiple commands although this is not usual.
                    exec_elt = Command( exec_directive, self.get_property( exec_directive ), self.remote_path, self.master_struct, self.log )
                    self._children.add( exec_elt )

        return self._children

    def get_property_children( self, prop ):
        """Get the set of "property" children for this Unit. These are Unit Instances that are associated
        with specific directives in a Unit file's definition.

        Args:
            prop: The Systemd directive property string to use as a key.

        Returns:
            The set of Unit Instances that are associates with dependency Systemd directives.
        """
        s = set()
        if prop in Element.EdgeDirectives and self.has_property( prop ):
            for c in self.get_property( prop ):
                s.add( ( c, 'UNIT' ) )
        return s

    def get_sequencing_children( self, prop ):
        """Get the set of "sequencing" children for this Unit. These are Unit Instances that are associated
        with the After= and Before= directives that establish Unit ordering.

        Args:
            prop: The Systemd directive property string to use as a key.

        Returns:
            The set of Unit Instances that are associates with sequencing Systemd directives.
        """
        s = set()
        if prop in ('After', 'Before') and self.has_property( prop ):
            for c in self.get_property( prop ):
                s.add( ( c, 'UNIT' ) )
        return s

    def add_to_graph( self, G ):
        """Add this Element instance to graph G

        Args:
            G: the graph to add this Element to.
        """
        G.add_node( repr(self), **Unit.vertex_attrs( self.id() ) )

    def make_graph_edges( self, G ):
        """Creates all the edges (and possibly new nodes) based on information in this Unit Element.

        Args:
            G: the networkx graph object for this Systemd specification.
        """
        for c in self.get_children():
            # Unit edge attributes for now with the label being the type of command.
            G.add_edge( repr(self), repr(c), **self.get_edge_attrs( c.exec_directive ) )

        for p in Element.EdgeDirectives:
            for c in self.get_property_children( p ):

                # There are some cases where nodes are created here but NOT normally.
                # we need to establish their attributes.
                if repr(c) not in G:
                    label = 'UNKNOWN'
                    if Unit.TemplateMatcher.match( c[0] ):
                        label = 'TEMPLATE'
                    G.add_node( repr(c), **Element.get_default_vertex_attrs( label, c[0] ) )

                G.add_edge( repr(self), repr(c), **self.get_edge_attrs( p ) )

        for seq in ( 'After', 'Before' ):
            for c in self.get_sequencing_children( seq ):
                if repr(c) not in G:
                    label = 'UNKNOWN'
                    G.add_node( repr(c), **Element.get_default_vertex_attrs( label, c[0] ) )

                if seq == 'After':
                    # this unit comes AFTER the one in the list (edge direction opposite)
                    G.add_edge( repr(c), repr(self), **self.get_edge_attrs( seq ) )
                else:
                    G.add_edge( repr(self), repr(c), **self.get_edge_attrs( seq ) )
    
class DropInFile( Element ):
    """DropIn files are 'unit_file' types that are named using their full path because the name could be duplicated.

    These files contain Systemd Directives that may include Exec* directives that should be parsed as well.
    """
    TypeKey = 'DROPIN'
    TemplateMatcher = re.compile( '^\S+@\S+\.\S+$' )

    @staticmethod
    def vertex_attrs( node_label ):
        """Return a dictionary containing the DropInFile Cytoscape vertex attributes

        Args:
            node_label:

        Returns:
            A dictonary containing the attributes for this vertex; the keys are special.
        """
        # sets subgraph, node_label, node_label_width, node_height, node_width
        attrs = Element.get_default_vertex_attrs( DropInFile.TypeKey, node_label )

        # set the specifics for node_label_color, node_fill_color, node_shape
        attrs['node_label_color'] = colors.basic_colors['white']
        attrs['node_fill_color']  = colors.element_fill_colors[DropInFile.TypeKey]
        attrs['node_shape']       = 'RECTANGLE'

        return attrs

    @staticmethod
    def edge_attrs( edge_label ):
        """Return a dictionary containing the DropInFile Cytoscape edge attributes

        Args:
            edge_label:

        Returns:
            A dictonary containing the attributes for this edge; the keys are special.
        """
        # sets directed, subgraph, interaction are set here
        attrs = Element.get_default_edge_attrs( DropInFile.TypeKey, edge_label )

        # set the specifics for edge_label_color, edge_line_type, edge_color
        attrs['edge_line_type']     = 'EQUAL_DASH'
        attrs['edge_color']         = colors.green_colors['light']
        return attrs

    def __init__( self, uid, data, remote_path, master_struct, log ):
        """Constructor for a DropInFile Instance

        Args:
            uid:
            data:
            remote_path:
            log:
        """
        super().__init__( uid, data, log )
        self._key = ( uid, DropInFile.TypeKey )
        self.remote_path = remote_path
        self.master_struct = master_struct

        # this could be a template instantiation and not exist in our vertex set.
        self.target = Path( self.id() ).parent.stem

    def get_vertex_attrs( self ):
        """Return a dictionary containing the DropInFile Cytoscape vertex attributes

        Returns:
            A dictonary containing the attributes for this vertex; the keys are special.
        """
        return DropInFile.vertex_attrs( self.id() )

    def get_edge_attrs( self, edge_label ):
        """Return a dictionary containing the DropInFile Cytoscape edge attributes

        Args:
            edge_label:

        Returns:
            A dictonary containing the attributes for this edge; the keys are special.
        """
        return DropInFile.edge_attrs( edge_label )

    def get_children( self ):
        """Return this DropInFile's children as a set of DropInFile instances.

        Returns:
            The set of children of this Element as Command instances.
        """
        if not self._children:
            # the child set is empty.
            for exec_directive in Command.Directives:
                if self.has_property( exec_directive ):

                    # this unit contains an "Exec" directive; these will be constructed as distinct nodes.
                    # each execfile can perform multiple commands although this is not usual.
                    exec_elt = Command( exec_directive, self.get_property( exec_directive ), self.remote_path, self.master_struct, self.log )
                    self._children.add( exec_elt )
        return self._children

    def get_property_children( self, prop ):
        """Get the set of "property" children for this DropInFile. These are Unit Instances that are associated
        with specific directives in a Unit file's definition.

        Args:
            prop: The Systemd directive property string to use as a key.

        Returns:
            The set of Unit Instances that are associates with dependency Systemd directives.
        """
        s = set()
        if prop in Element.EdgeDirectives and self.has_property( prop ):
            for c in self.get_property( prop ):
                s.add( ( c, 'UNIT' ) )
        return s

    def get_sequencing_children( self, prop ):
        """Get the set of "sequencing" children for this DropInFile. These are Unit Instances that are associated
        with the After= and Before= directives that establish Unit ordering.

        Args:
            prop: The Systemd directive property string to use as a key.

        Returns:
            The set of Unit Instances that are associates with sequencing Systemd directives.
        """
        s = set()
        if prop in ('After', 'Before') and self.has_property( prop ):
            for c in self.get_property( prop ):
                s.add( ( c, 'UNIT' ) )
        return s

    def add_to_graph( self, G ):
        """Add this Element instance to graph G

        Args:
            G: the graph to add this Element to.
        """
        G.add_node( repr(self), **DropInFile.vertex_attrs( self.id() ) )

    def make_graph_edges( self, G ):
        """Creates all the edges (and possibly new nodes) based on information in this Unit Element.

        Args:
            G: the networkx graph object for this Systemd specification.
        """
        for c in self.get_children():
            # Unit edge attributes for now with the label being the type of command.
            G.add_edge( repr(self), repr(c), **self.get_edge_attrs( c.exec_directive ) )

        for p in Element.EdgeDirectives:
            for c in self.get_property_children( p ):
                # There are some cases where nodes are created here but NOT normally.
                # we need to establish their attributes.
                if repr(c) not in G:
                    label = 'UNKNOWN'
                    if DropInFile.TemplateMatcher.match( c[0] ):
                        label = 'TEMPLATE'
                    G.add_node( repr(c), **Element.get_default_vertex_attrs( label, c[0] ) )

                G.add_edge( repr(self), repr(c), **self.get_edge_attrs( p ) )

        for seq in ( 'After', 'Before' ):
            for c in self.get_sequencing_children( seq ):
                if repr(c) not in G:
                    label = 'UNKNOWN'
                    G.add_node( repr(c), **Element.get_default_vertex_attrs( label, c[0] ) )

                if seq == 'After':
                    # this unit comes AFTER the one in the list (edge direction opposite)
                    G.add_edge( repr(c), repr(self), **self.get_edge_attrs( seq ) )
                else:
                    G.add_edge( repr(self), repr(c), **self.get_edge_attrs( seq ) )

    def get_target( self ):
        return self.target

class CommandLine:
    """Represents a command found in an Exec* directive in a Systemd Unit file. This class will parse
    these specially formatted lines and provide accessors to all the elements within the command.

    This is NOT AN ELEMENT.
    """
    SpecialPrefixes = ('@', '-', ':', '+', '!' )

    def __init__( self, cstr ):
        """Constructor for a CommandLine instances"""
        self.cstr = cstr
        self.prefixes = set()
        self.executable = None
        self.arguments = None
        self.__parse_command_string( cstr )

    def get_executable( self ):
        """Return the executable command string; this usually includes the full path.

        Returns:
            A string that is the path to the executable.
        """
        return self.executable

    def __str__( self ):
        """The command line WITHOUT the Systemd prefix characters.

        Returns:
            The command line without prefixes.
        """
        s = self.executable
        if self.arguments:
            # add arguments only if they are present.
            s += ' ' + self.arguments
        return s

    def __parse_command_string( self, cstr ):
        """Make a Command instance from the cstr. This parses out the special prefix characters and
        splits the executable command from its arguments.

        Args:
            cstr: a command string found in a systemd unit file; these have special prefixes.

        Returns:
            An ExecCommand instance that characterizes the command and its prefixes.
        """
        parts = cstr.split(maxsplit=1)

        print("cstr: {} parts: {}".format( cstr, parts ))

        # the command may NOT have any arguments.
        if len(parts)>1:
            self.arguments = parts[1]

        executable = parts[0]

        i = 0
        while i < len(executable):
            if executable[i] in CommandLine.SpecialPrefixes:
                ch = executable[i]
                if ch == '!':
                    try:
                        if executable[i+1] == '!':
                            i += 1
                            ch += '!'
                    except IndexError:
                        # end of the executable; this is a problem, but just record the single !
                        pass
                self.prefixes.add( ch )
            else:
                # we have reached the actual path to the executable.
                break
            i += 1
        # set the executable WITHOUT the special prefix characters.
        self.executable = executable[i:]

class Command( Element ):
    """An Element that represents a SEQUENCE of executable commands (usually only one tho) that are associated with 
    ONLY ONE of the following directives:

    ExecStart : command to execute when this service is started.
    ExecCondition : optional commands executed before ExecStartPre
    ExecStartPre : commands executed BEFORE ExecStart
    ExecStartPost : commands executed AFTER ExecStart
    ExecReload : commands to execute to trigger a configuration reload for the service.
    ExecStop : commands that will stop a service
    ExecStopPost : commands to execute AFTER the service is stopped.

    A Unit Element instance is the parent of a Command Element instance.
    So, a single UNIT file (e.g., service) could generate several of Command instances because several Exec* directives
    could be used.

    First line must be an ABSOLUTE path to an executable or a simplified filename without any slashes.
    There may also be a prefix character used:
    @ : second token passed as argv[0]
    - : failure exit code has no effect.
    : : no environment variable substitution
    + : executed with FULL PRIVILEDGES
    ! : execute with ELEVATED PRIVILEDGES
    !! : also related to PRIVILEDGES
    """
    TypeKey = 'COMMAND'

    Directives = ('ExecStart', 'ExecCondition', 'ExecStartPre', 'ExecStartPost', 'ExecReload', 'ExecStop', 'ExecStopPost')

    @staticmethod
    def vertex_attrs( node_label ):
        """Return a dictionary containing the Command Cytoscape vertex attributes

        Args:
            node_label:

        Returns:
            A dictonary containing the attributes for this vertex; the keys are special.
        """
        # sets subgraph, node_label, node_label_width, node_height, node_width
        attrs = Element.get_default_vertex_attrs( Command.TypeKey, node_label )

        # set the specifics for node_label_color, node_fill_color, node_shape
        # attrs['node_label_color'] = colors.orange_colors['darkest']
        attrs['node_fill_color']  = colors.element_fill_colors[Command.TypeKey]
        attrs['node_shape']       = 'RECTANGLE'
        return attrs

    @staticmethod
    def edge_attrs( edge_label ):
        """Return a dictionary containing the Edge Cytoscape edge attributes

        Args:
            edge_label:

        Returns:
            A dictonary containing the attributes for this edge; the keys are special.
        """
        # sets directed, subgraph, interaction are set here
        attrs = Element.get_default_edge_attrs( Command.TypeKey, edge_label )

        # set the specifics for edge_label_color, edge_line_type, edge_color
        attrs['edge_line_type']     = 'SOLID'
        attrs['edge_color']         = colors.orange_colors['dark']
        return attrs

    def __init__( self, exec_directive, exec_list, remote_path, master_struct, log ):
        """Constructor for an Command Element

        A single command could be called by multiple unit files. All units that use these commands
        should be captured as parents.

        Args:
            exec_directive: The Systemd executable directive, e.g., ExecStart
            exec_list: A list of command strings to execute; the master struct breaks these out into a list.
            remote_path: The prefix path on this system needed to get to the firmware root.
            log: logging messaging.

        Returns:
            A Command instance.

        Raises:
            Exception when the directive is not correct.
        """
        # we will update the id later.
        super().__init__( None, dict(), log )

        if exec_directive not in Command.Directives:
            raise Exception("Bad Exec command directive: {}".format( exec_directive ))

        self.exec_directive = exec_directive
        self.master_struct = master_struct

        self.commands = list()
        full_command = self.__parse_commands( exec_list )

        self._key = ( full_command, "{}.{}".format( Command.TypeKey, exec_directive[4:].upper() ) )
        self.remote_path = remote_path

    def get_vertex_attrs( self ):
        """Return a dictionary containing the Command Cytoscape vertex attributes

        Returns:
            A dictonary containing the attributes for this vertex; the keys are special.
        """
        return Command.vertex_attrs( self.id() )

    def get_edge_attrs( self, edge_label ):
        """Return a dictionary containing the Command Cytoscape edge attributes

        Args:
            edge_label:

        Returns:
            A dictonary containing the attributes for this edge; the keys are special.
        """
        return Command.edge_attrs( edge_label )

    def get_children( self ):
        """Return this Command's children as a set of Executable instances.

        Returns:
            The set of children of this Command Element as Executable instances.
        """
        if not self._children:
            # the child set is empty.
            for cmd in self.commands:
                self._children.add( Executable( cmd.get_executable(), self.remote_path, self.master_struct, self.log ) )
        return self._children

    def add_to_graph( self, G ):
        """Add this Element instance to graph G

        Args:
            G: the graph to add this Element to.
        """
        label = '\n'.join( self.id().split(';') )
        G.add_node( repr(self), **Command.vertex_attrs( label ) )

    def make_graph_edges( self, G ):
        """Creates all the edges based on information in this Unit Element.

        Args:
            G: the networkx graph object for this Systemd specification.
        """
        for c in self.get_children():
            # Command edge attributes for now with the label being the type of command.
            G.add_edge( repr(self), repr(c), **self.get_edge_attrs( Executable.TypeKey ) )

    def __parse_commands( self, exec_list ):
        """Parse the list of executable commands that the exec_directive systemd directive maps to.

        There could be multiple commands in this single directive, so add each one to a commands
        list. The sequence in the list is the execution order of the individual commands.
        
        Args:
            exec_list: a list of executable commands; The master structure breaks the commands down into 
                       a list of individual commands.

        Returns:
            A unique string identifier for this list of commands; it is the concatenation of all of them.
            TODO: If this properties list is empty, then we will get an error...!

        Raises:
            Exception when the exec_directive key is NOT in the self.properties map.
        """
        for cstr in exec_list:
            # go through each command in the list.
            if not len(cstr):
                # JMC: There was a case of an empty command string; for now just skip it.
                self.log.warning("Empty command string found in directive: {} key: {}".format( self.exec_directive, self.key ))
            else:
                self.commands.append( CommandLine( cstr ) )

        full_command = '; '.join( [ str(c) for c in self.commands ] )
        return full_command

class Executable( Element ):
    """A single binary that is executed as part of a Command (e.g., starting a service)

    The parents of Executables are Commands; each Command may have multiple Executable children.

    Each Executable (distinct binary) has the following children:
    - Library set
    - String set

    This DOES NOT include the ARGUMENTS to the command.

    We will use this class to also execute linux tools to perform forensics on this particular binary.
    These tools should be as general as possible, so they can accomodate a variety of architectures.
    """
    TypeKey = 'EXECUTABLE'

    @staticmethod
    def vertex_attrs( node_label ):
        """Get the attribute dictionary to use in cytoscape for this Alias vertex.

        Args:
        Returns:
            the attribute dictionary.
        """
        # sets subgraph, node_label, node_label_width, node_height, node_width
        attrs = Element.get_default_vertex_attrs( Executable.TypeKey, node_label )

        # set the specifics for node_label_color, node_fill_color, node_shape
        # attrs['node_label_color'] = colors.purple_colors['white']
        attrs['node_fill_color']  = colors.element_fill_colors[Executable.TypeKey]
        attrs['node_shape']       = 'ROUND_RECTANGLE'

        return attrs

    @staticmethod
    def edge_attrs( edge_label ):
        """Get the attribute dictionary to use in cytoscape for this Alias edge.
        Args:
        Returns:
            the attribute dictionary.
        """
        # sets directed, subgraph, interaction are set here
        attrs = Element.get_default_edge_attrs( Executable.TypeKey, edge_label )

        # set the specifics for edge_label_color, edge_line_type, edge_color
        attrs['edge_line_type']     = 'SOLID'
        attrs['edge_color']         = colors.purple_colors['dark']

        return attrs


    def __init__( self, executable, remote_path, master_struct, log ):
        """Constructor for an Executable instance.

        Args:
            executable:
            remote_path:
            log:

        Returns:
            An Executable Instance.
        """
        super().__init__( executable, dict(), log )

        self.log = log
        self._key = ( executable, Executable.TypeKey )
        self.remote_path = remote_path
        self.binary_path = "{}{}".format( remote_path, executable )
        self.executable = executable
        self.master_struct = master_struct

        self.dlibs = set()
        self.fstrings = set()
        self.pstrings = set()

    def get_vertex_attrs( self ):
        """Return a dictionary containing the Executable Cytoscape vertex attributes

        Returns:
            A dictonary containing the attributes for this vertex; the keys are special.
        """
        return Executable.vertex_attrs( self.id() )

    def get_edge_attrs( self, edge_label ):
        """Return a dictionary containing the Executable Cytoscape edge attributes

        Args:
            edge_label:

        Returns:
            A dictonary containing the attributes for this edge; the keys are special.
        """
        return Executable.edge_attrs( edge_label )

    def get_children( self ):
        """Return this Command's children as a set of Executable instances.

        TODO: This is WHERE WE WOULD AUGMENT WHAT WE RUN AGAINST AN EXECUTABLE TO EXTRACT
        FORENSIC INFORMATION.

        Returns:
            The set of children of this Command Element as Executable instances.
        """
        if not self._children:
            # the child set is empty.
            self._children.update( self.get_dynamic_libs() )
            self._children.update( self.get_file_strings() )
            self._children.update( self.get_path_strings() )
        return self._children

    def add_to_graph( self, G ):
        """Add this Element instance to graph G

        Args:
            G: the graph to add this Element to.
        """
        G.add_node( repr(self), **Executable.vertex_attrs( self.id() ) )

    def make_graph_edges( self, G ):
        """Creates all the edges based on information in this Command Element.

        Args:
            G: the networkx graph object for this Systemd specification.
        """
        for c in self.get_children():
            s_str = repr(self)
            t_str = repr(c)
            if ( s_str, t_str ) not in G.edges():
                # When a single Executable is called multiple times, e.g., used with different command line arguments --
                # lets say we are starting a webserver and stopping a webserver -- same executable multiple commands and options.
                # there will be multiple edges created from that executable to its supporting libraries and strings.
                # this is CORRECT based on how this code was intended (proper multigraph), but it may clutter the graph. 
                # This mechanism eliminates THIS PARTICULAR set of multigraph edges.

                # Executable edge attributes for now with the label being the type of command.
                G.add_edge( s_str, t_str, **self.get_edge_attrs( c.get_type() ) )

    def get_dynamic_libs( self ):
        """Run a linux command to extract the supporting dynamic libraries (if any) for this executable.

        Execute the external command in a subprocess, gather the input, and perform the regex filter
        internally for the data of interest.

        Returns:
            The set of Library instances; these have the methods to grab attributes for graphing.
        """
        if not self.dlibs:
            # only do this operation one time.
            # do not need a / character here because the remote path does NOT end in one
            # and the executable is a full system path that begins with a /

            dlib_names = self.master_struct['libraries'][self.executable]
            self.dlibs = { Library( name, self.log ) for name in dlib_names }

        return self.dlibs

    def get_file_strings( self ):
        """Use the binutils strings command on the executable to find files that may be of use.

        Args:
            extension_list: a list of file extensions to search for within the strings.

        Returns:
            a set of strings (maybe file paths) that could indicate a file that is used by this
            binary.
        """
        if not self.fstrings:
            # only do this operation one time.

            file_strings = self.master_struct['files'][self.executable]

            for s in file_strings:
                str_elt = String( s.strip(), 'FILE', self.log )
                self.fstrings.add( str_elt )

        return self.fstrings

    def get_path_strings( self ):
        """Use the binutils strings command on the executable to find paths that may be of use.

        Returns:
            a set of strings (maybe paths) that could indicate a path/file that is used by this
            binary.
        """
        if not self.pstrings:
            # only do this operation one time.
            # do not need a / character here because the remote path does NOT end in one
            # and the executable is a full system path that begins with a /

            path_strings = self.master_struct['strings'][self.executable]

            for s in path_strings:
                str_elt = String( s.strip(), 'PATH', self.log )
                self.pstrings.add( str_elt )

        return self.pstrings

class Library( Element ):
    """A dynamic library that is needed by an Executable.

    This is MEANT to have NO CHILDREN.
    """
    TypeKey = 'LIBRARY'

    @staticmethod
    def vertex_attrs( node_label ):
        """Get the attribute dictionary to use in cytoscape for this Alias vertex.

        Args:
        Returns:
            the attribute dictionary.
        """
        # sets subgraph, node_label, node_label_width, node_height, node_width
        attrs = Element.get_default_vertex_attrs( Library.TypeKey, node_label )

        # set the specifics for node_label_color, node_fill_color, node_shape
        # attrs['node_label_color'] = colors.blue_colors['dark']
        attrs['node_fill_color']  = colors.element_fill_colors[Library.TypeKey]
        attrs['node_shape']       = 'ROUND_RECTANGLE'

        return attrs

    def edge_attrs( edge_label ):
        """Get the attribute dictionary to use in cytoscape for this Alias edge.
        Args:
        Returns:
            the attribute dictionary.
        """
        # sets directed, subgraph, interaction are set here
        attrs = Element.get_default_edge_attrs( Library.TypeKey, edge_label )

        # set the specifics for edge_label_color, edge_line_type, edge_color
        attrs['edge_line_type']     = 'SOLID'
        attrs['edge_color']         = colors.dark_colors['blue']

        return attrs

    def __init__( self, libname, log ):
        """Construct a Library instance

        Returns:
            A Library instance.
        """
        super().__init__( libname, dict(), log )
        self._key = ( libname, Library.TypeKey )

    def get_vertex_attrs( self ):
        """Return a dictionary containing the Library Cytoscape vertex attributes

        Returns:
            A dictonary containing the attributes for this vertex; the keys are special.
        """
        return Library.vertex_attrs( self.id() )

    def get_edge_attrs( self, edge_label ):
        """Return a dictionary containing the Library Cytoscape edge attributes

        Args:
            edge_label:

        Returns:
            A dictonary containing the attributes for this edge; the keys are special.
        """
        return Library.edge_attrs( edge_label )

    def add_to_graph( self, G ):
        """Add this Element instance to graph G

        Args:
            G: the graph to add this Element to.
        """
        G.add_node( repr(self), **Library.vertex_attrs( self.id() ) )

    def make_graph_edges( self, G ):
        """These are leafs, no children"""
        pass

class String( Element ):
    """A specific string extracted from an Executable

    This is MEANT to have NO CHILDREN.
    """
    TypeKey = 'STRING'

    @staticmethod
    def vertex_attrs( node_label ):
        """Get the attribute dictionary to use in cytoscape for this Alias vertex.

        Args:
        Returns:
            the attribute dictionary.
        """
        # sets subgraph, node_label, node_label_width, node_height, node_width
        attrs = Element.get_default_vertex_attrs( String.TypeKey, node_label )

        # set the specifics for node_label_color, node_fill_color, node_shape
        # attrs['node_label_color'] = colors.dark_colors['purple']
        attrs['node_fill_color']  = colors.element_fill_colors[String.TypeKey]
        attrs['node_shape']       = 'ROUND_RECTANGLE'

        return attrs

    @staticmethod
    def edge_attrs( edge_label ):
        """Get the attribute dictionary to use in cytoscape for this Alias edge.
        Args:
        Returns:
            the attribute dictionary.
        """
        # sets directed, subgraph, interaction are set here
        attrs = Element.get_default_edge_attrs( String.TypeKey, edge_label )

        # set the specifics for edge_label_color, edge_line_type, edge_color
        attrs['edge_line_type']     = 'SOLID'
        attrs['edge_color']         = colors.purple_colors['dark']

        return attrs

    def __init__( self, string, category, log ):
        """Construct a String instance.

        Returns:
            A String instance.
        """
        super().__init__( string, dict(), log )
        self._key = ( string, "{}.{}".format(String.TypeKey,category) )

    def get_vertex_attrs( self ):
        """Return a dictionary containing the String Cytoscape vertex attributes

        Returns:
            A dictonary containing the attributes for this vertex; the keys are special.
        """
        return String.vertex_attrs( self.id() )

    def get_edge_attrs( self, edge_label ):
        """Return a dictionary containing the String Cytoscape edge attributes

        Args:
            edge_label:

        Returns:
            A dictonary containing the attributes for this edge; the keys are special.
        """
        return String.edge_attrs( edge_label )

    def add_to_graph( self, G ):
        """Add this Element instance to graph G

        Args:
            G: the graph to add this Element to.
        """
        G.add_node( repr(self), **String.vertex_attrs( self.id() ) )

    def make_graph_edges( self, G ):
        """These are leafs, no children"""
        pass
