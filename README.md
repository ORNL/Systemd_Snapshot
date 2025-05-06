# Systemd Snapshot

# About

This tool creates a systemd snapshot of either locally or remotely hosted file
systems, and records collected data for forensic analysis.  It does this by
parsing all of the unit files contained within the default systemd unit paths
(system paths only) and records all unit file data, implicit dependencies, and
explicit dependencies. Systemd Snapshot will then record all of this info in a
master struct (ms) file, and create both an interactive graph file for use with
cytoscape and a json-formatted dependency map.

The dependency map begins with one unit file (default.target by default) and
maps out all dependencies that are created by that unit.  After dependencies
are recorded, this process repeats for each dependency that is created, until
no more dependencies remain. Both forward and backward dependency relationships
are maintained within the dependency map, but not all unit files in the master
structure will be recorded here since startup processes vary based on targets
(aka runlevels). Systemd Snapshot also allows users to start at an arbitrary
point within the startup process and view dependencies, conditions, etc. that
are required after a specific point during startup, or allow users to see what
will start up when a different runlevel is specified. This is extremely helpful
for debugging systems that fail to boot, in which case your typical `systemctl`
commands are not available.

Optionally, you can create networkx graphs from the information in the master
structure that is built from the Systemd filesystem and files. These graphs are
DIRECTED MULTIGRAPHS: each edge has a source and a target AND there can be
multiple edges between two vertices. The multiple edges are distinct and can be
distinguished by their labels.

Vertices in the graph represent the following information: UNIT files, ALIAS
symbolic links, COMMANDs executed via Systemd, EXECUTABLES within COMMANDS,
LIBRARYs used by EXECUTABLES, and useful STRINGS within EXECUTABLES. The edges
in the graph established NAMED relationships between these Systemd elements.

A Tree can be created from the complete graph by designating a root node from
any UNIT FILE within the systemd structure. This is actually VERY handy for
focusing your analysis efforts.

Graphs can also be trasferred to Cytoscape for visualization via Cytoscape's
REST api and the py4cytoscape library. There is a capability to build a
custom style for your graph -- that will require some additional documentation.

# Installation
---
git clone https://github.com/ornl/systemd_snapshot.git

cd systemd_snapshot

python systemd_snapshot.py -h

## Optional Dependencies (for graphing)
---

- py4cytoscape
- Cytoscape

Install optional graphing dependencies with `pip install py4cytoscape`. There
are 3 python module dependencies for systemd_snapshot.py's graphing
functionality to work. These are networkx, py4cytoscape and pandas, and are
only required if you are going to use the graphing functionality (which I
highly recommend!). The py4cytoscape library depends on networkx and pandas so
you only have to worry about installing py4cytoscape.

To render the graphs we use the open-source tool called Cytoscape, which also
needs to be installed via [Cytoscape's website](https://cytoscape.org/). I would
also highly recommend the yfiles addon for Cytoscape, which organizes all of
your nodes in super clean layouts. Systemd graphs are often quite massive and
these layouts make it far easier to visualize the information. You can get the
yfiles addons from the "cytoscape app store" (for free).

# Use Cases

- Forensic investigations for linux systems
    - Take a snapshot of all the startup services that are started on the
        default target.
    - View startup services that WOULD be started if the system were to boot
        into another runlevel without having to modify the system.
    - Compare current startup services with a baseline snapshot. You can use a
        golden image to create the baseline if you are interested in a system
        currently in production.
- System Hardening
    - Investigate and clean up unused/unwanted services with the dependency map
    - See exactly what commands your startup services are all running
    - See which config files are actually being referenced by startup services
- SBOMs 
    - This capability identifies both components used and not used by a system,
        as well as their dependencies.  This is additional information that is
        not captured in current SBOMs easily.
- Visualize all of the above with the graphing capability and cytoscape!
- System Evolution tracking
    - How does a new firmware version different from a previous version? A
        top-level view may be discernable by taking a diff of the systemd
        architecture.
- Investigate configuration weaknesses or vulnerable startup service commands
    with the master struct
- Rehosting
    - Aid identifying what could be "cut out" of a system to focus emulating
        targeted system behavior.  Decrease overall complexity of rehosting.
    - When a service doesn't start, this tool may help identifyvdependencies
        whose failure to cause the failure of the target service.

# Tutorial / Example

## Getting Help

View Systemd Snapshot's help menu with the `-h`, or `--help` option:

`python3 systemd_snapshot.py -h`

```
python3 systemd_snapshot -h
usage: systemd_snapshot [-h] [-a ACTION] [-o OUTPUT_FILE] [-f] [-p USER_PATH] [-t TARGET_UNIT] [-c COMP_FILE] [-l LOG_LEVEL] [-D DEPTH] [-S STYLE_FILE]

This tool creates a systemd snapshot of either locally or remotely hosted file systems, and records collected data for forensic analysis.

options:
  -h, --help            show this help message and exit
  -a, --action ACTION   Action to take. One of {'master', 'deps', 'graph', 'diff', 'all'}. If action is 'master' or 'all', path option will be used as a pointer to a remotely hosted fs.
                        Otherwise, the path option will be used as a pointer to a master struct snapshot file.
  -o, --output-file OUTPUT_FILE
                        File path to save master struct as. All artifacts will be created in the same directory. (Default: working-directory/snapshot)
  -f, --force-overwrite
                        Allow systemd snapshot to overwrite files if they already exist.
  -p, --path USER_PATH  Use -p followed by a path to set the root path to a remotely hosted filesystem if used with master or all actions, or the path to a ms.json file if used with other
                        actions. Defaults to the locally hosted filesystem.
  -t, --target-unit TARGET_UNIT
                        Use -t followed by a unit name to start the dependency map from the specified unit file instead of default.target
  -c, --comparison-file COMP_FILE
                        Required if the action to take is "diff". Use -c followed by a filename in order to set a comparison file.
  -l, --log-level LOG_LEVEL
                        Change logging level if desired. Options from most to least verbose: [ vDEBUG, DEBUG, INFO, WARNING, ERROR, CRITICAL ]
  -D, --depth DEPTH     the depth of the tree to produce.
  -S, --style-file STYLE_FILE
                        The style to use for the graph; if a path to a file it will be used as a json style specification; otherwise, it is assumed to be a current cytoscape style.

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
                                                                  If you try to compare a master struct file to a dependency map file you will get an error.
```

As you can see, there are a couple of different options available, so let's
check them out.

## Creating a Snapshot File

The first thing to note is that everything is built off of the snapshot file,
a.k.a. the master structure, so let's build that before we do anything else.

`python3 systemd_snapshot.py -a master`

This will create a master structure file, which is a big JSON file that lists
and records descriptions of all Systemd artifacts that were encountered. With
just the `-a`, or `--action` option being used above, Systemd Snapshot will be
looking at the Systemd files on the local filesystem.

If we want to record the Systemd artifacts from a filesystem other than the
one being used by the host system (a remote filesystem), we can use the `-p`
or `--path` option as shown below:

`python3 systemd_snapshot.py -a master -p /path/to/remote/filesystem`

This will parse a remote filesystem (one that the local system isn't using)
and, by default, will save the resultant file in data/snapshot_ms.json. There
are a few important things to note here:
1. You MUST set the path option to the ROOT directory of the remote filesystem,
otherwise Systemd Snapshot will not be able to find any of the Systemd paths it
needs.
2. If the dependency map or graphing options are used instead of the master
struct option, the `-p` option needs to point to the master struct file instead
of the remote filesystem. (shown later)
3. Systemd Snapshot will not overwrite files by default, so if this fails, make
sure that you have renamed the output file or that the file you are trying to
create does not already exist.

If you would like to name the file something more descriptive or applicable to
the fs you are taking a snapshot of, you can use the `-o`, or the
`--output-file`, option:

`python3 systemd_snapshot.py -a master -p remote/fs -o data/my_snap`

This command will create a master struct file from the remote fs, and record
the results in the file "data/my_snap_ms.json". The "_ms" appended to the end
of the file name is done automatically in order to differentiate between the
different types of output files, which is especially important when creating
multiple types of files at once or referencing the master stuct file to build
the other file types.

One final note from this portion of the tutorial is that now that you have the
snapshot of the filesystem in question, everything else is built off of it.
This means that you no longer have to interact with the filesystem to use the
rest of the functionality of Systemd Snapshot. This can be helpful if you are
automating the process of taking snapshots across an enterprise in order to
compare them all to a golden image for threat hunting, or if you are taking a
snapshot of an unpacked firmware image to document it with an SBOM.

In any case, once you have a copy of the master struct file, you no longer need
to interact with the fs it was built from.

## Creating a Dependency Map

Now that we have a master structure file that tells us every unit file that is
on the remote filesystem, along with its contents, we can create a dependency
map. The dependency map shows us the relationships between all of the unit
files during the startup process, and shows what types of dependencies each
unit file has on another. Forward or backward, explicit or implicit, the
dependency map gives you a good idea of what every startup process requires
during the system to bootup process.

To create a dependency map, we have to specify the action `-a`, or `--action`,
argument to be `dep`. We also need to point Systemd Snapshot at the snapshot
that we want to build the dependency map from:

`python3 systemd_snapshot.py -a dep -p data/my_snap_ms.json -o data/my_snap`

This command will create a dependency map from the "my_snap_ms.json" file that
was created in the previous section, and will save it to "my_snap_dm.json".

This will allow you to get a good idea of the dependencies that will actually
be expected during boot. This is important because not all unit files will be
called by default during the boot process, so its important to know what will
and won't be started.

You can also use the `-t`, or `--target-unit` to specify a unit file to start
the dependency mapping from, instead of using "default.target":

`python3 systemd_snapshot.py -a dep -p data/my_snap_ms.json -o data/my_snap -t apache.target`

This command will do the same thing as we did before, except the dependency
map will start from "apache.target" and map all dependencies created from that
point onward.

This is useful if you want to only see what dependencies a specific service
will create during boot, or if you want to see what startup processes will
start if a different target (or runlevel) is specified as the default target.

Keep in mind that Systemd Snapshot will not overwrite a file that already
exists unless you include the `-f` or `--force-overwrite` option, so if you are
creating different dependency maps make sure to name them uniquely or use `-f`!

## Creating a Graph

The graphing function of Systemd Snapshot allows users to use the Cytoscape UI
as a front end to visualize the targeted systemd startup via a graph. This is
also the only feature that requires extra dependencies to be installed to use,
so if you haven't already installed the graphing dependencies go back to the
installation section and install them.

Once you have the dependencies installed, we can create a graph similar to how
we created a dependency map. Make sure you have Cytoscape open, and run:

`python3 systemd_snapshot.py -a graph -p data/my_snap_ms.json`

This creates the graph based on the snapshot that is being pointed to by the
`-p` option. Once the graph is created, it will automatically be ported over to
Cytoscape, and will be viewable once it finishes.

Be warned! There is a LOT going on with Systemd and these graphs will be VERY
large by default. Which is why it is suggested to use the yfiles plugin for
Cytoscape, and if you can use the `-t` option to narrow down your search, do
it.

All of the vertices and edges of the graphs in Cytoscape are actually very
customizable, so if you want to change the color of something feel free! This
can be done via style files. These style files are basically just config files
to tell Cytoscape how to render the graph.

There is a default style file that is kept in the data folder of Systemd
Snapshot. This file can be modified, or if you want to create another style
file you can just point Systemd Snapshot to that style file with the `-S`, or
`--style-file`, option.

## Comparing Results

The last thing we will go over in the tutorial is the ability to compare the
different output files we are creating. This comparison is very useful if we
want to do a threat hunt, or if we want to see the differences between two
different versions of firmware:

`python3 systemd_snapshot.py -a compare -p data/snap1_ms.json -c data/snap2_ms.json -o data/comp`

This command will compare the "snap1_ms.json" and "snap2_ms.json" files and
save the differences to "data/comp_df.json". The comparison file will highlight
all of the differences between the two snapshots, including libraries,
binaries, interesting file paths that are referenced, config files, and even
differences between which command line arguments are used to start up a service
during the boot process.

Note that you can compare either master structure files or dependency maps, we
can only compare the same types of files. No comparing a master structure file
to a dependency map file.

As a last word, I hope this tool is helpful! If you have any ideas on how to
improve it, I would be happy to hear them!