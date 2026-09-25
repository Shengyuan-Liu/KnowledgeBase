# Saved-context answer inspection

Reviewer: Codex, inspecting recorded answers and their exact supplied evidence.
This is not independent human grading and does not replace or modify v11 scores.
All observations concern the frozen corpus, not current university policy or live
API documentation. The source excerpt numbering is local to each saved answer.

## Representative citation behavior

- `release-tool-definition`: the new answer gives every tool-field item its own
  citation to source 1. The table supports name, input_schema and description as
  fully supported and cache_control as ignored. The old answer cited only a
  sentence after the list. This is a concrete citation-placement improvement.
- `msds-waiver`: the new answer still cites only the final optional website item.
  The required course name and earlier transcript/highlighting/syllabus items
  remain uncited locally even though the supplied general FAQ supports them.
  The prompt change has not reliably fixed list-level compliance.
- `release-elective-approval`: the form and required information are present, but
  the citation remains after the final list item. The new answer names actual
  source contacts instead of the old answer's vague “appropriate program
  administrator.” Available support does not establish complete local citation
  coverage.
- `api-setup`: the new answer cites the package and client method, but the base
  URL line lacks its own citation. It also places a citation after command-like
  text instead of using the requested valid code-comment form. This should not
  be treated as a validated copy-and-run shell example.

## Remaining evidence-fidelity limitations

- `api-thinking`: source 1 says only `effort` is supported in `output_config`.
  The new answer adds that other parts “are not supported or are ignored.” The
  disjunction still introduces an undocumented runtime possibility. V11 accepts
  the answer as faithful, while Codex flags the wording as unnecessarily ambiguous;
  this is not recorded as a confirmed v11 faithfulness regression.
- `missing-personal-schedule`: the new answer refuses to invent a classroom or
  start time. It nevertheless introduces Albert Course Search in a paragraph
  framed around classroom locations and meeting times, while the source says
  only that course descriptions can be found there. V11 accepts the new answer's
  actual factual claims as supported; the explicit disclaimers improve on the
  old answer. Codex retains the framing concern rather than treating it as a
  confirmed new unsupported factual claim.
- `release-personal-capstone`: the new answer no longer proposes a course portal
  or coordinator as a documented way to find the user's assignment. It explicitly
  says the sources do not provide that process. Inspection of the complete source
  2 confirms its recap of prior-year project teams: the 2024/2025 poster section
  explicitly names student authors and mentors. Those historical examples do not
  identify this user's assignment. The answer's blanket wording about absent
  group compositions for “any” project should be scoped more narrowly to the
  user's personal assignment; v11 accepts the answer, and no score is overridden.

## Paired score regressions and rubric scope

`api-setup` receives partial credit for the invocation point because it names
`client.messages.create()` but omits constructing `anthropic.Anthropic()`. The
saved source 1 contains both. The frozen expected point requires both, so its
recorded score decreases; however, the question itself asks for the SDK,
environment variables and invoking method, not explicitly the constructor. Codex
flags a question/rubric scope mismatch rather than labeling the named method
incorrect. The original annotation and scores remain unchanged.

`msds-cpt-source-context` still answers the requested comparison, but its summary
says CPT is “only” available after the first year. Source 4 states “after the first
year” without exclusivity. It also turns a referral “for more information” into
“for more detailed requirements.” Both are stronger than the source; the first
is a material qualification problem and the second a smaller wording issue.
The v11 faithfulness decrease is retained, alongside unchanged expected-point
correctness. This demonstrates why fixing citation placement alone is insufficient.

Two other full answers, `msds-credits` and `msds-industry`, were generated but their
final assessment calls timed out. They do not have completed new v11 scores and
must not be included as successful assessed pairs or silently assigned zero.

The implementation is a prompt-level change. It preserves raw model output and
does not guarantee compliance. The completed-feature evaluation retains failures
instead of silently adding citations or regenerating until a favorable answer
appears. Baseline reviews are reused, all new reviews are preserved, and judge
classifications remain assessments requiring source inspection.
