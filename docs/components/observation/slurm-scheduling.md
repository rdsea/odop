# Slurm Scheduling

## Resource binding

CPU management steps:

- Select nodes
- Allocate CPU resources to jobs/step from the set of node selected in Step 1
- Distribute tasks to selected nodes
- Optional: distribute and bind tasks to CPUs

How cgroups plugin can be used in Slurm:

- proctrack/cgroup (for process tracking and management)
- task/cgroup (for constraining resources at step and task level)
- jobacct_gather/cgroup (for gathering statistics)

Slurm cgroup hierarchy:
![images](../img/cg_hierarchy.jpg)

Memory constraints:

- The min memory is 30M
- Slurm set the memory constraints in steps folder, not set in task. When checking memory.limit_in_bytes, it's 9223372036854771712 (PAGE_COUNTER_MAX)
- Mahti and Puhti seems to be diffent as I can't find the memory constraints in Puhti. I tried to create a big variable that should takes more memory than requested but it's not killed
- Weird Slurm cpuset config which may need more investigation: due to the hyper thread being disable
  ```
  b'Cpus_allowed_list:\t64-67\n'
  cpu set 0-3,64-67,128-131,192-195
  b'Cpus_allowed_list:\t0-3\n'
  cpu set 0-3,64-67,128-131,192-195
  ```

Useful command:

- scontrol show job -d $SLURM_JOBID: get information about a job
- cat /proc/cgroups: find which controller is used

```bash
  salloc --nodes=1 --account=project_462000509 --partition=dev-g --time=00:5:00 --exclusive
  srun --ntasks=1 --time=00:10:00 --mem=1G --pty --account=project_462000509 --partition=dev-g bash
```

## Cgroup v1 vs v2

- In v1, the resources contraints is implememeted by multiple cgroup or it can have multiple hierarchy while v2 only has one. Then, the resouces in v1 can be constrainted quite flexbible as each resources use a different hierarchy and process can belongs to multipleone. On the other hand, the resouces in v2 are constrainted top-down or the child process can only use the constrained resources that its parents has.
- Cpu controller is different from Cpuset controller where the first one control the distribution of cpu cycles and the second one constraints the CPU and memory node placement of tasks to only specified resources.

## Problems:

- Don't work with heterogeneous jobs yet
