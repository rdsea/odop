import fcntl

import yaml


class Status:
    def __init__(self, path):
        """Dictionary like interface for the status file."""
        self.path = path

    def reset(self):
        with open(self.path, "w") as f:
            yaml.dump({}, f)

    def load(self):
        """Load the status file and return the full dictionary."""
        try:
            with open(self.path) as f:
                status = yaml.safe_load(f)
            return status
        except FileNotFoundError:
            return {}

    def get(self, key, default=None):
        """Get a key from the status file with a default value."""
        status = self.load()
        return status.get(key, default)

    def __getitem__(self, key):
        """Get a key from the status file."""
        status = self.load()
        return status[key]

    def __setitem__(self, key, value):
        """Set a key in the status file.

        Each runtime component has it's own top level key in the status
        file. We use locks to ensure that only one process writes at a time.
        But we update an entire top level key at a time. Two processes
        should not want to update subkeys of the same top level key.
        """
        if type(key) is list:
            self.set_nested(key, value)
        with open(self.path, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            status = yaml.safe_load(f)
            status[key] = value
            f.seek(0)
            yaml.dump(status, f)
            fcntl.flock(f, fcntl.LOCK_UN)

    def set_nested(self, keys, value):
        """Set a nested key in the status file."""
        with open(self.path, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            status = yaml.safe_load(f)
            current = status
            for key in keys[:-1]:
                current = current.setdefault(key, {})
            current[keys[-1]] = value
            f.seek(0)
            yaml.dump(status, f)
            fcntl.flock(f, fcntl.LOCK_UN)
