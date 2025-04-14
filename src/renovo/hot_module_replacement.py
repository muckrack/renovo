import builtins
import fnmatch
import importlib
import logging
import timeit
from collections.abc import Callable
from typing import Any

from renovo.dependency_tracker import DependencyTracker


class HotModuleReplacement:
    def __init__(
        self,
        includes: list[str] | None = None,
        excludes: list[str] | None = None,
        error_handlers: list[Callable[[str, Exception], None]] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.dependency_graph = DependencyTracker()
        self.max_recursion_depth = 1_000
        self.original_import = builtins.__import__
        self.includes = includes or []
        self.excludes = excludes or []
        self.error_handlers = error_handlers or []
        self.pre_reload_hooks: list[Callable[[str], None]] = []
        self.post_reload_hooks: list[Callable[[str], None]] = []
        self.logger = logger or logging.getLogger(__name__)

        def tracking_import(
            name: str,
            globals: dict[str, Any] | None = None,
            locals: dict[str, Any] | None = None,
            fromlist: tuple[str, ...] = (),
            level: int = 0,
        ) -> Any:
            module = self.original_import(name, globals, locals, fromlist, level)
            importer_module = globals.get("__name__", "__main__") if globals else "__main__"
            self.dependency_graph.add_dependency(importer_module, name)

            return module

        # TODO: There should be a way to use import hooks instead of replacing the built-in __import__ function
        # However, we lose too much information in Finders and Loaders to build the dependency graph
        builtins.__import__ = tracking_import

    def add_error_handler(self, handler: Callable[[str, Exception], None]) -> None:
        self.error_handlers.append(handler)

    def add_pre_reload_hook(self, hook: Callable[[str], None]) -> None:
        self.pre_reload_hooks.append(hook)

    def add_post_reload_hook(self, hook: Callable[[str], None]) -> None:
        self.post_reload_hooks.append(hook)

    def get_dependencies(self, module: str) -> set[str]:
        return self.dependency_graph.get_dependents(module)

    def reload_module(self, root_module_name: str) -> tuple[dict[str, float], float]:
        reloaded_modules: dict[str, float] = {}
        total_time = 0.0

        def _reload(module_name: str, current_depth=1) -> None:
            nonlocal total_time
            if current_depth > self.max_recursion_depth:
                raise RecursionError(
                    f"Max recursion depth reached for module {root_module_name} at depth {current_depth}"
                )
            if not self._is_included(module_name) or self._is_excluded(module_name):
                self.logger.debug(f"Skipping module: {module_name}")
                return

            self._run_hooks(self.pre_reload_hooks, module_name)

            try:
                if module_name in reloaded_modules:
                    return
                self.logger.debug(f"Reloading module: {module_name}")
                elapsed_time = self._reload_single_module(module_name)

                # Skip modules that returned -1.0 elapsed time (indicating reload was skipped)
                if elapsed_time < 0:
                    self.logger.debug(f"Module {module_name} reload was skipped")
                    return

                reloaded_modules[module_name] = elapsed_time
                total_time += elapsed_time
                for dependency in self.get_dependencies(module_name):
                    _reload(dependency, current_depth + 1)
            except Exception as e:
                self.logger.error(f"Error reloading module {module_name}: {e}")
                self._handle_error(module_name, e)

            self._run_hooks(self.post_reload_hooks, module_name)

        _reload(root_module_name)
        return reloaded_modules, total_time

    def _reload_single_module(self, module_name: str) -> float:
        start_time = timeit.default_timer()
        # Skip reloading __main__ as it can't be properly reloaded
        if module_name == "__main__":
            self.logger.debug("Skipping reload of __main__ module")
            return -1.0
        try:
            module = importlib.import_module(module_name)
            importlib.reload(module)
            return timeit.default_timer() - start_time
        except ModuleNotFoundError as e:
            self.logger.warning(f"Module {module_name} not found: {str(e)}")
            return -1.0

    def _run_hooks(self, hooks: list[Callable[[str], None]], module_name: str) -> None:
        for hook in hooks:
            hook(module_name)

    def _handle_error(self, module_name: str, error: Exception) -> None:
        for handler in self.error_handlers:
            handler(module_name, error)

    def _is_included(self, module_name: str) -> bool:
        return not self.includes or any(fnmatch.fnmatch(module_name, pattern) for pattern in self.includes)

    def _is_excluded(self, module_name: str) -> bool:
        return any(fnmatch.fnmatch(module_name, pattern) for pattern in self.excludes)
