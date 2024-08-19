'''
dep_obj_parser_tests.py
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

Description: This is a test file that is used to test lib/dep_obj_parser.py. 
    All tests were placed into one test suite to make future testing easier if 
    more or different functionality is added later.
'''

import unittest
import logging

from typing import List

from lib.dep_obj_parser import DepMapUnit



class TestDepMapUnits(unittest.TestCase):

    def test_DepMapUnit_creation(self) -> None:
        '''Verify DepMapUnit objects are built correctly'''

        dep_unit = DepMapUnit('test_unit.wants', 'None', 'None')

        self.assertTrue(hasattr(dep_unit, 'sym_linked_to'))
        self.assertTrue(hasattr(dep_unit, 'sym_linked_from'))
        self.assertTrue(hasattr(dep_unit, 'wants'))
        self.assertTrue(hasattr(dep_unit, 'wanted_by'))
        self.assertTrue(hasattr(dep_unit, 'requires'))
        self.assertTrue(hasattr(dep_unit, 'required_by'))
        self.assertTrue(hasattr(dep_unit, 'requisite'))
        self.assertTrue(hasattr(dep_unit, 'requisite_of'))
        self.assertTrue(hasattr(dep_unit, 'bindsto'))
        self.assertTrue(hasattr(dep_unit, 'bound_by'))
        self.assertTrue(hasattr(dep_unit, 'partof'))
        self.assertTrue(hasattr(dep_unit, 'has_part'))
        self.assertTrue(hasattr(dep_unit, 'upholds'))
        self.assertTrue(hasattr(dep_unit, 'upheld_by'))
        self.assertTrue(hasattr(dep_unit, 'onsuccess'))
        self.assertTrue(hasattr(dep_unit, 'on_success_of'))
        self.assertTrue(hasattr(dep_unit, 'sockets'))
        self.assertTrue(hasattr(dep_unit, 'socket_of'))
        self.assertTrue(hasattr(dep_unit, 'service'))
        self.assertTrue(hasattr(dep_unit, 'uses_service'))
        self.assertTrue(hasattr(dep_unit, 'parents'))
        self.assertTrue(hasattr(dep_unit, 'reverse_deps'))
        self.assertTrue(hasattr(dep_unit, 'dependencies'))
        

    def test_update_ms_dep_dir(self) -> None:
        '''Verify the actual parsing for master struct dependency directories is correct'''

        test_ms_unit_struct = {
            'metadata': {
                'unit_file':    'test_unit.wants',
                'Wants':        ['wants1.target', 'wants2.target'],
                'Requires':     ['requires1.target', 'requires2.target'],
                'd':            ['config1.cfg', 'config2.cfg'],
                'file_type':    'dep_dir'
            }
        }

        dep_unit = DepMapUnit('test_unit.wants', 'None', 'None')
        dep_unit.update_ms_dep_dir(test_ms_unit_struct)

        self.assertIn('wants1.target', dep_unit.wants)
        self.assertIn('wants2.target', dep_unit.wants)
        self.assertIn('requires1.target', dep_unit.requires)
        self.assertIn('requires2.target', dep_unit.requires)
        self.assertIn('wants1.target', dep_unit.dependencies)
        self.assertIn('wants2.target', dep_unit.dependencies)
        self.assertIn('requires1.target', dep_unit.dependencies)
        self.assertIn('requires2.target', dep_unit.dependencies)

        self.assertFalse(hasattr(dep_unit, 'unit_file'))
        self.assertFalse(hasattr(dep_unit, 'd'))
        self.assertFalse(hasattr(dep_unit, 'file_type'))

        self.assertNotIn('requires1.target', dep_unit.wants)
        self.assertNotIn('config1.cfg', dep_unit.wants)
        self.assertNotIn('test_unit.wants', dep_unit.wants)
        self.assertNotIn('dep_dir', dep_unit.wants)
        self.assertNotIn('wants1.target', dep_unit.requires)
        self.assertNotIn('config1.cfg', dep_unit.requires)
        self.assertNotIn('test_unit.wants', dep_unit.requires)
        self.assertNotIn('dep_dir', dep_unit.requires)


    def test_update_ms_sym_link(self) -> None:
        '''Verify the actual parsing for master struct symbolic links is correct'''

        test_sym_link_struct = {
            "metadata": {
                "unit_file": "sym_link.target",
                "file_type": "sym_link",
                "sym_link_path": "/etc/systemd/system/",
                "sym_link_unit": "sym_link.target",
                "sym_link_target_path": "/lib/systemd/system/",
                "sym_link_target_unit": "target.target",
                "dependencies": [ "target.target" ]
            }
        }

        test_ms_sym_link_unit = DepMapUnit('sym_link.target', 'None', 'None')
        test_ms_sym_link_unit.update_ms_sym_link(test_sym_link_struct)

        self.assertTrue(test_ms_sym_link_unit.sym_linked_to == {'/lib/systemd/system/target.target'})
        self.assertTrue(test_ms_sym_link_unit.dependencies == {'target.target'})


    def test_update_ms_unit_file(self) -> None:
        '''Verify the actual parsing for master struct unit files is correct'''

        test_ms_unit_file_struct = {
            "metadata": { "file_type": "unit_file" },
            "Description": [ "Some random unit file" ],
            "PartOf": [ "enabled.target", "lxdm.target" ],
            "Wants": [ "graphical.target" ],
            "Before": [ "enabled.target" ],
            "OnFailure": [ "failure.service" ],
            "OnSuccess": [ "success.service" ],
            "Requisite": [ "default.target" ],
            "Requires": [ "multi-user.target" ],
            "LimitCORE": [ "infinity" ],
            "BindsTo": [ "multi-user.target", "graphical.target" ],
            "LimitNOFILE": [ "infinity " ],
            "RuntimeDirectory": [ "dir" ],
            "RuntimeDirectoryPreserve": [ "yes" ],
            "ExecStartPre": [ "rm -f /var/lib/bin/*.frc", "rm -f /var/lib/bin_failover/*.frc" ],
            "ExecStart": [ "/usr/bin/bin /run/bin/bin.cfg" ],
            "ExecStopPost": [ "/usr/bin/watchdogtickle -a" ],
            "Upholds": [ "default.target" ],
            "Sockets": [ "socket.socket" ],
            "Service": [ "service.service" ],
            "WantedBy": [ "enabled.target" ]
        }

        test_ms_unit_file = DepMapUnit('unit.target', 'None', 'None')
        test_ms_unit_file.update_ms_unit_file(test_ms_unit_file_struct)

        self.assertIn('enabled.target', test_ms_unit_file.partof)
        self.assertIn('lxdm.target', test_ms_unit_file.partof)
        self.assertIn('multi-user.target', test_ms_unit_file.bindsto)
        self.assertIn('graphical.target', test_ms_unit_file.bindsto)

        self.assertTrue(test_ms_unit_file.requires == {'multi-user.target'})
        self.assertTrue(test_ms_unit_file.wants == {'graphical.target'})
        self.assertTrue(test_ms_unit_file.requisite == {'default.target'})
        self.assertTrue(test_ms_unit_file.upholds == {'default.target'})
        self.assertTrue(test_ms_unit_file.onsuccess == {'success.service'})
        self.assertTrue(test_ms_unit_file.sockets == {'socket.socket'})
        self.assertTrue(test_ms_unit_file.service == {'service.service'})

        self.assertNotIn('enabled.target', test_ms_unit_file.wanted_by)


    def test_set_rev_dep(self) -> None:
        '''Verify reverse dependency attributes are being mapped correctly'''

        test_unit = DepMapUnit('multi-user.target', 'default.target', 'wanted_by')
        test_unit.set_rev_dep()

        # Overwrite original instance to verify values append and not overwrite if
        # the unit is called more than once
        test_unit.rev_dep = 'required_by'
        test_unit.parent_unit = 'multi-user.target'
        test_unit.set_rev_dep()

        test_unit.rev_dep = 'sym_linked_from'
        test_unit.parent_unit_path = '/etc/systemd/system/graphical.target'
        test_unit.parent_unit = 'graphical.target'
        test_unit.set_rev_dep()

        test_unit.rev_dep = 'invalid'
        test_unit.parent_unit = 'invalid.target'
        test_unit.set_rev_dep()

        with self.assertLogs('root', level='WARNING') as logs:
            logging.getLogger('root').warning('Invalid reverse dependency: invalid.  This does not map to any attribute sets')

        self.assertIn('default.target', test_unit.parents)
        self.assertIn('multi-user.target', test_unit.parents)
        self.assertIn('graphical.target', test_unit.parents)
        self.assertIn('default.target', test_unit.wanted_by)
        self.assertIn('multi-user.target', test_unit.required_by)
        self.assertIn('/etc/systemd/system/graphical.target', test_unit.sym_linked_from)
        self.assertIn('wanted_by', test_unit.reverse_deps)
        self.assertIn('required_by', test_unit.reverse_deps)
        self.assertIn('sym_linked_from', test_unit.reverse_deps)
        
        self.assertEqual(logs.output, ['WARNING:root:Invalid reverse dependency: invalid.  This does not map to any attribute sets'])

        self.assertNotIn('/etc/systemd/system/multi-user.target', test_unit.parents)


    def test_load_from_ms(self) -> None:
        '''Verify master struct entries are identified correctly.  See above for parsing verification'''

        test_config_dir_entry = {
            "metadata": { "file_type": "dep_dir" }
        }
        test_wants_dir_entry = {
            "metadata": {
                "file_type": "dep_dir",
                "dependency_folder_paths": [ "/etc/systemd/system/timers.target.wants" ],
                "Wants": [ "logrotate.timer", "hwclock-sync.timer" ]
            }
        }
        test_requires_dir_entry = {
            "metadata": {
                "file_type": "dep_dir",
                "dependency_folder_paths": [ "/etc/systemd/system/random.service.requires" ],
                "Requires": [ "another.service" ]
            }
        }
        test_sym_link_entry = {
            "metadata": {
                "file_type": "sym_link",
                "sym_link_target_path": "/lib/systemd/system/",
                "sym_link_target_unit": "rsyslog.service",
                "dependencies": [ "rsyslog.service" ]
            }
        }
        test_unit_file_entry = {
            "metadata": { "file_type": "unit_file" },
            "Requires": [ "syslog.socket" ]
        }
        test_invalid_file_entry = {
            "metadata": { "file_type": "invalid" }
        }

        test_unit = DepMapUnit('default.target', 'None', 'None')
        test_unit.load_from_ms(test_config_dir_entry)

        test_unit.load_from_ms(test_wants_dir_entry)
        self.assertIn('logrotate.timer', test_unit.wants)
        self.assertIn('hwclock-sync.timer', test_unit.wants)

        test_unit.load_from_ms(test_requires_dir_entry)
        self.assertTrue(test_unit.requires == {'another.service'})

        test_unit.load_from_ms(test_sym_link_entry)
        self.assertTrue(test_unit.sym_linked_to == {'/lib/systemd/system/rsyslog.service'})

        test_unit.load_from_ms(test_unit_file_entry)
        self.assertIn('syslog.socket', test_unit.requires)

        test_unit.load_from_ms(test_invalid_file_entry)
        with self.assertLogs('root', level='WARNING') as logs:
            logging.getLogger('root').warning('Not sure how to parse file type: invalid from default.target')
        self.assertEqual(logs.output, ['WARNING:root:Not sure how to parse file type: invalid from default.target'])


    def test_load_from_dep_map(self) -> None:
        '''Verifying correct loading of previously recorded dependency map entries.  See above for parsing verification'''

        test_old_dep_map_entry = {
            "unit_name": "multi-user.target",
            "parents": [ "enabled.target" ],
            "reverse_deps": [ "required_by" ],
            "Wants": [ "gfarmond.service", "rngd.service", "dnsmasq.service" ],
            "Requires": [ "basic.target" ],
            "required_by": [ "graphical.target" ],
            "dependencies": [ "gfarmond.service", "rngd.service", "dnsmasq.service", "basic.target" ]
        }

        test_unit = DepMapUnit('multi-user.target', 'default.target', 'required_by')
        test_unit.load_from_dep_map(test_old_dep_map_entry)
        with self.assertLogs('root', level='WARNING') as logs:
            logging.getLogger('root').warning('Could not load "{dep}" attribute from unit already in dep map.  If this is not "unit_file" investigate')

        self.assertTrue(test_unit.rev_dep == 'required_by')
        self.assertTrue(test_unit.reverse_deps == {'required_by'})
        self.assertTrue(test_unit.requires == {'basic.target'})

        self.assertIn('default.target', test_unit.required_by)
        self.assertIn('graphical.target', test_unit.required_by)
        self.assertIn('enabled.target', test_unit.parents)
        self.assertIn('default.target', test_unit.parents)
        self.assertIn('gfarmond.service', test_unit.wants)
        self.assertIn('rngd.service', test_unit.wants)
        self.assertIn('dnsmasq.service', test_unit.wants)
        self.assertIn('gfarmond.service', test_unit.dependencies)
        self.assertIn('rngd.service', test_unit.dependencies)
        self.assertIn('dnsmasq.service', test_unit.dependencies)
        self.assertIn('basic.target', test_unit.dependencies)

        self.assertEqual(logs.output, ['WARNING:root:Could not load "{dep}" attribute from unit already in dep map.  If this is not "unit_file" investigate'])


    def test_create_dep_tups(self) -> None:
        '''Verify correct creation of dependency tuples.  See above for parsing verification'''

        test_unit = DepMapUnit('test.target', 'None', 'None')
        test_unit.sym_linked_to = {'/path/to/sym_link.target'}

        test_dep_tups_list = test_unit.create_dep_tups('/path/to/test.target')
        self.assertIn(('sym_link.target', '/path/to/test.target', 'sym_linked_from'), test_dep_tups_list)
               
        test_unit.sym_linked_from = {'/path/to/parent/sym_link'}
        test_unit.wants = {'wants.target'}
        test_unit.wanted_by = {'wanted_by.target'}
        test_unit.requires = {'requires.target'}
        test_unit.requisite = {'requisite.target'}
        test_unit.bindsto = {'bindsto.target'}
        test_unit.partof = {'partof.target'}
        test_unit.upholds = {'upholds.target'}
        test_unit.onsuccess = {'onsuccess.target'}
        test_unit.sockets = {'sockets.socket'}
        test_unit.service = {'service.service'}
        test_unit.itimer_for = {'timer.service'}
        test_unit.isocket_of = {'socket.service'}
        test_unit.ipath_for = {'path.service'}

        test_dep_tups_list = test_unit.create_dep_tups('test.target')

        self.assertIn(('wants.target', 'test.target', 'wanted_by'), test_dep_tups_list)
        self.assertIn(('requires.target', 'test.target', 'required_by'), test_dep_tups_list)
        self.assertIn(('requisite.target', 'test.target', 'requisite_of'), test_dep_tups_list)
        self.assertIn(('bindsto.target', 'test.target', 'bound_by'), test_dep_tups_list)
        self.assertIn(('partof.target', 'test.target', 'has_part'), test_dep_tups_list)
        self.assertIn(('upholds.target', 'test.target', 'upheld_by'), test_dep_tups_list)
        self.assertIn(('onsuccess.target', 'test.target', 'on_success_of'), test_dep_tups_list)
        self.assertIn(('sockets.socket', 'test.target', 'socket_of'), test_dep_tups_list)
        self.assertIn(('service.service', 'test.target', 'uses_service'), test_dep_tups_list)
        self.assertIn(('timer.service', 'test.target', 'has_timer'), test_dep_tups_list)
        self.assertIn(('socket.service', 'test.target', 'has_socket'), test_dep_tups_list)
        self.assertIn(('path.service', 'test.target', 'needs_path'), test_dep_tups_list)


    def test_get_significant_attributes(self) -> None:
        '''Verify only interesting attributes are returned'''

        test_unit = DepMapUnit('default.target', '/path/to/default.target', 'required_by')
        significant_attributes = test_unit.get_significant_attributes()

        self.assertIn('unit_name', significant_attributes)
        self.assertIn('parents', significant_attributes)
        self.assertIn('reverse_deps', significant_attributes)

        self.assertNotIn('parent_unit_path', significant_attributes)

        test_unit.wants = {'unit1.target', 'unit2.target', 'unit3.target'}
        test_unit.requires = {'unit4.target', 'unit5.target'}
        test_unit.required_by = {'unit6.target'}
        significant_attributes: List = test_unit.get_significant_attributes()

        self.assertIn('wants', significant_attributes)
        self.assertIn('requires', significant_attributes)
        self.assertIn('required_by', significant_attributes)


    def test_dep_map_unit_record(self) -> None:
        '''Verify record function transforms sets to lists and returns a dictionary of values'''

        test_unit = DepMapUnit('multi-user.target', '/path/to/default.target', 'required_by')

        test_unit.requires = {'unit1.target', 'unit2.target', 'unit3.target'}
        test_unit.sockets = {'unit4.target', 'unit5.target'}
        test_unit.uses_service = {'unit6.target'}
        test_unit.service = {'unit7.target'}
        test_unit.wanted_by = {'unit8.target'}

        out_struct = test_unit.record()

        self.assertTrue(isinstance(out_struct, dict))

        self.assertIn('unit_name', out_struct)
        self.assertIn('parents', out_struct)
        self.assertIn('reverse_deps', out_struct)
        self.assertIn('requires', out_struct)
        self.assertIn('sockets', out_struct)
        self.assertIn('uses_service', out_struct)
        self.assertIn('service', out_struct)
        self.assertIn('wanted_by', out_struct)

        self.assertTrue(isinstance(out_struct['requires'], list))
        self.assertTrue(isinstance(out_struct['sockets'], list))
        self.assertTrue(isinstance(out_struct['uses_service'], list))
        self.assertTrue(isinstance(out_struct['service'], list))
        self.assertTrue(isinstance(out_struct['wanted_by'], list))


def get_dep_map_unit_tests() -> unittest.TestSuite:
    '''Create a test suite to test all dep map unit functions'''

    dep_map_test_suite = unittest.TestSuite()
    dep_map_test_suite.addTest(TestDepMapUnits('test_DepMapUnit_creation'))
    dep_map_test_suite.addTest(TestDepMapUnits('test_update_ms_dep_dir'))
    dep_map_test_suite.addTest(TestDepMapUnits('test_update_ms_sym_link'))
    dep_map_test_suite.addTest(TestDepMapUnits('test_update_ms_unit_file'))
    dep_map_test_suite.addTest(TestDepMapUnits('test_set_rev_dep'))
    dep_map_test_suite.addTest(TestDepMapUnits('test_load_from_ms'))
    dep_map_test_suite.addTest(TestDepMapUnits('test_load_from_dep_map'))
    dep_map_test_suite.addTest(TestDepMapUnits('test_create_dep_tups'))
    dep_map_test_suite.addTest(TestDepMapUnits('test_get_significant_attributes'))
    dep_map_test_suite.addTest(TestDepMapUnits('test_dep_map_unit_record'))

    return dep_map_test_suite


def main() -> None:
    runner = unittest.TextTestRunner()

    print('\nTesting dependency mapping functions...')
    runner.run(get_dep_map_unit_tests())
    print('No artifacts to clean up')

if __name__ == '__main__':
    main()