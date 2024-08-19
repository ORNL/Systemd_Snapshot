'''
unit_file_lists.py
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

Description:  This file holds all of the file lists that are used by the tool. This is where the tool
    goes to find which options are available to which unit files, as well as which sections are available
    to which unit types. For more information, check the doc strings of a specific list below.
'''

sys_unit_paths = [
    '/etc/systemd/system.control/',
    '/run/systemd/system.control/',
    '/run/systemd/transient/',
    '/run/systemd/generator.early/',
    '/etc/systemd/system/',
    '/etc/systemd/system.attached/',
    '/run/systemd/system/',
    '/run/systemd/system.attached/',
    '/run/systemd/generator/',
    '/lib/systemd/system/',
    '/usr/local/lib/systemd/system',
    '/usr/lib/systemd/system/',
    '/run/systemd/generator.late/'
]
'''List of all of the system paths systemd will check for unit files'''

usr_unit_paths = [
    '~/.config/systemd/user.control/',
    '$XDG_RUNTIME_DIR/systemd/user.control/',
    '$XDG_RUNTIME_DIR/systemd/transient/',
    '$XDG_RUNTIME_DIR/systemd/generator.early/',
    '~/.config/systemd/user/',
    '$XDG_CONFIG_DIRS/systemd/user/',
    '/etc/systemd/user/',
    '$XDG_RUNTIME_DIR/systemd/user/',
    '/run/systemd/user/',
    '$XDG_RUNTIME_DIR/systemd/generator/',
    '$XDG_DATA_HOME/systemd/user/',
    '$XDG_DATA_DIRS/systemd/user/',
    '/usr/lib/systemd/user/',
    '$XDG_RUNTIME_DIR/systemd/generator.late/'
]
'''List of all the user paths systemd will check for unit files'''

unit_generic_opts = [
    'Description',
    'Documentation',
    'Before',
    'After',
    'Wants',
    'Conflicts',
    'Requires',
    'Requisite',
    'BindsTo',
    'PartOf',
    'Upholds',
    'OnSuccess',
    'OnFailure',
    'PropagatesReloadTo',
    'ReloadPropagatedFrom',
    'PropagatesStopTo',
    'StopPropagatedFrom',
    'JoinsNamespaceOf',
    'RequiresMountsFor',
    'OnFailureJobMode',
    'IgnoreOnIsolate',
    'StopWhenUnneeded',
    'RefuseManualStart',
    'RefuseManualStop',
    'AllowIsolate',
    'DefaultDependencies',
    'CollectMode',
    'FailureAction',
    'FailureActionExitStatus',
    'SuccessAction',
    'SuccessActionExitStatus',
    'JobTimeoutSec',
    'JobRunningTimeoutSec',
    'JobTimeoutAction',
    'JobTimeoutRebootArgument',
    'StartLimitIntervalSec',
    'StartLimitInterval',
    'StartLimitBurst',
    'StartLimitAction',
    'RebootArgument',
    'SourcePath'
]
'''This is a full listing of generic unit options. 
This is used to parse the unit file [Unit] section.'''

unit_cond_assert_opts = [
    'ConditionArchitecture',
    'ConditionFirmware',
    'ConditionVirtualization',
    'ConditionHost',
    'ConditionKernelCommandLine',
    'ConditionKernelVersion',
    'ConditionCredential',
    'ConditionEnvironment',
    'ConditionSecurity',
    'ConditionCapability',
    'ConditionACPower',
    'ConditionNeedsUpdate',
    'ConditionFirstBoot',
    'ConditionPathExists',
    'ConditionPathExistsGlob',
    'ConditionPathIsDirectory',
    'ConditionPathIsSymbolicLink',
    'ConditionPathIsMountPoint',
    'ConditionPathIsReadWrite',
    'ConditionPathIsEncrypted',
    'ConditionDirectoryNotEmpty',
    'ConditionFileNotEmpty',
    'ConditionFileIsExecutable',
    'ConditionUser',
    'ConditionGroup',
    'ConditionControlGroupController',
    'ConditionMemory',
    'ConditionCPUs',
    'ConditionCPUFeature',
    'ConditionOSRelease',
    'ConditionMemoryPressure',
    'ConditionCPUPressure',
    'ConditionIOPressure',
    'AssertArchitecture',
    'AssertVirtualization',
    'AssertHost',
    'AssertKernelCommandLine',
    'AssertKernelVersion',
    'AssertCredential',
    'AssertEnvironment',
    'AssertSecurity',
    'AssertCapability',
    'AssertACPower',
    'AssertNeedsUpdate',
    'AssertFirstBoot',
    'AssertPathExists',
    'AssertPathExistsGlob',
    'AssertPathIsDirectory',
    'AssertPathIsSymbolicLink',
    'AssertPathIsMountPoint',
    'AssertPathIsReadWrite',
    'AssertPathIsEncrypted',
    'AssertDirectoryNotEmpty',
    'AssertFileNotEmpty',
    'AssertFileIsExecutable',
    'AssertUser',
    'AssertGroup',
    'AssertControlGroupController',
    'AssertMemory',
    'AssertCPUs',
    'AssertCPUFeature',
    'AssertOSRelease',
    'AssertMemoryPressure',
    'AssertCPUPressure',
    'AssertIOPressure'
]
'''This is a full list of generic unit file conditions/assertions.
This is also used to parse the unit file [Unit] section, but these 
are grouped separately due to usage similiarty and number of items.'''

unit_install_opts = [
    'Alias',
    'WantedBy',
    'RequiredBy',
    'Also',
    'DefaultInstance'
]
'''This is a list of all generic unit file install options. 
This is used to parse the unit file [Install] section.'''

serv_unit_opts = [
    'Type',
    'ExitType',
    'RemainAfterExit',
    'GuessMainPID',
    'PIDFile',
    'BusName',
    'ExecStart',
    'ExecStartPre',
    'ExecStartPost',
    'ExecCondition',
    'ExecReload',
    'ExecStop',
    'ExecStopPost',
    'RestartSec',
    'TimeoutStartSec',
    'TimeoutStopSec',
    'TimeoutAbortSec',
    'TimeoutSec',
    'TimeoutStartFailureMode',
    'TimeoutStopFailureMode',
    'RuntimeMaxSec',
    'RuntimeRandomizedExtraSec',
    'WatchdogSec',
    'Restart',
    'SuccessExitStatus',
    'RestartPreventExitStatus',
    'RestartForceExitStatus',
    'PermissionsStartOnly',
    'RootDirectoryStartOnly',
    'NonBlocking',
    'NotifyAccess',
    'Sockets',
    'FileDescriptorStoreMax',
    'USBFunctionDescriptors',
    'USBFunctionStrings',
    'OOMPolicy',
    'OpenFile',
    'ReloadSignal'
]
'''
    This is a list of options that are unit.service specific.  This will be used to parse the unit files.
    Service unit files may include [Unit] and [Install] sections, and must include a [Service] section.

    Implicit dependencies:
        - Type=Dbus automatically sets Requires= and After= on dbus.socket
        - If service is activated by file.socket, service will automatically set After=file.socket
        - Also subject to implicit rules from .exec and .resource-control units

    Default dependencies:
        - Requires= and After=sysinit.target
        - After=basic.target
        - Before= and Conflicts=shutdown.target
'''

'''
    Target units exist only to group units via dependencies.  As such, no unit.target file specific options are supported.
    Target unit files may include [Unit] and [Install] sections.  See systemd.target man page for more info.

    Implicit dependencies:
        - None

    Default dependencies:
        - Adds After= to all unit files that this unit Wants= and Requires=
        - Before= and Conflicts=shutdown.target
'''

'''
    Device units have no file specific options.  They may use the generic [Unit] and [Install] sections and
    options, but there is no [Device] section.  Device units are named after the sys and dev paths they control.
    See systemd.device man page for more info.

    Implicit dependencies:
        - None on device files, but some other files may have deps on this file

    Default dependencies:
        - None
'''

'''
    Slice units are like central repos to control system resource usage.  No unit.slice file specific options are supported,
    but slice unit files may include [Unit] and [Install] sections, and may have a [Slice] section that enables the
    use of resource-control unit options.  See systemd.slice man page for more info.

    Implicit dependencies:
        - After= and Requires=parent.unit

    Default dependencies:
        - Before= and Conflicts=shutdown.target
'''

sock_unit_opts = [
    'ListenStream',
    'ListenDatagram',
    'ListenSequentialPacket',
    'ListenFIFO',
    'ListenSpecial',
    'ListenNetlink',
    'ListenMessageQueue',
    'ListenUSBFunction',
    'SocketProtocol',
    'BindIPv6Only',
    'Backlog',
    'BindToDevice',
    'SocketUser',
    'SocketGroup',
    'SocketMode',
    'DirectoryMode',
    'Accept',
    'Writable',
    'FlushPending',
    'MaxConnections',
    'MaxConnectionsPerSource',
    'KeepAlive',
    'KeepAliveTimeSec',
    'KeepAliveIntervalSec',
    'KeepAliveProbes',
    'NoDelay',
    'Priority',
    'DeferAcceptSec',
    'ReceiveBuffer',
    'SendBuffer',
    'IPTOS',
    'IPTTL',
    'Mark',
    'ReusePort',
    'SmackLabel',
    'SmackLabelIPIn',
    'SmackLabelIPOut',
    'SELinuxContextFromNet',
    'PipeSize',
    'MessageQueueMaxMessages',
    'MessageQueueMessageSize',
    'FreeBind',
    'Transparent',
    'Broadcast',
    'PassCredentials',
    'PassSecurity',
    'PassPacketInfo',
    'Timestamping',
    'TCPCongestion',
    'ExecStartPre',
    'ExecStartPost',
    'ExecStopPre',
    'ExecStopPost',
    'TimeoutSec',
    'Service',
    'RemoveOnStop',
    'Symlinks',
    'FileDescriptorName',
    'TriggerLimitIntervalSec',
    'TriggerLimitBurst'
]
'''
    This is a list of options that are unit.socket specific.  This will be used to parse the unit files.
    Socket unit files may include [Unit] and [Install] sections, and may include a [Socket] section that
    enables the use of exec, kill, and resource-control unit options as well as the listed socket specific options.

    Implicit dependencies:
        - .socket unit files automatically start their matching .service unit unless Service= is set
        - Before=matching.service
        - Requires= and After= on all mount units necessary to access system paths that are referred to.
        - Socket units using BindToDevice= will gain a BindsTo= and After= dependency on the device unit specified.
        
    Default dependencies:
        - Before=sockets.target
        - Requires= and After=sysinit.target
        - Before= and Conflicts=shutdown.target
'''

mnt_unit_opts = [
    'What',
    'Where',
    'Type',
    'Options',
    'SloppyOptions',
    'LazyUnmount',
    'ReadWriteOnly',
    'ForceUnmount',
    'DirectoryMode',
    'TimeoutSec'
]
'''
    This is a list of options that are unit.mount specific.  This will be used to parse the unit files.
    Mount unit files may include [Unit] and [Install] sections, and must include a [Mount] section that
    enables the use of exec, kill, and resource-control unit options as well as the listed mount specific options.
    Systemd will turn each entry in the fstab into a .mount unit dynamically at runtime.

    Implicit dependencies:
        - Requires=parent.mount and Before/After=parent/child.mount
        - Block device units gain BindsTo= and After= on fs unit files
        - Before= and Wants=systemd-quotacheck.service and quotaon.service if fs quota is enabled
        
    Default dependencies:
        - Before= and Conflicts=umount.target
        - After=local-fs-pre.target
        - Before=local-fs.target
        - After=remote-fs-pre.target, network.target and network-online.target if mount is a network mount
        - Before=remote-fs.target if mount is a network mount
'''

automnt_unit_opts = [
    'Where',
    'ExtraOptions',
    'DirectoryMode',
    'TimeoutIdleSec'
]
'''
    This is a list of options that are unit.automount specific.  This will be used to parse the unit files.
    Automount unit files may include [Unit], [Install], and [Automount] sections, and must be named after
    the automount directories they control, as well as a matching mount unit file.

    Implicit dependencies:
        - Before=unit.mount that will be activated
        
    Default dependencies:
        - Before= and Conflicts=umount.target
        - Before=local-fs.target
        - After=local-fs-pre.target
'''

swap_unit_opts = [
    'What',
    'Priority',
    'Options',
    'TimeoutSec'
]
'''
    This is a list of options that are unit.swap specific. This will be used to parse the unit files.
    Swap unit files may include [Unit] and [Install] sections, and may include a [Swap] section that
    enables the use of exec, kill, and resource-control unit options as well as the listed swap specific options.

    Implicit dependencies:
        - After= and BindsTo=unit_that_activates_this_unit
        
    Default dependencies:
        - Before= and Conflicts=umount.target
        - Before=swap.target
'''

path_unit_opts = [
    'PathExists',
    'PathExistsGlob',
    'PathChanged',
    'PathModified',
    'DirectoryNotEmpty',
    'Unit',
    'MakeDirectory',
    'DirectoryMode',
    'TriggerLimitIntervalSec',
    'TriggerLimitBurst'
]
'''
    This is a list of options that are unit.path specific.  This will be used to parse the unit files.
    Path unit files may include [Unit] and [Install] sections, and must include a [Path] section, which
    enables the use of the listed path specific options.

    Implicit dependencies:
        - ordering dependency created on mount paths above this unit
        - Before=unit_to_activate
        
    Default dependencies:
        - Before=paths.target
        - After= and Requires=sysinit.target
        - Before= and Conflicts=shutdown.target
'''

timer_unit_opts = [
    'OnActiveSec',
    'OnBootSec',
    'OnStartupSec',
    'OnUnitActiveSec',
    'OnUnitInactiveSec',
    'OnCalendar',
    'AccuracySec',
    'RandomizedDelaySec',
    'FixedRandomDelay',
    'OnClockChange',
    'OnTimezoneChange',
    'Unit',
    'Persistent',
    'WakeSystem',
    'RemainAfterElapse'
]
'''
    This is a list of options that are unit.timer specific.  This will be used to parse the unit files.
    Timer unit files may include [Unit] and [Install] sections, and must include a [Timer] section, which
    enables the use of the listed timer specific options.
    Services with the same name as timer units will be automatically activated when the matching
    unit.timer file is activated.

    Implicit dependencies:
        - Before=matching_unit.service
        
    Default dependencies:
        - After= and Requies=sysinit.target
        - Before=timers.target
        - Before= and Conflicts=shutdown.target
        - After=time-set.target time-sync.target IF OnCalendar= is used
'''

scope_unit_opts = [
    'OOMPolicy',
    'RuntimeMaxSec',
    'RuntimeRandomizedExtraSec'
]
'''
    This is a list of options that are unit.scope specific.  This will be used to parse the unit files.
    Scope units manage a set of externally created system processes, and unlike service units, they can't fork.
    Scope unit files may include a [Unit] section, as well as a [Scope] section that enables the use of exec,
    kill, and resource-control options, as well as the listed scope specific options.

    Implicit dependencies:
        - None
    
    Default dependencies:
        - Before= and Conflicts=shutdown.target
'''

kill_unit_opts = [
    'KillMode',
    'KillSignal',
    'RestartKillSignal',
    'SendSIGHUP',
    'SendSIGKILL',
    'FinalKillSignal',
    'WatchdogSignal'
]
'''This is a list of options that are labelled as systemd.kill options, and are 
made available to multiple types of units.  See systemd.kill man page for more info.'''

res_con_unit_opts = [
    'CPUAccounting',
    'CPUWeight',
    'StartupCPUWeight',
    'CPUQuota',
    'CPUQuotaPeriodSec',
    'AllowedCPUs',
    'StartupAllowedCPUs',
    'AllowedMemoryNodes',
    'StartupAllowedMemoryNodes',
    'MemoryAccounting',
    'MemoryMin',
    'MemoryLow',
    'MemoryHigh',
    'MemoryMax',
    'MemorySwapMax',
    'MemoryZSwapMax',
    'TasksAccounting',
    'TasksMax',
    'IOAccounting',
    'IOWeight',
    'StartupIOWeight',
    'IODeviceWeight',
    'IOReadBandwidthMax',
    'IOWriteBandwidthMax',
    'IOReadIOPSMax',
    'IOWriteIOPSMax',
    'IODeviceLatencyTargetSec',
    'IPAccounting',
    'IPAddressAllow',
    'IPAddressDeny',
    'IPIngressFilterPath',
    'IPEgressFilterPath',
    'BPFProgram',
    'SocketBindAllow',
    'SocketBindDeny',
    'RestrictNetworkInterfaces',
    'DeviceAllow',
    'DevicePolicy',
    'Slice',
    'Delegate',
    'DisableControllers',
    'ManagedOOMSwap',
    'ManagedOOMMemoryPressure',
    'ManagedOOMMemoryPressureLimit',
    'ManagedOOMPreference'
]
'''This is a list of options that are labelled as systemd.resource-control options, and 
are available to multiple types of units.  See systemd.resource-control man page for more info.'''

exec_unit_opts = [
    'ExecSearchPath',
    'WorkingDirectory',
    'RootDirectory',
    'RootImage',
    'RootImageOptions',
    'RootHash',
    'RootHashSignature',
    'RootVerity',
    'MountAPIVFS',
    'ProtectProc',
    'ProcSubset',
    'BindPaths',
    'BindReadOnlyPaths',
    'MountImages',
    'MountFlags',
    'ExtensionImages',
    'ExtensionDirectories',
    'User',
    'Group',
    'DynamicUser',
    'SupplementaryGroups',
    'PAMName',
    'CapabilityBoundingSet',
    'Capabilities',
    'AmbientCapabilities',
    'NoNewPrivileges',
    'SecureBits',
    'SELinuxContext',
    'AppArmorProfile',
    'SmackProcessLabel',
    'LimitCPU',
    'LimitFSIZE',
    'LimitDATA',
    'LimitSTACK',
    'LimitCORE',
    'LimitRSS',
    'LimitNOFILE',
    'LimitAS',
    'LimitNPROC',
    'LimitMEMLOCK',
    'LimitLOCKS',
    'LimitSIGPENDING',
    'LimitMSGQUEUE',
    'LimitNICE',
    'LimitRTPRIO',
    'LimitRTTIME',
    'UMask',
    'CoredumpFilter',
    'KeyringMode',
    'OOMScoreAdjust',
    'TimerSlackNSec',
    'Personality',
    'IgnoreSIGPIPE',
    'Nice',
    'CPUSchedulingPolicy',
    'CPUSchedulingPriority',
    'CPUSchedulingResetOnFork',
    'CPUAffinity',
    'NUMAPolicy',
    'NUMAMask',
    'IOSchedulingClass',
    'IOSchedulingPriority',
    'ProtectSystem',
    'ProtectHome',
    'RuntimeDirectory',
    'StateDirectory',
    'CacheDirectory',
    'LogsDirectory',
    'ConfigurationDirectory',
    'RuntimeDirectoryMode',
    'StateDirectoryMode',
    'CacheDirectoryMode',
    'LogsDirectoryMode',
    'ConfigurationDirectoryMode',
    'RuntimeDirectoryPreserve',
    'TimeoutCleanSec',
    'ReadWritePaths',
    'ReadOnlyPaths',
    'ReadWriteDirectories',
    'ReadOnlyDirectories',
    'InaccessibleDirectories',
    'InaccessiblePaths',
    'ExecPaths',
    'NoExecPaths',
    'TemporaryFileSystem',
    'PrivateTmp',
    'PrivateDevices',
    'PrivateNetwork',
    'NetworkNamespacePath',
    'PrivateIPC',
    'IPCNamespacePath',
    'PrivateUsers',
    'ProtectHostname',
    'ProtectClock',
    'ProtectKernelTunables',
    'ProtectKernelModules',
    'ProtectKernelLogs',
    'ProtectControlGroups',
    'RestrictAddressFamilies',
    'RestrictFileSystems',
    'RestrictNamespaces',
    'LockPersonality',
    'MemoryDenyWriteExecute',
    'RestrictRealtime',
    'RestrictSUIDSGID',
    'RemoveIPC',
    'PrivateMounts',
    'PrivateMounts',
    'SystemCallFilter',
    'SystemCallErrorNumber',
    'SystemCallArchitectures',
    'SystemCallLog',
    'Environment',
    'EnvironmentFile',
    'PassEnvironment',
    'UnsetEnvironment',
    'StandardInput',
    'StandardOutput',
    'StandardError',
    'StandardInputText',
    'StandardInputData',
    'LogLevelMax',
    'LogExtraFields',
    'LogRateLimitIntervalSec',
    'LogRateLimitBurst',
    'LogFilterPatterns',
    'LogNamespace',
    'SyslogIdentifier',
    'SyslogFacility',
    'SyslogLevel',
    'SyslogLevelPrefix',
    'TTYPath',
    'TTYReset',
    'TTYVHangup',
    'TTYRows',
    'TTYColumns',
    'TTYVTDisallocate',
    'LoadCredential',
    'LoadCredentialEncrypted',
    'SetCredential',
    'SetCredentialEncrypted',
    'UtmpIdentifier',
    'UtmpMode'
]
'''This is a list of options that are labelled as systemd.exec options, and are 
available to multiple types of units.  See systemd.exec man page for more info.'''

possible_unit_opts = {
    'target'    : [unit_generic_opts,
                   unit_cond_assert_opts,
                   unit_install_opts],

    'device'    : [unit_generic_opts,
                   unit_cond_assert_opts,
                   unit_install_opts],

    'service'   : [unit_generic_opts,
                   unit_cond_assert_opts,
                   unit_install_opts,
                   serv_unit_opts,
                   exec_unit_opts,
                   res_con_unit_opts,
                   kill_unit_opts],

    'slice'     : [unit_generic_opts,
                   unit_cond_assert_opts,
                   unit_install_opts,
                   res_con_unit_opts],

    'socket'    : [unit_generic_opts,
                   unit_cond_assert_opts,
                   unit_install_opts,
                   sock_unit_opts,
                   kill_unit_opts,
                   res_con_unit_opts,
                   exec_unit_opts],

    'mount'     : [unit_generic_opts,
                   unit_cond_assert_opts,
                   unit_install_opts,
                   mnt_unit_opts,
                   kill_unit_opts,
                   res_con_unit_opts,
                   exec_unit_opts],

    'automount' : [unit_generic_opts,
                   unit_cond_assert_opts,
                   unit_install_opts,
                   automnt_unit_opts],

    'swap'      : [unit_generic_opts,
                   unit_cond_assert_opts,
                   unit_install_opts,
                   swap_unit_opts,
                   kill_unit_opts,
                   res_con_unit_opts,
                   exec_unit_opts],

    'path'      : [unit_generic_opts,
                   unit_cond_assert_opts,
                   unit_install_opts,
                   path_unit_opts],

    'timer'     : [unit_generic_opts,
                   unit_cond_assert_opts,
                   unit_install_opts,
                   timer_unit_opts],

    'scope'     : [unit_generic_opts,
                   unit_cond_assert_opts,
                   scope_unit_opts,
                   kill_unit_opts,
                   res_con_unit_opts,
                   exec_unit_opts],

    'conf'      : [unit_generic_opts,
                   unit_cond_assert_opts,
                   unit_install_opts,
                   serv_unit_opts,
                   res_con_unit_opts,
                   exec_unit_opts]
}
'''
    This is a mapping struct that maps a unit type to all of the possible lists of options above that should be 
    available to it.  This will make the main code a lot cleaner and easier to read. The idea is to get a unit file 
    suffix, and iterate through possible_unit_opts[unit_type].
'''

unit_dependency_opts = [
    'Wants',
    'Requires',
    'Requisite',
    'BindsTo',
    'PartOf',
    'Upholds',
    'OnSuccess',
    'Sockets',
    'Service',
    'Unit'
]
'''
    This is a list of unit options that create dependencies to build the dependency and runtime tree.
    This will be used to check the unit files after they are parsed and, if necessary, place those dependencies in the
    unrecorded_dependencies list, right before the current unit file's info is sent to the dependency map dictionary.
'''

space_delim_opts = [
    'Documentation',
    'Before',
    'After',
    'Wants',
    'WantedBy',
    'Requires',
    'RequiredBy',
    'Requisite',
    'BindsTo',
    'PartOf',
    'Upholds',
    'Conflicts',
    'OnFailure',
    'OnSuccess',
    'PropagatesReloadTo',
    'ReloadPropagatedFrom',
    'PropagatesStopTo',
    'StopPropagatedFrom',
    'JoinsNamespaceOf',
    'RequiresMountsFor',
    'Sockets'
]
'''
    List of all space-delimited options that ensures that all unit dependencies are recorded, and 
    options like Exec and Description aren't a list of strings when they need to be a single string.
'''

command_directives = [
    'ExecStart',
    'ExecCondition',
    'ExecStartPre',
    'ExecStartPost',
    'ExecReload',
    'ExecStop',
    'ExecStopPost'
]
'''
    These command directives are options that list binaries that are used when the service contaning 
    these options is triggered. These are used by the master struct to map the binary specified to
    libraries it requires, files it uses or references, and other interesting strings found in the binary.
'''

ms_only_keys = [
    'remote_path',
    'libraries',
    'files',
    'strings'
]
'''
    This is a list of keys that have different formatting than the unit file entries and shouldn't be 
    parsed by the dependency map.
'''