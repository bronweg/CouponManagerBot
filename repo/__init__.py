import importlib
import json
import os
import pkgutil


COUPON_REPO_TYPE = os.getenv("COUPON_REPO_TYPE", "sqlite")
COUPON_REPO_CONFIG = json.loads(os.getenv("COUPON_REPO_CONFIG", "{}"))



# Dynamically import all modules in this package
for _, mod_name, _ in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{mod_name}")