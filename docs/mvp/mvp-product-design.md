# Personal Knowledge Base MVP Product Design

## Product Overview

A personal knowledge base where users upload TXT files, ask questions through chat, and receive answers grounded in their materials with supporting source excerpts.

Materials include study notes, course content, and campus information such as course registration rules, academic calendar dates, and printer instructions. The project also serves as an MLE / AI Engineer portfolio piece, demonstrating basic RAG, source traceability, testing, and evaluation.

## MVP Goals and Scope

Deliver a complete workflow: upload materials → build an index → ask questions → receive answers with sources.

- Support a single user and UTF-8 encoded `.txt` files initially.
- Use basic vector retrieval RAG as a baseline for future improvements.
- Ground answers in uploaded materials; do not automatically search the web or update information.
- This document defines product direction and scope. Model, database, and framework choices will be made during implementation.

## Core Features

### 1. TXT File Management

- Upload files and view a file list with processing states: processing, ready, or failed.
- Provide clear feedback for empty files, unsupported formats, and processing failures. Only successfully indexed materials participate in retrieval.
- Delete a file together with its associated chunks and vectors so subsequent queries no longer use it.

### 2. Basic RAG Question Answering

- Ingestion: read text → split into chunks → generate embeddings → store chunks, source metadata, and vectors.
- Question answering: interpret the question → retrieve the top K chunks by vector similarity → pass relevant excerpts to the LLM → return an answer with sources.
- Search all available materials by default. Advanced categorization and filtering are outside the MVP scope.
- Support follow-up questions within the current conversation by resolving their meaning from prior turns before retrieval. Conversation history is not a factual source for rules or dates.

### 3. Sources and Answer Boundaries

- Display source filenames and corresponding excerpts so users can verify answers.
- Explicitly state when retrieved materials provide insufficient evidence. Do not invent rules, dates, or fees.
- When retrieved materials refer to different academic years or contain conflicting information, explain the source differences and ask the user to clarify the applicable context when needed.
- Upload time does not indicate when a rule takes effect. Preserve explicit year or semester information from the source when answering date-related questions.

### 4. Simple Chat Interface

- Provide one chat page with a file list for uploading, checking status, deleting files, asking questions, and following up.
- Display sources below each answer, with expandable source excerpts.
- Include a lightweight debug view showing retrieved chunks, similarity scores, and processing time. Similarity scores are not probabilities that an answer is correct.

### 5. Testing and Evaluation

- Cover upload validation, text chunking, retrieval, source associations, and index cleanup after deletion with automated tests.
- Create a small, fixed evaluation set with questions, expected evidence, and key answer points. Cover study materials, campus rules, dates, follow-ups, unanswerable questions, and conflicting sources.
- Evaluate retrieval of the correct evidence separately from whether the answer is supported by that evidence. Record latency and preserve configurations and results for comparisons across versions.
- Use mock models for deterministic development tests where appropriate. Verify the complete workflow with real embedding and LLM providers before delivery.

## Acceptance Scenarios

| Scenario | Expected Result |
| --- | --- |
| Upload study notes and ask about a concept they contain | Explain the concept with the source filename and supporting excerpt |
| Upload registration rules or an academic calendar and ask about requirements or dates | Answer with source evidence and preserve the applicable year or semester |
| Ask how to use a printer, then ask "How much does it cost?" | Use the conversation context to retrieve fees; explicitly state if fee information is unavailable |
| Ask a question not covered by the materials | Explain the lack of evidence without inventing an answer |
| Retrieve rules from different years or conflicting sources | Show source differences or request clarification of the applicable context |
| Delete an uploaded file and ask another question | Exclude the deleted material from retrieval results |

## Future Iterations

- V2: Support Markdown and PDF, with improved parsing and source location references.
- V3: Add hybrid search, reranking, and other retrieval improvements; compare them against basic RAG using the fixed evaluation set.
- V4: Introduce agent capabilities such as question decomposition and multi-step retrieval based on actual needs.

OCR, knowledge graphs, long-term user memory, study planning, automatic web updates, and multi-user permissions are outside the MVP scope.
