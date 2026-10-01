"""Per-call limits for the opt-in planned request path."""

from collections.abc import Callable
from dataclasses import dataclass
import json

import tiktoken


def input_tokens(value, encoding_name: str) -> int:
    """Count serialized request content locally; not a provider billing estimate."""
    return len(tiktoken.get_encoding(encoding_name).encode_ordinary(json.dumps(value, ensure_ascii=False)))


@dataclass(frozen=True)
class GenerationLimits:
    remaining: Callable[[], float]
    max_input_tokens: int
    max_output_tokens: int
    encoding_name: str

    def check_input(self, messages) -> None:
        if input_tokens(messages, self.encoding_name) > self.max_input_tokens:
            raise ValueError("The request exceeds the configured model input budget. Please narrow the question.")
