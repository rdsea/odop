import os

from odop.common import create_logger

logger = create_logger("engine")


def get_cgroup_path():
    """Get the path to the cgroup folder"""

    try:
        with open("/proc/self/cgroup") as f:
            lines = f.readlines()
        for line in lines:
            parts = line.split(":")
            if len(parts) > 2:
                return os.path.join("/sys/fs/cgroup", parts[2].strip())
    except Exception:
        logger.info("Could not read cgroup file")
    return None


def find_cpuset_file(cgroup_path):
    """Find the cpuset.cpus.effective file in the cgroup folder or a parent folder"""
    cgroup_path = cgroup_path.strip("/")
    current_path = os.path.join("/sys/fs/cgroup", cgroup_path)
    while current_path:
        cpuset_file = os.path.join(current_path, "cpuset.cpus.effective")
        if os.path.exists(cpuset_file):
            return cpuset_file
        # Move to the parent folder
        current_path = os.path.dirname(current_path)
        if current_path == "/sys/fs/" or current_path == "/":
            break
    return None


def get_cpu_group():
    """Get the list of allowed cpus in the current cgroup"""

    cgroup_path = get_cgroup_path()
    if cgroup_path is None:
        return None

    cpuset_file = find_cpuset_file(cgroup_path)
    if cpuset_file is None:
        return None

    try:
        with open(cpuset_file) as f:
            cpu_list = f.read().strip()
            cpus = []
            for part in cpu_list.split(","):
                if "-" in part:
                    start, end = part.split("-")
                    cpus.extend(range(int(start), int(end) + 1))
                else:
                    cpus.append(int(part))
            return cpus
    except OSError:
        logger.info("Could not read cpuset file")
    except Exception:
        logger.info("Could not parse cpuset file")
    return None
