'''
dep_obj_parser.py
Authors: Mike Huettel, Jason M. Carter
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

Description:  This file is designed to instantiate the DepMapUnit objects and 
    contains the logic for all of master struct and previously recorded unit entry
    parsing. For more information, see the function comments or the README.md.
'''

import logging

from typing import Dict, List, Set, Tuple, Any, Union

from lib.unit_file_lists import command_directives



class DepMapUnit:

    rev_dep_map = {
        'sym_linked_to':    'sym_linked_from',
        'Wants':            'wanted_by',
        'Requires':         'required_by',
        'Requisite':        'requisite_of',
        'BindsTo':          'bound_by',
        'PartOf':           'has_part',
        'Upholds':          'upheld_by',
        'OnSuccess':        'on_success_of',
        'Sockets':          'socket_of',
        'Service':          'uses_service',
        'iTimer_for':       'has_timer',
        'iSocket_of':       'has_socket',
        'iPath_for':        'needs_path',
        'iTemplate_of':     'uses_template',
        'iSlice_of':        'uses_slice'
    }
    '''Map of all reverse dependencies. If you are going to add a new rev dep make sure to create the 
    corresponding key in sysd_obj_parser.py so it can be seen in the master struct. Things to keep in mind 
    about this map:

    - All KEYS create dependencies when they are found in a master struct entry
    - All VALUES directly mirror the type of dependency for their KEYS, e.g. 
        unit1 Wants unit2 is the forward dependency, and unit2 wanted_by unit1 is the corresponding reverse
        dependency
    - Any KEY that begins with a capital letter is a dependency option explicitly set in a unit file
    - Any KEY beginning with 'i' is not stated explicitly in a unit file, but a dependency is being created
        implicitly.  See check_implicit_dependencies() in sysd_obj_parser.py for more info and references.
    - sym_linked_to is a dependency this tool is creating in order to separate symbolic links and the unit
        file they point to. If the links were followed instead we would have an incomplete picture of what
        systemd is actually seeing.'''

    # DO NOT MODIFY THE CASE FOR THESE STRINGS. This is required to verify proper options in unit files.
    dep_creating_dirs = ['Wants', 'Requires']


    def __init__(self, unit_file: str, parent_unit_path: str, rev_dep: str) -> None:
        '''The DepMapUnit class creates the dep object shell for dep map units and uses the
        dep tup that is passed to it to create the reverse dependencies for the units.'''

        self.unit_name = unit_file
        self.parent_unit_path = parent_unit_path
        self.parent_unit = self.parent_unit_path.split('/')[-1]
        self.rev_dep = rev_dep

        # Create an attribute for each dep and rev_dep in rev_dep_map as an empty set
        for key, value in self.rev_dep_map.items():
            setattr(self, key.lower(), set())
            setattr(self, value, set())
        
        # These are all inferred by other dep/rev_dep types so they aren't mapped in rev_dep_map
        self.parents: Set[str] = set()
        self.reverse_deps: Set[str] = set()
        self.dependencies: Set[str] = set()
        self.commands: Set[str] = set()
        self.where: Set[str] = set()

        self.set_rev_dep()


    def get_commands(self) -> Set:
        '''Returns a list of executables for dep map to map out forensic dependencies'''

        return self.commands


    def get_significant_attributes(self, mapping='all') -> List[Union[Tuple[str, str], str]]:
        '''Return any attributes that aren't empty. By default, all attributes containing values will be returned, 
        but users can specify only forward or only backward dependencies to be returned as well. Mapping options:
        
        - 'for_deps' - returns a list of tuples containing forward deps and their corresponding attributes [ ('key1', 'attr1'), ('key2', 'attr2') ]
        - 'rev_deps' - returns a list of reverse dependencies/attributes [ 'attr1', 'attr2' ].  Possible because rev_deps are all lowercase
        - 'all' (default) - returns a list of all attributes that contain values [ 'attr1', 'attr2' ]. Discards all methods and empty sets.'''

        attribute_list = []

        if mapping == 'for_deps':
            for key in self.rev_dep_map:
                if len( getattr(self, key.lower()) ) > 0:
                    attribute_list.append( (key, key.lower()) )
        elif mapping == 'rev_deps':
            return [ attr for attr in dir(self) if
                ( attr in self.rev_dep_map.values() ) and
                ( isinstance( getattr(self, attr), set ) and len( getattr(self, attr)) > 0 )
                ]
        elif mapping == 'all':
            return [ attr for attr in dir(self) if 
                attr == 'unit_name' or 
                ( isinstance( getattr(self, attr), set ) and len( getattr(self, attr) ) > 0)
                ]
        else:
            logging.warning(f'Invalid mapping type. Please review code to pass a valid mapping type')

        return attribute_list


    def set_rev_dep(self) -> None:
        '''Check to see which reverse dependency is being passed when the object is created, and record it.'''

        if self.parent_unit_path != 'None':
            self.parents.add(self.parent_unit)
            self.reverse_deps.add(self.rev_dep)

            try:
                if self.rev_dep == 'sym_linked_from':
                    getattr(self, self.rev_dep).add(self.parent_unit_path)
                else:
                    getattr(self, self.rev_dep).add(self.parent_unit)

            except AttributeError:
                logging.warning(f'Invalid reverse dependency: {self.rev_dep}.  This does not map to any attribute sets')


    def load_from_ms(self, master_struct_unit: Dict[str, Union[str, Dict[str, Union[str, List]]]]) -> None:
        '''Handler function for when an entry matching the dep unit is found in the master struct. It will 
        look at the file_type to see what type of file was encountered and then parse it accordingly'''

        # Disregard remote_path entry
        if isinstance(master_struct_unit, str):
            pass
        elif master_struct_unit['metadata']['file_type'] == 'dep_dir':
            self.update_ms_dep_dir(master_struct_unit)
        elif master_struct_unit['metadata']['file_type'] == 'sym_link':
            self.update_ms_sym_link(master_struct_unit)
        elif ( master_struct_unit['metadata']['file_type'] == 'unit_file' or
               master_struct_unit['metadata']['file_type'] == 'fstab_unit' ):
            self.update_ms_unit_file(master_struct_unit)
        else:
            logging.warning(f'Not sure how to parse file type: {master_struct_unit["metadata"]["file_type"]} from {self.unit_name}')


    def update_ms_dep_dir(self, ms_unit_struct: Dict[str, Any]) -> None:
        '''Parse dependency directories given by load_from_ms(). '.d' directories 
        don't create dependencies so they are not included in dep objects.'''

        for dep in self.dep_creating_dirs:
            if dep in ms_unit_struct['metadata']:
                getattr(self, dep.lower()).update(ms_unit_struct['metadata'][dep])
                self.dependencies.update( getattr(self, dep.lower()) )


    def update_ms_sym_link(self, ms_unit_struct: Dict[str, Any]) -> None:
        '''Parse symbolic link entries given by load_from_ms(). These are parsed independently to retain the full sym link file path 
        creating the dependency, since there can be many sym links pointing to a single file from different places within the filesystem.'''

        self.sym_linked_to.add(f"{ms_unit_struct['metadata']['sym_link_target_path']}{ms_unit_struct['metadata']['sym_link_target_unit']}")
        self.dependencies.add(f"{ms_unit_struct['metadata']['sym_link_target_unit']}")


    def update_ms_unit_file(self, ms_unit_struct: Dict[str, Any]) -> None:
        '''Parse unit file entries given by load_from_ms(). This function is creating most of the dependencies for the entries in the 
        dep map. This function is separated from load_dep_map_unit() because unit files actually create deps, and loading previous dep 
        map entires only needs to copy the entries that have already been recorded. ms_unit_struct can either be full ms_unit_struct
        or the metadata dict within the ms_unit_struct in order to check for implicit dependencies.'''

        for option in ms_unit_struct:
            try:
                getattr(self, option.lower()).update(ms_unit_struct[option])
                if option != 'Where':
                    self.dependencies.update(ms_unit_struct[option])
            except AttributeError:
                # If current key is metadata, send it back into the func as a new dictionary to parse implicit dependencies
                if option == 'metadata':
                    self.update_ms_unit_file(ms_unit_struct['metadata'])
                elif option == 'file_type':
                    return
                else:
                    logging.debug(f'No set in the dep_to_attr_map matches {option} (from {ms_unit_struct[option]})')

            if option in command_directives:
                if len(ms_unit_struct[option]) < 1:
                    continue

                self.commands.update( ms_unit_struct[option] )


    def load_from_dep_map(self, dep_map_unit: Dict[str, Any]) -> None:
        '''Companion to load_from_ms(). This function takes an entry from the dep map and records that info to the dep object. This 
        prevents duplicates in the dep map, and makes sure nothing is lost when the current dep object overwrites a previously 
        recorded dep object with the same name. This duplication may happen when dep tups have the same dep unit, but different parents.'''

        for dep in dep_map_unit:
            try:
                getattr(self, dep.lower()).update(dep_map_unit[dep])

            except AttributeError:
                if dep not in ('name', 'binaries', 'libraries', 'files', 'strings', 'mount_points'):
                    logging.warning(f'Could not load "{dep}" attribute from unit already in dep map. Investigate {self.unit_name} in the master struct')



    def create_dep_tups(self, current_item: str) -> List[tuple]:
        '''Checks each dependency set to see if it is populated. Dep tups will be created in order to map reverse dependencies to
        later unit files.  This function does not deduplicate anything.  Instead, map_dependencies() in systemd_mapping.py keeps 
        track of whether dep tups are duplicates.'''
        
        dep_tup_list = []

        for key, attribute in self.get_significant_attributes('for_deps'):
            for dep in getattr(self, attribute):
                dep_tup = (dep.split('/')[-1], current_item, self.rev_dep_map[key])
                dep_tup_list.append(dep_tup)

        return dep_tup_list


    def record(self) -> Dict[str, Union[str, List[str]]]:
        '''Inspects all of the attributes of the dep object, and if any
        of them contain info, will add them to the dict that is returned.  This
        returned dict will be recorded in the dep map, overwriting any previous entry
        with the same name (same unit file).  This prevents duplicate entries.'''

        out_struct: Dict[str, Union[str, List[str]]] = {'unit_name': self.unit_name}

        for attribute in self.get_significant_attributes():
            out_struct.update({ attribute: getattr(self, attribute) })

        return out_struct
