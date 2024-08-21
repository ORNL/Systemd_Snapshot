'''
file_handlers.py
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

Description:  This file is currently unused, but is intended to provide a central location for all
    file handling/processing operations when more functionality is added to the tool. In the future, 
    I would like to include the ability to specify input files, possibly encode or format the data in 
    other formats, etc., but for now it's just able to deal with the output files.  For more information, 
    see function comments or the README.md.
'''

import logging

from json           import JSONEncoder, dump, load
from json.decoder   import JSONDecodeError
from pathlib        import Path
from sys            import exit


class MyEncoder(JSONEncoder):
    """Allows us to send arbitrary data structures to json.dump and json.dumps and get reasonable
    output. This will detect SETS and convert then to LISTS that json knows how to output.
    NOTE: Here we are IGNORING several of the critical objects. If custom encoders are needed place
    them here."""

    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, tuple):
            return list(obj)
        return JSONEncoder.default(self, obj)


def load_input_file(file_path: str, log: logging) -> dict:
    '''Takes a user path as a string, checks to verify it is a file, and then returns the dictionary saved in the file.'''

    try:
        with open(file_path) as user_file:
            loaded_struct = load(user_file)
            log.info( f'Successfully de-serialized file: {file_path}' )
            log.vdebug( f'Data extracted:\n\n{loaded_struct}' )
            return loaded_struct
        
    except FileNotFoundError as e:
        log.error( f'{e}\n' )
        log.error( f'{file_path} is not a valid file, can\'t parse master struct from it. See error message above for more info.' )
        exit(1)

    except JSONDecodeError as e:
        log.error( f'{e}\n' )
        log.error( f'Could not parse {file_path} properly. Fix file formatting or create a new systemd snapshot.' )
        exit(1)

    except IsADirectoryError as e:
        log.error( f'{e}\n' )
        log.error( f'Given path "{file_path}" ends with a directory and not a file. Be sure to point to a master struct file if using deps or graph actions.' )
        exit(1)


def create_output_file(file_struct: dict, struct_type: str, output_file: str, overwrite: bool, log: logging) -> None:
    '''The print_output() function will either send the final master_struct to a file or stdout depending on
    whether the user includes the -o option when running systemd_mapper.  If nothing is stored in the dict
    that is being printed then a message will be sent to the user indicating no data was found.  If there is
    something in the specified dict, the function will either print the data to stdout or check to see if
    the filename specified is already a file.  If the file already exists then no file will be written to
    avoid accidently overwriting files.'''

    if file_struct != {}:

        stype_len = len(struct_type) + 1

        # strip possible suffixes from user input to ensure output_file comparison is accurate
        if '.json' in output_file[-5:]:
            output_file = output_file[:-5]
        if f'_{struct_type}' in output_file[ -stype_len : ]:
            output_file = output_file[ : -stype_len ]

        log.info( f'Writing data to {output_file}_{struct_type}.json...' )

        if Path( f'{output_file}_{struct_type}.json' ).is_file() and overwrite == False:
            log.warning( f'{output_file}_{struct_type}.json already exists.  Skipping to avoid overwriting' )
            log.info('FAIL')
            return
       
        try:
            dump( file_struct, open( f'{output_file}_{struct_type}.json', 'w' ), indent=4, cls=MyEncoder )
            log.info('SUCCESS')

        except FileNotFoundError as e:
            log.warning( f'{e}\n' )
            log.warning('Specified directory was not found.  Verify the path you are trying to write to.')
            log.info('FAIL')
            return

        except PermissionError as e:
            log.warning( f'{e}\n' )
            log.warning('Not allowed to access specified directory.  Verify the path you are trying to write to.')
            log.info('FAIL')
            return

    else:
        log.warning( f'Nothing in {struct_type} to print.' )
        log.info('FAIL')
        return
