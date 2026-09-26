"""Run a tiny local cross-encoder offline; never download pretrained test weights."""

from unittest.mock import Mock

import pytest
import torch
from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.pre_tokenizers import Whitespace
from transformers import PreTrainedTokenizerFast, XLMRobertaConfig, XLMRobertaForSequenceClassification

from knowledgebase.providers.reranker import RerankerClient, build_rerank_pairs
from knowledgebase.schemas import RerankCandidate


@pytest.fixture
def client(tmp_path):
    tokenizer = Tokenizer(WordLevel({"[UNK]": 0, "[PAD]": 1, "Question": 2, "fact": 3}, unk_token="[UNK]"))
    tokenizer.pre_tokenizer = Whitespace()
    PreTrainedTokenizerFast(tokenizer_object=tokenizer, unk_token="[UNK]", pad_token="[PAD]").save_pretrained(tmp_path)
    model = XLMRobertaForSequenceClassification(XLMRobertaConfig(
        vocab_size=4, hidden_size=8, num_hidden_layers=1, num_attention_heads=2,
        intermediate_size=16, max_position_embeddings=64, num_labels=1, pad_token_id=1,
    ))
    with torch.no_grad():
        model.classifier.out_proj.weight.zero_()
        model.classifier.out_proj.bias.fill_(-2.75)
    model.save_pretrained(tmp_path)
    return RerankerClient(str(tmp_path), device="cpu", batch_size=2, max_pair_tokens=32)


def candidates():
    return [RerankCandidate(chunk_id=f"child-{i}", text="fact\n", heading_path=["Heading"], rank=i+1, rrf_score=0.01)
            for i in range(3)]


def test_actual_local_model_batches_preserve_ids_and_unbounded_float_scores(client, monkeypatch):
    forward = Mock(wraps=client._model.forward)
    monkeypatch.setattr(client._model, "forward", forward)
    inputs = candidates()
    result = client.score("Question", inputs)
    assert [r.chunk_id for r in result] == [c.chunk_id for c in inputs]
    assert [r.score for r in result] == [-2.75] * 3
    assert [call.kwargs["input_ids"].shape[0] for call in forward.call_args_list] == [2, 1]
    assert not client._model.training
    assert client.device == "cpu"
    assert inputs[0].text == "fact\n"
    assert build_rerank_pairs("Question", inputs)[0] == ["Question", "Heading: Heading\n\nfact\n"]


def test_pair_budget_fails_before_inference_without_shortening_text(client, monkeypatch):
    forward = Mock(wraps=client._model.forward)
    monkeypatch.setattr(client._model, "forward", forward)
    inputs = candidates()
    pairs = build_rerank_pairs("Question", inputs)
    limit = max(map(len, client._tokenizer(pairs, truncation=False)["input_ids"]))
    client.max_pair_tokens = limit
    assert len(client.score("Question", inputs)) == 3
    forward.reset_mock()
    client.max_pair_tokens = limit - 1
    with pytest.raises(ValueError, match="no text was truncated"):
        client.score("Question", inputs)
    forward.assert_not_called()


def test_empty_input_skips_inference(client, monkeypatch):
    forward = Mock()
    monkeypatch.setattr(client._model, "forward", forward)
    assert client.score("Question", []) == []
    forward.assert_not_called()


def test_local_model_failure_propagates_without_llm_fallback(client, monkeypatch):
    monkeypatch.setattr(client._model, "forward", Mock(side_effect=RuntimeError("Local scoring failed")))
    with pytest.raises(RuntimeError, match="Local scoring failed"):
        client.score("Question", candidates())


def test_shared_model_serializes_concurrent_forward_calls(client, monkeypatch):
    """Regression for concurrent MPS command-buffer corruption in the live run."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier, Lock
    from time import sleep

    gate, counter = Barrier(2), Lock()
    active = maximum = 0
    forward = client._model.forward

    def observed_forward(**kwargs):
        nonlocal active, maximum
        with counter:
            active += 1
            maximum = max(maximum, active)
        try:
            sleep(0.02)
            return forward(**kwargs)
        finally:
            with counter:
                active -= 1

    monkeypatch.setattr(client._model, "forward", observed_forward)

    def ask(_):
        gate.wait(timeout=5)
        return client.score("Question", candidates())

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(ask, range(2)))
    assert maximum == 1
    assert all([s.score for s in result] == [-2.75] * 3 for result in results)
