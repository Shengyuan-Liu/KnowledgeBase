"""Shared domain models. Components import contracts from this public namespace."""

from .documents import (
    BlockType, Chunk, ChunkBatch, File, SourceBlock, FrozenRecord,
    PdfRegion, PdfWarning, PdfSupplement, PdfTableSpan, PdfEvidence,
    PdfPage, PdfCell, PdfTable, PdfParserIdentity,
)

from .planning import (
    PlanRecord, AnswerRequirement, DraftQuery, PlannedQuery, DependentQuery, RetrievalPlan,
    direct_plan, PlanDecision, EvidenceReference, TargetDecision, TargetDecisions,
    PassageReference, RequirementAssessment, GapQuery, SufficiencyAssessment,
)

from .retrieval import (
    VectorMatch, BM25Match, FusedMatch, RerankCandidate, RelevanceScore, RerankedMatch,
    RerankResult, RetrievedChunk, RetrievalCandidate, ExcludedEvidence, ScopeFile,
    DocumentScope, RetrievalDiagnostics, RetrievedEvidence, QueryRun, QueryVote,
    MergedCandidate, RequirementEvidence, PlanTrace, PlannedEvidence,
)

from .chat import (
    AnswerSource, CitationCheck, ChatAnswer, ChatRequest, StreamChatRequest, ChatStreamEvent,
    ConversationAnswer, ConversationInfo, MessageInfo, HistoricalSource, ConversationMessage,
    ConversationDetail,
)

__all__ = [
    'BlockType', 'PdfRegion', 'PdfWarning', 'PdfSupplement', 'PdfTableSpan', 'PdfEvidence', 'File',
    'Chunk', 'SourceBlock', 'ChunkBatch', 'FrozenRecord', 'PdfPage', 'PdfCell', 'PdfTable',
    'PdfParserIdentity', 'PlanRecord', 'AnswerRequirement', 'DraftQuery', 'PlannedQuery',
    'DependentQuery', 'RetrievalPlan', 'direct_plan', 'PlanDecision', 'EvidenceReference',
    'TargetDecision', 'TargetDecisions', 'PassageReference', 'RequirementAssessment', 'GapQuery',
    'SufficiencyAssessment', 'VectorMatch', 'BM25Match', 'FusedMatch', 'RerankCandidate',
    'RelevanceScore', 'RerankedMatch', 'RerankResult', 'RetrievedChunk', 'RetrievalCandidate',
    'ExcludedEvidence', 'ScopeFile', 'DocumentScope', 'RetrievalDiagnostics', 'RetrievedEvidence',
    'QueryRun', 'QueryVote', 'MergedCandidate', 'RequirementEvidence', 'PlanTrace',
    'PlannedEvidence', 'AnswerSource', 'CitationCheck', 'ChatAnswer', 'ChatRequest',
    'StreamChatRequest', 'ChatStreamEvent', 'ConversationAnswer', 'ConversationInfo',
    'MessageInfo', 'HistoricalSource', 'ConversationMessage', 'ConversationDetail',
]
