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

## Quick Start

HMR needs to be the first thing injected into the Python process because it currently monkey-patches `builtins.__import__` to track module dependencies. While this approach works reliably, future versions aim to leverage Python's importlib machinery for a more standard implementation.

Run your script with the `-m renovo` option to enable hot module replacement:

```console
$ python -m renovo <script> [arguments...]
```

This makes `builtins.__hmr__` available in your code. Here's a simple example:

```python
# foo.py
def baz():
    print("Second")

def bar():
    print("First")
    baz()
```

Now we'll create a main file that uses this module and demonstrates HMR in action:

```python
# main.py
import builtins
import foo  # Import the module as a whole for best HMR experience

# Initial function call
print("Initial call:")
foo.bar()  # Outputs: "First" followed by "Second"

# Now let's simulate making a change to foo.py
# In a real scenario, you'd edit foo.py in your editor and save the file
input("Press Enter after you've modified foo.py...")

# Reload the modified module
reloaded_modules, duration = builtins.__hmr__.reload_module("foo")
print(f"Reloaded {len(reloaded_modules)} module(s) in {duration:.2f}ms")

# Call the function again to see the changes
print("\nAfter modifying foo.py:")
foo.bar()  # The behavior will reflect your changes
```

For example, if you modify `foo.py` to look like this:

```python
# foo.py (after modification)
def baz():
    print("Second - MODIFIED!")

def bar():
    print("First - MODIFIED!")
    baz()
```

When you run the main script and press Enter after modifying foo.py, the output will show:

```console
$ python -m renovo main.py
Initial call:
First
Second

Press Enter after you've modified foo.py...
Reloaded 1 module(s) in 3.45ms

After modifying foo.py:
First - MODIFIED!
Second - MODIFIED!
```

The key difference between `builtins.__hmr__.reload_module` and Python's built-in `importlib.reload` is that HMR tracks dependencies. When you reload a module with HMR, it also updates all modules that depend on it, ensuring consistent behavior throughout your application.

## Detailed Usage

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

## Advanced Features

### Hooks

Hooks can be used to further customize the behavior of your code around the import system:

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

## Limitations and Gotchas

### The `__main__` Module and Direct Imports

The `__main__` module (your entry script) is special in Python and has unique behavior with hot module replacement:

1. The `__main__` module itself cannot be reloaded
2. Objects directly imported into `__main__` using `from module import object` will not be updated when their source module is reloaded

Here's what happens in a typical scenario:

```python
# in main.py (running as __main__)
from foo import bar  # Direct import creates a reference that won't be updated

# Initial call works as expected
print("Initial call:")
bar()  # Outputs original behavior

input("Press Enter after you've modified foo.py...")
reloaded_modules, duration = builtins.__hmr__.reload_module("foo")
print(f"Reloaded {len(reloaded_modules)} module(s) in {duration:.2f}ms")

print("\nAfter modifying foo.py:")
bar()  # Still uses the old version of bar()

# But this works correctly:
print("\nImporting foo as a module:")
import foo
foo.bar()  # This will use the newly reloaded version
```

Example output

```console
$ python -m renovo main.py
Initial call:
First
Second
Press Enter after you've modified foo.py...
Reloaded 1 module(s) in 3.45ms

After modifying foo.py:
First             # This line is from the old bar() function
Second - MODIFIED! # This line shows updated baz() being called by bar()

Importing foo as a module:
First - MODIFIED!
Second - MODIFIED!
```

This partial update happens because:

- The old `bar()` function in `__main__`'s namespace stays intact (prints "First")
- When that old function calls `baz()`, it looks it up in the module's namespace, which has been updated
- So you see the old `bar()` output but the updated `baz()` output

For the most reliable HMR experience:

1. Use fully qualified imports in your main script (`import foo` instead of `from foo import bar`)
2. Access objects through their module (`foo.bar()`)
3. If you need direct imports, re-import after reloading:
   ```python
   builtins.__hmr__.reload_module("foo")
   from foo import bar  # Get the updated reference
   ```

Regular modules (not `__main__`) don't have this limitation. When Renovo reloads a module, all other modules that import it will automatically use the updated code.
