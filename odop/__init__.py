import pkgutil
import importlib

# import all modules in the current folder
for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    globals()[module_name] = importlib.import_module("." + module_name, __name__)
