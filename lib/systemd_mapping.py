'''
systemd_mapping.py
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

Description:  This is the main logic for the tool that searches for which files and folders to parse.
    After files and folders are found they will be passed to sysd_obj_parser to be validated and then
    recorded to the master structure dictionary.  After the master struct is built, systemd snapshot
    can run the dependency mapping function.  The dependency mapping function starts with the origin
    unit file ('default.target' by default) and searches through the master struct to find any and all 
    dependencies that are created by that unit. It does this dependency mapping for each dependency that 
    is created unitl none remain.  For more information, including struct mappings, see doc strings.
'''

import logging
import re

from os import readlink
from subprocess import run
from pathlib import Path
from typing import List, Dict, Set, Tuple

from lib.unit_file_lists import sys_unit_paths, command_directives, ms_only_keys
from lib.sysd_obj_parser import SystemdFileFactory
from lib.dep_obj_parser import DepMapUnit

master_struct = {}
'''holds information about each individual unit file and folder within the
default systemd system paths'''


def get_bin_path(cmd_string: str) -> str:
    '''Extracted out of check_binaries to make it usable for dep map.
    
    TODO:
    - Check to see if binary is a path.  If not we need to get the path variables that should be set and
        try to figure out which one contains the bin we are looking for.'''

    binary = cmd_string.split()[0]
    binary = remove_prefixes(binary)
    return binary


def remove_prefixes(binary: str) -> str:
    '''This function removes all of the prefixes from a command directive option's corresponding argument. 
        "@", "-", ":", and one of "+"/"!"/"!!"  may be used together and they can appear in any order. However, 
        only one of "+", "!", "!!" may be used at a time. For more info see systemd.service (5) man page.'''
    
    cmd_prefixes = ( '@', '-', ':', '+', '!' )

    i = 0
    while i < len(binary):
        if binary[i] in cmd_prefixes:
            i += 1
        else:
            # If we reach the end of the cmd_prefixes exit the loop
            break
    
    return binary[i:]


def get_bin_libs(remote_path: str, binary: str) -> Set:
    '''Use objdump to enumerate the given binary and return  that are required by it. This function 
    is ONLY meant to be used when building the master struct.  If this function is used outside of the 
    machine being snapshot, it WILL either return nothing or return false info based on the machine being used.
    
    TODO:
    - Create version check and use check_output for versions older than 3.7'''

    lib_regex = re.compile('\s*NEEDED\s+(.+)')

    output = run( ['objdump', '-p', f'{remote_path}{binary}' ], capture_output=True, text=True )
    return set( lib_regex.findall(output.stdout) )


def get_bin_strings(remote_path: str, binary: str) -> Tuple[Set, Set]:
    '''Use strings to enumerate the given binary and return paths and files that are referenced. This function 
    is ONLY meant to be used when building the master struct.  If this function is used outside of the 
    machine being snapshot, it WILL either return nothing or return false info based on the machine being used.
    
    TODO:
    - Create version check and use check_output for versions older than 3.7'''
    
    file_ext_list = ['cfg','conf','ini','log','exe']
    file_regex = re.compile( '^.+\.({})$'.format(  '|'.join(file_ext_list) ) )
    path_regex = re.compile('^/\w+(/[\w\.-]*)+$')
    # begin with / followed by at least 1 alphanum char with at least one more / followed by alphanum, '.', or '-' chars any num of times

    output = run( [ 'strings', f'{remote_path}{binary}' ], capture_output=True, text=True )
    files = { file.split('=')[-1] for file in filter( file_regex.match, output.stdout.split() ) }
    strings = { string.split('=')[-1] for string in filter( path_regex.match, output.stdout.split() ) }

    # Since path regex will match on the same strings as file_regex, remove files from strings
    strings.symmetric_difference_update(files)

    return (files, strings)


def check_binaries(remote_path: str, unit_struct: Dict[str, List]) -> Dict[str, Dict[str, Set]]:
    '''This function checks for unit file command options and inspects the binaries specified in the 
    command to get a listing of all of the libraries, config and log files, and other potentially 
    interesting filepath strings that are specified in the binary.'''

    exec_deps = { 'libraries': {}, 'files': {}, 'strings': {} }

    for option in unit_struct:
        if option in command_directives:
            for cmd in unit_struct[option]:
                if len(cmd) < 1:
                    continue

                binary = get_bin_path(cmd)
                
                if (binary not in master_struct['libraries'] and
                    binary not in exec_deps['libraries']):

                    exec_deps['libraries'].update({ binary: get_bin_libs(remote_path, binary) })
                    bin_files, bin_strings = get_bin_strings(remote_path, binary)
                    exec_deps['files'].update({ binary: bin_files })
                    exec_deps['strings'].update({ binary: bin_strings })

    return exec_deps


def map_systemd_full(remote_path: str, log: logging) -> dict:
    '''Map Systemd Full is designed to create a master_struct that will store all unit files on the system 
        regardless of dependencies.  Ideally this will be used in conjunction with the output file option to
        allow users to create a "outfile_master_struct.json" file that can be referenced in the future to map
        dependencies without having to create a new master_struct every time.  
        
        The function iterates through all of the default systemd system paths, and checks to see if each one is
        present.  If the system path is present, all files and dependency folders will be established
        independently as a SystemdFile object, and then, depending on the file type, will be parsed as a
        dependency directory, symbolic link, or unit file.
        
        If a unit file has command directives that will run an binary upon getting started, we will record 
        additional info on the binary in the libraries and files dictionaries. These are maps from the 
        binaries found in the unit file command directives to libraries and files that the binary requires. 
        These are recorded independently of the unit file entries to avoid duplication.
        
        Lastly, the function will update the master_struct with the parsed info.  The final product should follow 
        the format detailed below:

    master_struct = {
        'remote_path': '/some/remote/file/system/root/dir',
        'libraries': {
            '/usr/bin/exe1':    ['lib1', 'lib2', 'lib3'],
            '/bin/exe2':        ['lib3', 'lib4']
            },
        'files': {
            '/usr/bin/exe1':    ['file.config'],
            '/bin/exe2':        ['file.ini', 'file.log']
            },
        'strings': {
            '/bin/exe2':        ['/var/log/exe2/']
            },
        'wants folder example' : {
            'metadata': {
                'file_type' : 'dep_dir',
                'dependency_folder_paths' : ['/sys/path/to/dep/dir'],
                'dependencies' : ['unitA', 'unitB', 'unitC'],
                'Wants' : [ 'Wants', 'field', 'Units' ]
                }
            },
        'symbolic link example' : {
            'metadata' : {
                'file_type': 'sym_link',
                'sym_link_path' : path,
                'sym_link_unit' : 'unit.target',
                'sym_link_target_path' : target_path,
                'sym_link_target_unit' : target_unit,
                'dependencies' : target_unit
                }
            },
        'unit file example' : {
            'metadata' : {
                'file_type': 'unit_file'
                },
            unit_file_option : option_arguments,
            ...
            }
        }
    '''

    log.info('Beginning recording of all files in Systemd folders.')
    master_struct.update({
        'remote_path': remote_path,
        'libraries': {},
        'files': {},
        'strings': {}
        })

    UnitFactory = SystemdFileFactory(remote_path)

    # Prevent duplicate dir traversal if /lib is sym linked to /usr/lib
    try:
        if readlink( f'{remote_path}/lib' ) == f'usr/lib':
            sys_unit_paths.remove('/lib/systemd/system/')
    except OSError:
        log.debug('/lib is not sym linked to /usr/lib.  Retaining /lib/systemd/system system path.')

    for sys_path in sys_unit_paths:
        check_path = Path( f'{remote_path}{sys_path}' )

        if check_path.exists():
            for unit_file_fp in [files for files in check_path.glob('**/*')]:

                log.debug( f'Sending {unit_file_fp} for processing' )

                current_unit = str(unit_file_fp).split('/')[-1]
                unit_path = str(unit_file_fp.parents[0]) + '/'

		        # If there is a remote path, remove it to avoid duplication
                if remote_path != '' and remote_path in unit_path:
                    unit_path = unit_path.split(remote_path)[-1]

                # Reset unit file info
                unit_file = None
                unit_file = UnitFactory.parse_file(unit_path, current_unit)

                log.debug( f'Finished recording {unit_file_fp}' )

                log.debug( f'Checking for binaries, libraries, and files required by {unit_file_fp}' )

                bin_requirements = check_binaries(remote_path, unit_file)
                for requirement_type in bin_requirements:
                    # requirement_type is referencing either the libraries, files, or strings dict

                    for binary in bin_requirements[requirement_type]:
                        # binary is referencing the bin dicts w/in the Lib, File, or String dicts
                        master_struct[requirement_type].update({ binary: bin_requirements[requirement_type][binary] })

                log.debug( f'Finished getting binaries, libraries, and files required by {unit_file_fp}' )

                master_struct.update({ f'{unit_path}{current_unit}': unit_file })

    log.info( f'Finished recording all Systemd unit files into Master Structure' )
    log.vdebug( f'\n\n{master_struct}' )

    return master_struct


dependency_map = {}
'''dictionary that will hold all of the dependency relationships for a given master_struct
json.  Both "forward" and "backward" relationships will be established and recorded here.'''


def map_dependencies(master_struct: Dict, origin_unit: str, log: logging) -> dict:
    '''This function uses the information in the master struct to create a dependency list that users can view
    and record to investigate dependencies that are being created when the system is booting up.  The function
    will start with one unit ('default.target') and find all of the dependencies it creates.  Once it is done
    recording the dependencies for a unit, it checks to see if there are any dependencies that have not yet
    been recorded, and then records any that are missing one at a time.  Dependency tuples are created upon
    each iteration in order to maintain a backwards mapping of dependencies (e.g. what created the deps).  This
    is very useful when investigating the startup processes of something failing to boot properly.
    
    To record the unit files, the function unpacks a dependency tuple and uses it to create a DepMapUnit object.
    Once this object is created, any entries in the master struct that are associated with that unit file will
    be parsed and recorded.  If the master struct entry is a sym link entry, the dependency tuples will be
    created immediately after being parsed and deduplicated in order to maintain the full path to the sym link.
    Otherwise, all of the master struct entries, as well as previous dep map entires, that are associated with
    the unit file in question will be parsed, deduplicated, and then recorded to the dependency map.  Lastly,
    once everything is recorded the function will use the entry to create unique dependency tuples if needed.

    Unit files and their dependencies will have following structure.  Note that the first unit pointed to will
    not have any parents or reverse dependency mappings because no dependency tuples have been created for it:

    dependency_map = {
        'first.unit' : {
            'unit_file': 'default.target',
            'parents' : ['None'],
            'rev_deps' : ['None'],
            'dependencies' : ['multi-user.target', 'display-manager.serivce']
            },
        'all_other.units' : {
            'unit_file' : 'multi-user.target',
            'parents' : 'default.target',
            'rev_deps' : ['wanted_by', 'required_by', 'etc.']
            'Requires' : ['requires.units'],
            'Wants' : ['wants.units'],
            'dependencies' : [...]
            }
        }
    '''

    log.info('Starting the dependency relationship mapping...')
    log.vdebug( f'Searching for dependency relationships in:\n\n{master_struct}' )

    unrecorded_dependencies: List[tuple] = [(origin_unit, 'None', 'None')]

    recorded_dependencies: List[tuple] = []
    new_dep_tups: List[tuple] = []

    while len(unrecorded_dependencies) > 0:

        current_unit, parent_unit_path, dep_type = unrecorded_dependencies[0]
        new_dep_unit = DepMapUnit(current_unit, parent_unit_path, dep_type)

        log.debug( f'searching master struct for {current_unit} to satisfy {unrecorded_dependencies[0]}' )

        for sysd_obj_key in master_struct:
            if current_unit in dependency_map:
                log.debug( f'{current_unit} is already recorded. Copying old entry instead re-searching master struct' )
                new_dep_unit.load_from_dep_map( dependency_map[current_unit] )
                break

            # skip parsing non-unit file keys. This list is located in unit file lists
            if sysd_obj_key in ms_only_keys:
                continue

            # Dep dir names will trigger false positives on all units contained in the dir unless we only look
            # at the last item in the filepath split. (basic.target.wants/unit.file will trigger on basic.target)
            if new_dep_unit.unit_name in sysd_obj_key.split('/')[-1]:
                log.debug( f'Found {current_unit} in {sysd_obj_key}' )
                new_dep_unit.load_from_ms( master_struct[sysd_obj_key] )

                if master_struct[sysd_obj_key]['metadata']['file_type'] == 'sym_link':
                    new_dep_tups.extend( new_dep_unit.create_dep_tups(sysd_obj_key) )


        dependency_map.update({ new_dep_unit.unit_name: new_dep_unit.record() })
        new_dep_tups.extend( new_dep_unit.create_dep_tups(current_unit) )

        # check for bins so we can add libraries, files, and strings to the unit entry
        commands = new_dep_unit.get_commands()
        for command in commands:
            binary = get_bin_path(command)
            if 'libraries' not in dependency_map[current_unit]:
                dependency_map[current_unit].update({
                    'binaries': set(),
                    'libraries': set(),
                    'files': set(),
                    'strings': set()
                    })
            dependency_map[current_unit]['binaries'].update({ binary })
            dependency_map[current_unit]['libraries'].update( master_struct['libraries'][binary] )
            dependency_map[current_unit]['files'].update( master_struct['files'][binary] )
            dependency_map[current_unit]['strings'].update( master_struct['strings'][binary] )

        log.debug( f'info recorded for {new_dep_unit.unit_name}:' )
        log.vdebug( f'{new_dep_unit.record()}\n' )

        for tups in new_dep_tups:
            if tups[2] == 'sym_linked_from' and '/' not in tups[1]:
                log.debug( f'discarding {tups} because it is a sym link duplicate.' )
            elif tups in recorded_dependencies or tups in unrecorded_dependencies:
                log.debug( f'skipping recording dep tup: {tups}' )
            else:
                log.debug( f'adding {tups} to unrecorded dependencies' )
                unrecorded_dependencies.append(tups)

        # Clean up and prepare for next iteration
        new_dep_tups = []
        recorded_dependencies.append(unrecorded_dependencies.pop(0))

        log.vdebug( f'\nrecorded dependencies: {recorded_dependencies}' )
        log.vdebug( f'unrecorded dependencies: {unrecorded_dependencies}' )
        log.vdebug( f'\n\nnew dependency map: {dependency_map}\n' )

    log.info('Finished recording all dependency relationships')
    log.vdebug( f'\n\n{dependency_map}' )

    return dependency_map
