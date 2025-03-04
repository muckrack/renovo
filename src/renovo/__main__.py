import builtins
import logging
import runpy
import sys

from .hot_module_replacement import HotModuleReplacement

logger = logging.getLogger("HotModuleReplacement")


def main():
    logger.debug("Loader is running...")
    if len(sys.argv) < 2:
        print("Usage: python -m renovo <script> [arguments...]")
        sys.exit(1)
    hmr = HotModuleReplacement()
    builtins.__hmr__ = hmr  # type: ignore
    logger.debug("Hot Module Replacement initialized and injected into builtins.")

    # Extract the target script/module and arguments
    script = sys.argv[1]
    args = sys.argv[2:]

    # Update sys.argv to pass the arguments to the target script
    sys.argv = [script] + args

    # Execute the script's __main__ block
    try:
        runpy.run_path(script, run_name="__main__")
    except FileNotFoundError:
        print(f"Error: Script '{script}' not found.")
        sys.exit(1)


if __name__ == "__main__":
    main()
