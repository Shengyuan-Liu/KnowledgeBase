# Important Notes

- Use English for all project documentation and text content, including UI text, prompts, comments, examples, and commit messages. Do not add Chinese text to the project.
- After completing each change, create a corresponding Git commit so that the change can be tracked and rolled back later.
- For code changes, write or update the relevant tests and ensure that all applicable tests and verification checks pass before delivery. For documentation-only changes, review the content and check links and formatting; automated tests are not required.

# Learning and Code Ownership

- The user intends to write most of the project's Python backend and MLE / AI Engineer code by hand. By default, Codex should explain each proposed code file's purpose, the responsibilities of its functions, and the underlying concepts, reasoning, and implementation guidance so the user can write the code.
- Only write or modify Python implementation code when the user explicitly asks Codex to do so. A request for an explanation, design, or guidance does not authorize implementation. Keep any authorized implementation within the requested scope.
- Exceptions: Codex may directly implement Python code explicitly marked with `# TODO` or `#TODO`, and may directly write or modify code in any language other than Python as needed for the user's task. A TODO marker authorizes only the associated unfinished code, not unrelated Python changes.
