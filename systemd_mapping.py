"""
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
"""

import logging
import re

from subprocess import run
from pathlib import Path
from typing import List, Dict, Set, Tuple, Union

import unit_file_lists, sysd_obj_parser, dep_obj_parser


def get_bin_path(remote_path: str, cmd_string: str) -> str:
    """Return the path to a binary that will be called by a unit file 'Exec' command.
    
    Args:
        remote_path - String specifying the root directory of a remote filesystem to
            parse. Used as the root directory from which to start searches for binaries.
        cmd_string - An 'Exec' command string from a unit file.
        
    Returns:
        binary - String containing the full path to a binary that is referenced
            by a command string in a unit file. The path will start from the
            root directory of the target filesystem and will not include the
            remote_path.
    """
    bin_paths = [ '/bin/', '/sbin/', '/usr/bin/', '/usr/sbin' ]

    binary = cmd_string.split()[0]
    binary = remove_prefixes(binary)

    if not Path( binary ).is_file():
        for bin_path in bin_paths:
            if Path( f'{remote_path}{bin_path}{binary}' ).is_file():
                return f'{bin_path}{binary}'

    return binary


def remove_prefixes(binary: str) -> str:
    """Return an 'Exec' command with all Systemd command prefixes removed.
    
    This function removes all of the prefixes from a command directive option's
    corresponding argument. "@", "-", ":", and one of "+"/"!"/"!!"  may be used
    together and they can appear in any order. However, only one of "+", "!", "!!"
    may be used at a time. For more info see systemd.service (5) man page.
    
    Args:
        binary - path to a binary that is referenced in a unit file command line
        
    Returns:
        binary - path to a binary with all of the systemd prefixes removed
    """
    cmd_prefixes = ( '@', '-', ':', '+', '!' )

    i = 0
    while i < len(binary):
        if binary[i] in cmd_prefixes:
            i += 1
        else:
            # break when we hit the beginning of the actual command
            break
    
    return binary[i:]


def get_bin_libs(remote_path: str, binary: str) -> Set:
    """Return any libraries an executable requires.
    
    Use objdump to enumerate the given binary and return  that are required by it.
    This function is ONLY meant to be used when building the master struct.  If this
    function is used outside of the machine being snapshot, it WILL either return
    nothing or return false info based on the machine being used.
    
    Args:
        remote_path - String that specifies the root directory of a remote
            filesystem to parse.
        binary - abs path to a binary starting from the remote root directory

    Returns:
        set containing all of the libraries that are required by a binary
        
    TODO:
    - Create version check and use check_output for versions older than 3.7
    """
    lib_regex = re.compile('\s*NEEDED\s+(.+)')

    output = run( ['objdump', '-p', f'{remote_path}{binary}' ], capture_output=True, text=True )
    return set( lib_regex.findall(output.stdout) )


def get_bin_strings(remote_path: str, binary: str) -> Tuple[Set, Set]:
    """Return any interesting filenames or strings found in a binary.
    
    Use strings to enumerate the given binary and return paths and files that are
    referenced. This function is ONLY meant to be used when building the master struct.
    If this function is used outside of the machine being snapshot, it WILL either return
    nothing or return false info based on the machine being used.
    
    Args:
        remote_path - String that specifies the root directory of a remote
            filesystem to parse.
        binary - abs path to a binary starting from the remote root directory

    Returns:
        set containing interesting file and string references in a binary

    TODO:
    - Create version check and use check_output for versions older than 3.7
    """
    file_ext_list = [ 'cfg','conf','ini','log','exe',
        'der', 'crt', 'cer', 'pem', 'crl', 'pfx', 'p8', 'p8e', 'pk8', 'p10', 'csr',
        'p7r', 'p7s', 'p7m', 'p7c', 'p7b', 'keystore', 'p12', 'pkcs12' ]
    
    file_regex = re.compile( '^.+\.({})$'.format(  '|'.join(file_ext_list) ) )
    path_regex = re.compile('^/\w+(/[\w\.-]*)+$')
    # begin with / followed by at least 1 alphanum char with at least
    # one more / followed by alphanum, '.', or '-' chars any num of times

    output = run( [ 'strings', f'{remote_path}{binary}' ], capture_output=True, text=True )
    files = { file.split('=')[-1] for file in filter( file_regex.match, output.stdout.split() ) }
    strings = { string.split('=')[-1] for string in filter( path_regex.match, output.stdout.split() ) }

    # Since path regex will match on the same strings as file_regex, remove files from strings
    strings.symmetric_difference_update(files)

    return (files, strings)


def check_binaries(
        remote_path: str,
        master_struct: Dict,
        unit_struct: Dict[str, List]
    ) -> Dict[str, Dict[str, Set]]:
    """Return a dictionary containing forensic metadata about a binary.
    
    Check for unit file command options and inspect the binaries specified in the 
    command to get a listing of all of the libraries, config and log files, and other
    potentially interesting filepath strings that are specified in the binary.
    
    Args:
        remote_path - String that specifies the root directory of a remote
            filesystem to parse.
        master_struct - A reference to the master structure that contains all of the unit
            files that were found on a systemd system, including the binaries, libraries,
            files, and strings that were found on the system.
        unit_struct - a single unit file entry that will be parsed for any command
            directive options.
    """
    exec_deps = { 'binaries': {}, 'libraries': {}, 'files': {}, 'strings': {} }
    lib_paths = [ '/lib/', '/lib32/', '/lib64/', '/libexec/', '/lib/systemd/',
                '/usr/lib/systemd/', '/usr/lib/', '/usr/lib/x86_64-linux-gnu/',
                '/usr/lib32/', '/usr/lib64/', '/usr/libexec/', '/var/lib' ]
    unrecorded_binaries = []

    for option in unit_struct:
        if option in unit_file_lists.command_directives:
            for cmd in unit_struct[option]:
                if len(cmd) < 1:
                    continue

                binary = get_bin_path(remote_path, cmd)
                
                if (binary not in master_struct['binaries'] and
                    binary not in exec_deps['binaries']):

                    exec_deps['binaries'].update({ binary: get_bin_libs(remote_path, binary) })
                    bin_files, bin_strings = get_bin_strings(remote_path, binary)
                    exec_deps['files'].update({ binary: bin_files })
                    exec_deps['strings'].update({ binary: bin_strings })

    # Check each binary in the 'binaries' dictionary for library dependencies
    for binary in exec_deps['binaries']:
        if len(exec_deps['binaries'][binary]) > 0:
            unrecorded_binaries.append(binary)

    # Recursively record all encountered library dependencies
    for binary in unrecorded_binaries:
        record_library_deps( remote_path, exec_deps['binaries'][binary], lib_paths, exec_deps )

    return exec_deps


def record_library_deps( remote_path: str,
                        lib_list: List[str],
                        lib_paths: List[str],
                        lib_deps: Dict[ str, List[str] ] 
                    ) -> None:
    """Add all library dependencies to the dependency map.
    
    Iterate through each library and recursively add library dependencies. During the
    first call, lib_list will be the value of a single 'binaries' key in the master_struct.
    During any recursive call, lib_list will contain libraries required for the previous
    iteration's library.
    
    Args:
        remote_path - String that specifies the root directory of a remote filesystem
            to parse.
        lib_list - List of libraries that will be iterated through to find all library
            dependencies.
        lib_paths - Various paths to check for libraries
        lib_deps - A reference to the calling function's executable dependency dictionary.
    """
    for library in lib_list:
        if library not in lib_deps['libraries']:
            for lib_path in lib_paths:
                if Path( f'{remote_path}{lib_path}{library}' ).is_file():
                    new_libs = get_bin_libs( remote_path, f'{lib_path}{library}' )
                    lib_deps['libraries'].update({ library: new_libs })

                    if len(new_libs) > 0:
                        record_library_deps( remote_path, new_libs, lib_paths, lib_deps )


def map_systemd_full(master_struct: Dict, log: logging) -> dict:
    """Parse a filesystem and record all Systemd unit files.
    
    Map Systemd Full is designed to create a master_struct that will store all
    unit files on the system regardless of dependencies.  Ideally this will be used
    in conjunction with the output file option to allow users to create a
    "outfile_master_struct.json" file that can be referenced in the future to map
    dependencies without having to create a new master_struct every time.  
    
    The function iterates through all of the default systemd system paths, and
    checks to see if each one is present.  If the system path is present, all files
    and dependency folders will be established independently as a SystemdFile object,
    and then, depending on the file type, will be parsed as a dependency directory,
    symbolic link, or unit file.
    
    If a unit file has command directives that will run an binary upon getting started,
    we will record additional info on the binary in the libraries and files dictionaries.
    These are maps from the binaries found in the unit file command directives to
    libraries and files that the binary requires. These are recorded independently of the
    unit file entries to avoid duplication.
    
    Lastly, the function will update the master_struct with the parsed info.  The final
    product should follow the format detailed below:

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
    
    Args:
        master_struct - Empty at this point, but will be a reference to the master
            structure that contains all of the unit files that were found on a systemd
            system, including the binaries, libraries, files, and strings that were
            found on the system.
        log - a logging instance for logging functionality
    """
    log.info('Beginning recording of all files in Systemd folders.')
    remote_path = master_struct['remote_path']
    master_struct.update( spawn_skeletor('dict') )

    UnitFactory = sysd_obj_parser.SystemdFileFactory(remote_path)

    # Prevent duplicate dir traversal if /lib is sym linked to /usr/lib
    try:
        if Path( f'{remote_path}/lib' ).readlink() == f'usr/lib':
            unit_file_lists.sys_unit_paths.remove('/lib/systemd/system/')
    except OSError:
        log.debug('/lib is not sym linked to /usr/lib.  Retaining /lib/systemd/system system path.')

    for sys_path in unit_file_lists.sys_unit_paths:
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

                bin_requirements = check_binaries(remote_path, master_struct, unit_file)
                for requirement_type in bin_requirements:
                    # requirement_type is referencing either the binaries, libraries, files, or strings dict
                    for binary in bin_requirements[requirement_type]:
                        # binary is referencing the bin dicts w/in the Lib, File, or String dicts
                        master_struct[requirement_type].update({ binary: bin_requirements[requirement_type][binary] })
                log.debug( f'Finished getting binaries, libraries, and files required by {unit_file_fp}' )

                master_struct.update({ f'{unit_path}{current_unit}': unit_file })

    log.info( f'Finished recording all Systemd unit files into Master Structure' )
    log.vdebug( f'\n\n{master_struct}' )

    fstab = sysd_obj_parser.parse_fstab(remote_path)

    for unit in fstab:
        if unit not in master_struct:
            master_struct.update({ unit: fstab[unit] })

    return master_struct

dependency_map = {}
"""Hold all dependency relationships described by a master_struct."""


def map_dependencies( master_struct: Dict, origin_unit: str, log: logging ) -> dict:
    """Record all "forward" and "backward" dependency relationships in a Systemd filesystem.
    
    This function uses the information in the master struct to create a dependency list that users
    can view and record to investigate dependencies that are being created when the system is
    booting up.  The function will start with one unit ('default.target') and find all of the 
    dependencies it creates.  Once it is done recording the dependencies for a unit, it checks to
    see if there are any dependencies that have not yet been recorded, and then records any that are
    missing one at a time. Dependency tuples are created upon each iteration in order to maintain a
    backwards mapping of dependencies (e.g. what created the deps). This is very useful when
    investigating the startup processes of something failing to boot properly.
    
    To record the unit files, the function unpacks a dependency tuple and uses it to create a
    DepMapUnit object. Once this object is created, any entries in the master struct that are
    associated with that unit file will be parsed and recorded.  If the master struct entry is a sym
    link entry, the dependency tuples will be created immediately after being parsed and deduplicated
    in order to maintain the full path to the sym link. Otherwise, all of the master struct entries,
    as well as previous dep map entires, that are associated with the unit file in question will be
    parsed, deduplicated, and then recorded to the dependency map.  Lastly, once everything is recorded
    the function will use the entry to create unique dependency tuples if needed.

    Unit files and their dependencies will have following structure.  Note that the first unit pointed
    to will not have any parents or reverse dependency mappings because no dependency tuples have been
    created for it:

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

    Args:
        master_struct - Dictionary that holds all of the information gathered
            from parsing a system. All map_dependencies() operations will use
            the information contained within this dictionary.
        origin_unit - Unit file to start creating the dependency map from. This
            must be a valid unit inside of the master_struct.
        log - Logging instance for logging functionality.

    Returns:
        dependency_map - Dictionary containing all of the dependencies that
            will be created when a systemd system starts up.
    """
    log.info('Starting the dependency relationship mapping...')
    log.vdebug( f'Searching for dependency relationships in:\n\n{master_struct}' )

    unrecorded_dependencies: List[tuple] = [(origin_unit, 'None', 'None')]

    recorded_dependencies: List[tuple] = []
    new_dep_tups: List[tuple] = []

    while len(unrecorded_dependencies) > 0:

        current_unit, parent_unit_path, dep_type = unrecorded_dependencies[0]
        new_dep_unit = dep_obj_parser.DepMapUnit(current_unit, parent_unit_path, dep_type)

        log.debug( f'searching master struct for {current_unit} to satisfy {unrecorded_dependencies[0]}' )

        for sysd_obj_key in master_struct:
            if current_unit in dependency_map:
                log.debug( f'{current_unit} is already recorded. Copying old entry instead re-searching master struct' )
                new_dep_unit.load_from_dep_map( dependency_map[current_unit] )
                break

            # skip parsing non-unit file keys
            if sysd_obj_key in unit_file_lists.ms_only_keys:
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

        record_binary_metadata( new_dep_unit, master_struct, dependency_map )
        log.debug( f'info recorded for {new_dep_unit.unit_name}:' )
        log.vdebug( f'{new_dep_unit.record()}\n' )

        record_dep_tups(new_dep_tups, recorded_dependencies, unrecorded_dependencies)
        recorded_dependencies.append(unrecorded_dependencies.pop(0))
        log.vdebug( f'\nrecorded dependencies: {recorded_dependencies}' )
        log.vdebug( f'unrecorded dependencies: {unrecorded_dependencies}' )
        log.vdebug( f'\n\nnew dependency map: {dependency_map}\n' )

    log.info('Finished recording all dependency relationships...')
    log.vdebug( f'\n\n{dependency_map}' )

    log.info( 'Searching for fstab units that will be dynamically created during bootup...' )
    dependency_map['dynamic_mount_points'] = record_fstab_units( dependency_map, master_struct )

    log.info('Creating nested mount unit dependencies...')
    record_nested_mounts( dependency_map )

    return dependency_map


def record_binary_metadata( new_dep_unit: 'DepMapUnit', master_struct, dependency_map ) -> None:
    """Record metadata from binary dependencies created from the master_struct.
    
    Check for commands that are specified in a single unit file. Once commands are found,
    check the master structure for any binaries that are referenced in those commands. Once
    the binaries are found, recursively find all libraries, files, and strings that are
    referenced by the binary in the master structure.
    
    Args:
        new_dep_unit - A single instance of a DepMapUnit object.  Each iteration of the
            map_dependencies main loop will pass in a different DepMapUnit object.
        master_struct - A reference to the master structure that contains all of the unit
            files that were found on a systemd system, including the binaries, libraries,
            files, and strings that were found on the system.
        dependency_map - A reference to the dependency map which contains all of the
            dependency mappings between all of the unit files in the master structure.
            Only unit files that are scheduled to run on startup will be recorded.
    """
    commands = new_dep_unit.get_commands()
    unit = new_dep_unit.unit_name
    for command in commands:
        binary = get_bin_path(master_struct['remote_path'], command)

        if 'binaries' not in dependency_map[unit]:
            dependency_map[unit].update( spawn_skeletor('set') )
        dependency_map[unit]['binaries'].update({ binary })
        find_lib_deps( master_struct['binaries'][binary], master_struct['libraries'], dependency_map[unit]['libraries'] )
        dependency_map[unit]['files'].update( master_struct['files'][binary] )
        dependency_map[unit]['strings'].update( master_struct['strings'][binary] )


def spawn_skeletor( collection: str ) -> Dict[str, Set]:
    """Create a standardized set of dictionary entries for various functions."""
    if collection.lower() == 'dict':
        skeleton = {
            'binaries': {},
            'libraries': {},
            'files': {},
            'strings': {}
        }
    
    elif collection.lower() == 'set':
        skeleton = {
            'binaries': set(),
            'libraries': set(),
            'files': set(),
            'strings': set()
        }

    elif collection.lower() == 'list':
        skeleton = {
            'binaries': [],
            'libraries': [],
            'files': [],
            'strings': []
        }

    return skeleton


def record_dep_tups(
        new_dep_tups: List[Tuple],
        recorded_dependencies: List[Tuple],
        unrecorded_dependencies: List[Tuple]
        ) -> List[Tuple]:
    """Add unique dependency tuples that have been found to the dependency map.
    
    Iterate through a list of dependency tuples to update the unrecorded dependencies with any unique
    dependency tuples that have been gained from the last iteration of the dependency map main loop.
    
    Args:
        new_dep_tups - A list of dependency tuples containing various required dependency data.
        recorded_dependencies - List of dependency tuples that have already been recorded.
        unrecorded_dependencies - List of dependency tuples that are scheduled to be recorded.
    """
    new_dependencies = []

    for tups in new_dep_tups:
        if tups[2] == 'sym_linked_from' and '/' not in tups[1]:
            logging.debug( f'Discarding {tups} because it is a sym link duplicate.' )
        elif tups in recorded_dependencies or tups in unrecorded_dependencies:
            logging.debug( f'Skipping dep tup ({tups}) because it is already recorded or tracked' )
        else:
            logging.debug( f'Adding {tups} to unrecorded dependencies' )
            unrecorded_dependencies.append(tups)
        new_dependencies.append(tups)


def find_lib_deps(
        search_libs: List,
        libraries_dict: Dict[str, List[str]],
        dep_map_entry_libs: Set[str]
        ) -> None:
    """Recursively record library dependencies created by a binary.
    
    Take a list of libraries and recursively find all library dependencies.
    dep_map_entry_libs are being passed by reference in order to update the
    set of libraries required as new and unique libraries are found.
    
    Args:
        search_libs - list of libraries to search for dependencies. On the first
            call to this function, a list of libraries requied by a binary is passed
            in. For all recursive calls, the list that is passed in is a list of 
            libraries required by a library.
        libraries_dict - Full dictionary of all libraries in the dependency map to
            reference when checking for dependencies.
        dep_map_entry_libs - Running list of library dependencies. This is being
            passed in to keep track of libraries during recursive calls. Otherwise,
            if two dependencies require one another it will initiate an infinite loop.
    """
    for lib in search_libs:
        if lib not in dep_map_entry_libs:
            dep_map_entry_libs.add( lib )
            find_lib_deps( libraries_dict[lib], libraries_dict, dep_map_entry_libs )


def record_nested_mounts( dependency_map: Dict[str, Dict[str, Union[str, List[str]] ] ] ) -> None:
    """Create dependency relationships for nested mount unit files.
    
    Checking for mount file path dependencies after all unit file deps have been recorded.
    This is different from other implicit deps because it is dependant on all other unit file
    info being loaded, otherwise we might not see a nested filepath.
    """
    for unit_file in dependency_map:
        # Check to see if this mount file is nested under any other mount units
        unit_type = unit_file.split('.')[-1]
        if 'mount' in unit_type:
            
            # systemd.mount(5), implicit dependencies, bullet 1
            # Once we find a mount or automount unit, check to see if it lies beneath another mount unit
            for comp_unit in dependency_map:
                comp_unit_type = comp_unit.split('.')[-1]

                if 'mount' in comp_unit_type:
                    if ( unit_file.split('.')[0] in comp_unit.split('.')[0] and
                         unit_file != comp_unit ):
                        
                        logging.debug( f"'{unit_file}' is a mount unit nested under '{comp_unit}'")

                        if 'Requires' in dependency_map[comp_unit]:
                            dependency_map[comp_unit]['Requires'].append( unit_file )
                        else:
                            dependency_map[comp_unit].update({ 'Requires': [unit_file] })

                        if 'After' in dependency_map[comp_unit]:
                            dependency_map[comp_unit]['After'].append( unit_file )
                        else:
                            dependency_map[comp_unit].update({ 'After': [unit_file] })

        ## block device backed file-systems gain BindsTo and After on the corresponding device unit


def record_fstab_units( dependency_map, master_struct ) -> None:
    """Return a DepMapUnit representing a unit file that will be dynamically created by Systemd
    
    Systemd parses /etc/fstab to generate a unit file based on the fstab entries. These unit files
    will be created in /run/systemd/generator when the system boots up, but if a remote filesystem
    is being parsed, these unit files will not be shown.
    """
    dynamic_mount_points = {}

    for entry in master_struct:
        if ( entry not in unit_file_lists.ms_only_keys and
             master_struct[entry]['metadata']['file_type'] == 'fstab_unit' ):
            
            unit_name = entry.split('/')[-1]
            new_dep_unit = dep_obj_parser.DepMapUnit( unit_name, 'None', 'None' )
            new_dep_unit.load_from_ms( master_struct[entry] )
            # Create an actual unit file entry and record it to dep map while we have the obj
            dependency_map.update({ new_dep_unit.name: new_dep_unit.record() })

            # Only fstab units will dynamically mount things, so only these units should
            # create entries here
            dynamic_mount_points.update({
                unit_name: f"'{master_struct[entry]['Where'][0]}' will be dynamically mounted by '{entry}' as a(n) '{master_struct[entry]['Type'][0]}' filesystem"
            })

    return dynamic_mount_points


def compare_map_files( 
        origin_file,
        comp_file,
        log: logging
        ) -> Dict[ str, Union[ str, Dict[ str, Dict[str, str] ] ] ]:
    """Return a dictionary containing any differences between two systemd files.
    
    This function takes two previously recorded master struct or dependency map files and
    compares all of the objects in each to find the differences between them. It does this
    by iterating through each of the files after they have been translated back into their
    original dictionaries and a line-by-line comparison is performed.  Any differences are
    recorded in the diff_dict.

    diff_dict = {
        'top level key': 'This key was found in the init file but not the comp file!',
        'top level key2': 'This key was found in the comp file but not the init file!',
        'top level key3': {
            'subkey 2': 'This subkey was found in the init file but not the comp file!',
            'subkey 1': {
                'init file has: x': 'comp file has: y',
                'init file has: z': 'comp file does not have: z'
            },
        }
    }

    Args:
        - origin_file - Either a master struct file or a dependency map file.  This must be
            the same type of file as the comparison file.
        - comp_file - Either a master struct file or a dependency map file.  This must be
            the same type of file as the origin file.
        - log - A reference to our logging instance so that we can use logging
    
    Returns:
        - diff_dict - Dictionary containing all of the differences between the origin_file
            and the comp_file.
    """
    diff_dict = {}

    for tlk in origin_file:
        # All top level key values should be either strings or dicts, and if that is not the case,
        # we need to create a new check for that type of colleciton
        if not isinstance(origin_file[tlk], str) and not isinstance(origin_file[tlk], dict):
            diff_dict.update({ tlk: f'This origin file key has an unusual value type.  Expected either a string or dictionary, and got {type(origin_file[tlk])}' })
            log.warning( f"The origin file's '{tlk}' key has an unusual value type.  Expected either a string or a dict, and got '{type(origin_file[tlk])}'" )
            continue

        elif tlk not in comp_file:
            diff_dict.update({ tlk: 'This key was found in the origin file but not the comparison file' })
            log.vdebug( f'Origin file entry:\n{origin_file.keys()},\nComparison file entry:\n{comp_file.keys()}' )
            continue

        elif isinstance(origin_file[tlk], str):
            if origin_file[tlk] != comp_file[tlk]:
                diff_dict.update({ tlk: f"Origin file has: '{origin_file[tlk]}', but comparison file has: '{comp_file[tlk]}'" })
                log.vdebug( f'Origin file entry:\n{origin_file[tlk]},\nComparison file entry:\n{comp_file[tlk]}' )
            continue

        for subkey in origin_file[tlk]:
            
            if tlk =='libraries' and tlk in diff_dict:
                if 'updates' in diff_dict[tlk] and subkey.split('.')[0] in diff_dict[tlk]['updates']:
                    continue
            
            if subkey not in comp_file[tlk]:
                if tlk not in diff_dict:
                    diff_dict.update({ tlk: { subkey: 'This subkey was found in the origin file but not the comparison file!' } })
                else:
                    diff_dict[tlk].update({ subkey: 'This subkey was found in the origin file but not the comparison file!' })

                log.vdebug( f'Origin file entry:\n{origin_file[tlk]},\nComparison file entry:\n{comp_file[tlk]}' )
                continue

            # Check to see if subkey value is a dict or a list, since lists will always
            # be at the end of a nest and will always only contain strings.
            elif isinstance(origin_file[tlk][subkey], list):
                diff_return = compare_lists( origin_file[tlk][subkey], comp_file[tlk][subkey], diff_dict, tlk )
                if diff_return != None:
                    if tlk not in diff_dict:
                        diff_dict.update({ tlk: { subkey: diff_return } })
                    else:
                        diff_dict[tlk].update({ subkey: diff_return })
            
            # Only 'metadata' subkeys within the unit files should trigger this
            elif isinstance(origin_file[tlk][subkey], dict):

                for item in origin_file[tlk][subkey]:
                    if item not in comp_file[tlk][subkey]:
                        if tlk not in diff_dict:
                            diff_dict.update({ tlk: { subkey: { item: 'This subkey was found in the origin file but not the comparison file!' } } })
                        elif subkey not in diff_dict[tlk]:
                            diff_dict[tlk].update({ subkey: { item: 'This subkey was found in the origin file but not the comparison file!' } })
                        else:
                            diff_dict[tlk][subkey].update({ item: 'This subkey was found in the origin file but not the comparison file!' })
                            log.vdebug( f'Origin file entry:\n{origin_file[tlk][subkey]},\ncomparison file entry:\n{comp_file[tlk][subkey]}' )

                    elif isinstance(origin_file[tlk][subkey][item], str):
                        if origin_file[tlk][subkey][item] != comp_file[tlk][subkey][item]:
                            if tlk not in diff_dict:
                                diff_dict.update({ tlk: { subkey: { item: f'Origin file has: "{origin_file[tlk][subkey][item]}", but comparison file has: "{comp_file[tlk][subkey][item]}"'} } })
                            elif subkey not in diff_dict[tlk]:
                                diff_dict[tlk].update({ subkey: { item: f'Origin file has: "{origin_file[tlk][subkey][item]}", but comparison file has: "{comp_file[tlk][subkey][item]}"' } })
                            else:
                                diff_dict[tlk][subkey].update({ item: f'Origin file has: "{origin_file[tlk][subkey][item]}", but comparison file has: "{comp_file[tlk][subkey][item]}"' })

                    elif isinstance(origin_file[tlk][subkey][item], list):
                        diff_return = compare_lists( origin_file[tlk][subkey][item], comp_file[tlk][subkey][item], diff_dict, tlk )

                        if diff_return != None:
                            if tlk not in diff_dict:
                                diff_dict.update({ tlk: { subkey: { item: diff_return } } })
                            elif subkey not in diff_dict[tlk]:
                                diff_dict[tlk].update({ subkey: { item: diff_return } })
                            else:
                                diff_dict[tlk][subkey].update({ item: diff_return })

        """ Since we don't want to iterate over the top level keys in the comparison file that we already know are in the origin
            file, we will check all of the subkeys in the comparison file's corresponding tlk now.  This way we can be sure that
            all of the comparison file subkeys and items are seen for the tlk's that are also in the origin file."""
        for subkey in comp_file[tlk]:
            if tlk =='libraries' and tlk in diff_dict:
                if 'updates' in diff_dict[tlk] and subkey.split('.')[0] in diff_dict[tlk]['updates']:
                    continue
            
            if subkey not in origin_file[tlk]:
                if tlk not in diff_dict:
                    diff_dict.update({ tlk: { subkey: 'This subkey was found in the comparison file but not the origin file!' } })
                else:
                    diff_dict[tlk].update({ subkey: 'This subkey was found in the comparison file but not the origin file!' })
                log.vdebug( f'Comparison file entry:\n{comp_file[tlk]},\nOrigin file entry:\n{origin_file[tlk]}' )

            elif isinstance(comp_file[tlk][subkey], dict):

                for item in comp_file[tlk][subkey]:

                    # Since we are already doing the comparison of values between the keys/subkeys/items in the origin and comparison
                    # files, we only want to verify whether or not the key/subkey/item exists in the origin file to avoid duplication.

                    if item not in origin_file[tlk][subkey]:
                        if tlk not in diff_dict:
                            diff_dict.update({ tlk: { subkey: { item: f'This subkey was found in the comparison file but not the origin file!' } } })
                        elif subkey not in diff_dict[tlk]:
                            diff_dict[tlk].update({ subkey: { item: f'This subkey was found in the comparison file but not the origin file!' } })
                        else:
                            diff_dict[tlk][subkey].update({ item: f'This subkey was found in the comparison file but not the origin file!' })
                        log.vdebug( f'Comparison file entry:\n{comp_file[tlk][subkey]},\nOrigin file entry:\n{origin_file[tlk][subkey]}' )

    # After we iterate through all of the top level keys in the origin file, we want to make sure that
    # there aren't any top level keys that were in the comparison file that weren't in the origin file
    for tlk in comp_file:
        if not isinstance(comp_file[tlk], str) and not isinstance(comp_file[tlk], dict):
            diff_dict.update({ tlk: f'This comparison file key has an unusual value type.  Expected either a string or a dictionary, and got "{type(comp_file[tlk])}"' })
            log.warning( f'The comparison file\'s "{tlk}" key has an unusual value type.  Expected either a str or a dict, and got "{type(comp_file[tlk])}"')

        elif tlk not in origin_file:
            diff_dict.update({ tlk: 'This key was found in the comparison file but not the origin file!' })
            log.vdebug( f'Comparison file entry:\n{comp_file.keys()},\nOrigin file entry:\n{origin_file.keys()}' )

    return diff_dict


def compare_lists( origin_file_list: List[str],
                comp_file_list: List[str],
                diff_dict: Dict[str, Union[ str, Dict[ str, Union[ str, Dict[str, str] ] ] ]],
                tlk: str
                ) -> str:
    """Return a message detailing any unique entries between two lists.
    
    Any time libraries are updated between versions it causes a lot of redundant info
    to be output in the 'binaries' and 'libraries' keys of the diff_dict. In order to
    make the output more succinct and useful, this function iterates through each of
    the 'unique' lists to check whether the item in question is merely a library update
    or something more interesting to output.

    Args:
        origin_file_list - List of items specific to the origin file
        comp_file_list - List of items specific to the comparison file
        diff_dict - Reference to the comparison dictionary that will be output
        tlk - Current top level key we are looking at within the diff_dict. This
            will be used to skip unit file info and ensure we are only discarding
            redundant library updates.
    
    Returns:
        ret_entry - String that describes the differences in items found between
            the origin file and the comparison file. ret_entry is returned to the
            caller to be recorded in the diff_dict.
    """
    unique_to_origin = []
    unique_to_comp = []
    removal_libs = []
    ret_entry = None

    for item in origin_file_list:
        if item not in comp_file_list:
            unique_to_origin.append(item)

    for item in comp_file_list:
        if item not in origin_file_list:
            unique_to_comp.append(item)
    
    if tlk in unit_file_lists.ms_only_keys:
        # Discard redundant differences if they are just library updates
        for orig_lib in unique_to_origin:
            for comp_lib in unique_to_comp:
                if orig_lib.split('.')[0] == comp_lib.split('.')[0]:
                    removal_libs.append( (orig_lib, comp_lib) )
                    
                    if 'libraries' not in diff_dict:
                        diff_dict.update({ 
                            'libraries': {
                                'updates': {
                                    orig_lib.split('.')[0]: f"Changed from '{orig_lib}' in origin file to '{comp_lib}' in comparison file."
                                }
                            }
                        })
                    elif 'updates' not in diff_dict['libraries']:
                        diff_dict['libraries'].update({
                            'updates': {
                                orig_lib.split('.')[0]: f"Changed from '{orig_lib}' in origin file to '{comp_lib}' in comparison file."
                            }
                        })
                    elif orig_lib.split('.')[0] not in diff_dict['libraries']['updates']:
                        diff_dict['libraries']['updates'].update({
                            orig_lib.split('.')[0]: f"Changed from '{orig_lib}' in origin file to '{comp_lib}' in comparison file."
                        })

        for olib, clib in removal_libs:
            unique_to_origin.remove(olib)
            unique_to_comp.remove(clib)

    if unique_to_origin != [] and unique_to_comp != []:
        ret_entry = f'Origin file contains {unique_to_origin}, which comparison file doesn\'t have.\nComparison file contains {unique_to_comp}, which origin file doesn\'t have.'
    
    elif unique_to_origin != []:
        ret_entry = f'Origin file contains {unique_to_origin}, which the comparison file doesn\'t have'

    elif unique_to_comp != []:
        ret_entry = f'Comparison file contains {unique_to_comp}, which the origin file doesn\'t have'

    return ret_entry