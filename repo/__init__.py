import importlib
import pkgutil

# Dynamically import all modules in this package
for _, mod_name, _ in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{mod_name}")