import importlib
import sys

import pytest


@pytest.fixture
def fresh_import():
    def _fresh_import(module_name: str, *extra_prefixes: str):
        prefixes = (module_name, *extra_prefixes)
        for loaded_name in list(sys.modules):
            if any(
                loaded_name == prefix or loaded_name.startswith(f"{prefix}.")
                for prefix in prefixes
            ):
                sys.modules.pop(loaded_name, None)
        return importlib.import_module(module_name)

    return _fresh_import
