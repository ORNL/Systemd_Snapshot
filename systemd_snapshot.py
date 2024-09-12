#!/usr/bin/python3
'''
Systemd Snapshot
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

Description: This tool creates a systemd snapshot of either locally or remotely hosted file systems, and 
    records collected data for forensic analysis.  It does this by parsing all of the unit files contained
    within the default systemd unit paths (system only) and records all unit file data, implicit dependencies, 
    and explicit dependencies. Systemd Snapshot will then record all of this information in a master struct
    (ms) file, and create both an interactive graph file for use with cytoscape and a json-formatted
    dependency map.

    The dependency map begins with one unit file (default.target by default) and maps out all dependencies
    that are created by that unit.  After dependencies are recorded the dependency repeats this dependency
    mapping for each dependency that is created, until no more dependencies remain.  Both forward and
    backward dependency relationships are maintained within the dependency map, but not all unit files in
    the master structure will be recorded here since startup processes vary based on runlevel.  Currently,
    only default.target is supported as the initial unit file without changing this in the systemd_mapping
    file, but in the future the -t option will be able to be used from the cmd line to start the dependency
    map with a different unit file. This will allow users to start at an arbitrary point within the startup
    process and view dependencies, conditions, etc. that are required after a specific point during startup,
    or allow users to see what will start up when a different runlevel is specified.

    Optionally, you can create networkx graphs from the information in the master structure that is built from
    the Systemd filesystem and files. These graphs are DIRECTED MULTIGRAPHS: each edge has a source and a
    target AND there can be multiple edges between two vertices. The multiple edges are distinct by their labels.

    Vertices in the graph represent the following information: UNIT files, ALIAS symbolic links, COMMANDs executed
    via Systemd, EXECUTABLES within COMMANDS, LIBRARYs used by EXECUTABLES, and useful STRINGS within EXECUTABLES.
    The edges in the graph established NAMED relationships between these Systemd elements.

    A Tree can be created from the complete graph by designating a root node from any UNIT FILE within the
    systemd structure. This is actually VERY handy for focusing your analysis efforts.

    Graphs can also be trasferred to Cytoscape for visualization via Cytoscape's REST api and the py4cytoscape
    library. There is a capability to build a custom style for your graph -- that will require some additional
    documentation.
'''

import logging
import pdb

from argparse   import ArgumentParser, RawDescriptionHelpFormatter
from pathlib    import Path

from lib.systemd_mapping    import map_systemd_full, map_dependencies, compare_map_files
from lib.file_handlers      import create_output_file, load_input_file

# JMC: for graphing capability in Cytoscape.
from lib.grapher          import Grapher
from lib.style            import Style


def init_logger( name: str, level: str ) -> logging:
    """Establish a logger for the system to use with a given name and log level.
    This also uses a log message formatter that can be customized as needed.
    """

    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(5):
            self._log(5, message, args, **kwargs)
    
    def logToRoot(message, *args, **kwargs):
        logging.log(5, message, *args, **kwargs)

    logging.addLevelName(5, 'VDEBUG')
    setattr(logging, 'VDEBUG', 5)
    setattr(logging.getLoggerClass(), 'vdebug', logForLevel)
    setattr(logging, 'vdebug', logToRoot)

    logger = logging.getLogger( name )
    logger.setLevel( level.upper() )

    custom_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt='%(asctime)s.%(msecs)02d %(levelname)s [%(funcName)s]: %(message)s',
        datefmt='%H:%M:%S'
        )
    custom_handler.setFormatter( formatter )
    logger.addHandler( custom_handler )

    return logger


def main():
    '''This tool creates a systemd snapshot of either locally or remotely hosted file systems, and records 
    collected data for forensic analysis.'''

    parser = ArgumentParser(
        prog='systemd_snapshot',
        formatter_class=RawDescriptionHelpFormatter,
        description='This tool creates a systemd snapshot of either locally or remotely hosted file systems, and records collected data for forensic analysis.',
        epilog='''
Example usage:

systemd_snapshot.py -a master                                   - create a systemd snapshot of the local system, saved to working-dir/snapshot_ms.json
systemd_snapshot.py -a deps                                     - a master struct is required for dep map and graph.  Since no path is specified,
                                                                  snapshot_ms.json will be created first, and then a dep map will be made from it
systemd_snapshot.py -a deps -p ss_ms.json -t runlevel2.target   - use ss_ms.json file to create a dep map originating from runlevel2.target
systemd_snapshot.py -a master -o new/snapshot                   - save snapshot to new/snapshot_ms.json
systemd_snapshot.py -a deps -p /path/to/snapshot_ms.json        - use specified master struct snapshot to build only the dep map
systemd_snapshot.py -a graph -p /path/to/snapshot_ms.json       - use specified master struct snapshot to build only the graph
systemd_snapshot.py -a all -p /remotely/hosted/fs/root          - create ms snapshot from remote fs and build dep map and graph from it
systemd_snapshot.py -a all -p /remote/fs -o new/snaps           - create ms snapshot from remote fs, build dep map and graph from master struct,
                                                                  and save all files as new/snaps_*
systemd_snapshot.py -a diff -p snap1_ms.json -c snap2_ms.json   - compare the differences between snap1 and snap2. Both files need to be the same type.
                                                                  If you try to compare a master struct file to a dependency map file you will get an error.''')
    parser.add_argument(
        '-a',
        '--action',
        type=str,
        dest='action',
        default='all',
        help='''Action to take. One of {'master', 'deps', 'graph', 'diff', 'all'}.  If action is 'master' or 'all', path option will be used as a pointer to a remotely 
        hosted fs. Otherwise, the path option will be used as a pointer to a master struct snapshot file.''')

    parser.add_argument(
        '-o',
        '--output-file',
        type=str,
        dest='output_file',
        default=f'{Path.cwd()}/data/snapshot',
        help='File path to save master struct as. All artifacts will be created in the same directory. (Default: working-directory/snapshot)')

    parser.add_argument(
        '-f',
        '--force-overwrite',
        dest='overwrite',
        action='store_true',
        help='Allow systemd snapshot to overwrite files if they already exist.')

    parser.add_argument(
        '-p',
        '--path',
        type=Path,
        dest='user_path',
        default='/',
        help='''Use -p followed by a path to set the root path to a remotely hosted filesystem if used with master or all actions, 
        or the path to a ms.json file if used with other actions.  Defaults to the locally hosted filesystem.''')

    parser.add_argument(
        '-t',
        '--target-unit',
        type=str,
        metavar='TARGET_UNIT',
        dest='origin_unit',
        default='default.target',
        help='Use -t followed by a unit name to start the dependency map from the specified unit file instead of default.target')

    parser.add_argument(
        '-c',
        '--comparison-file',
        type=str,
        dest='comp_file',
        default=None,
        help='Required if the action to take is "diff".  Use -c followed by a filename in order to set a comparison file.')
    
    parser.add_argument(
        '-l',
        '--log-level',
        type=str,
        dest='log_level',
        default='INFO',
        help='Change logging level if desired. Options from most to least verbose: [ vDEBUG, DEBUG, INFO, WARNING, ERROR, CRITICAL ]')

    parser.add_argument(
        '-D',
        '--depth',
        type=int,
        dest='depth',
        default=0,
        help='the depth of the tree to produce.')

    parser.add_argument(
        "-S",
        "--style-file",
        type=str,
        default='data/graph_style.json',
        dest='style_file',
        help='''The style to use for the graph; if a path to a file it will be used as a json style specification; 
        otherwise, it is assumed to be a current cytoscape style.''')

    args = parser.parse_args()
    output_file = args.output_file
    
    log = init_logger(__name__, args.log_level)
    action = args.action.lower()
    origin_unit = args.origin_unit.lower()
    comp_file_path = args.comp_file

    if args.user_path == Path('/'):
        user_path = ''
    else:
        user_path = str( args.user_path.absolute() )
        
    log.debug( f'path given: {user_path}' )
    log.debug( f'action: {args.action}' )
    log.debug( f'log level: {args.log_level}' )
    log.debug( f'graph style: {args.style_file}' )

    log.info( f'overwrite output files: {args.overwrite}')

    if action in ('master', 'all'):
        # if master or all is the chosen action, user_path will be passed as the remote_path
        master_struct = map_systemd_full({'remote_path': user_path}, log)
        create_output_file(master_struct, 'ms', output_file, args.overwrite, log)

    elif action not in ('master', 'all') and user_path == '':
        # if no path to a ms file is given, no remote_path is used which parses the locally hosted system
        log.info( f'No path given. Parsing local systemd system to build a master struct' )
        master_struct = map_systemd_full({'remote_path': user_path}, log)
        create_output_file(master_struct, 'ms', output_file, args.overwrite, log)

    else:
        # if a path is given w/other than master or all, load the file at the given path for future actions
        master_struct = load_input_file(user_path, log)

    if action in ('dep', 'deps', 'all'):
        dependency_map = map_dependencies(master_struct, origin_unit, log)
        create_output_file(dependency_map, 'dm', output_file, args.overwrite, log)

    if action in ('graph', 'all'):
        # the user wants a graph created and transmitted via REST to Cytoscape.
        # this requires the master_struct map.
        # optional arguments requires are: args.root and args.depth and args.style_file

        grapher = Grapher( 'systemd_graph', log )

        # build the ENTIRE graph; if we want a tree subgraph, that will be constructed FROM THIS
        # larger graph -- we will need all the attributes provided here.
        log.info("Starting to build main graph tree...")
        G = grapher.build( master_struct )
        log.info("Finished building main graph tree...")

        if origin_unit != 'default.target':
            # build a TREE from the larger graph.
            # TODO: Make this more general -- right now we can only specify UNIT type nodes.
            log.info( f'Building subgraph starting with {origin_unit}...' )
            source = ( origin_unit, 'UNIT' )
            T = grapher.build_tree( G, source, args.depth )
            grapher.transmit_to_cytoscape( T )
            log.info('Finished building subgraph...')

        else:
            # just transmit the entire graph.
            grapher.transmit_to_cytoscape( G )

        if args.style_file:
            log.info('Applying style settings to graph...')
            # the user has provided either a style file or a style name.
            sf = Path( args.style_file )
            if sf.is_file():
                # a json style file has been provided.
                style_json = Style.read_style_file( sf )

                gstyle = Style('systemd_graph_style', log)
                name = gstyle.create( style_json )
                log.debug("The style name used for the newly created style is: {}".format( name ))
                gstyle.activate()
            else:
                # the user has provided a style name.
                gstyle = Style( args.style_file, log )
                gstyle.activate()

    if action in ('compare', 'diff'):

        if user_path == '' or comp_file_path == None:
            log.error( 'Please specify an origin file with -p and a comparison file with -c in order to do a comparison.' )
            return

        initial_file = load_input_file( user_path, log )
        comp_file = load_input_file( comp_file_path, log )

        if ( 'remote_path' in initial_file ) ^ ( 'remote_path' in comp_file ):
            log.error('These appear to be two different types of files.\r\nPlease compare the same types of files (eg. two master struct files or two dependency map files)')
            return

        # if a change has been made in either of the comparison items, record necessary changes.
        diff_dict = compare_map_files( initial_file, comp_file, log )
        create_output_file( diff_dict, 'df', output_file, args.overwrite, log )

if __name__ == '__main__':
    main()
