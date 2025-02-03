import ast
import builtins
import importlib.util
import os
import sys
import traceback
import uuid

import cloudpickle

from odop.common import create_logger

"""
We detect files with an odop decorator if the decorator is at the top level and
the name has not been overwritten. This means any odop decorator is contains a line
that starts with "@odop.task(".

If a python file with a decorator is found, we then find the end of the next block
after the decorator. This is the end of the task definition. We construct a module
that ends after the last task definition and import it. This way the any potentially
expensive code below the
"""

logger = create_logger("scanner")


class OdopTaskScanner:
    def __init__(self, path):
        """Scanner for odop tasks. Checks whether the odop task decorator is
        called in a module. If it is, runs the module to create the task object.
        """
        self.path = path
        self.original_import = builtins.__import__

        self.odop_imported = False
        self.decorator_called = False
        self.last_decorator_line = 0

    def find_tasks(self):
        """Inspect the module file to find if it contains tasks and load them."""
        if not self.path.endswith(".py"):
            return

        with open(self.path) as f:
            text_content = f.read()
        if "@odop.task" not in text_content:
            return

        original_stdout = sys.stdout
        original_stderr = sys.stderr

        try:
            tree = ast.parse(text_content, filename=self.path)
            # Check for the odop decorator
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call):
                            decorator = decorator.func
                        if not isinstance(decorator, ast.Attribute):
                            continue
                        if not isinstance(decorator.value, ast.Name):
                            continue
                        if decorator.value.id == "odop" and decorator.attr == "task":
                            self.decorator_called = True
                            self.last_decorator_line = node.end_lineno

        except Exception as e:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            logger.info(f"Error encountered while scanning {self.path}")
            traceback.print_exc()
            raise e

        finally:
            # Restore stdout and stderr
            # sys.stdout.close()
            # sys.stderr.close()
            sys.stdout = original_stdout
            sys.stderr = original_stderr

    def import_tasks(self):
        """Import the tasks from the module if the decorator is called."""
        self.find_tasks()
        if not self.decorator_called:
            return

        # read the file up to the last decorator line
        with open(self.path) as f:
            lines = f.readlines()
        lines = lines[: self.last_decorator_line]

        # construct a module from the lines
        module_name = os.path.basename(self.path).replace(".py", "")
        module_name = f"{module_name}_{uuid.uuid4()!s}"
        spec = importlib.util.spec_from_file_location(module_name, self.path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        cloudpickle.register_pickle_by_value(module)

        module_code = "".join(lines)
        exec(module_code, module.__dict__)


if __name__ == "__main__":
    path = sys.argv[1]

    scanner = OdopTaskScanner(path)
    scanner.find_tasks()
    scanner.import_tasks()

    print(scanner.decorator_called, scanner.last_decorator_line)
