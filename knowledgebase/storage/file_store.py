"""Save, read, and delete original UTF-8 text files."""

from pathlib import Path


class FileStore:
    """Store text under application-generated file IDs in an upload directory."""

    def __init__(self, upload_dir: str | Path) -> None:
        self._upload_dir = Path(upload_dir)
        self._upload_dir.mkdir(parents=True, exist_ok=True)

    def save_text(self, file_id: str, text: str) -> None:
        """Save text as UTF-8, replacing any existing file with the same ID."""
        path = self._upload_dir / f"{file_id}.txt"
        path.write_text(text, encoding="utf-8", newline="")

    def read_text(self, file_id: str) -> str:
        """Read original text without normalizing line endings."""
        path = self._upload_dir / f"{file_id}.txt"
        return path.read_text(encoding="utf-8", newline="")

    def delete_text(self, file_id: str) -> None:
        """Delete the file; filesystem errors propagate to the caller."""
        path = self._upload_dir / f"{file_id}.txt"
        path.unlink()
