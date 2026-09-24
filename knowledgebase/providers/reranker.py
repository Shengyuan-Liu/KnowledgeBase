"""Score query/passage pairs with a local sequence-classification cross-encoder."""

from collections.abc import Sequence
from threading import Lock

from knowledgebase.schemas import RelevanceScore, RerankCandidate


def build_rerank_pairs(question: str, candidates: Sequence[RerankCandidate]) -> list[list[str]]:
    """Preserve source text; prepend heading context only to the scoring input."""
    return [[question, ("Heading: " + " > ".join(candidate.heading_path) + "\n\n"
                        if candidate.heading_path else "") + candidate.text]
            for candidate in candidates]


class RerankerClient:
    """Load once per application process; score bounded batches without generation."""

    def __init__(self, model: str, *, device: str = "auto", batch_size: int = 4,
                 max_pair_tokens: int = 1024) -> None:
        # Keep model dependencies out of disabled retrieval paths.
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self._inference_lock = Lock()
        self.model = model
        self.batch_size = batch_size
        self.max_pair_tokens = max_pair_tokens
        self.device = ("cuda" if torch.cuda.is_available() else
                       "mps" if torch.backends.mps.is_available() else "cpu") if device == "auto" else device
        self._tokenizer = AutoTokenizer.from_pretrained(model)
        self._model = AutoModelForSequenceClassification.from_pretrained(model)
        self._model.to(self.device).eval()
        self.model_revision = self._model.config._commit_hash

    def score(self, question: str, candidates: Sequence[RerankCandidate]) -> list[RelevanceScore]:
        import torch

        if not candidates:
            return []
        pairs = build_rerank_pairs(question, candidates)
        encoded = self._tokenizer(pairs, padding=False, truncation=False)
        # Check the model tokenizer, not the separate evidence-budget tokenizer.
        if any(len(ids) > self.max_pair_tokens for ids in encoded["input_ids"]):
            raise ValueError("Rerank pair exceeds max_pair_tokens; no text was truncated.")
        scores = []
        # Concurrent MPS forwards triggered a native Metal assertion in the live run.
        with self._inference_lock, torch.inference_mode():
            for start in range(0, len(candidates), self.batch_size):
                batch = {key: values[start:start + self.batch_size] for key, values in encoded.items()}
                inputs = self._tokenizer.pad(batch, padding=True, return_tensors="pt").to(self.device)
                logits = self._model(**inputs).logits.flatten().float().cpu().tolist()
                scores.extend(RelevanceScore(chunk_id=candidate.chunk_id, score=value)
                              for candidate, value in zip(candidates[start:start + self.batch_size], logits, strict=True))
        return scores
