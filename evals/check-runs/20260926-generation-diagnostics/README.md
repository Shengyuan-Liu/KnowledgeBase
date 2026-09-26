# Generation diagnostics and comparison contract

The three anomalous generation calls in the retained September 25 correction
start within one second of recorded macOS sleep events (UTC-04:00):

| Case | Call start UTC | Local sleep | Observed stall |
| --- | --- | --- | --- |
| Independent study | 21:09:44 | 17:09:44 | 38.434 s before first delta |
| Message subfields | 21:15:38 | 17:15:38 | 44.706 s between deltas |
| Unspecified API error | 21:17:32 | 17:17:32 | 60.003 s after last delta, then timeout |

[Raw power events](power-events.log) and [derived call evidence](diagnosis.json)
are retained. The original call timestamps are rounded to a second, and original
per-event wall elapsed was not measured. This is strong evidence of a host-sleep
confound, not proof that all delay came from sleep or that the provider was healthy.
The original failed run and latency gates stay failed. Its active-time measurements
must not be presented as an uncontaminated awake-host service benchmark.

Local SDK inspection (`openai` 3.16.2, `AsyncStream._iter_events`) shows streamed
transport timeouts are propagated as APITimeoutError; the 60-second silent tail
matches the configured evaluation timeout. No evidence of auth/quota errors.
No production timeout, retry or model setting was changed. A new real-SDK offline
regression confirms that partial output survives, the connection closes and the
request is not automatically replayed on a stream read timeout.

The evaluation recorder now retains stream-open timing, UTC start/finish,
active and wall elapsed on deltas and termination, and the exception cause type.
Private exception messages are not stored. Both clocks are needed to expose
suspension/clock divergence; neither alone diagnoses network or provider behavior.
Temporary `caffeinate -i -s` applies only to the next bounded acceptance process;
it does not change saved power settings or guarantee against manual sleep.

The generation prompt already requested per-source comparison but ended with
one item per requested question part. This can encourage compressing a 'which page'
question into one item. The change makes one labeled item per named document the
explicit comparison format, with evidence-limited absence and no opposite-policy
inference. It replaces and reconciles existing instructions rather than adding
an output repair pass. This is a prompt-consistency hypothesis, not a demonstrated
root cause. [OpenAI GPT-4.1 guidance](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-4.1)
recommends clear consistent instructions and empirical evaluation; live validation
uses the unchanged frozen questions and references in the
[acceptance plan](../../library-runs/20260926-comparison-awake/PLAN.md).

- `scoped-1`: 75 passed; generation parity, real SDK streaming cleanup, recording
  both clocks and error causes, service history atomicity and evaluation wiring.
- `backend-1`: 593 passed, one intentionally skipped opt-in live provider test.
  Existing Starlette/AnyIO deprecation warning remains.
- `preflight-1`: two frozen-input and real-corpus scope checks, before live calls.

Each JSON/log pair retains command, code hashes, duration, counts and the full
measurement inventory. Mocked timings are not production latency. The diagnosis
reuses historical paid observations and makes no new provider requests. This
change requires no frontend implementation or index migration. Work remains on
`v1`; no merge authorized.
