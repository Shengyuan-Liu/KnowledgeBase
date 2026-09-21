# Pre-release acceptance failure

The original automated workflow passed, but a subsequent Codex semantic inspection failed three of the eight completed answers. The raw evidence is preserved unchanged.

- The 2025 printer instructions were refused despite the relevant source being retrieved.
- The price follow-up lost the 2025 reference and answered with a 2026 price range.
- The conflicting-notices answer omitted whether the sources establish an applicable price.

The resolver sometimes generated an answer instead of a question, and the application replaced the original question with that output. This run is **not release acceptance**. It motivated preserving the original question in generation, testing a different default model, and adding explicit semantic assertions to the browser workflow.
