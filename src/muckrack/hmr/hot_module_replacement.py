import builtins
import fnmatch
import importlib
import logging
import timeit
from collections import defaultdict
from collections.abc import Callable
from threading import Lock
from typing import Any


class DependencyTracker:
    def __init__(self) -> None:
        self.lock = Lock()
        self.dependents: defaultdict[str, list[str]] = defaultdict(list)

    def add_dependent(self, fullname: str, dependent: str) -> None:
        if dependent not in self.dependents[fullname]:
            with self.lock:
                self.dependents[fullname].append(dependent)

    def get_dependents(self, fullname: str) -> list[str]:
        return self.dependents[fullname]


class HotModuleReplacement:
    def __init__(
        self,
        includes: list[str] | None = None,
        excludes: list[str] | None = None,
        error_handlers: list[Callable[[str, Exception], None]] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.dependency_graph = DependencyTracker()
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
            importer_module = globals.get("__name__", "__main__") if globals else "__main__"
            self.dependency_graph.add_dependent(name, importer_module)
            return self.original_import(name, globals, locals, fromlist, level)

        # TODO: There should be a way to use import hooks instead of replacing the built-in __import__ function
        # However, we lose too much information in Finders and Loaders to build the dependency graph
        builtins.__import__ = tracking_import

    def add_error_handler(self, handler: Callable[[str, Exception], None]) -> None:
        self.error_handlers.append(handler)

    def add_pre_reload_hook(self, hook: Callable[[str], None]) -> None:
        self.pre_reload_hooks.append(hook)

    def add_post_reload_hook(self, hook: Callable[[str], None]) -> None:
        self.post_reload_hooks.append(hook)

    def get_dependencies(self, module: str) -> list[str]:
        return self.dependency_graph.get_dependents(module)

    def reload_module(self, module_name: str) -> tuple[list[dict[str, float]], float]:
        reloaded_modules = []
        total_time = 0.0

        def _reload(module_name: str) -> None:
            nonlocal total_time
            if not self._is_included(module_name) or self._is_excluded(module_name):
                self.logger.debug(f"Skipping module: {module_name}")
                return

            self._run_hooks(self.pre_reload_hooks, module_name)

            try:
                self.logger.debug(f"Reloading module: {module_name}")
                elapsed_time = self._reload_single_module(module_name)
                reloaded_modules.append({module_name: elapsed_time})
                total_time += elapsed_time
                for dependency in self.get_dependencies(module_name):
                    _reload(dependency)
            except Exception as e:
                self.logger.error(f"Error reloading module {module_name}: {e}")
                self._handle_error(module_name, e)

            self._run_hooks(self.post_reload_hooks, module_name)

        _reload(module_name)
        return reloaded_modules, total_time

    def _reload_single_module(self, module_name: str) -> float:
        start_time = timeit.default_timer()
        module = importlib.import_module(module_name)
        importlib.reload(module)
        return timeit.default_timer() - start_time

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
