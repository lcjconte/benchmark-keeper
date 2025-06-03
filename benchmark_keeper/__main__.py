"""Entry point"""

import benchmark_keeper.cmd
from benchmark_keeper import app, TRACKED_DIR, get_path
import importlib.util
import sys


def main():
    # Import custom code

    custom_code_path = get_path().joinpath(TRACKED_DIR, "custom.py")
    if custom_code_path.exists():
        try:
            sys.dont_write_bytecode = True
            spec = importlib.util.spec_from_file_location("custom", custom_code_path)
            foo = importlib.util.module_from_spec(spec)  # type: ignore
            spec.loader.exec_module(foo)  # type: ignore
        except Exception as e:
            raise RuntimeError("Error loading custom code")

    # Run app
    app()
