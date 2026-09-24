# Interrupted BGE comparison

The first three-worker paired run aborted during concurrent MPS inference with a
native Metal command-buffer assertion (exit 134). One hybrid answer was recorded;
no BGE answer completed. This is failure evidence, not a quality or latency result.
See [failure.json](failure.json), [run.json](run.json), and [answers.jsonl](answers.jsonl).

The next attempt serializes inference on the shared local model. Original records
are retained unchanged. The evaluation did not upload, delete, or write conversations.
