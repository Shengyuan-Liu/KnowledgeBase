# Development inspection of automatic judgments

Reviewer: Codex; this is not independent human grading. The inspection covers the
known credits error, every current pending-review reason, and every current
unsupported/contradicted claim. It is not an exhaustive external correctness audit.

- The new judge detects the previous MSDS answer's extra false assertion that all
  three first-fall courses are required/core. The source has two required courses
  and one elective. Expected-point correctness alone missed this error.
- The current admissions-prerequisites judgment has a **false positive**: the
  answer includes the mathematically-intensive qualifier, but the extracted claim
  omits it. The judge scores the incomplete extraction as an answer contradiction.
  Exact text and reasons are in `development-inspection.json`.
- The GPA wording “main requirements” is arguably judged too strictly. The
  Pathbreaker statement about using one source is judged as though its source
  document must assert the answer's own provenance. Both need reviewer attention.
- Three current reviews are pending: waiver, personal schedule and API setup. The
  waiver inventory turns an alternative (undergraduate OR graduate transcripts)
  into two independent requirements. The personal-schedule audit mixes source
  support problems with extraction fidelity. API setup omits a factual statement.
- The citation metric uses a conservative same-line boundary. It can undercount
  citations placed after a list or in a later summary; it is not a universal
  natural-language citation-resolution metric.

The report retains the raw automatic scores and pending status. No model score is
manually changed to manufacture a clean pass, and no full-set quality improvement
is claimed. The framework exposes these errors; it does not make an LLM judge a
source of ground truth.
