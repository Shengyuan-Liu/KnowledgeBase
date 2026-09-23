"""Obtain structured relevance scores through the existing OpenAI SDK."""

from openai import OpenAI
from openai.types.responses import EasyInputMessageParam
from pydantic import Field, create_model

from knowledgebase.schemas import RelevanceScore


class RerankerClient:
    """One structured-output call; the caller owns the SDK and model selection."""

    def __init__(self, client: OpenAI, model: str) -> None:
        self._client = client
        self.model = model

    def score(self, messages: list[EasyInputMessageParam], chunk_ids: list[str]) -> list[RelevanceScore]:
        # Required keyed fields prevent the observed 19-of-20 list omission.
        score_format = create_model("CandidateScores", **{
            f"candidate_{index}": (int, Field(alias=identity, ge=0, le=3, strict=True))
            for index, identity in enumerate(chunk_ids)
        })
        response = self._client.responses.parse(
            model=self.model, input=messages, text_format=score_format,
            truncation="disabled",
        )
        if response.status != "completed" or response.output_parsed is None:
            raise RuntimeError("Reranker did not return structured relevance scores.")
        return [RelevanceScore(chunk_id=identity, score=score)
                for identity, score in response.output_parsed.model_dump(by_alias=True).items()]
