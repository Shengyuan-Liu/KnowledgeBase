"""Shared domain models. Components import contracts from this public namespace."""

from .documents import (
    BlockType, PdfRegion, PdfWarning, PdfSupplement, PdfTableSpan, PdfEvidence, FileInfo,
    Chunk, SourceBlock, StructuredChunk, ParentChunk, ChildChunk, ParentChildChunks,
    DocumentSource, FrozenRecord, PdfPage, PdfCell, PdfTable, PdfBlock, PdfParserIdentity,
    PdfExtraction,
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
    'BlockType', 'PdfRegion', 'PdfWarning', 'PdfSupplement', 'PdfTableSpan', 'PdfEvidence',
    'FileInfo', 'Chunk', 'SourceBlock', 'StructuredChunk', 'ParentChunk', 'ChildChunk',
    'ParentChildChunks', 'DocumentSource', 'FrozenRecord', 'PdfPage', 'PdfCell', 'PdfTable',
    'PdfBlock', 'PdfParserIdentity', 'PdfExtraction', 'PlanRecord', 'AnswerRequirement',
    'DraftQuery', 'PlannedQuery', 'DependentQuery', 'RetrievalPlan', 'direct_plan',
    'PlanDecision', 'EvidenceReference', 'TargetDecision', 'TargetDecisions',
    'PassageReference', 'RequirementAssessment', 'GapQuery', 'SufficiencyAssessment',
    'VectorMatch', 'BM25Match', 'FusedMatch', 'RerankCandidate', 'RelevanceScore',
    'RerankedMatch', 'RerankResult', 'RetrievedChunk', 'RetrievalCandidate',
    'ExcludedEvidence', 'ScopeFile', 'DocumentScope', 'RetrievalDiagnostics',
    'RetrievedEvidence', 'QueryRun', 'QueryVote', 'MergedCandidate', 'RequirementEvidence',
    'PlanTrace', 'PlannedEvidence', 'AnswerSource', 'CitationCheck', 'ChatAnswer',
    'ChatRequest', 'StreamChatRequest', 'ChatStreamEvent', 'ConversationAnswer',
    'ConversationInfo', 'MessageInfo', 'HistoricalSource', 'ConversationMessage',
    'ConversationDetail',
]
