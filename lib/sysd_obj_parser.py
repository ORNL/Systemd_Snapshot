'''
sysd_obj_parser.py
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

Description:  This file is used to parse any of the systemd objects that are found in any
of the systemd unit file system paths.  For more information, see the function comments
or the README.md.
'''

import logging

from pathlib import Path
from os import readlink, getcwd, chdir, path
from typing import Any, Dict, List

from lib.unit_file_lists import possible_unit_opts, space_delim_opts



class SystemdFileFactory:


	def __init__(self, remote_path: str) -> None:
		'''The SystemdFile class is the initial object created for each file to be parsed.  After
		creating this object shell, the systemd_mapping.py file will decide which type of file
		it should be parsed as, and create a subclass modeled for that file type.  This class
		also contains the .record() and .info() handlers for each of the subclasses.'''

		self.remote_path = remote_path


	def parse_file(self, unit_path: str, unit_name: str) -> Dict[str, Any]:
		'''Check input to evaluate file type and parse accordingly'''

		self.unit_file_fp = Path( f'{self.remote_path}{unit_path}{unit_name}' )
		self.unit_path = unit_path
		self.name = unit_name

		if self.unit_file_fp.is_dir():
			self.dep_dir = self.parse_dep_dir(self.unit_path)
			return self.dep_dir.record()
		elif self.unit_file_fp.is_symlink():
			self.sym_link = self.parse_sym_link(self.unit_path)
			return self.sym_link.record()
		elif self.unit_file_fp.is_file():
			self.unit_file = self.parse_unit_file(self.unit_path)
			return self.unit_file.record()
		else:
			logging.warning( f'Error determining which systemd file type "{self.unit_file_fp}" is' )


	def parse_dep_dir(self, path: str) -> "DepDir":
		'''SystemdFileFactory.parse_dep_dir()

		After the SystemdFile object is created, the systemd_mapping.py file checks to see what
		type of subclass to create, and then sends it to the proper parse_file() function.
		parse_dep_dir() creates a new DepDir subclass where it is then verified as a valid
		dependency or config file directory, and then parsed accordingly.'''

		self.dep_dir = DepDir()
		self.dep_dir.check_dep_dir(self.remote_path, path, self.name)
		return self.dep_dir


	def parse_sym_link(self, path: str) -> "SymLink":
		'''SystemdFileFactory.parse_sym_link()

		After the SystemdFile object is created, the systemd_mapping.py file checks to see what
		type of subclass to create, and then sends it to the proper parse_file() function.
		parse_sym_link() creates a new SymLink subclass where it is then verified as a valid
		symbolic link, and then parsed accordingly.'''

		self.sym_link = SymLink(self.remote_path, path, self.name)
		return self.sym_link


	def parse_unit_file(self, path: str) -> "UnitFile":
		'''SystemdFileFactory.parse_unit_file()

		After the object is created, the systemd_mapping.py file checks to see what
		type of subclass to create, and then sends it to the proper parse_file() function.
		parse_unit_file() creates a new UnitFile subclass where it is verified as a valid
		unit file, and then parsed accordingly.'''

		self.unit_file = UnitFile(path, self.name)
		self.unit_file.update_unit_file(self.remote_path, path, self.name)
		self.unit_file.check_implicit_dependencies(self.unit_file.unit_type)
		return self.unit_file



class DepDir:


	def __init__(self) -> None:
		'''The SystemdFileFactory.DepDir class will be created and will automatically call check_dep_dir()
		to validate that it is a valid dependency or config directory any time systemd_mapping.py
		discovers what it believes to be a dep dir.  If it is a valid dep dir, the directory will
		be parsed to record all of the dependencies within that folder along with which type of
		dependencies are being created.'''

		self.dep_dir_paths: List[str] = []
		self.config_files: List[str] = []
		self.wants_deps: List[str] = []
		self.requires_deps: List[str] = []
		self.all_deps: List[str] = []


	def check_dep_dir(self, remote_path: str, path: str, dep_dir: str) -> None:
		'''SystemdFileFactory.DepDir.check_dep_dir()
		
		Validates that a dep dir has been encountered.  Can be one of .d, .wants, or .requires 
		directories. After validation, update functions are called to record the dependencies.'''
		
		self.dep_type: str = dep_dir.split('.')[-1]

		if self.dep_type == 'd':
			self.update_dep_dir(remote_path, path, dep_dir)
			self.update_config_files(self.dir_items)
		elif self.dep_type == 'wants':
			self.update_dep_dir(remote_path, path, dep_dir)
			self.update_wants_deps(self.dir_items)
		elif self.dep_type == 'requires':
			self.update_dep_dir(remote_path, path, dep_dir)
			self.update_requires_deps(self.dir_items)
		else:
			logging.warning( f'Unknown or invalid folder type: "{self.dep_type}" for {remote_path}{path}{dep_dir}' )		


	def update_dep_dir(self, remote_path: str, path: str, dep_dir: str) -> None:
		'''SystemdFileFactory.DepDir.update_dep_dir()
		
		Adds the dir path to the dep_dir_paths list and gets all file contents from the dep dir.'''

		self.dep_dir_paths.append( f'{path}{dep_dir}' )
		self.dir_items: List[str] = [ str(dep).split('/')[-1] for dep in Path( f'{remote_path}{path}{dep_dir}' ).glob('*') ]


	def update_config_files(self, dir_items: List[str]) -> None:
		'''SystemdFileFactory.DepDir.update_config_files()
		
		Adds all items from the dir into the config_files list'''

		self.config_files.extend(dir_items)


	def update_wants_deps(self, dir_items: List[str]) -> None:
		'''SystemdFileFactory.DepDir.update_wants_deps()
		
		Adds all items from the dir to both the wants_deps and all_deps lists. This is so 
		we can independently keep track of which units are wanted and which are required.'''

		self.wants_deps.extend(dir_items)
		self.all_deps.extend(dir_items)


	def update_requires_deps(self, dir_items: List[str]) -> None:
		'''SystemdFileFactory.DepDir.update_requires_deps()
		
		Adds all items from the dir to both the requires_deps and all_deps lists. This is so 
		we can independently keep track of which units are wanted and which are required.'''

		self.requires_deps.extend(dir_items)
		self.all_deps.extend(dir_items)


	def record(self) -> Dict[str, List[str]]:
		'''SystemdFileFactory.DepDir.record()
		
		Creates a dictionary of metadata containing the file_type, dependency_folder_paths, 
		dependencies, and any other lists that have been populated belonging to this object.'''

		dep_dir_data = {
			'file_type': 'dep_dir',
			'dependency_folder_paths': self.dep_dir_paths,
			'dependencies': self.all_deps
			}

		logging.vdebug( f'Initial dependency directory structure created:\n{dep_dir_data}' )

		if len(self.config_files) > 0:
			dep_dir_data['config_files'] = self.config_files
		if len(self.wants_deps) > 0:
			dep_dir_data['Wants'] = self.wants_deps
		if len(self.requires_deps) > 0:
			dep_dir_data['Requires'] = self.requires_deps

		logging.debug( f'Final dependency directory structure being returned:\n{dep_dir_data}' )

		return { 'metadata': dep_dir_data }


		
class SymLink:


	def __init__(self, remote_path: str, path: str, unit_name: str) -> None:
		'''The SystemdFileFactory.SymLink class is designed to make sure that each unit file is its own validated object.
		The intent is to make sure that there are no unknown or weird unit file types slipping through
		the cracks, and to verify that we know every unit file type that is being recorded.  If there are
		any weird unit file extensions or unit file types being used we should investigate them.'''

		sl_full_path = f'{remote_path}{path}{unit_name}'
		self.remote_path = remote_path

		if Path(sl_full_path).is_symlink():
			self.name = unit_name
			self.path = path

			self.target_unit: str = readlink(sl_full_path).split('/')[-1]
			self.target_path: str = self.get_target_path(sl_full_path)

		else:
			logging.warning( f'{sl_full_path} is not a sym link but is being parsed as one.' )


	def get_target_path(self, sl_full_path: str) -> str:
		'''SystemdFileFactory.SymLink.get_target_path()
		
		Checks to see if the target that the symbolic link is pointing to is specified through absolute 
		or relative pathing, and converts it to an absolute path. The resulting path will be specified as 
		the system path the sym link WOULD resolve to if the system were booting up, and the remote path 
		will be dropped if it is present.'''

		sl_ret_path = Path( readlink(sl_full_path) )

		if not sl_ret_path.is_absolute():
				current_dir = getcwd()
				chdir( Path(sl_full_path).parent )
				absolute_path = path.abspath(sl_ret_path)
				sl_ret_path = Path(absolute_path)
				chdir(current_dir)

		if self.remote_path != '' and self.remote_path in str(sl_ret_path):
				sl_ret_path = str(sl_ret_path.parent).split(self.remote_path)[-1]

		sl_ret_path = str(sl_ret_path).split( f'/{self.target_unit}' )[0]

		return f'{sl_ret_path}/'


	def record(self) -> Dict[str, Any]:
		'''SystemdFileFactory.SymLink.record()
		
		Creates a dictionary of metadata containing the file_type, sym link 
		information, and the dependency that has been recorded to this object.'''

		sym_link_data = {'file_type': 'sym_link'}
		sym_link_data['sym_link_path'] = self.path
		sym_link_data['sym_link_unit'] = self.name
		sym_link_data['sym_link_target_path'] = self.target_path
		sym_link_data['sym_link_target_unit'] = self.target_unit
		sym_link_data['dependencies'] = [self.target_unit]

		logging.debug( f'Symbolic link structure created:\n{sym_link_data}' )

		return { 'metadata': sym_link_data }



class UnitFile:


	def __init__(self, path: str, unit_file: str) -> None:
		'''The SystemdFileFactory.UnitFile class is designed to ensure that each unit file is its own validated object.
		The intent is to make sure that there are no unknown or weird unit file types or unit options slipping
		through the cracks, and to verify that we know every unit file type that and option that is being
		recorded. If there are any weird unit file extensions, unit types, or unit file options being used we
		should investigate them.'''

		self.name = unit_file
		self.path = path
		self.unit_type = self.get_unit_type(self.name)
		self.unit_struct: Dict[str, List[str]] = { 'metadata': { 'file_type': 'unit_file'} }


	def get_unit_type(self, unit_name: str) -> str:
		'''SystemdFileFactory.UnitFile.get_unit_type()
		
		Designed to make sure that each unit file has a valid suffix. The intent is to make sure that there are no unknown 
		unit file types slipping through the cracks, and to verify that we are aware of all unit file types being recorded. 
		If there are any unknown unit file extensions or unit file types being used we should investigate them.'''

		if unit_name.split('.')[-1] in possible_unit_opts:
			logging.debug( f'"{unit_name}" is a valid unit file type' )
			return unit_name.split('.')[-1]
		else:
			logging.warning( f'"{self.path}{unit_name}" is an invalid or unknown unit file type, returning "target" as the type instead' )
			return 'target'


	def update_unit_file(self, remote_path: str, path: str, unit_file: str) -> None:
		'''SystemdFileFactory.UnitFile.update_unit_file()
		
		Opens the specified unit file and parses it line by line. If an '=' is encountered on any of the lines it considers this 
		an option line, and will check the option and it's associated arguments to make sure they are valid before recording.'''

		with open( f'{remote_path}{path}{unit_file}', 'r' ) as in_file:
			for line in in_file:

				if '=' in line and '#' != line[0]:

					''' Some unit files have newline escapes '\\' for exec start opts.  This combines them
						until no more newline escapes '\\' are encountered at the end of the command/line.
						Otherwise, the newlines won't be recorded as arguments for that option and we will 
						lose part of the commands. '''
					
					if line[-2] == '\\':
						extra_line_marker = True
						while extra_line_marker == True:
							line = line.rstrip('\\\n') + in_file.readline()
							if line[-2] != '\\':
								extra_line_marker = False

					line_option = line.rstrip('\n').split('=')[0]
					arguments = '='.join( line.rstrip('\n').split('=')[1:] )

					self.option = self.check_option(line_option)
					self.arguments = self.format_arguments(line_option, arguments)

					if self.option in self.unit_struct:
						self.unit_struct[self.option].extend(self.arguments)
					else:
						self.unit_struct.update({ self.option: self.arguments })


	def check_option(self, line_option: str) -> None:
		'''SystemdFileFactory.UnitFile.check_option()
		
		Checks that each option being parsed is an option accepted by systemd.  Valid options are contained in
		the many section option lists in the unit_file_lists.py file, and may need to be updated periodically.'''

		for option_list in possible_unit_opts[self.unit_type]:
			if line_option in option_list:
				return line_option

		logging.warning( f'"{line_option}" is not a valid option for {self.unit_type} units.  Please investigate "{line_option}" option in {self.name}' )
		return line_option


	def format_arguments(self, line_option: str, line_arguments: str) -> None:
		'''SystemdFileFactory.UnitFile.format_arguments()
		
		Checks to see if valid options have space delimited arguments or not and records arguments based on this specification.'''

		if line_option in space_delim_opts:
			return line_arguments.split()

		return [line_arguments]


	def check_implicit_dependencies(self, unit_type: str) -> None:
		'''SystemdFileFactory.UnitFile.check_implicit_dependencies()
		
		Handle all implicit deps that are created based on the unit file type. Default 
		deps are automatically placed in the unit file upon creation, implicit deps are not.

		- TODO: look at escaping logic, slices, device paths, and auto/mount paths and check for paths on the system?'''

		# systemd.automount(5), automatic dependencies, implicit dependencies
		if unit_type == 'automount':
			self.unit_struct['metadata'].update({ 'Before': [ f'{self.name.split(".")[0]}.mount' ] })

		# systemd.path(5), description, para 3
		elif unit_type == 'path' and 'Unit' not in self.unit_struct:
			self.unit_struct['metadata'].update({ 
				'iPath_for': [ f'{self.name.split(".")[0]}.service' ],
				'Before': [ f'{self.name.split(".")[0]}.service' ]
				})

		# systemd.socket(5), description, para 4
		elif unit_type == 'socket' and 'Service' not in self.unit_struct:
			self.unit_struct['metadata'].update({ 'iSocket_of': [ f'{self.name.split(".")[0]}.service' ] })

		# systemd.socket(5), automatic dependencies, implicit dependencies
		elif unit_type == 'socket' and 'BindToDevice' in self.unit_struct:
			self.unit_struct['metadata'].update({ 'BindsTo': [ self.unit_struct['BindsToDevice'] ] })

		# systemd.service(5), automatic dependencies, implicit dependencies, bullet 1
		elif unit_type == 'service' and 'Type' in self.unit_struct:
			if self.unit_struct['Type'] == 'dbus':
				self.unit_struct['metadata'].update({ 'Requires': ['dbus.socket'], 'After': ['dbus.socket'] })
		
		# systemd.service(5), automatic dependencies, implicit dependencies, bullet 2
		elif unit_type == 'service' and 'Sockets' in self.unit_struct:
			socket_unit_list = [ unit for unit in self.unit_struct['Sockets'].split(' ') ]
			self.unit_struct['metadata'].update({
				'Wants': socket_unit_list,
				'After': socket_unit_list
				})

		# systemd.timer(5), description, para 3/ systemd.timer(5), implicit dependencies, bullet 1
		elif unit_type == 'timer' and 'Unit' not in self.unit_struct:
			self.unit_struct['metadata'].update({ 
				'iTimer_for': [ f'{self.name.split(".")[0]}.service' ],
				'Before': [ f'{self.name.split(".")[0]}.service' ]
				})

		# systemd.exec(5), implicit dependencies, bullet 4
		elif 'TTYPath' in self.unit_struct:
			self.unit_struct['metadata'].update({ 'After': ['systemd-vconsole-setup.service'] })
		
		# systemd.exec(5), implicit dependencies, bullet 5
		elif 'LogNamespace' in self.unit_struct:
			self.unit_struct['metadata'].update({ 'Requires': ['systemd-journald@.service'] })

		# systemd.resource-control(5), implicit dependencies, bullet 1
		elif 'Slice' in self.unit_struct:
			self.unit_struct['metadata'].update({
				'Requires': [ self.unit_struct['Slice'] ],
				'After': [ self.unit_struct['Slice'] ]
				})


	def record(self) -> Dict[str, List[str]]:
		'''SystemdFileFactory.UnitFile.record()
		
		Creates a dictionary of all valid options that were encountered while parsing the unit file, 
		along with their associated arguments. The metadata dict contains all implicit dependencies.'''

		logging.vdebug( f'Final unit file structure being returned:\n{self.unit_struct}' )

		return self.unit_struct
