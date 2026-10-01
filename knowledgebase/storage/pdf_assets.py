"""Original PDF assets addressed only by generated file identities."""

from pathlib import Path


class PdfAssets:
    def __init__(self, data_dir: Path):
        self.directory = data_dir.resolve() / "originals"

    def path(self, file_id: str) -> Path:
        return self.directory / f"{file_id}.pdf"

    def save(self, file_id: str, content: bytes) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path(file_id).write_bytes(content)

    def delete(self, file_id: str) -> None:
        self.path(file_id).unlink(missing_ok=True)
