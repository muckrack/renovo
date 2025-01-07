# Python Hot Module Replacement
`muckrack-python-hmr` is a Python library that allows for hot module replacement, enabling you to reload modules and their dependencies dynamically during runtime. This is useful for development and debugging purposes.

The idea of hot module replacement is commonly found in frontend dev tooling, such as [webpack](https://webpack.js.org/concepts/hot-module-replacement/).
However, nothing reliable exists for Python. Other libraries, tools, and frameworks like Django, for example, restart the entire process.
This can be painfully slow in larger code bases. `muckrack-python-hmr` dynamically replaces all references to the updated module with the new version in milliseconds.

## Highlights
- 🔥 **Blazing Fast Reloads**: Reload modules and their dependencies in **milliseconds**.
- 🔄 **Dynamic Updates**: Automatically updates all references to the reloaded modules no matter where or how you imported. E.g. lazy import.
- 🛠️ **Customizable**: Add custom error handlers and hooks for pre and post reload actions.
- 🐍 **Pythonic**: Seamlessly integrates with your existing Python codebase.
- 🧩 **Dependency Tracking**: Tracks module dependencies to ensure all related modules are reloaded.

## Usage

HMR needs to be the first thing injected into the Python process because it wraps `builtins.__import__` to add dependency tracking.
`builtins.__hmr__` will be made available to the underlying Python code for further customization if you so desire.
You should invoke this module as a script for the best results.

Assuming you have the auto reload test runner:
```sh
python -m muckrack.hmr <script> [arguments...]
```

You can run any Python code the same way you normally would. However, Django's runserver will not function properly because of their own reloading logic.

## API
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
