# Systemd Snapshot

### Cytrics
---
Why? There are four areas that this tool aids:

- Rehosting
    - Aid identifying what could be "cut out" of a system to focus emulating targeted system behavior.  Decrease overall complexity of rehosting.
        - When a service doesn't start, this tool may help identify dependencies whose failure to cause the failure of the target service.
- System Evolution
    - How does a new firmware version different from a previous version.  A top-level view may be discernable by taking a diff of the systemd architecture.
- SBOMs 
    - This capability identifies both components used (and not used) by a system, but also their dependencies.  This is additional information that is not captured in current SBOMs easily.
- Weakness and Vulnerability Identification
    - (maybe) bug propagation : if there is a bug in one component, what else could be effected.
    - (maybe) identify which components communicate with one another.

Our initial goal with this capability was for rehosting.

### IT Admins / Defensive Cybersecurity
---
- Forensic investigations for linux systems
    - Take a snapshot of all the startup services that are started on the default runlevel
    - View startup services that WOULD be started if the system were to boot into another runlevel without having to modify the system
    - Compare current startup services with a baseline snapshot.  You can use a golden image to create the baseline if you are interested in a system currently in production!
- System Hardening
    - Investigate and clean up unused or unwanted services with the dependency map (dm.json)
    - See exactly what commands your startup services are all running with the master struct (ms.json)
    - See which config files are actually being referenced by startup services with the master struct (ms.json)
- Visualize anything listed above with Systemd Snapshot's graphing capability and cytoscape! (graph.json?)

### Vulnerability Research / Offensive Cybersecurity
---
- System enumeration
    - No installation necessary! Just move scripts to target system and as long as python 3 is installed you can create a master struct (ms.json)
    - Enumerate startup services without touching systemctl
    - Enumerate POTENTIAL startup service that aren't yet enabled or started
- Vulnerability research
    - See above for potential implications
    - Investigate configuration weaknesses or vulnerable startup service commands with the master struct (ms.json)

# Status

# Installation

# Use
