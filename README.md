# Renovo: Python Hot Module Replacement

Renovo is a Python library that allows for hot module replacement, enabling you to reload modules and their dependencies dynamically during runtime. This is useful for development and debugging purposes.

The idea of hot module replacement is commonly found in frontend dev tooling, such as [webpack](https://webpack.js.org/concepts/hot-module-replacement/).
However, nothing reliable exists for Python. Other libraries, tools, and frameworks like Django, for example, restart the entire process.
This can be painfully slow in larger code bases. Renovo dynamically replaces all references to the updated module with the new version in milliseconds.

## Highlights

- 🔥 **Blazing Fast Reloads**: Reload modules and their dependencies in **milliseconds**.
- 🛠️ **Customizable**: Add custom error handlers and hooks for pre and post reload actions.
- 🐍 **Pythonic**: Seamlessly integrates with your existing Python codebase.

## Installation

`pip install renovo`

## Usage

HMR needs to be the first thing injected into the Python process because it wraps `builtins.__import__` to add dependency tracking.
`builtins.__hmr__` will be made available to the underlying Python code for further customization if you so desire.
You should invoke this module as a script for the best results.

### Invoke HMR Module as a Script

Invoke any Python script as you normally would, just with the `-m renovo` option to turn on HMR.

```console
$ python -m renovo <script> [arguments...]
```

This will make the HMR module available in your codebase as `builtins.__hmr__`

```python
# foo.py
import builtins
if getattr(builtins, "__hmr__", None):
    print("foo.py ran with HMR on")
else:
    print("foo.py ran with HMR off")
```

```console
$ python -m renovo foo.py
foo.py ran with HMR on

$ python foo.py
foo.py ran with HMR off
```

### Reloading Your First Module

```python
# foo.py
def baz():
  print("Second")

def bar():
  print("First")
  baz()
```

```python
# main.py
import builtins
from foo import bar

bar()
# Prints:
# First
# Second
input("Edit foo.py, comment out the call to baz() in the bar() function. Hit enter when you've saved the changes to foo.py")
builtins.___hmr__.reload_module("foo")
bar()
# Prints:
# First
```

```python
# foo.py -- after editing
def baz():
  print("Second")

def bar():
  print("First")
  # baz()
```

Notice how calling `foo.bar()` after editing `foo.py` with `builtins.___hmr__.reload_module("foo")` now only prints "First" instead of "First" and "Second"
because we commented out `baz()`. The module `foo` and its function `bar` have their references updated to the new function.

`builtins.__hmr__.reload_module` has the exact same interface as [`importlib.reload_module`](https://docs.python.org/3/library/importlib.html#importlib.import_module).

The major difference between `builtins.__hmr__.reload_module` and `importlib.reload_module` is HMR tracks dependencies and updates those modules that depend on `foo.py`.
`importlib` does not track dependencies which means all files that import `foo.py` will reference the old, outdatted code before our edit.

Note: Django's runserver will not function properly because of their own conflicting reloading logic that restarts the process.

### Reloading on File Changes

One of the advantages of HMR, as you might have already guessed, is reloading a module whenever its file changes.

This example assumes you are using [watchdog](https://pypi.org/project/watchdog/) to monitor for file changes.

```python
# watch.py
import builtins
import os
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

class ModuleReloader(FileSystemEventHandler):
  def __init__(self, module_name, module_path):
    self.module_name = module_name
    self.module_path = module_path
    super().__init__()

  def on_modified(self, event):
    if event.src_path == self.module_path:
      print(f"🔄 Detected changes in {self.module_name}, reloading...")
      try:
        reloaded, duration = builtins.__hmr__.reload_module(self.module_name)
        print(f"✅ Reloaded {len(reloaded)} module(s) in {duration:.2f}ms")
      except Exception as e:
        print(f"❌ Failed to reload {self.module_name}: {e}")

if __name__ == "__main__":
  import foo  # Import the module we want to watch

  # Get the full path to the module file
  module_path = os.path.abspath(foo.__file__)
  module_name = "foo"

  # Setup watchdog
  event_handler = ModuleReloader(module_name, module_path)
  observer = Observer()
  observer.schedule(event_handler, os.path.dirname(module_path), recursive=False)
  observer.start()

  try:
    print(f"👀 Watching for changes in {module_name} ({module_path})")
    while True:
      time.sleep(1)
  except KeyboardInterrupt:
    observer.stop()

  observer.join()
```

With this script, you can automatically reload the `foo` module whenever its file changes:

```console
$ python -m renovo watch.py
👀 Watching for changes in foo (/path/to/foo.py)
🔄 Detected changes in foo, reloading...
✅ Reloaded 1 module(s) in 2.24ms
```

## Hooks

Hooks can be used to further customize the behaviour of your code around the import system:

- Before reloading `add_pre_reload_hook`
- After reloading `add_post_reload_hook`
- On import error, E.g. a syntax error in your module: `add_error_handler`

```python
import builtins

# Add custom error handler
def error_handler(module_name: str, error: Exception) -> None:
    print(f"Error reloading {module_name}: {error}")

builtins.__hmr__.add_error_handler(error_handler)

# Add pre-reload hook
def pre_reload_hook(module_name: str) -> None:
    print(f"About to reload {module_name}")

builtins.__hmr__.add_pre_reload_hook(pre_reload_hook)

# Add post-reload hook
def post_reload_hook(module_name: str) -> None:
    print(f"Finished reloading {module_name}")

builtins.__hmr__.add_post_reload_hook(post_reload_hook)

# Reload a module
reloaded_modules, total_time = builtins.__hmr__.reload_module("my_module")
print(f"Reloaded modules: {reloaded_modules}")
print(f"Total reload time: {total_time}ms")
```
