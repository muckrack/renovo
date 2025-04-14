import queue
import threading
from collections import defaultdict
from threading import Lock


class DependencyTracker:
    def __init__(self) -> None:
        self.lock = Lock()
        self.reverse_dependencies: defaultdict[str, set[str]] = defaultdict(set)
        self.dependency_queue = queue.Queue()
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._running = True
        self._worker_thread.start()

    def add_dependency(self, importer_module: str, dependency: str) -> None:
        # Just put the dependency in the queue and return immediately
        self.dependency_queue.put_nowait((importer_module, dependency))

    def _process_queue(self) -> None:
        while self._running:
            try:
                importer_module, dependency = self.dependency_queue.get(timeout=0.5)
                with self.lock:
                    self.reverse_dependencies[dependency].add(importer_module)
                self.dependency_queue.task_done()
            except queue.Empty:
                continue

    def shutdown(self) -> None:
        self._running = False
        if self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)

    def get_dependents(self, module_name: str) -> set[str]:
        # Process all pending items in queue before returning results
        self.dependency_queue.join()
        return self.reverse_dependencies[module_name]
