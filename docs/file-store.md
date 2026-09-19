# Original Text Storage

This utility is available for optional original-file retention. The current
[ingestion workflow](file-ingestion.md) stores text in SQLite chunks and does not
write a separate TXT copy.

`knowledgebase/storage/file_store.py` provides `FileStore` for retaining original
TXT content. Construct it with an upload directory; the directory is created if
needed. Files use application-generated IDs and are named `{file_id}.txt`.
The caller supplies those IDs, not user-provided filenames or paths.

- `save_text(file_id, text)` writes UTF-8 text, replacing a file with the same ID.
- `read_text(file_id)` returns the text with whitespace and line endings preserved.
- `delete_text(file_id)` removes that file.

Filesystem exceptions propagate directly, including `FileNotFoundError` when
reading or deleting a missing file. Upload validation, file ID generation,
database records, and ingestion status belong to the file service.

## Example

Run this from the repository root with `uv run python`:

```python
from knowledgebase.storage.file_store import FileStore

store = FileStore("data/uploads")
store.save_text("example-file", "First line.\r\nSecond line.\n")
text = store.read_text("example-file")
print(repr(text))
store.delete_text("example-file")
```

`data/` is ignored by Git. Tests use temporary directories to check UTF-8 bytes,
exact line endings, replacement, reading through a new store, and deletion.
