# Question-aligned generation checks

- `backend-1`: full product backend, 561 passed, 1 intentional opt-in provider skip.
  Existing Starlette/AnyIO deprecation warning; no provider calls.
- `preflight-1`: frozen-question/source isolation and limited annotation correction,
  2 passed, 1 pre-collection skip. No provider calls.

Each JSON/log pair records exact command, code hashes, duration, counts and the
complete metric inventory. These checks verify contracts, not model compliance.
Product tests were run against `tests/`; historical experiment modules are not
part of the product test suite. Frontend unchanged; no fresh browser/build run.
