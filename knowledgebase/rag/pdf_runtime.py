"""Lazy, sequential access to the optional local PDF converter."""

from pathlib import Path
from threading import Lock

from knowledgebase.schemas import File


class LocalPdfParser:
    def __init__(self, model_dir: Path):
        self.model_dir = model_dir
        self._parser = None
        self._lock = Lock()

    def parse(self, content: bytes) -> File:
        # Share loaded models, but do not run simultaneous conversions on this instance.
        with self._lock:
            if self._parser is None:
                try:
                    from knowledgebase.rag.pdf import PdfParser
                except ImportError as error:
                    raise RuntimeError(
                        "PDF support requires installation with uv sync --extra pdf."
                    ) from error
                self._parser = PdfParser(self.model_dir)
            return self._parser.parse(content)
