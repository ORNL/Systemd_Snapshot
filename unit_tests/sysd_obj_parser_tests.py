'''
sysd_obj_parser_tests.py
Author: Michael R. Huettel
Author: Jason M. Carter
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

Description: This is a test file that is used to test lib/sysd_obj_parser.py. 
    Tests were broken into test suites based on the class being tested, and tests 
    are performed from the bottom up for each test suite.  When adding new unit
    tests be sure to add them to the corresponding test suite function as well.
'''

import unittest
import logging

from os import mkdir, rmdir, remove, symlink, unlink, getcwd
from typing import List, Dict, Union

from lib.sysd_obj_parser import SystemdFileFactory, DepDir, SymLink, UnitFile



class TestSymLinks(unittest.TestCase):


    def test_get_target_path_with_relative_path(self) -> None:
        '''Verify relative paths are translated to absolute paths correctly when parsing sym links'''

        test_unit = SymLink(f'{getcwd()}/', 'test/', 'relative_sym_link.target')

        self.assertEqual(test_unit.target_path, 'test/target_dir/')
        self.assertEqual(test_unit.target_unit, 'sym_link_target.target')

        sym_link_struct: Dict[str, Dict[str, Union[str, List]]] = test_unit.record()

        self.assertEqual(sym_link_struct, {
            'metadata': {
                'file_type': 'sym_link',
                'sym_link_path': 'test/',
                'sym_link_unit': 'relative_sym_link.target',
                'sym_link_target_path': 'test/target_dir/',
                'sym_link_target_unit': 'sym_link_target.target',
                'dependencies': ['sym_link_target.target']
                }
            })


    def test_get_target_path_with_same_parent(self) -> None:
        '''Verify relative paths within the same dir as the target are translated to absolute paths correctly when parsing sym links'''

        test_unit = SymLink(f'{getcwd()}/', 'test/target_dir/', 'same_parent_sym_link.target')

        self.assertEqual(test_unit.target_path, 'test/target_dir/')
        self.assertEqual(test_unit.target_unit, 'sym_link_target.target')

        sym_link_struct: Dict[str, Dict[str, Union[str, List]]] = test_unit.record()

        self.assertEqual(sym_link_struct, {
            'metadata': {
                'file_type': 'sym_link',
                'sym_link_path': 'test/target_dir/',
                'sym_link_unit': 'same_parent_sym_link.target',
                'sym_link_target_path': 'test/target_dir/',
                'sym_link_target_unit': 'sym_link_target.target',
                'dependencies': ['sym_link_target.target']
                }
            })

    def test_get_target_path_with_relative_dot_path(self) -> None:
        '''Verify relative paths with ../ notation are translated to absolute paths correctly when parsing sym links'''

        test_unit = SymLink(f'{getcwd()}/', 'test/relative_sym_link_dir/', 'relative_dot_sym_link.target')

        self.assertEqual(test_unit.target_path, 'test/target_dir/')
        self.assertEqual(test_unit.target_unit, 'sym_link_target.target')

        sym_link_struct: Dict[str, Dict[str, Union[str, List]]] = test_unit.record()

        self.assertEqual(sym_link_struct, {
            'metadata': {
                'file_type': 'sym_link',
                'sym_link_path': 'test/relative_sym_link_dir/',
                'sym_link_unit': 'relative_dot_sym_link.target',
                'sym_link_target_path': 'test/target_dir/',
                'sym_link_target_unit': 'sym_link_target.target',
                'dependencies': ['sym_link_target.target']
                }
            })


    def test_get_target_path_with_abs_path(self) -> None:
        '''Verify absolute paths are copied over correctly when parsing sym links'''

        test_unit = SymLink(f'{getcwd()}/', 'test/abs_sym_link_dir/', 'abs_sym_link.target')

        self.assertEqual(test_unit.target_path, 'test/target_dir/')
        self.assertEqual(test_unit.target_unit, 'sym_link_target.target')

        sym_link_struct: Dict[str, Dict[str, Union[str, List]]] = test_unit.record()
        
        self.assertEqual(sym_link_struct, {
            'metadata': {
                'file_type': 'sym_link',
                'sym_link_path': 'test/abs_sym_link_dir/',
                'sym_link_unit': 'abs_sym_link.target',
                'sym_link_target_path': 'test/target_dir/',
                'sym_link_target_unit': 'sym_link_target.target',
                'dependencies': ['sym_link_target.target']
                }
            })


    def test_sym_link_parsing_failure(self) -> None:
        '''Verify logging message is displayed when file is being parsed as a sym link when it isn't one.'''

        test_unit = SymLink(f'{getcwd()}/', 'test/', 'not_a_sym_link.target')

        with self.assertLogs('root', level='WARNING') as logs:
            logging.getLogger('root').warning('"test/not_a_sym_link.target" is not a sym link but is being parsed as one.')
        self.assertEqual(logs.output, ['WARNING:root:"test/not_a_sym_link.target" is not a sym link but is being parsed as one.'])


    def test_sym_link_record(self) -> None:
        '''Verify all sym link info is being recorded and returned correctly. See above for path parsing validation'''

        test_unit = SymLink(f'{getcwd()}/', 'test/', 'relative_sym_link.target')

        sym_link_struct: Dict[str, Dict[str, Union[str, List]]] = test_unit.record()

        self.assertEqual(sym_link_struct, {
            'metadata': {
                'file_type': 'sym_link',
                'sym_link_path': 'test/',
                'sym_link_unit': 'relative_sym_link.target',
                'sym_link_target_path': 'test/target_dir/',
                'sym_link_target_unit': 'sym_link_target.target',
                'dependencies': ['sym_link_target.target']
                }
            })

        with self.assertLogs('root', level='DEBUG') as logs:
            logging.getLogger('root').debug("Symbolic link structure created:\n{'file_type': 'sym_link', 'sym_link_path': 'test/', 'sym_link_unit': 'test_unit.target', 'sym_link_target_path': 'test/sym_link_dir/', 'sym_link_target_unit': 'unit.target', 'dependencies': ['unit.target']}")
        self.assertEqual(logs.output, ["DEBUG:root:Symbolic link structure created:\n{'file_type': 'sym_link', 'sym_link_path': 'test/', 'sym_link_unit': 'test_unit.target', 'sym_link_target_path': 'test/sym_link_dir/', 'sym_link_target_unit': 'unit.target', 'dependencies': ['unit.target']}"])



class TestDependencyDirectories(unittest.TestCase):

    def test_update_config_files(self) -> None:
        '''Verify that config files are parsed correctly'''

        test_dep_dir = DepDir()
        dir_items = ['config1', 'config2', 'config3']
        test_dep_dir.update_config_files(dir_items)

        self.assertTrue(test_dep_dir.config_files == ['config1', 'config2', 'config3'])
        self.assertTrue(test_dep_dir.wants_deps == [])
        self.assertTrue(test_dep_dir.requires_deps == [])
        self.assertTrue(test_dep_dir.all_deps == [])

        more_dir_items = ['config4', 'config5', 'config6']
        test_dep_dir.update_config_files(more_dir_items)

        self.assertTrue(test_dep_dir.config_files == ['config1', 'config2', 'config3', 'config4', 'config5', 'config6'])
        self.assertTrue(test_dep_dir.wants_deps == [])
        self.assertTrue(test_dep_dir.requires_deps == [])
        self.assertTrue(test_dep_dir.all_deps == [])


    def test_update_wants_deps(self) -> None:
        '''Verify that wants directories are parsed correctly'''

        test_dep_dir = DepDir()
        dir_items = ['unit1.target', 'unit2.target']
        test_dep_dir.update_wants_deps(dir_items)

        self.assertTrue(test_dep_dir.wants_deps == ['unit1.target', 'unit2.target'])
        self.assertTrue(test_dep_dir.all_deps == ['unit1.target', 'unit2.target'])
        self.assertTrue(test_dep_dir.config_files == [])
        self.assertTrue(test_dep_dir.requires_deps == [])
        
        more_dir_items = ['unit3.target', 'unit4.target']
        test_dep_dir.update_wants_deps(more_dir_items)

        self.assertTrue(test_dep_dir.wants_deps == ['unit1.target', 'unit2.target', 'unit3.target', 'unit4.target'])
        self.assertTrue(test_dep_dir.all_deps == ['unit1.target', 'unit2.target', 'unit3.target', 'unit4.target'])
        self.assertTrue(test_dep_dir.config_files == [])
        self.assertTrue(test_dep_dir.requires_deps == [])

    def test_update_requires_deps(self) -> None:
        '''Verify that requires directories are parsed correctly'''

        test_dep_dir = DepDir()
        dir_items = ['unit1.target', 'unit2.target']
        test_dep_dir.update_requires_deps(dir_items)

        self.assertTrue(test_dep_dir.requires_deps == ['unit1.target', 'unit2.target'])
        self.assertTrue(test_dep_dir.all_deps == ['unit1.target', 'unit2.target'])
        self.assertTrue(test_dep_dir.config_files == [])
        self.assertTrue(test_dep_dir.wants_deps == [])
        
        more_dir_items = ['unit3.target', 'unit4.target']
        test_dep_dir.update_requires_deps(more_dir_items)

        self.assertTrue(test_dep_dir.requires_deps == ['unit1.target', 'unit2.target', 'unit3.target', 'unit4.target'])
        self.assertTrue(test_dep_dir.all_deps == ['unit1.target', 'unit2.target', 'unit3.target', 'unit4.target'])
        self.assertTrue(test_dep_dir.config_files == [])
        self.assertTrue(test_dep_dir.wants_deps == [])

    def test_update_all_deps(self) -> None:
        '''Verify that wants and requires directories are both adding units to the all_deps list'''

        test_dep_dir = DepDir()
        dir_items = ['unit1.target', 'unit2.target']
        test_dep_dir.update_wants_deps(dir_items)

        self.assertTrue(test_dep_dir.wants_deps == ['unit1.target', 'unit2.target'])
        self.assertTrue(test_dep_dir.all_deps == ['unit1.target', 'unit2.target'])
        self.assertTrue(test_dep_dir.config_files == [])
        self.assertTrue(test_dep_dir.requires_deps == [])

        more_dir_items = ['unit3.target', 'unit4.target']
        test_dep_dir.update_requires_deps(more_dir_items)

        self.assertTrue(test_dep_dir.wants_deps == ['unit1.target', 'unit2.target'])
        self.assertTrue(test_dep_dir.requires_deps == ['unit3.target', 'unit4.target'])
        self.assertTrue(test_dep_dir.all_deps == ['unit1.target', 'unit2.target', 'unit3.target', 'unit4.target'])
        self.assertTrue(test_dep_dir.config_files == [])

    def test_update_dep_dir(self) -> None:
        '''Verify dep_dir_paths is updated correctly'''

        test_dep_dir = DepDir()

        test_dep_dir.update_dep_dir('/etc/systemd', '/system/', 'unit.target.wants')
        self.assertEqual(test_dep_dir.dep_dir_paths, ['/system/unit.target.wants'])

        test_dep_dir.update_dep_dir('/etc/systemd', '/system/', 'unit.target.requires')
        self.assertEqual(test_dep_dir.dep_dir_paths, ['/system/unit.target.wants', '/system/unit.target.requires'])

    def test_check_dep_dir(self) -> None:
        '''Finishing testing parsing update functions by verifying invalid dep dir types are caught'''

        test_dep_dir = DepDir()
        test_dep_dir.check_dep_dir('/etc/systemd', '/system/', 'unit.service.invalid')

        with self.assertLogs('root', level='WARNING') as logs:
            logging.getLogger('root').warning('Unknown or invalid folder type: "invalid" for /etc/systemd/system/unit.service.invalid')
        self.assertTrue(logs.output, 'WARNING:root:Unknown or invalid folder type: "invalid" for /etc/systemd/system/unit.service.invalid')

        test_dep_dir.check_dep_dir('/etc/systemd', '/system/', 'unit.target.wants')
        test_dep_dir.check_dep_dir('/etc/systemd', '/system/', 'unit.target.requires')
        test_dep_dir.check_dep_dir('/etc/systemd', '/system/', 'config.files.d')


    def test_dep_dir_record(self):
        '''Verify record function records all entries that aren't empty and returns them. See above for parsing verification'''

        test_dep_dir = DepDir()
        wants_items = ['unit1.target', 'unit2.target']
        config_items = ['config1', 'config2']
        requires_items = ['unit3.target', 'unit4.target']

        test_dep_dir.update_wants_deps(wants_items)
        test_dep_dir.update_requires_deps(requires_items)
        test_dep_dir.update_config_files(config_items)
        dep_dir_struct: Dict[str, Union[str, List]] = test_dep_dir.record()

        self.assertIn('file_type', dep_dir_struct['metadata'])
        self.assertIn('dependency_folder_paths', dep_dir_struct['metadata'])
        self.assertIn('dependencies', dep_dir_struct['metadata'])
        self.assertIn('Wants', dep_dir_struct['metadata'])
        self.assertIn('Requires', dep_dir_struct['metadata'])
        self.assertNotIn('Config', dep_dir_struct['metadata'])

        with self.assertLogs('root', level='DEBUG') as init_logs:
            logging.getLogger('root').debug("Initial dependency directory structure created:\n{'file_type': 'dep_dir', 'dependency_folder_paths': ['/system/unit.service.wants'], 'dependencies': ['unit1.target', 'unit2.target']}")
        self.assertTrue(init_logs.output, ["DEBUG:root:Initial dependency directory structure created:\n{'file_type': 'dep_dir', 'dependency_folder_paths': ['/system/unit.service.wants'], 'dependencies': ['unit1.target', 'unit2.target']}"])



class TestUnitFiles(unittest.TestCase):

    def test_get_unit_type(self) -> None:
        '''Verify that error message pops up when invalid unit type are presented'''
        test_unit = UnitFile('/system/path/', 'unit.invalid')

        with self.assertLogs('root', level='WARNING') as logs:
            logging.getLogger('root').warning('"/system/path/unit.invalid" is an invalid or unknown unit file type, returning target type instead')
        self.assertEqual(logs.output, ['WARNING:root:"/system/path/unit.invalid" is an invalid or unknown unit file type, returning target type instead'])
        self.assertEqual(test_unit.unit_type, 'target')

        test_unit = UnitFile('/system/path/', 'unit.target')
        self.assertEqual(test_unit.unit_type, 'target')
        test_unit = UnitFile('/system/path/', 'unit.device')
        self.assertEqual(test_unit.unit_type, 'device')
        test_unit = UnitFile('/system/path/', 'unit.service')
        self.assertEqual(test_unit.unit_type, 'service')
        test_unit = UnitFile('/system/path/', 'unit.slice')
        self.assertEqual(test_unit.unit_type, 'slice')
        test_unit = UnitFile('/system/path/', 'unit.socket')
        self.assertEqual(test_unit.unit_type, 'socket')
        test_unit = UnitFile('/system/path/', 'unit.mount')
        self.assertEqual(test_unit.unit_type, 'mount')
        test_unit = UnitFile('/system/path/', 'unit.automount')
        self.assertEqual(test_unit.unit_type, 'automount')
        test_unit = UnitFile('/system/path/', 'unit.swap')
        self.assertEqual(test_unit.unit_type, 'swap')
        test_unit = UnitFile('/system/path/', 'unit.path')
        self.assertEqual(test_unit.unit_type, 'path')
        test_unit = UnitFile('/system/path/', 'unit.timer')
        self.assertEqual(test_unit.unit_type, 'timer')
        test_unit = UnitFile('/system/path/', 'unit.scope')
        self.assertEqual(test_unit.unit_type, 'scope')
        test_unit = UnitFile('/system/path/', 'unit.conf')
        self.assertEqual(test_unit.unit_type, 'conf')


    def test_check_implicit_dependencies(self) -> None:
        '''Verify implicit dependencies are being added correctly'''

        test_unit = UnitFile('/system/path', 'unit.socket')
        test_unit.unit_struct = {
            'metadata' : { 'file_type': 'unit_file' },
            'Service': 'other_unit.service'
            }
        test_unit.check_implicit_dependencies(test_unit.unit_type)

        self.assertEqual(test_unit.unit_struct, {'metadata': {'file_type': 'unit_file'}, 'Service': 'other_unit.service'})

        test_unit = UnitFile('/system/path', 'unit.socket')
        test_unit.unit_struct = {
            'metadata' : { 'file_type': 'unit_file' }
            }
        test_unit.check_implicit_dependencies(test_unit.unit_type)

        self.assertEqual(test_unit.unit_struct, {'metadata': { 'file_type': 'unit_file', 'iSocket_of': ['unit.service']}})

        test_unit = UnitFile('/system/path', 'unit.timer')
        test_unit.unit_struct = {
            'metadata' : { 'file_type': 'unit_file' },
            'Unit': 'other_unit.service'
            }
        test_unit.check_implicit_dependencies(test_unit.unit_type)

        self.assertEqual(test_unit.unit_struct, {'metadata': {'file_type': 'unit_file'}, 'Unit': 'other_unit.service'})

        test_unit = UnitFile('/system/path', 'unit.timer')
        test_unit.unit_struct = {
            'metadata' : { 'file_type': 'unit_file' }
            }
        test_unit.check_implicit_dependencies(test_unit.unit_type)

        self.assertEqual(test_unit.unit_struct, {'metadata': { 'file_type': 'unit_file', 'iTimer_for': ['unit.service']}})

        test_unit = UnitFile('/system/path', 'unit.target')
        test_unit.unit_struct = {
            'metadata' : { 'file_type': 'unit_file' }
            }
        test_unit.check_implicit_dependencies(test_unit.unit_type)

        self.assertEqual(test_unit.unit_struct, {'metadata': {'file_type': 'unit_file'}})


    def test_check_option(self) -> None:
        '''Verify option is check for validity and raise a warning if an invalid option is detected'''
        test_unit = UnitFile('/system/path', 'unit.target')

        option = test_unit.check_option('Wants')
        self.assertTrue(option == 'Wants')

        option = test_unit.check_option('Invalid')
        with self.assertLogs('root', level='WARNING') as logs:
            logging.getLogger('root').warning('"Invalid" is not a valid option for target units.  Please investigate "Invalid" option in unit.target')
        self.assertEqual(logs.output, ['WARNING:root:"Invalid" is not a valid option for target units.  Please investigate "Invalid" option in unit.target'])


    def test_format_arguments(self) -> None:
        '''Verify aruguments are parsed correctly when encountered'''

        test_unit = UnitFile('/system/path', 'unit.target')

        test_unit.arguments = test_unit.format_arguments('Wants', 'unit1.target unit2.target unit3.target')
        self.assertEqual(test_unit.arguments, ['unit1.target', 'unit2.target', 'unit3.target'])

        test_unit.arguments = test_unit.format_arguments('Requires', 'unit1.target unit2.target')
        self.assertEqual(test_unit.arguments, ['unit1.target', 'unit2.target'])

        test_unit.arguments = test_unit.format_arguments('ExecStart', '/usr/bin/bin -f options -t now')
        self.assertEqual(test_unit.arguments, ['/usr/bin/bin -f options -t now'])


    def test_update_unit_file(self) -> None:
        '''Verify unit files are found and sent to be parsed correctly.  See above for parsing verification'''

        test_unit = UnitFile('/system/', 'unit.service')
        test_unit.update_unit_file('test/', 'lib/', 'unit.service')

        self.assertEqual(test_unit.unit_struct, {
            'metadata': {'file_type': 'unit_file'},
            'Wants': ['unit1.target', 'unit2.target'],
            'ExecStart': ['/usr/bin/bin --some-args', '/usr/bin/another.bin'],
            'ExecStartPost': ['/usr/bin/bin --another-arg  --multi-line-arg']
            })


    def test_unit_file_record(self):
        '''Verify unit file is recorded and returned'''

        test_unit = UnitFile('/system/', 'unit.target')
        test_unit.unit_struct = {
            'metadata': {'file_type': 'unit_file'},
            'Wants': ['unit1.target', 'unit2.target'],
            'ExecStart': ['/usr/bin/bin --some-args']
            }

        unit_struct = test_unit.record()
        with self.assertLogs('root', level='DEBUG') as logs:
            logging.getLogger('root').debug("Final unit file structure being returned: {'metadata': {'file_type': 'unit_file'}, 'Wants': ['unit1.target', 'unit2.target'], 'ExecStart': ['/usr/bin/bin --some-args']}")

        self.assertEqual(unit_struct, {
            'metadata': {'file_type': 'unit_file'},
            'Wants': ['unit1.target', 'unit2.target'],
            'ExecStart': ['/usr/bin/bin --some-args']
            })
        self.assertEqual(logs.output, ["DEBUG:root:Final unit file structure being returned: {'metadata': {'file_type': 'unit_file'}, 'Wants': ['unit1.target', 'unit2.target'], 'ExecStart': ['/usr/bin/bin --some-args']}"])



class TestSystemdFileFactory(unittest.TestCase):

    def test_parse_dep_dir(self) -> None:
        test_unit = SystemdFileFactory(f'{getcwd()}/')
        test_unit.parse_file('test/', 'unit.target.wants')

        self.assertIsNotNone(test_unit.dep_dir)


    def test_parse_sym_link(self) -> None:
        test_unit = SystemdFileFactory(f'{getcwd()}/')
        test_struct = test_unit.parse_file('test/', 'sym_link.target')

        self.assertIsNotNone(test_unit.sym_link)

        self.assertEqual(test_unit.sym_link.target_path, 'test/')
        self.assertEqual(test_unit.sym_link.target_unit, 'unit.target')
        
        self.assertEqual(test_struct, {
            'metadata': {
                'file_type': 'sym_link',
                'sym_link_path': 'test/',
                'sym_link_unit': 'sym_link.target',
                'sym_link_target_path': 'test/',
                'sym_link_target_unit': 'unit.target',
                'dependencies': ['unit.target']
                }
            })


    def test_parse_dupe_sym_link(self) -> None:
        test_unit = SystemdFileFactory(f'{getcwd()}/')
        test_unit.parse_file('test/', 'sym_link.target')
        test_unit.parse_file('test/unit.target.wants/', 'sym_link.target')

        with self.assertLogs('root', level='WARNING') as logs:
            logging.getLogger('root').warning(f'''Systemd Mapper is trying to record multiple sym links for one unit file.
                        Investigate "dupe_link.target" to see if there is a sym link chain for sysd files or a logic flaw in the program.''')
        self.assertEqual(logs.output, ['''WARNING:root:Systemd Mapper is trying to record multiple sym links for one unit file.
                        Investigate "dupe_link.target" to see if there is a sym link chain for sysd files or a logic flaw in the program.'''])


    def test_parse_unit_file(self) -> None:
        test_unit = SystemdFileFactory(f'{getcwd()}/')
        test_unit.parse_file('test/', 'unit.target')

        self.assertIsNotNone(test_unit.unit_file)


    def test_dedupe_remote_path(self) -> None:
        test_unit = SystemdFileFactory(f'{getcwd()}/')
        test_unit.parse_file(f'{getcwd()}/test/', 'sym_link.target')

        self.assertEqual(test_unit.unit_path, 'test/')


    def test_parse_failure(self) -> None:
        test_unit = SystemdFileFactory(f'{getcwd()}/')
        test_unit.parse_file('test/', 'not_a_file')

        with self.assertLogs('root', level='WARNING') as logs:
            logging.getLogger('root').warning(f'Error determining which systemd file type "not_a_file" is')
        self.assertEqual(logs.output, ['WARNING:root:Error determining which systemd file type "not_a_file" is'])


def get_sym_link_tests() -> unittest.TestSuite:
    '''Create a test suite to test all symlink functions'''

    sym_link_test_suite = unittest.TestSuite()
    sym_link_test_suite.addTest(TestSymLinks('test_get_target_path_with_relative_path'))
    sym_link_test_suite.addTest(TestSymLinks('test_get_target_path_with_same_parent'))
    sym_link_test_suite.addTest(TestSymLinks('test_get_target_path_with_relative_dot_path'))
    sym_link_test_suite.addTest(TestSymLinks('test_get_target_path_with_abs_path'))
    sym_link_test_suite.addTest(TestSymLinks('test_sym_link_parsing_failure'))
    sym_link_test_suite.addTest(TestSymLinks('test_sym_link_record'))

    return sym_link_test_suite


def get_dep_dir_tests() -> unittest.TestSuite:
    '''Create a test suite to test all dependency directories'''

    dep_dir_test_suite = unittest.TestSuite()
    dep_dir_test_suite.addTest(TestDependencyDirectories('test_update_config_files'))
    dep_dir_test_suite.addTest(TestDependencyDirectories('test_update_wants_deps'))
    dep_dir_test_suite.addTest(TestDependencyDirectories('test_update_requires_deps'))
    dep_dir_test_suite.addTest(TestDependencyDirectories('test_update_all_deps'))
    dep_dir_test_suite.addTest(TestDependencyDirectories('test_update_dep_dir'))
    dep_dir_test_suite.addTest(TestDependencyDirectories('test_check_dep_dir'))
    dep_dir_test_suite.addTest(TestDependencyDirectories('test_dep_dir_record'))

    return dep_dir_test_suite


def get_unit_file_tests() -> unittest.TestSuite:
    '''Create a test suite to test all unit file parsing operations'''

    unit_file_test_suite = unittest.TestSuite()
    unit_file_test_suite.addTest(TestUnitFiles('test_get_unit_type'))
    unit_file_test_suite.addTest(TestUnitFiles('test_check_implicit_dependencies'))
    unit_file_test_suite.addTest(TestUnitFiles('test_check_option'))
    unit_file_test_suite.addTest(TestUnitFiles('test_format_arguments'))
    unit_file_test_suite.addTest(TestUnitFiles('test_update_unit_file'))
    unit_file_test_suite.addTest(TestUnitFiles('test_unit_file_record'))

    return unit_file_test_suite


def get_systemd_factory_tests() -> unittest.TestSuite:
    '''Create a test suite for all of the factory operation tests'''

    factory_test_suite = unittest.TestSuite()
    factory_test_suite.addTest(TestSystemdFileFactory('test_parse_dep_dir'))
    factory_test_suite.addTest(TestSystemdFileFactory('test_parse_sym_link'))
    factory_test_suite.addTest(TestSystemdFileFactory('test_parse_unit_file'))
    factory_test_suite.addTest(TestSystemdFileFactory('test_parse_dupe_sym_link'))
    factory_test_suite.addTest(TestSystemdFileFactory('test_dedupe_remote_path'))
    factory_test_suite.addTest(TestSystemdFileFactory('test_parse_failure'))
    
    return factory_test_suite


def test_suite_setup(test_directories: List[str], sym_link_map: Dict[str, str], target_file: str) -> str:
    '''Create necessary directories and symbolic links for testing'''

    status = 'SUCCESS'

    for directory in test_directories:
        try:
            mkdir(directory)
        except FileExistsError as exception:
            logging.warning(f'{exception}')
            status = 'FAIL'

    with open(target_file, 'w') as out_file:
        out_file.write('#This is a comment line and should not be recorded\n')
        out_file.write('This line should also not be recorded\n')
        out_file.write('[Unit]\n')
        out_file.write('Wants=unit1.target unit2.target\n')
        out_file.write('[Service]\n')
        out_file.write('ExecStart=/usr/bin/bin --some-args\n')
        out_file.write('ExecStart=/usr/bin/another.bin\n')
        out_file.write('ExecStartPost=/usr/bin/bin --another-arg \\\n')
        out_file.write(' --multi-line-arg')

    for target, source in sym_link_map.items():
        try:
            symlink(target, source)
        except FileExistsError as exception:
            logging.warning(f'{exception}')
            status = 'FAIL'
    
    return status


def test_suite_cleanup(test_directories: List[str], sym_link_map: Dict[str, str], target_file: str) -> bool:
    '''Remove artifacts that were created for symbolic link testing'''

    status = 'SUCCESS'

    for sym_link in sym_link_map.values():
        try:
            unlink(sym_link)
        except FileNotFoundError as exception:
            logging.warning(f'{exception}')
            status = 'FAIL'

    try:
        remove(target_file)
    except FileNotFoundError as exception:
        logging.warning(f'{exception}')
        status = 'FAIL'

    for directory in test_directories[::-1]:
        try:
            rmdir(directory)
        except OSError as exception:
            logging.warning(f'{exception}')
            status = 'FAIL'

    return status


def main() -> None:
    runner = unittest.TextTestRunner()

    sym_link_test_dirs = [ 'test', 'test/target_dir', 'test/relative_sym_link_dir', 'test/abs_sym_link_dir' ]
    sym_link_map = {
        'target_dir/sym_link_target.target': 'test/relative_sym_link.target',
        'sym_link_target.target': 'test/target_dir/same_parent_sym_link.target',
        '../target_dir/sym_link_target.target': 'test/relative_sym_link_dir/relative_dot_sym_link.target',
        f'{getcwd()}/test/target_dir/sym_link_target.target': 'test/abs_sym_link_dir/abs_sym_link.target'
        }
    sym_link_tgt_file = 'test/target_dir/sym_link_target.target'

    unit_file_test_dirs = [ 'test', 'test/lib' ]
    unit_file_sym_link_map = {}
    unit_file_tgt_file = 'test/lib/unit.service'

    factory_dirs = [ 'test', 'test/unit.target.wants', 'test/target_dir' ]
    factory_sym_link_map = {
        'unit.target': 'test/sym_link.target',
        '../unit.target': 'test/unit.target.wants/sym_link.target'
        }
    factory_tgt_file = 'test/unit.target'

    print('\nSetting up sym link artifacts')
    status = test_suite_setup(sym_link_test_dirs, sym_link_map, sym_link_tgt_file)
    print(f'Sym link artifact creation: {status}')
    print('\nTesting sym link parsing and recording functions...')
    runner.run(get_sym_link_tests())
    print('Cleaning up sym link artifacts')
    status = test_suite_cleanup(sym_link_test_dirs, sym_link_map, sym_link_tgt_file)
    print(f'Sym link artifact cleanup: {status}')

    print('\nTesting dependency directory parsing and recording functions...')
    runner.run(get_dep_dir_tests())
    print('No artifacts to clean up')

    print('\nSetting up unit file artifacts')
    status = test_suite_setup(unit_file_test_dirs, unit_file_sym_link_map, unit_file_tgt_file)
    print(f'Unit file artifact creation: {status}')
    print('\nTesting unit file parsing and recording functions...')
    runner.run(get_unit_file_tests())
    print('Cleaning up unit file artifacts')
    status = test_suite_cleanup(unit_file_test_dirs, unit_file_sym_link_map, unit_file_tgt_file)
    print(f'Unit file artifact cleanup: {status}')

    print('\nSetting up factory artifacts')
    status = test_suite_setup(factory_dirs, factory_sym_link_map, factory_tgt_file)
    print(f'Factory artifact creation: {status}')
    print('\nTesting unit file factory functionality...')
    runner.run(get_systemd_factory_tests())
    print('Cleaning up factory artifacts')
    status = test_suite_cleanup(factory_dirs, factory_sym_link_map, factory_tgt_file)
    print(f'Factory artifact cleanup: {status}')

if __name__ == '__main__':
    main()