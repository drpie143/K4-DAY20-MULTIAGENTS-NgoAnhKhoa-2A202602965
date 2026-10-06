---
name: enforce-relative-file-paths
description: Use when specifying file paths in code to ensure they are relative and not absolute.
---
# Title

1. Always use relative paths for file operations (e.g., reading/writing files).
2. Avoid starting file paths with '/' or drive letters (e.g., C:\).
3. Use the current working directory as the base for relative paths.
4. Verify that all file paths in the code are relative before execution.
5. Test file operations to ensure they work correctly with the specified relative paths.
6. Document the expected directory structure in the project README for clarity.
7. Use `os.path.join()` to construct file paths dynamically and avoid hardcoding.
8. Check for any hardcoded paths in configuration files and update them to be relative.
