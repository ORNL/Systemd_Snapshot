# Systemd Notes

- systemd is a system and service manager for Linux operating systems.
- When run as the first process on boot (as PID 1), it acts as init system that brings up and maintains userspace services.
- systemd is usually installed as the `/sbin/init` symlink and started during early boot. 
- systemd provides a dependency system between entities, called "units," that have 11 different types. 
- Units encapsulate various objects (e.g., executables, configuration files, ...) that are relevant for system boot-up and maintenance. 

## Units
- Plain Unit: not a template or instance.
- Template Unit: a unit that can be instantiated into a concrete or instance unit; many units can be created and customized from a template.
- Instance Unit: created from a template

## Systemd Information
- The best information is probably in the man files for systemd
- bootup(7)
- boot(7)
- systemctl(1)
- journalctl(1)
- systemd-notify(1)
- systemd-cgls(1)
- systemd-analyze(1)
- systemd.generator(7)
- systemd.boot(7)
- systemd(1)
- systemd.unit(5): 
    - lists default search directories (system and user)
- systemd.syntax(7)
- systemd.directives(7)
- systemd.target(5)
- systemd.device(5)
- systemd.mount(5)
- systemd.automount(5)
- systemd.timer(5)
- systemd.time(7)
- systemd.swap(5)
- systemd.path(5)
- systemd.slice(5)
- systemd.scope(5)
- systemd.special(7)
- systemd.service(5)
- systemd.socket(5)
- systemd-halt.service(8)
- dracut(8)
- user@.service(5)
- systemd-system.conf(5)
- systemd-user.conf(5)
- systemd.unit(5)

## Unit File Load Paths (systemd.unit(5))
- Unit files are loaded from a set of paths determined during compilation (kernel comp?)
    - See the man pages above for the list.
- Unit files found first OVERRIDE files with the same name found LATER.

## Boot
- On first boot, systemd will enable or disable units according to a preset policy. 
    - See systemd.preset(5) and "First Boot Semantics" in machine-id(5).
- systemd contains NATIVE IMPLEMENTATIONS of various tasks that need to be executed as part of the boot process.  For example, it sets the hostname or configures the loopback network device. It also sets up and mounts various API file systems, such as /sys/ or /proc/.
    - JMC: Does this mean it does these things as part of the systemd binary implementation and NOT due to a unit file?

### Unit Creation
- Most units are configured in unit configuration files.
- Some are created automatically from other configuration files, 
- Some are dynamically created from system state, and
- Some are created programmatically at runtime. 

NOTE: based on the above, a STATIC ANALYSIS may NOT be sufficient to fully understand system setup.

### Unit Loading
- systemd attempts to keep a minimal set of units loaded into memory (read from disk)
- systemd will automatically and implicitly load units (read unit files) from disk into memory when they are referenced. Referencing occurs when:
    1. A loaded unit references it with a dependency, e.g., After=
    2. The unit is starting, running, reloading, or stopping.
    3. The unit is in the FAILED state.
    4. A job for the unit is PENDING.
    5. The unit is pinned by an active IPC client program.
    6. The unit is a special PERPETUAL unit.
    7. The unit has running processes associated with it.

- If a unit is in memory AND NONE of the above conditions apply, then it and its accounting data is removed from memory (freed). This is called GARBAGE COLLECTION.
- When a unit is garbage collected, all configuration, state, execution results are lost (exception is what is in a log file)

### Unit States
Units are in one of several GENERAL STATES; these states describe the active or dynamic status of units and the processes they create:
- "active": meaning started, bound, plugged in, ...,  depending on the unit type, see below,
- "inactive": meaning stopped, unbound, unplugged, ..., 
- "activating": in the process of being activated, i.e. between the two states
- "deactivating" : in the process of being deactivated
- "failed": similar to "inactive" but signifies the service failed in some way.

- NOTE: unit types may have a number of additional substates, which are mapped to the five generalized unit states described here.
- NOTE: If a unit file is empty OR it is symlinked to /dev/null no configuration will be loaded and it will be given a state of MASKED (cannot be activiated). Use this to DISABLE services.

## Specific Unit Types
- `.service`: start and control daemons.
- `.scope`: similar to service units, but manage foreign processes instead of starting them as well. See systemd.scope(5).
- `.socket`: encapsulate local IPC or network sockets in the system.
    - For each .socket unit, a matching service unit must exist that will start when traffic comes in on the socket.
    - Names of .service is the same as the socket by default.
        - Service= option in .socket unit changes the default name to something different. 
- `.target`: group units, or provide well-known synchronization points during boot-up, see systemd.target(5).
- `.device`: expose kernel devices in systemd and may be used to implement device-based activation. For details, see systemd.device(5).
- `.mount`: control mount points in the file system, for details see systemd.mount(5).
- `.swap`: similar to mount units and encapsulate memory swap partitions or files of the operating system. They are described in systemd.swap(5).
- `.automount`: provide on-demand mounting of file systems as well as parallelized boot-up. See systemd.automount(5).
- `.timer`: trigger activation of other units based on timers. You may find details in systemd.timer(5).
- `.path`: used to activate other services when file system objects change or are modified. See systemd.path(5).
    - Paths can be monitored by systemd, this unit file directs what is done when this happens.
    - For each *.path unit, a matching *.service file must exist that describes the unit that activates.
    - The default name are equivalent, to change this use the `Unit=` directive in the Path file.
- `.slice`: used to group units which manage system processes (such as service and scope units) in a hierarchical tree for resource management purposes. See systemd.slice(5).

### Unit File Naming
- unit files are named as follows:

```
<unit name prefix>[<optional template specifier>].<unit type suffix>`
```

- unit name prefix: a string.
    - may be parameterized using a instance name in which case it is constructed using a template.

- A template specifier (unit file name) is translated into ONE or MORE concrete unit files.
    - A template is designated by an `@` character with NOTHING between it and the `.` character.
    - A template instance is designated by an `@` character and some non-empty string after it and before the `.` character.

- a unit type suffix: one of the following strings that determines unit type.
    - ".service", 
    - ".socket", 
    - ".device", 
    - ".mount", 
    - ".automount", 
    - ".swap", 
    - ".target", 
    - ".path", 
    - ".timer", 
    - ".slice", 
    - ".scope".

### Unit Aliases (systemd.unit(5))
- Unit aliases are defined by creating a symlink having an alias name that points to the target unit name. 
    - Aliases are used as an alternative name to specify the exact unit that gets loaded.
- Alias names (symlinks) are expected to be in one of the unit search paths.
- Alias name suffix (the type. e.g., .service, .socket) MUST MATCH the unit file they link to.
- Linked unit files DO NOT have to be in the unit search paths; this is DIFFERENT from alias names.
    - Example:
        - `default.target` is used to designate how to default boot the system.
        - `default.target` is a symlink (alias) to either `multi-user.target` or `graphical.target` to SELECT which system startup process should be followed.
- Alias names may be used in commands like disable, start, stop, status, and similar
- Alias names may also be used in all unit dependency directives, including Wants=, Requires=, Before=, After=. 
- Alias names CANNOT be used with the preset command.
- Unit files MAY specify their aliases using the `Alias=` directive in the `[Install]` section of the unit file.
    - This provides a way to see all the symlinks that COULD EXIST and point to THIS unit.
    - The the `Alias=` directive is used two things will happen:
        - When the unit is ENABLED (by the systemd tool), symlinks WILL BE DYNAMICALLY CREATED for those names.
        - When the unit is DISABLED the symlinks WILL BE REMOVED.
- A plain unit may only be aliased by a plain name (not a template or template instance)
- A template instance may only be aliased by another template instance ( must have a string between @ and .)
- A template may be aliased to another template -- alias will apply to all linked templates.

Dependencies:
    - Implicit: see respective manpages for which dependencies are established for certain services, etc.
    - Explicit: can be turned on and off by setting DefaultDependencies= to yes (the default) and no, while implicit dependencies are always in effect.
    
### Templates
- A mechanism to create multiple unit files from a single file (the template).
- Literal or full unit file names will always be the target of the initial search.
- Template FILES and directories with a specific naming convention:
    - `<name>@.<type>` : template file that defines MULTIPLE SERVICES or UNITS
    - Notice the `@.` the characters between the gap between these two characters completes the name of the INSTANCE for that template when it is created.
- Template INSTANCES have a specific name when they are INSTANTIATED.
    - `<name>@<instance name>.<type>` : instantiated unit template
    - We would specify that we want a service, etc., of this type and it would be created using the Template that lives on the file system.
- Example: If the system searches for `name@xxx.service` and it CANNOT be found, `name@.service` will become the target. We start searching for a TEMPLATE as opposed to a TEMPLATE INSTANCE. If that is found, the target `name@xxx.service` will be created with the configuration found in `name@.service`.
- In configuration files, use `%i` to identify the `xxx` above in configuration files that live in `name@.service`

### Dropins (see systemd.unit(5))
- A unit file (e.g., foo.service) MAY BE paired with a "dropin" directory, e.g., foo.service.d
    - xxx.yyy.d
- All files with the suffix `.conf` from this directory will be merged in alphabetical order and added after parsing the main unit file. 
    - The directives in the `.conf` files are MERGED with the directives in the main unit file and other `.conf` files.
- These dropin `.conf` files provide a simple way to augment the original unit file without explicitly modifying it.
- For units with aliases, all `.conf` files in all dropin alias directories are also parsed.
- For top-level unit types, e.g., service or socket, dropins with directory `<type>.d/` are supported.
    - The `.conf` files in this directory, altering or add to the settings of ALL CORRESPONDING UNIT FILES ON THE SYSTEM OF THAT TYPE. 
    - The `<type>.d/` files have lower precedence compared to files in name-specific override directories.
- In addition to `/etc/systemd/system`, the dropin ".d/" directories for system services can be placed in 
  /usr/lib/systemd/system or /run/systemd/system directories. 
- Precedence Rules:
    - Precedence ( 1, ... n ): ( /etc/, /run/, /lib/, UNIT FILE )
    - `/etc/` take precedence over those in `/run/`
    - `/run/` take precedence over those in `/usr/lib/`.
    - Drop-in files under any of these directories take precedence over unit files wherever located. 
    - Multiple dropin files with different names are applied in lexicographic order.

### Slice Units
- A group of processes.
    - Units that manage processes (scope and service units) may be assigned to a SPECIFIC SLICE.
    - For each slice, resource limits may be set. They apply to all units that are in the slice.
- Hierarchical managed.
    - Create a node in the Linux Control Group (cgroup) tree.
    - Organized in a tree structure.
    - NAME OF SLICE encodes location in TREE.
        - NAME has a dash-separated names which describe the path to the slice from the root slice.
        - The ROOT SLICE is named: -.slice
        - foo.bar.slice : ROOT (-.slice) -> foo.slice -> bar.slice (leaf)
- Cannot be templated.
- Cannot add multiple names to slice units via symlinks.
- Default systemd behavior: 
    - service and scope units are placed in system.slice.
    - virtual machines and containers are in machine.slice
    - user sessions are in user.slice

### Dependencies
- systemd uses DEPENDENCY DIRECTIVES to establish the dependency relationships between units
- systemd uses ORDERING and REQUIREMENT dependencies; they are orthogonal (different purposes)
- USUALLY requirement AND ordering dependencies are placed between two units. 
- The MAJORITY of dependencies are implicitly (we don't use the above terms...) created and maintained by systemd. 

#### Implicit Dependencies
- STANDARD DEPENDENCIES that are understood and DO NOT need to be explicitly stated.
- CANNOT BE turned off.

#### Default Dependencies
- The set of dependencies that are established AUTOMATICALLY when the `DefaultDependencies={no,yes}` directive is YES/TRUE.
    - REMEMBER when this directive IS NOT specified it defaults to YES/TRUE.
- See the specific documentation for the unit type, e.g., `system.service(5)`
- Otherwise similar to Implicit Dependencies.

##### Defaults: Service
- (implicit) Requires= and After= on `dbus.socket` for services of Type=dbus
- (implicit) Socket activated services ordered AFTER their `.socket` units by adding After= dependency.
- (implicit) Services having Sockets= pull in all in that list automatically with Wants= and After= dependencies.
- (default) sysinit.target becomes a Requires= and After= dependency.
- (default) basic.target becomes an After= dependency.
- (default) shutdown.target becomes a Conflicts= and Before= dependency.
- See docs on special case for instanced template units.

##### Defaults and Implicits: Socket
- (implicit) Before= dependency on the service unit they activate.
- (implicit) Requires= and After= dependencies on all mounts necessary to access file system paths for socket units referencing those paths.
- (implicit) BindsTo= and After= dependencies on the device unit encapsulating the network interface if the socket unit uses BindToDevice=
- (default) Before= dependency on `socket.target`
- (default) After= and Requires= dependency on `sysinit.target`
- (default) Before= and Conflicts= dependency on `shutdown.target`

##### Defaults and Implicits: Device
- None.

##### Defaults and Implicits: Mount
- (implicit) If a mount unit is BENEATH another mount unit a requirement and ordering dependency is created.
- (implicit) BindsTo= and After= dependencies on the device unit encapsulating the block device.
- (default) Before= and Conflicts= dependencies on `umount.target`
- (default) After= dependency on `local-fs-pre.target` if mount unit refers to local file system
- (default) Before= dependency on `local-fs.target` if mount unit refers to local file system UNLESS nofail set on mount
- (default) After= dependency on `remote-fs-pre.target, network.target, network-online.target` if a network mount unit.
- (default) Before= dependency on `remote-fs.target` if a network unit unless nofail set.

##### Defaults and Implicits: Automount
- (implicit) If an automount unit is BENEATH another mount unit a requirement and ordering dependency is created.
- (implicit) Before= dependency created between automount and mount unit it activates.
- (default) Before= and Conflicts= on `umount.target`
- (default) After= on `local-fs-pre.target`
- (default) Before= on `local-fs.target`

##### Defaults and Implicits: Swap
- (implicit) BindsTo= and After= dependencies on the device and mount units they are activated FROM.
- (default) Conflicts= and Before= on `umount.target`
- (default) Before=swap.target 

##### Defaults and Implicits: Target
- (default) After= dependencies for all configured Wants= and Requires= (unless it wants or requires ITSELF)
- (default) Conflicts= and Before= dependencies on `shutdown.target`

##### Defaults and Implicits: Path
- (implicit) If a path unit is BENEATH another mount unit a requirement and ordering dependency is created for both.
- (implicit) Before= dependency added between path unit and the unit it is supposed to activate.
- (default) Before= on `paths.target`
- (default) After= and Requires= on `sysinit.target`
- (default) Conflicts= and Before= on `shutdown.target`

##### Defaults and Implicits: Timer
- (implicit) Before= dependency on the service they activate.
- (default) Requires= and After= on `sysinit.target`
- (default) Before= on `timers.target`
- (default) Conflicts= and Before= on `shutdown.target`
- (default) With at least on OnCalendar= directive, After=time-set.target time-sync.target

##### Defaults and Implicits: Slice
- (implicit) After= and Requires= on their immediate parent slice unit.
- (default) Conflicts= and Before= on `shutdown.target`

##### Defaults and Implicits: Scope
- (implicit) See systemd.resource-control(5)
- (default) Conflicts= and Before= on shutdown.target

### Requirement Dependencies
- These dependencies DO NOT establish an ORDER!
- Wants, Requires, Conflicts
- systemd uses positive requirement dependencies (i.e., Requires=) signifying this unit REQUIRES the units in the list.
- systemd uses negative requirement dependencies (i.e., Conflicts=) signifying this unit CONFLICTS (or cannot run or be used) with the units in the list.
- If only a requirement dependency exists between two units (e.g. foo.service requires bar.service) and both are requested to start, they will be started in parallel. 
- In both cases (wants and requires) the PREFERRED WAY to install these links is to use the [Install] section of that target unit file, systemctl enable (or disable to remove them).

## Unit File Directives

### Wants
- A REQUIREMENT dependency
- When THIS UNIT is started, all units listed in the WANTS list will ATTEMPT TO be started immediately and in parallel.
- THIS UNIT file (e.g., foo.service) MAY BE paired with a "wants" directory: foo.service.wants
    - All units linked in the example foo.service.wants/ directory will be treated as if they were in the WANTS list in the unit file.
- If ANY of the units in the WANTS list fails to start, then THIS UNIT will still start and its validity will not be effected.

- Unit --> Unit.wants ----> { all links here } --- for each link --> Unit file

### Requires
- A REQUIREMENT dependency
- Similar to WANTS but with a stronger dependency.
    - All `requires` units SHOULD be activiated.
    - If one in the list fails an ordering AFTER= dependency is set on the failing unit (THIS UNIT cannot start until AFTER the failed unit starts) and THIS UNIT WILL NOT START.
    - If one of the requires list unit is STOPPED, THIS UNIT WILL BE EXPLICITLY STOPPED.
- Requires DOES NOT IMPLY all the units in THIS UNIT's list always have to be active when this unit is running.
- As with wants directories, requires directories can contain links and they are treated as if they are in the REQUIRES list.

### Requisite
- A REQUIREMENT dependency
- If the units in the Requisite= list are not ALREADY STARTED, they WILL NOT be started AND this unit will NOT BE STARTED AND FAIL.
- SHOULD be combined with ordering dependency After= to ensure THIS UNIT is not started BEFORE the unit in the Requisite= list.
- Requisite=B in A and RequisiteOf=A in B specify opposite ends of this REQUIREMENT

### BindsTo
- A REQUIREMENT dependency
- Similar to REQUIRES, but this is stronger.
- If the BindsTo unit STOPS (or enters the INACTIVE state), then THIS UNIT STOPS.
- When combined with After= this becomes stronger yet: the bound to unit must be in the ACTIVE state for THIS UNIT to be in the ACTIVE state.
- BindsTo=B in A and BoundBy=A in B specify opposite ends of this REQUIREMENT

### PartOf
- Similar to REQUIRES, but limited to Starting and Stopping of Units
- When units IN the PartOf= list are STOPPED or RESTARTED that action is propagated to THIS UNIT
- A ONE WAY dependency; things that happen to THIS UNIT do not propagate to the units in the PartOf= list.
- PartOf=B in A and ConsistsOf=A in B specify opposite ends of this REQUIREMENT; ConsistsOf= cannot exist by itself.

### Upholds
- Similar to WANTS.
- When THIS UNIT is up (active?), all units in the Upholds list are started when found to be inactive or failed AND no job is queued for them.
- Has a CONTINUOUS effect; this dependency will always act when the condition holds (it is not a one-time thing)
- Upholds=B in A and UpheldBy=A in B specify opposite ends of this REQUIREMENT; UpheldBy= cannot exist by itself.

### Conflicts=
- A NEGATIVE REQUIREMENTS dependency.
- Starting THIS UNIT will STOP the units in the Conflicts= list.
- Starting the units in the Conflicts= list will STOP THIS UNIT.
- Does NOT imply ordering.
- After= or Before= ordering when applied ensures a conflicting unit is STOPPED before the other unit is started.

### Ordering Dependencies
- After, Before
- systemd uses ordering dependencies: (i.e., After= and Before=). 
- After dependencies indicate this UNIT should be started AFTER the UNITS in the After= list.
- Before dependencies indicate this UNIT should be started BEFORE the UNITS in the Before= list.
- Programs and Units may "request" state changes; requests are encapsulated in JOBS and maintained in a queue.
- Ordering dependencies establish when JOBS will be scheduled.
    - JOB:
    - A JOB may succeed or fail.

    On boot systemd activates the target unit `default.target` whose job is to activate on-boot services and other on-boot units by pulling them in via dependencies. 
    USUALLY, the unit name is just an ALIAS (symlink) for either `graphical.target` or `multi-user.target`. See systemd.special(7) for details about these target units.

#### Before
- An ORDERING dependency.
- In foo.service with Before=bar.service, bar.service's start is DELAYED until foo.service has finished starting.
    - foo.service ---> bar.service [ foo before bar, or bar after foo ]
- When two units with a Before= dependency are shutdown, the inverse of the start-up order is applied
- Before= dependencies on device units have NO EFFECT (not supported)

#### After
- An ORDERING dependency
- The LOGICAL INVERSE of Before=
- In foo.service with After=bar.service, when bar.service has finished starting, foo.service ,may start.
    - bar.service ---> foo.service [ bar before foo, or foo after bar ]
- When shutdown the inverse occurs, foo.service ---> bar.service [ foo shutodown, then bar ]
- With ANY ordering dependency (Before= or After=) if one unit is SHUTDOWN, the other is STARTED (SHUTDOWN before STARTED)
- IF no ordering dependency, units can be shutdown or started simultaneously.

### OnFailure
- A list of units that are activated with THIS UNIT enters the FAILED state.

### OnSuccess
- A list of units that are activated when this unit enters the INACTIVE state.

### PropagatesReloadTo, ReloadPropagatedFrom
- When a reload request is issued to THIS UNIT, all units in the `PropagatesReloadTo=` list will also be queued to reload.
- When a reload request is issued from a unit containing this unit in its `ReloadPropagatedFrom=` THIS UNIT will be reloaded.

### PropagatesStopTo, StopPropagatedFrom
- When a stop request is issued to THIS UNIT, all units in the `PropagatesStopTo=` list will also be queued to stop.
- When a stop request is issued from a unit containing this unit in its `StopPropagatedFrom=` THIS UNIT will be stopped.

### JoinsNamespaceOf
- Used for units that start processes (service units).
- Lists one or more other units whose network or temporary file namespace to join.

### RequiresMountsFor
- A list of absolute paths.
- Using this list dependencies of `Requires=` and `After=` are automatically added as dependencies for all mount points required to access the specified paths.

### OnFailureJobMode
- Specifies how the units listed in the `OnFailure=` directive will be enqueued.

### IgnoreOnIsolate
- See documentation

### StopWhenUnneeded
- When TRUE, this unit will be stopped when it is no longer USED.
- This unit will automatically be cleaned up when NO OTHER UNIT REQUIRES it.

### RefuseManualStart, RefuseManualStop
- This unit can only be activated or deactivated INDIRECTLY and NOT thru the command line or other explicit methods.

### AllowIsolate
- See documentation.

### DefaultDependencies
- A boolean value
- If yes/true, default dependencies will be CREATED; what is created depends on the unit type.
- It is recommended that this be set to the default or TRUE for almost all units.

### CollectMode
- Relates to how this unit is garbage collected.

### FailureAction, SuccessAction
- The action to take when a UNIT STOPS or enters the FAILED or INACTIVE STATES.

#### FailureActionExitStatus, SuccessActionExitStatus
- Used in conjunction with FailureAction and SuccessAction

### JobTimeoutSec, JobRunningTimeoutSec
- Time limitations on Jobs

#### JobTimeoutAction, JobTimeoutRebootArgument
- Used in conjunction with JobTimeoutSec, etc.

### StartLimitIntervalSec, StartLimitBurst
- Rate limits unit starting

#### StartLimitAction
- Used with StartLimitIntervalSec, etc.

### RebootArgument

### SourcePath
- The path to the configuration file from which this unit file was generated; used for generator tools and not used in normal units.

## Groups
- Processes (executables) systemd spawns are placed in individual Linux control groups named after the unit to which they belong. This forms a private systemd hierarchy. 
    - The systemd hierarchy is used to keep track of processes. 
    - Control group information is maintained in the kernel.
    - Control group information is accessible via the file system hierarchy (sysfs beneath /sys/fs/cgroup/).
    - Control group information can also be accessed using tools such as systemd-cgls(1) or ps(1).
        - `$ ps xawf -eo pid,user,cgroup,args`
        - Useful to list all processes and the systemd units they belong to.

- systemd is compatible with the SysV init system
    - SysV init scripts are read as an alternative (though limited) configuration file format.
    - The SysV /dev/initctl interface is provided, and compatibility implementations of the various SysV client tools are available. 
    - In addition to that, various established Unix functionality such as /etc/fstab or the utmp database are supported.

- systemd has a minimal transaction system: 
    - if a unit is requested to start up or shut down, it will add it and all its dependencies to a temporary transaction. 
    - The temporary transaction will be verified for consistency (what does this entail?). If not consistent, systemd will try to fix it up and remove non-essential jobs from the transaction that might remove the loop (what does loop mean here?).  
    - Effectively this means that before executing a requested operation, systemd will verify that it makes sense, fixing it if possible, and only failing if it really cannot work.

    - [HARD TO TRANSLATE THIS!] Transactions are generated independently of a unit's state at runtime. For example, if a start job is requested on an already started unit, it will still generate a transaction and wake up any inactive dependencies (and cause propagation of other jobs as per the defined relationships). This is because the enqueued job is at the time of execution compared to the target unit's state and is marked successful and complete when both satisfy.  However, this job also pulls in other dependencies due to the defined relationships and thus leads to, in our example, start jobs for any of those inactive units getting queued as well.

# Systemd Mapper Items
Questions about master struct data:
    - What is the reason behind symlinks being both dependencies and aliases (all symlinks are aliases)?
    - Why did you not just make the key the full path string (not the remote path but system path)?
    - There are units that are not SYMLINKS or FILES. Describe how these function?
        - systemd-random-seed.service : not on filesystem??  In a unit file but not a link or file.
    - How are we handling units with Condition= and Assert=
    - systemd.preset
    - Implicit Dependencies for each type.



    - ".device", 
    - ".mount", 
    - ".automount", 
    - ".swap", 
    - ".target", 
    - ".path", 
    - ".timer", 
    - ".slice", 
    - ".scope".

#### Requirement Dependencies
- These dependencies DO NOT establish an ORDER!
- Wants, Requires, Conflicts
- systemd uses positive requirement dependencies (i.e., Requires=) signifying this unit REQUIRES the units in the list.
- systemd uses negative requirement dependencies (i.e., Conflicts=) signifying this unit CONFLICTS (or cannot run or be used) with the units in the list.
- If only a requirement dependency exists between two units (e.g. foo.service requires bar.service) and both are requested to start, they will be started in parallel. 
- In both cases (wants and requires) the PREFERRED WAY to install these links is to use the [Install] section of that target unit file, systemctl enable (or disable to remove them).

## Unit File Directives

### Wants
- A REQUIREMENT dependency
- When THIS UNIT is started, all units listed in the WANTS list will ATTEMPT TO be started immediately and in parallel.
- THIS UNIT file (e.g., foo.service) MAY BE paired with a "wants" directory: foo.service.wants
    - All units linked in the example foo.service.wants/ directory will be treated as if they were in the WANTS list in the unit file.
- If ANY of the units in the WANTS list fails to start, then THIS UNIT will still start and its validity will not be effected.

- Unit --> Unit.wants ----> { all links here } --- for each link --> Unit file

### Requires
- A REQUIREMENT dependency
- Similar to WANTS but with a stronger dependency.
    - All `requires` units SHOULD be activiated.
    - If one in the list fails an ordering AFTER= dependency is set on the failing unit (THIS UNIT cannot start until AFTER the failed unit starts) and THIS UNIT WILL NOT START.
    - If one of the requires list unit is STOPPED, THIS UNIT WILL BE EXPLICITLY STOPPED.
- Requires DOES NOT IMPLY all the units in THIS UNIT's list always have to be active when this unit is running.
- As with wants directories, requires directories can contain links and they are treated as if they are in the REQUIRES list.

### Requisite
- A REQUIREMENT dependency
- If the units in the Requisite= list are not ALREADY STARTED, they WILL NOT be started AND this unit will NOT BE STARTED AND FAIL.
- SHOULD be combined with ordering dependency After= to ensure THIS UNIT is not started BEFORE the unit in the Requisite= list.
- Requisite=B in A and RequisiteOf=A in B specify opposite ends of this REQUIREMENT

### BindsTo
- A REQUIREMENT dependency
- Similar to REQUIRES, but this is stronger.
- If the BindsTo unit STOPS (or enters the INACTIVE state), then THIS UNIT STOPS.
- When combined with After= this becomes stronger yet: the bound to unit must be in the ACTIVE state for THIS UNIT to be in the ACTIVE state.
- BindsTo=B in A and BoundBy=A in B specify opposite ends of this REQUIREMENT

### PartOf
- Similar to REQUIRES, but limited to Starting and Stopping of Units
- When units IN the PartOf= list are STOPPED or RESTARTED that action is propagated to THIS UNIT
- A ONE WAY dependency; things that happen to THIS UNIT do not propagate to the units in the PartOf= list.
- PartOf=B in A and ConsistsOf=A in B specify opposite ends of this REQUIREMENT; ConsistsOf= cannot exist by itself.

### Upholds
- Similar to WANTS.
- When THIS UNIT is up (active?), all units in the Upholds list are started when found to be inactive or failed AND no job is queued for them.
- Has a CONTINUOUS effect; this dependency will always act when the condition holds (it is not a one-time thing)
- Upholds=B in A and UpheldBy=A in B specify opposite ends of this REQUIREMENT; UpheldBy= cannot exist by itself.

### Conflicts=
- A NEGATIVE REQUIREMENTS dependency.
- Starting THIS UNIT will STOP the units in the Conflicts= list.
- Starting the units in the Conflicts= list will STOP THIS UNIT.
- Does NOT imply ordering.
- After= or Before= ordering when applied ensures a conflicting unit is STOPPED before the other unit is started.

### Ordering Dependencies
- After, Before
- systemd uses ordering dependencies: (i.e., After= and Before=). 
- After dependencies indicate this UNIT should be started AFTER the UNITS in the After= list.
- Before dependencies indicate this UNIT should be started BEFORE the UNITS in the Before= list.
- Programs and Units may "request" state changes; requests are encapsulated in JOBS and maintained in a queue.
- Ordering dependencies establish when JOBS will be scheduled.
    - JOB:
    - A JOB may succeed or fail.

    On boot systemd activates the target unit `default.target` whose job is to activate on-boot services and other on-boot units by pulling them in via dependencies. 
    USUALLY, the unit name is just an ALIAS (symlink) for either `graphical.target` or `multi-user.target`. See systemd.special(7) for details about these target units.

#### Before
- An ORDERING dependency.
- In foo.service with Before=bar.service, bar.service's start is DELAYED until foo.service has finished starting.
    - foo.service ---> bar.service [ foo before bar, or bar after foo ]
- When two units with a Before= dependency are shutdown, the inverse of the start-up order is applied
- Before= dependencies on device units have NO EFFECT (not supported)

#### After
- An ORDERING dependency
- The LOGICAL INVERSE of Before=
- In foo.service with After=bar.service, when bar.service has finished starting, foo.service ,may start.
    - bar.service ---> foo.service [ bar before foo, or foo after bar ]
- When shutdown the inverse occurs, foo.service ---> bar.service [ foo shutodown, then bar ]
- With ANY ordering dependency (Before= or After=) if one unit is SHUTDOWN, the other is STARTED (SHUTDOWN before STARTED)
- IF no ordering dependency, units can be shutdown or started simultaneously.

### OnFailure
- A list of units that are activated with THIS UNIT enters the FAILED state.

### OnSuccess
- A list of units that are activated when this unit enters the INACTIVE state.

### PropagatesReloadTo, ReloadPropagatedFrom
- When a reload request is issued to THIS UNIT, all units in the `PropagatesReloadTo=` list will also be queued to reload.
- When a reload request is issued from a unit containing this unit in its `ReloadPropagatedFrom=` THIS UNIT will be reloaded.

### PropagatesStopTo, StopPropagatedFrom
- When a stop request is issued to THIS UNIT, all units in the `PropagatesStopTo=` list will also be queued to stop.
- When a stop request is issued from a unit containing this unit in its `StopPropagatedFrom=` THIS UNIT will be stopped.

### JoinsNamespaceOf
- Used for units that start processes (service units).
- Lists one or more other units whose network or temporary file namespace to join.

### RequiresMountsFor
- A list of absolute paths.
- Using this list dependencies of `Requires=` and `After=` are automatically added as dependencies for all mount points required to access the specified paths.

### OnFailureJobMode
- Specifies how the units listed in the `OnFailure=` directive will be enqueued.

### IgnoreOnIsolate
- See documentation

### StopWhenUnneeded
- When TRUE, this unit will be stopped when it is no longer USED.
- This unit will automatically be cleaned up when NO OTHER UNIT REQUIRES it.

### RefuseManualStart, RefuseManualStop
- This unit can only be activated or deactivated INDIRECTLY and NOT thru the command line or other explicit methods.

### AllowIsolate
- See documentation.

### DefaultDependencies
- A boolean value
- If yes/true, default dependencies will be CREATED; what is created depends on the unit type.
- It is recommended that this be set to the default or TRUE for almost all units.

### CollectMode
- Relates to how this unit is garbage collected.

### FailureAction, SuccessAction
- The action to take when a UNIT STOPS or enters the FAILED or INACTIVE STATES.

#### FailureActionExitStatus, SuccessActionExitStatus
- Used in conjunction with FailureAction and SuccessAction

### JobTimeoutSec, JobRunningTimeoutSec
- Time limitations on Jobs

#### JobTimeoutAction, JobTimeoutRebootArgument
- Used in conjunction with JobTimeoutSec, etc.

### StartLimitIntervalSec, StartLimitBurst
- Rate limits unit starting

#### StartLimitAction
- Used with StartLimitIntervalSec, etc.

### RebootArgument

### SourcePath
- The path to the configuration file from which this unit file was generated; used for generator tools and not used in normal units.

## Groups
- Processes (executables) systemd spawns are placed in individual Linux control groups named after the unit to which they belong. This forms a private systemd hierarchy. 
    - The systemd hierarchy is used to keep track of processes. 
    - Control group information is maintained in the kernel.
    - Control group information is accessible via the file system hierarchy (sysfs beneath /sys/fs/cgroup/).
    - Control group information can also be accessed using tools such as systemd-cgls(1) or ps(1).
        - `$ ps xawf -eo pid,user,cgroup,args`
        - Useful to list all processes and the systemd units they belong to.

- systemd is compatible with the SysV init system
    - SysV init scripts are read as an alternative (though limited) configuration file format.
    - The SysV /dev/initctl interface is provided, and compatibility implementations of the various SysV client tools are available. 
    - In addition to that, various established Unix functionality such as /etc/fstab or the utmp database are supported.

- systemd has a minimal transaction system: 
    - if a unit is requested to start up or shut down, it will add it and all its dependencies to a temporary transaction. 
    - The temporary transaction will be verified for consistency (what does this entail?). If not consistent, systemd will try to fix it up and remove non-essential jobs from the transaction that might remove the loop (what does loop mean here?).  
    - Effectively this means that before executing a requested operation, systemd will verify that it makes sense, fixing it if possible, and only failing if it really cannot work.

    - [HARD TO TRANSLATE THIS!] Transactions are generated independently of a unit's state at runtime. For example, if a start job is requested on an already started unit, it will still generate a transaction and wake up any inactive dependencies (and cause propagation of other jobs as per the defined relationships). This is because the enqueued job is at the time of execution compared to the target unit's state and is marked successful and complete when both satisfy.  However, this job also pulls in other dependencies due to the defined relationships and thus leads to, in our example, start jobs for any of those inactive units getting queued as well.

# Systemd Mapper Items
Questions about master struct data:
    - What is the reason behind symlinks being both dependencies and aliases (all symlinks are aliases)?
    - Why did you not just make the key the full path string (not the remote path but system path)?
    - There are units that are not SYMLINKS or FILES. Describe how these function?
        - systemd-random-seed.service : not on filesystem??  In a unit file but not a link or file.
    - How are we handling units with Condition= and Assert=
    - systemd.preset
    - Implicit Dependencies for each type.


    - ".device", 
    - ".mount", 
    - ".automount", 
    - ".swap", 
    - ".target", 
    - ".path", 
    - ".timer", 
    - ".slice", 
    - ".scope".

#### Requirement Dependencies
- These dependencies DO NOT establish an ORDER!
- Wants, Requires, Conflicts
- systemd uses positive requirement dependencies (i.e., Requires=) signifying this unit REQUIRES the units in the list.
- systemd uses negative requirement dependencies (i.e., Conflicts=) signifying this unit CONFLICTS (or cannot run or be used) with the units in the list.
- If only a requirement dependency exists between two units (e.g. foo.service requires bar.service) and both are requested to start, they will be started in parallel. 
- In both cases (wants and requires) the PREFERRED WAY to install these links is to use the [Install] section of that target unit file, systemctl enable (or disable to remove them).

## Unit File Directives

### Wants
- A REQUIREMENT dependency
- When THIS UNIT is started, all units listed in the WANTS list will ATTEMPT TO be started immediately and in parallel.
- THIS UNIT file (e.g., foo.service) MAY BE paired with a "wants" directory: foo.service.wants
    - All units linked in the example foo.service.wants/ directory will be treated as if they were in the WANTS list in the unit file.
- If ANY of the units in the WANTS list fails to start, then THIS UNIT will still start and its validity will not be effected.

- Unit --> Unit.wants ----> { all links here } --- for each link --> Unit file

### Requires
- A REQUIREMENT dependency
- Similar to WANTS but with a stronger dependency.
    - All `requires` units SHOULD be activiated.
    - If one in the list fails an ordering AFTER= dependency is set on the failing unit (THIS UNIT cannot start until AFTER the failed unit starts) and THIS UNIT WILL NOT START.
    - If one of the requires list unit is STOPPED, THIS UNIT WILL BE EXPLICITLY STOPPED.
- Requires DOES NOT IMPLY all the units in THIS UNIT's list always have to be active when this unit is running.
- As with wants directories, requires directories can contain links and they are treated as if they are in the REQUIRES list.

### Requisite
- A REQUIREMENT dependency
- If the units in the Requisite= list are not ALREADY STARTED, they WILL NOT be started AND this unit will NOT BE STARTED AND FAIL.
- SHOULD be combined with ordering dependency After= to ensure THIS UNIT is not started BEFORE the unit in the Requisite= list.
- Requisite=B in A and RequisiteOf=A in B specify opposite ends of this REQUIREMENT

### BindsTo
- A REQUIREMENT dependency
- Similar to REQUIRES, but this is stronger.
- If the BindsTo unit STOPS (or enters the INACTIVE state), then THIS UNIT STOPS.
- When combined with After= this becomes stronger yet: the bound to unit must be in the ACTIVE state for THIS UNIT to be in the ACTIVE state.
- BindsTo=B in A and BoundBy=A in B specify opposite ends of this REQUIREMENT

### PartOf
- Similar to REQUIRES, but limited to Starting and Stopping of Units
- When units IN the PartOf= list are STOPPED or RESTARTED that action is propagated to THIS UNIT
- A ONE WAY dependency; things that happen to THIS UNIT do not propagate to the units in the PartOf= list.
- PartOf=B in A and ConsistsOf=A in B specify opposite ends of this REQUIREMENT; ConsistsOf= cannot exist by itself.

### Upholds
- Similar to WANTS.
- When THIS UNIT is up (active?), all units in the Upholds list are started when found to be inactive or failed AND no job is queued for them.
- Has a CONTINUOUS effect; this dependency will always act when the condition holds (it is not a one-time thing)
- Upholds=B in A and UpheldBy=A in B specify opposite ends of this REQUIREMENT; UpheldBy= cannot exist by itself.

### Conflicts=
- A NEGATIVE REQUIREMENTS dependency.
- Starting THIS UNIT will STOP the units in the Conflicts= list.
- Starting the units in the Conflicts= list will STOP THIS UNIT.
- Does NOT imply ordering.
- After= or Before= ordering when applied ensures a conflicting unit is STOPPED before the other unit is started.

### Ordering Dependencies
- After, Before
- systemd uses ordering dependencies: (i.e., After= and Before=). 
- After dependencies indicate this UNIT should be started AFTER the UNITS in the After= list.
- Before dependencies indicate this UNIT should be started BEFORE the UNITS in the Before= list.
- Programs and Units may "request" state changes; requests are encapsulated in JOBS and maintained in a queue.
- Ordering dependencies establish when JOBS will be scheduled.
    - JOB:
    - A JOB may succeed or fail.

    On boot systemd activates the target unit `default.target` whose job is to activate on-boot services and other on-boot units by pulling them in via dependencies. 
    USUALLY, the unit name is just an ALIAS (symlink) for either `graphical.target` or `multi-user.target`. See systemd.special(7) for details about these target units.

#### Before
- An ORDERING dependency.
- In foo.service with Before=bar.service, bar.service's start is DELAYED until foo.service has finished starting.
    - foo.service ---> bar.service [ foo before bar, or bar after foo ]
- When two units with a Before= dependency are shutdown, the inverse of the start-up order is applied
- Before= dependencies on device units have NO EFFECT (not supported)

#### After
- An ORDERING dependency
- The LOGICAL INVERSE of Before=
- In foo.service with After=bar.service, when bar.service has finished starting, foo.service ,may start.
    - bar.service ---> foo.service [ bar before foo, or foo after bar ]
- When shutdown the inverse occurs, foo.service ---> bar.service [ foo shutodown, then bar ]
- With ANY ordering dependency (Before= or After=) if one unit is SHUTDOWN, the other is STARTED (SHUTDOWN before STARTED)
- IF no ordering dependency, units can be shutdown or started simultaneously.

### OnFailure
- A list of units that are activated with THIS UNIT enters the FAILED state.

### OnSuccess
- A list of units that are activated when this unit enters the INACTIVE state.

### Triggers=
- Created implicitly between a socket, path, or automount unit and the unit they activate.
    - TriggeredBy= is created implicitly on the triggered unit.
- Default: a unit with the same name is triggered.
- Override: Use Sockets=, Service=, and Unit= settings to OVERRIDE default naming behavior.

### PropagatesReloadTo, ReloadPropagatedFrom
- When a reload request is issued to THIS UNIT, all units in the `PropagatesReloadTo=` list will also be queued to reload.
- When a reload request is issued from a unit containing this unit in its `ReloadPropagatedFrom=` THIS UNIT will be reloaded.

### PropagatesStopTo, StopPropagatedFrom
- When a stop request is issued to THIS UNIT, all units in the `PropagatesStopTo=` list will also be queued to stop.
- When a stop request is issued from a unit containing this unit in its `StopPropagatedFrom=` THIS UNIT will be stopped.

### JoinsNamespaceOf
- Used for units that start processes (service units).
- Lists one or more other units whose network or temporary file namespace to join.

### RequiresMountsFor
- A list of absolute paths.
- Using this list dependencies of `Requires=` and `After=` are automatically added as dependencies for all mount points required to access the specified paths.

### OnFailureJobMode
- Specifies how the units listed in the `OnFailure=` directive will be enqueued.

### IgnoreOnIsolate
- See documentation

### StopWhenUnneeded
- When TRUE, this unit will be stopped when it is no longer USED.
- This unit will automatically be cleaned up when NO OTHER UNIT REQUIRES it.

### RefuseManualStart, RefuseManualStop
- This unit can only be activated or deactivated INDIRECTLY and NOT thru the command line or other explicit methods.

### AllowIsolate
- See documentation.

### DefaultDependencies
- A boolean value
- If yes/true, default dependencies will be CREATED; what is created depends on the unit type.
- It is recommended that this be set to the default or TRUE for almost all units.

### CollectMode
- Relates to how this unit is garbage collected.

### FailureAction, SuccessAction
- The action to take when a UNIT STOPS or enters the FAILED or INACTIVE STATES.

#### FailureActionExitStatus, SuccessActionExitStatus
- Used in conjunction with FailureAction and SuccessAction

### JobTimeoutSec, JobRunningTimeoutSec
- Time limitations on Jobs

#### JobTimeoutAction, JobTimeoutRebootArgument
- Used in conjunction with JobTimeoutSec, etc.

### StartLimitIntervalSec, StartLimitBurst
- Rate limits unit starting

#### StartLimitAction
- Used with StartLimitIntervalSec, etc.

### RebootArgument

### SourcePath
- The path to the configuration file from which this unit file was generated; used for generator tools and not used in normal units.

## Groups
- Processes (executables) systemd spawns are placed in individual Linux control groups named after the unit to which they belong. This forms a private systemd hierarchy. 
    - The systemd hierarchy is used to keep track of processes. 
    - Control group information is maintained in the kernel.
    - Control group information is accessible via the file system hierarchy (sysfs beneath /sys/fs/cgroup/).
    - Control group information can also be accessed using tools such as systemd-cgls(1) or ps(1).
        - `$ ps xawf -eo pid,user,cgroup,args`
        - Useful to list all processes and the systemd units they belong to.

- systemd is compatible with the SysV init system
    - SysV init scripts are read as an alternative (though limited) configuration file format.
    - The SysV /dev/initctl interface is provided, and compatibility implementations of the various SysV client tools are available. 
    - In addition to that, various established Unix functionality such as /etc/fstab or the utmp database are supported.

- systemd has a minimal transaction system: 
    - if a unit is requested to start up or shut down, it will add it and all its dependencies to a temporary transaction. 
    - The temporary transaction will be verified for consistency (what does this entail?). If not consistent, systemd will try to fix it up and remove non-essential jobs from the transaction that might remove the loop (what does loop mean here?).  
    - Effectively this means that before executing a requested operation, systemd will verify that it makes sense, fixing it if possible, and only failing if it really cannot work.

    - [HARD TO TRANSLATE THIS!] Transactions are generated independently of a unit's state at runtime. For example, if a start job is requested on an already started unit, it will still generate a transaction and wake up any inactive dependencies (and cause propagation of other jobs as per the defined relationships). This is because the enqueued job is at the time of execution compared to the target unit's state and is marked successful and complete when both satisfy.  However, this job also pulls in other dependencies due to the defined relationships and thus leads to, in our example, start jobs for any of those inactive units getting queued as well.

# Systemd Mapper Items
Questions about master struct data:
    - What is the reason behind symlinks being both dependencies and aliases (all symlinks are aliases)?
    - Why did you not just make the key the full path string (not the remote path but system path)?
    - There are units that are not SYMLINKS or FILES. Describe how these function?
        - systemd-random-seed.service : not on filesystem??  In a unit file but not a link or file.
    - How are we handling units with Condition= and Assert=
    - systemd.preset
    - Implicit Dependencies for each type.

## Aggregation 
- `.d` dropin directory: all directives in `.conf` files in this directory need to be added to the unit object they are associated with (dropins)
- `.wants` directory: all the links (full path) here need to be added to the Wants= directive in the base unit.
- `.requires` directory: all the links (full path) here need to be added to the Requires= directive in the base unit.

## Dependency Relations
- What is the fundamental meaning of the ( source, target ) relationship?
    - "Depends On"  or, source cannot function unless I attempt or succeed in starting / using the target.

- There are three types of fundamental relationships to distinguish in Systemd:
    - "Depends On" : these are the wants, requires, conflicts, etc.
        - UNDIRECTED EDGES. 
        - HOW these are related will be indicated by COLOR.
        - The edge label will be the directive.
        - So, these DO NOT define any order only some sort of relationship.
    - "Order" : after and before
        - DIRECTED EDGES. 1 --> 2 is equivalent to 1 BEFORE 2 or 2 AFTER 1.
        - Edge color == black.
        - The label SHOULD NOT BE NEEDED, but we can add AFTER and BEFORE to make clear which unit file the directive was in.
    - "Aliased" : symlinks.
        - All aliases in the dependency graph should be identified by full paths.
        - DIRECTED EDGES.  Alias --> Target
        - Edge Color == green
        - The label SHOULD BE ALIAS, although if the color is distinct it shouldn't be needed.
    - As long as the shared names for the edges (id) are different you can build a multigraph.

### Alias Relations
- Aliases: ( Alias [full path], Target )

### Order Relations
- In a, Before=b.service: a.service --> b.service
- In a, After=b.service: b.service --> a.service

### Depends On Relations
- All the directives that provide a LIST OF OTHER UNITS.
- Wants: ( THIS UNIT, { each unit in wants= list } )
    - wants directory ( THIS UNIT, { all links in wants dir for unit } )
    - A WEAK dependency (no arrows; these can be started in parallel)
- Requires: ( THIS UNIT, { each unit in requires= list OR in requires directory } )
    - A STRONG dependency ( maybe a diamond arrow head? )
- Requisite: ( THIS UNIT, { Requisite list } )
    - The STRONGEST dependency ( all in the relation must be running and those in the target position must start first )
- BindsTo: ( THIS UNIT, { BindsTo list } )
    - The STRONGEST dependency: if a bindsto unit stops, this unit stops.
- PartOf: ( { PartOf list }, THIS UNIT )
    - This is like unit object-oriented composition: things that happen to units in the PartOf list happen to THIS UNIT.
    - Use the composition arrow head.
- Upholds: ( THIS UNIT, { Upholds list } )
    - When THIS UNIT up, all in upholds list will be started (has continuous effect)
- Conflicts: ( THIS UNIT, { Conflicts list } )
    - THIS IS A NEGATIVE DEPENDENCY; the items in conflicts list will stop if THIS UNIT is started and vice versa
    - Need a way to IDENIFY NEGATIVE DEPENDENCIES.
    - This should be a double arrow since the effects occur both ways.
- Sockets= : ( { sockets, ... }, THIS UNIT ) 
    - should be directed edge THIS UNIT inherits this set of sockets.
- Service= : in a socket unit, this makes explict which service unit this socket unit matches. The default behavior (I don't think you need to use the Service= directive) is that the service unit will have the same name as the socket unit with the extension replaced.


- OnFailure, OnSuccess
- PropagatesReloadTo, ReloadPropagatedFrom
- PropagatesStopTo, StopPropagatedFrom
- JoinsNamespaceOf
- RequiresMountsFor
