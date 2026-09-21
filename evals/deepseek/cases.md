# DeepSeek documentation evaluation cases

Generated from hand-authored case definitions. Evidence offsets and lines refer to the frozen corpus. Do not ingest this file.

## ds-base-url-semantic

I have a client for an OpenAI-shaped service and another for an Anthropic-shaped service. Where should each connect to DeepSeek?

- Category: semantic; split: test; family: base-url; answerable: true

Expected answer points:

- Use https://api.deepseek.com for the OpenAI format.
- Use https://api.deepseek.com/anthropic for the Anthropic format.

Evidence:

- [index, lines 10–10](../materials/deepseek/md/index.md) — https://api-docs.deepseek.com/
- [index, lines 11–11](../materials/deepseek/md/index.md) — https://api-docs.deepseek.com/

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-base-url-keyword

What are the documented base_url values for the OpenAI and Anthropic API formats?

- Category: keyword; split: test; family: base-url; answerable: true

Expected answer points:

- Use https://api.deepseek.com for the OpenAI format.
- Use https://api.deepseek.com/anthropic for the Anthropic format.

Evidence:

- [index, lines 10–10](../materials/deepseek/md/index.md) — https://api-docs.deepseek.com/
- [index, lines 11–11](../materials/deepseek/md/index.md) — https://api-docs.deepseek.com/

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-retired-aliases-semantic

If I keep using either of the older Flash model names, do I still get the retired model and its old billing?

- Category: semantic; split: test; family: retired-aliases; answerable: true

Expected answer points:

- Both legacy names remain accepted, but their retired models are replaced by DeepSeek-V4.1-Flash and billed at the Flash price.

Evidence:

- [index, lines 15–15](../materials/deepseek/md/index.md) — https://api-docs.deepseek.com/

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-retired-aliases-keyword

How are deepseek-v4-flash and deepseek-v4-flash-vision-exp requests served and billed in this snapshot?

- Category: keyword; split: test; family: retired-aliases; answerable: true

Expected answer points:

- Both legacy names remain accepted, but their retired models are replaced by DeepSeek-V4.1-Flash and billed at the Flash price.

Evidence:

- [index, lines 15–15](../materials/deepseek/md/index.md) — https://api-docs.deepseek.com/

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-thinking-default-semantic

Will the service reason before answering if I do not explicitly choose a reasoning setting, and how much effort does it use?

- Category: semantic; split: dev; family: thinking-default; answerable: true

Expected answer points:

- Thinking is enabled by default and the default effort is high.

Evidence:

- [guides/thinking_mode, lines 15–16](../materials/deepseek/md/guides/thinking_mode.md) — https://api-docs.deepseek.com/guides/thinking_mode

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-thinking-default-keyword

What are the default thinking mode and default effort?

- Category: keyword; split: dev; family: thinking-default; answerable: true

Expected answer points:

- Thinking is enabled by default and the default effort is high.

Evidence:

- [guides/thinking_mode, lines 15–16](../materials/deepseek/md/guides/thinking_mode.md) — https://api-docs.deepseek.com/guides/thinking_mode

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-effort-mapping-semantic

My client offers the very small, middle, extra-high and ultra reasoning presets. How are those translated by DeepSeek?

- Category: semantic; split: dev; family: effort-mapping; answerable: true

Expected answer points:

- minimal maps to low.
- medium and xhigh both map to high.
- ultra maps to max.

Evidence:

- [guides/thinking_mode, lines 18–26](../materials/deepseek/md/guides/thinking_mode.md) — https://api-docs.deepseek.com/guides/thinking_mode

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-effort-mapping-keyword

Map minimal, medium, xhigh, and ultra to actual DeepSeek reasoning efforts.

- Category: keyword; split: dev; family: effort-mapping; answerable: true

Expected answer points:

- minimal maps to low.
- medium and xhigh both map to high.
- ultra maps to max.

Evidence:

- [guides/thinking_mode, lines 18–26](../materials/deepseek/md/guides/thinking_mode.md) — https://api-docs.deepseek.com/guides/thinking_mode

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-thinking-sdk-semantic

How should I pass the extra switch that turns reasoning on when using the Python chat client?

- Category: semantic; split: dev; family: thinking-sdk; answerable: true

Expected answer points:

- Place the thinking parameter inside extra_body.

Evidence:

- [guides/thinking_mode, lines 28–28](../materials/deepseek/md/guides/thinking_mode.md) — https://api-docs.deepseek.com/guides/thinking_mode

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-thinking-sdk-keyword

Where must thinking be placed in an OpenAI SDK Chat Completion request?

- Category: keyword; split: dev; family: thinking-sdk; answerable: true

Expected answer points:

- Place the thinking parameter inside extra_body.

Evidence:

- [guides/thinking_mode, lines 28–28](../materials/deepseek/md/guides/thinking_mode.md) — https://api-docs.deepseek.com/guides/thinking_mode

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-ignored-sampling-semantic

My attempts to change randomness and repetition penalties seem ineffective during reasoning. Is this expected or an invalid request?

- Category: semantic; split: dev; family: ignored-sampling; answerable: true

Expected answer points:

- These parameters have no effect in thinking mode, but setting them does not trigger an error for compatibility.

Evidence:

- [guides/thinking_mode, lines 41–41](../materials/deepseek/md/guides/thinking_mode.md) — https://api-docs.deepseek.com/guides/thinking_mode

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-ignored-sampling-keyword

What happens to temperature, presence_penalty and frequency_penalty in thinking mode?

- Category: keyword; split: dev; family: ignored-sampling; answerable: true

Expected answer points:

- These parameters have no effect in thinking mode, but setting them does not trigger an error for compatibility.

Evidence:

- [guides/thinking_mode, lines 41–41](../materials/deepseek/md/guides/thinking_mode.md) — https://api-docs.deepseek.com/guides/thinking_mode

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-top-p-semantic

What happens if I ask for a nucleus sampling value below the allowed reasoning threshold, or set it with reasoning off?

- Category: semantic; split: dev; family: top-p; answerable: true

Expected answer points:

- Thinking mode clamps values below 0.95 to 0.95; non-thinking mode fixes top_p at 1.0 and ignores the supplied value.

Evidence:

- [guides/thinking_mode, lines 43–43](../materials/deepseek/md/guides/thinking_mode.md) — https://api-docs.deepseek.com/guides/thinking_mode

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-top-p-keyword

Explain top_p=0.5 in thinking mode and top_p in non-thinking mode.

- Category: keyword; split: dev; family: top-p; answerable: true

Expected answer points:

- Thinking mode clamps values below 0.95 to 0.95; non-thinking mode fixes top_p at 1.0 and ignores the supplied value.

Evidence:

- [guides/thinking_mode, lines 43–43](../materials/deepseek/md/guides/thinking_mode.md) — https://api-docs.deepseek.com/guides/thinking_mode

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-cot-without-tools-semantic

For a reasoning conversation without any tool definitions, must I resend earlier reasoning, and does it consume context if I do?

- Category: semantic; split: dev; family: cot-without-tools; answerable: true

Expected answer points:

- It need not be passed back; if supplied it is ignored and is not concatenated into the context.

Evidence:

- [guides/thinking_mode, lines 47–48](../materials/deepseek/md/guides/thinking_mode.md) — https://api-docs.deepseek.com/guides/thinking_mode

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-cot-without-tools-keyword

What happens to reasoning_content when a subsequent request does not carry tools?

- Category: keyword; split: dev; family: cot-without-tools; answerable: true

Expected answer points:

- It need not be passed back; if supplied it is ignored and is not concatenated into the context.

Evidence:

- [guides/thinking_mode, lines 47–48](../materials/deepseek/md/guides/thinking_mode.md) — https://api-docs.deepseek.com/guides/thinking_mode

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-cot-with-tools-semantic

I use reasoning with tools. Must I preserve earlier reasoning even on turns that did not invoke a function, and what happens if I omit it?

- Category: semantic; split: dev; family: cot-with-tools; answerable: true

Expected answer points:

- Fully pass back reasoning_content in all subsequent requests, including turns with no tool call; incorrect omission returns a 400 error.

Evidence:

- [guides/thinking_mode, lines 132–132](../materials/deepseek/md/guides/thinking_mode.md) — https://api-docs.deepseek.com/guides/thinking_mode

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-cot-with-tools-keyword

When tools is present, what reasoning_content must be passed back and what error can omission cause?

- Category: keyword; split: dev; family: cot-with-tools; answerable: true

Expected answer points:

- Fully pass back reasoning_content in all subsequent requests, including turns with no tool call; incorrect omission returns a 400 error.

Evidence:

- [guides/thinking_mode, lines 132–132](../materials/deepseek/md/guides/thinking_mode.md) — https://api-docs.deepseek.com/guides/thinking_mode

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-json-setup-semantic

I need a machine-readable object rather than free-form prose. What output setting and prompt instructions are required?

- Category: semantic; split: dev; family: json-setup; answerable: true

Expected answer points:

- Set response_format to {"type":"json_object"}.
- Include the word json in a system or user prompt and provide an example of the desired JSON format.

Evidence:

- [guides/json_mode, lines 14–17](../materials/deepseek/md/guides/json_mode.md) — https://api-docs.deepseek.com/guides/json_mode

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-json-setup-keyword

How do response_format, json in the prompt, and the example format enable JSON Output?

- Category: keyword; split: dev; family: json-setup; answerable: true

Expected answer points:

- Set response_format to {"type":"json_object"}.
- Include the word json in a system or user prompt and provide an example of the desired JSON format.

Evidence:

- [guides/json_mode, lines 14–17](../materials/deepseek/md/guides/json_mode.md) — https://api-docs.deepseek.com/guides/json_mode

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-json-truncation-semantic

How can I avoid a structured response ending halfway through, and what does the guide suggest for an occasional blank result?

- Category: semantic; split: dev; family: json-truncation; answerable: true

Expected answer points:

- Set max_tokens reasonably to avoid truncating the JSON.
- Empty content can occur; try modifying the prompt.

Evidence:

- [guides/json_mode, lines 14–17](../materials/deepseek/md/guides/json_mode.md) — https://api-docs.deepseek.com/guides/json_mode

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-json-truncation-keyword

What do the JSON Output notes say about max_tokens and empty content?

- Category: keyword; split: dev; family: json-truncation; answerable: true

Expected answer points:

- Set max_tokens reasonably to avoid truncating the JSON.
- Empty content can occur; try modifying the prompt.

Evidence:

- [guides/json_mode, lines 14–17](../materials/deepseek/md/guides/json_mode.md) — https://api-docs.deepseek.com/guides/json_mode

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-cache-default-semantic

Do I have to add special cache-management code before repeated prompts benefit from stored context?

- Category: semantic; split: dev; family: cache-default; answerable: true

Expected answer points:

- Disk context caching is enabled by default for all users and requires no code modification.

Evidence:

- [guides/kv_cache, lines 6–6](../materials/deepseek/md/guides/kv_cache.md) — https://api-docs.deepseek.com/guides/kv_cache

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-cache-default-keyword

Is DeepSeek Context Caching on Disk enabled by default?

- Category: keyword; split: dev; family: cache-default; answerable: true

Expected answer points:

- Disk context caching is enabled by default for all users and requires no code modification.

Evidence:

- [guides/kv_cache, lines 6–6](../materials/deepseek/md/guides/kv_cache.md) — https://api-docs.deepseek.com/guides/kv_cache

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-cache-full-unit-semantic

Is sharing just any initial text enough for a cache hit, or does a complete previously stored unit have to match?

- Category: semantic; split: dev; family: cache-full-unit; answerable: true

Expected answer points:

- The matching prefix must already have been persisted, and a subsequent request must fully match a complete cache prefix unit.

Evidence:

- [guides/kv_cache, lines 12–12](../materials/deepseek/md/guides/kv_cache.md) — https://api-docs.deepseek.com/guides/kv_cache

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-cache-full-unit-keyword

What must fully match a persisted cache prefix unit for a cache hit?

- Category: keyword; split: dev; family: cache-full-unit; answerable: true

Expected answer points:

- The matching prefix must already have been persisted, and a subsequent request must fully match a complete cache prefix unit.

Evidence:

- [guides/kv_cache, lines 12–12](../materials/deepseek/md/guides/kv_cache.md) — https://api-docs.deepseek.com/guides/kv_cache

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-cache-abac-semantic

Three requests begin with the same section but have different endings. Why might only the third reuse that common section?

- Category: semantic; split: dev; family: cache-abac; answerable: true

Expected answer points:

- A+C does not fully match the A+B unit; detecting shared A causes A to be persisted, so A+D can then hit A.

Evidence:

- [guides/kv_cache, lines 24–24](../materials/deepseek/md/guides/kv_cache.md) — https://api-docs.deepseek.com/guides/kv_cache

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-cache-abac-keyword

Explain cache hits for A+B, then A+C, then A+D in the documented Example 2.

- Category: keyword; split: dev; family: cache-abac; answerable: true

Expected answer points:

- A+C does not fully match the A+B unit; detecting shared A causes A to be persisted, so A+D can then hit A.

Evidence:

- [guides/kv_cache, lines 24–24](../materials/deepseek/md/guides/kv_cache.md) — https://api-docs.deepseek.com/guides/kv_cache

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-cache-counters-semantic

Which response counters tell me how much input reused stored computation and how much did not?

- Category: semantic; split: dev; family: cache-counters; answerable: true

Expected answer points:

- prompt_cache_hit_tokens counts input tokens that hit the cache.
- prompt_cache_miss_tokens counts input tokens that missed the cache.

Evidence:

- [guides/kv_cache, lines 89–89](../materials/deepseek/md/guides/kv_cache.md) — https://api-docs.deepseek.com/guides/kv_cache
- [guides/kv_cache, lines 91–91](../materials/deepseek/md/guides/kv_cache.md) — https://api-docs.deepseek.com/guides/kv_cache

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-cache-counters-keyword

Define prompt_cache_hit_tokens and prompt_cache_miss_tokens in usage.

- Category: keyword; split: dev; family: cache-counters; answerable: true

Expected answer points:

- prompt_cache_hit_tokens counts input tokens that hit the cache.
- prompt_cache_miss_tokens counts input tokens that missed the cache.

Evidence:

- [guides/kv_cache, lines 89–89](../materials/deepseek/md/guides/kv_cache.md) — https://api-docs.deepseek.com/guides/kv_cache
- [guides/kv_cache, lines 91–91](../materials/deepseek/md/guides/kv_cache.md) — https://api-docs.deepseek.com/guides/kv_cache

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-cache-randomness-semantic

Does reusing cached input force the service to return an identical answer on every request?

- Category: semantic; split: dev; family: cache-randomness; answerable: true

Expected answer points:

- The cache matches only the input prefix; output is still generated by inference and can be random.

Evidence:

- [guides/kv_cache, lines 95–95](../materials/deepseek/md/guides/kv_cache.md) — https://api-docs.deepseek.com/guides/kv_cache

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-cache-randomness-keyword

Does the hard disk cache cache generated output or only the input prefix?

- Category: keyword; split: dev; family: cache-randomness; answerable: true

Expected answer points:

- The cache matches only the input prefix; output is still generated by inference and can be random.

Evidence:

- [guides/kv_cache, lines 95–95](../materials/deepseek/md/guides/kv_cache.md) — https://api-docs.deepseek.com/guides/kv_cache

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-cache-lifetime-semantic

Can I rely on stored context always being present, and when may unused cache disappear?

- Category: semantic; split: dev; family: cache-lifetime; answerable: true

Expected answer points:

- Cache is best effort, with no guaranteed 100% hit rate.
- Construction takes seconds; unused cache is normally cleared within hours to days.

Evidence:

- [guides/kv_cache, lines 99–99](../materials/deepseek/md/guides/kv_cache.md) — https://api-docs.deepseek.com/guides/kv_cache
- [guides/kv_cache, lines 101–101](../materials/deepseek/md/guides/kv_cache.md) — https://api-docs.deepseek.com/guides/kv_cache

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-cache-lifetime-keyword

What are the cache hit guarantee, construction time and usual cache eviction interval?

- Category: keyword; split: dev; family: cache-lifetime; answerable: true

Expected answer points:

- Cache is best effort, with no guaranteed 100% hit rate.
- Construction takes seconds; unused cache is normally cleared within hours to days.

Evidence:

- [guides/kv_cache, lines 99–99](../materials/deepseek/md/guides/kv_cache.md) — https://api-docs.deepseek.com/guides/kv_cache
- [guides/kv_cache, lines 101–101](../materials/deepseek/md/guides/kv_cache.md) — https://api-docs.deepseek.com/guides/kv_cache

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-stateless-chat-semantic

The model forgets the earlier exchange when I send only my next question. What conversation data should my client resend?

- Category: semantic; split: dev; family: stateless-chat; answerable: true

Expected answer points:

- The API is stateless; the client must concatenate and send all prior conversation history with each request.

Evidence:

- [guides/multi_round_chat, lines 8–8](../materials/deepseek/md/guides/multi_round_chat.md) — https://api-docs.deepseek.com/guides/multi_round_chat

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-stateless-chat-keyword

Is /chat/completions stateful, and what history must be sent on each request?

- Category: keyword; split: dev; family: stateless-chat; answerable: true

Expected answer points:

- The API is stateless; the client must concatenate and send all prior conversation history with each request.

Evidence:

- [guides/multi_round_chat, lines 8–8](../materials/deepseek/md/guides/multi_round_chat.md) — https://api-docs.deepseek.com/guides/multi_round_chat

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-prefix-setup-semantic

I want the assistant to continue a beginning I supply. Which final message and endpoint configuration enable this?

- Category: semantic; split: dev; family: prefix-setup; answerable: true

Expected answer points:

- The last message must have role assistant and prefix set to True.
- Use https://api.deepseek.com/beta.

Evidence:

- [guides/chat_prefix_completion, lines 10–11](../materials/deepseek/md/guides/chat_prefix_completion.md) — https://api-docs.deepseek.com/guides/chat_prefix_completion

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-prefix-setup-keyword

For Chat Prefix Completion, what role, prefix flag, and base_url are required?

- Category: keyword; split: dev; family: prefix-setup; answerable: true

Expected answer points:

- The last message must have role assistant and prefix set to True.
- Use https://api.deepseek.com/beta.

Evidence:

- [guides/chat_prefix_completion, lines 10–11](../materials/deepseek/md/guides/chat_prefix_completion.md) — https://api-docs.deepseek.com/guides/chat_prefix_completion

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-fim-purpose-semantic

I know the beginning and end of a code fragment and want the missing middle filled in. Which feature does that, and is the ending mandatory?

- Category: semantic; split: dev; family: fim-purpose; answerable: true

Expected answer points:

- FIM completes content between a prefix and optional suffix, often for text or code completion.

Evidence:

- [guides/fim_completion, lines 6–6](../materials/deepseek/md/guides/fim_completion.md) — https://api-docs.deepseek.com/guides/fim_completion

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-fim-purpose-keyword

What does FIM completion accept as prefix and suffix, and is suffix optional?

- Category: keyword; split: dev; family: fim-purpose; answerable: true

Expected answer points:

- FIM completes content between a prefix and optional suffix, often for text or code completion.

Evidence:

- [guides/fim_completion, lines 6–6](../materials/deepseek/md/guides/fim_completion.md) — https://api-docs.deepseek.com/guides/fim_completion

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-fim-limit-semantic

What generation cap and service address should I use for filling a gap inside a code fragment?

- Category: semantic; split: dev; family: fim-limit; answerable: true

Expected answer points:

- The maximum is 4K tokens.
- Use https://api.deepseek.com/beta.

Evidence:

- [guides/fim_completion, lines 10–11](../materials/deepseek/md/guides/fim_completion.md) — https://api-docs.deepseek.com/guides/fim_completion

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-fim-limit-keyword

What are the FIM completion max tokens and beta base_url?

- Category: keyword; split: dev; family: fim-limit; answerable: true

Expected answer points:

- The maximum is 4K tokens.
- Use https://api.deepseek.com/beta.

Evidence:

- [guides/fim_completion, lines 10–11](../materials/deepseek/md/guides/fim_completion.md) — https://api-docs.deepseek.com/guides/fim_completion

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-tools-execution-semantic

When the assistant asks for weather through a function, does DeepSeek actually run my weather lookup?

- Category: semantic; split: dev; family: tools-execution; answerable: true

Expected answer points:

- The user/client must provide and execute the function; the model itself does not execute specific functions.

Evidence:

- [guides/tool_calls, lines 73–73](../materials/deepseek/md/guides/tool_calls.md) — https://api-docs.deepseek.com/guides/tool_calls

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-tools-execution-keyword

Who implements and executes get_weather in the Tool Calls example?

- Category: keyword; split: dev; family: tools-execution; answerable: true

Expected answer points:

- The user/client must provide and execute the function; the model itself does not execute specific functions.

Evidence:

- [guides/tool_calls, lines 73–73](../materials/deepseek/md/guides/tool_calls.md) — https://api-docs.deepseek.com/guides/tool_calls

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-tool-insertion-semantic

My agent wants to insert a tool exchange it created itself into the middle of history. Which interface families permit that?

- Category: semantic; split: dev; family: tool-insertion; answerable: true

Expected answer points:

- Anthropic and Responses support inserted tool calls and system messages.
- Chat Completion supports inserted system messages but not inserted tool calls.

Evidence:

- [guides/tool_calls, lines 87–88](../materials/deepseek/md/guides/tool_calls.md) — https://api-docs.deepseek.com/guides/tool_calls

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-tool-insertion-keyword

Compare mid-conversation inserted tool calls in Anthropic, Responses and Chat Completion APIs.

- Category: keyword; split: dev; family: tool-insertion; answerable: true

Expected answer points:

- Anthropic and Responses support inserted tool calls and system messages.
- Chat Completion supports inserted system messages but not inserted tool calls.

Evidence:

- [guides/tool_calls, lines 87–88](../materials/deepseek/md/guides/tool_calls.md) — https://api-docs.deepseek.com/guides/tool_calls

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-strict-enable-semantic

How do I force generated function arguments to follow my schema, and will an unsupported schema be accepted?

- Category: semantic; split: dev; family: strict-enable; answerable: true

Expected answer points:

- Use the beta base URL and strict:true on every function.
- The server validates the schema and returns an error for invalid or unsupported schema definitions.

Evidence:

- [guides/tool_calls, lines 98–100](../materials/deepseek/md/guides/tool_calls.md) — https://api-docs.deepseek.com/guides/tool_calls

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-strict-enable-keyword

What base_url and strict property are needed for strict Tool Calls, and how is the schema checked?

- Category: keyword; split: dev; family: strict-enable; answerable: true

Expected answer points:

- Use the beta base URL and strict:true on every function.
- The server validates the schema and returns an error for invalid or unsupported schema definitions.

Evidence:

- [guides/tool_calls, lines 98–100](../materials/deepseek/md/guides/tool_calls.md) — https://api-docs.deepseek.com/guides/tool_calls

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-strict-object-semantic

In strict function definitions, may I leave some object properties optional or allow unlisted fields?

- Category: semantic; split: dev; family: strict-object; answerable: true

Expected answer points:

- All properties must be required and additionalProperties must be false.

Evidence:

- [guides/tool_calls, lines 143–143](../materials/deepseek/md/guides/tool_calls.md) — https://api-docs.deepseek.com/guides/tool_calls

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-strict-object-keyword

What required and additionalProperties rules apply to every strict-mode object?

- Category: keyword; split: dev; family: strict-object; answerable: true

Expected answer points:

- All properties must be required and additionalProperties must be false.

Evidence:

- [guides/tool_calls, lines 143–143](../materials/deepseek/md/guides/tool_calls.md) — https://api-docs.deepseek.com/guides/tool_calls

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-strict-string-semantic

Can strict function schemas constrain strings by a regular expression and length bounds equally?

- Category: semantic; split: test; family: strict-string; answerable: true

Expected answer points:

- pattern is supported.
- minLength and maxLength are unsupported.

Evidence:

- [guides/tool_calls, lines 165–172](../materials/deepseek/md/guides/tool_calls.md) — https://api-docs.deepseek.com/guides/tool_calls
- [guides/tool_calls, lines 174–175](../materials/deepseek/md/guides/tool_calls.md) — https://api-docs.deepseek.com/guides/tool_calls

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-strict-string-keyword

Are pattern, minLength and maxLength supported for strict-mode strings?

- Category: keyword; split: test; family: strict-string; answerable: true

Expected answer points:

- pattern is supported.
- minLength and maxLength are unsupported.

Evidence:

- [guides/tool_calls, lines 165–172](../materials/deepseek/md/guides/tool_calls.md) — https://api-docs.deepseek.com/guides/tool_calls
- [guides/tool_calls, lines 174–175](../materials/deepseek/md/guides/tool_calls.md) — https://api-docs.deepseek.com/guides/tool_calls

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-strict-array-semantic

Can a strict tool schema enforce the smallest and largest permitted number of list elements?

- Category: semantic; split: dev; family: strict-array; answerable: true

Expected answer points:

- minItems and maxItems are unsupported.

Evidence:

- [guides/tool_calls, lines 232–234](../materials/deepseek/md/guides/tool_calls.md) — https://api-docs.deepseek.com/guides/tool_calls

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-strict-array-keyword

Are minItems and maxItems supported in strict-mode arrays?

- Category: keyword; split: dev; family: strict-array; answerable: true

Expected answer points:

- minItems and maxItems are unsupported.

Evidence:

- [guides/tool_calls, lines 232–234](../materials/deepseek/md/guides/tool_calls.md) — https://api-docs.deepseek.com/guides/tool_calls

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-strict-ref-semantic

How does this guide spell the reusable schema-definition key and the key that refers to it?

- Category: semantic; split: dev; family: strict-ref; answerable: true

Expected answer points:

- $def defines reusable modules; $ref references them and can also define recursive structures.

Evidence:

- [guides/tool_calls, lines 301–301](../materials/deepseek/md/guides/tool_calls.md) — https://api-docs.deepseek.com/guides/tool_calls

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-strict-ref-keyword

In this documentation, what do $def and $ref do? Preserve the documented spelling.

- Category: keyword; split: dev; family: strict-ref; answerable: true

Expected answer points:

- $def defines reusable modules; $ref references them and can also define recursive structures.

Evidence:

- [guides/tool_calls, lines 301–301](../materials/deepseek/md/guides/tool_calls.md) — https://api-docs.deepseek.com/guides/tool_calls

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-upload-semantic

I want to upload an image once and reuse it later. What request encoding, endpoint and purpose value should I use?

- Category: semantic; split: dev; family: file-upload; answerable: true

Expected answer points:

- Use multipart/form-data with POST /files.
- Set purpose to user_data.

Evidence:

- [guides/files_api, lines 21–21](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api
- [guides/files_api, lines 25–30](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-upload-keyword

What are the upload method/path, Content-Type and purpose for the Files API?

- Category: keyword; split: dev; family: file-upload; answerable: true

Expected answer points:

- Use multipart/form-data with POST /files.
- Set purpose to user_data.

Evidence:

- [guides/files_api, lines 21–21](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api
- [guides/files_api, lines 25–30](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-upload-limit-semantic

How large can an uploaded image be, and how long can its upload take?

- Category: semantic; split: dev; family: file-upload-limit; answerable: true

Expected answer points:

- The file limit is 64 MiB and upload must complete within 10 minutes.

Evidence:

- [guides/files_api, lines 21–21](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-upload-limit-keyword

What are the maximum Files API upload size and upload duration?

- Category: keyword; split: dev; family: file-upload-limit; answerable: true

Expected answer points:

- The file limit is 64 MiB and upload must complete within 10 minutes.

Evidence:

- [guides/files_api, lines 21–21](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-expiry-semantic

How do I make an image expire automatically, and how do I keep it permanently instead?

- Category: semantic; split: dev; family: file-expiry; answerable: true

Expected answer points:

- Use expires_after[anchor]=created_at together with expires_after[seconds].
- The lifetime range is 3600 to 2592000 seconds; omitting both fields keeps the file permanently.

Evidence:

- [guides/files_api, lines 25–30](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-expiry-keyword

What anchor and seconds range does expires_after require, and what does omitting both fields do?

- Category: keyword; split: dev; family: file-expiry; answerable: true

Expected answer points:

- Use expires_after[anchor]=created_at together with expires_after[seconds].
- The lifetime range is 3600 to 2592000 seconds; omitting both fields keeps the file permanently.

Evidence:

- [guides/files_api, lines 25–30](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-expiry-result-semantic

Will every upload response include an expiration timestamp even if I chose permanent storage?

- Category: semantic; split: dev; family: file-expiry-result; answerable: true

Expected answer points:

- expires_at is present only when expiration was set at upload time.

Evidence:

- [api/create-file, lines 76–78](../materials/deepseek/md/api/create-file.md) — https://api-docs.deepseek.com/api/create-file

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-expiry-result-keyword

When is expires_at present in the Upload File response?

- Category: keyword; split: dev; family: file-expiry-result; answerable: true

Expected answer points:

- expires_at is present only when expiration was set at upload time.

Evidence:

- [api/create-file, lines 76–78](../materials/deepseek/md/api/create-file.md) — https://api-docs.deepseek.com/api/create-file

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-pagination-semantic

How can I request the next batch of uploaded files and choose their creation-time ordering?

- Category: semantic; split: test; family: file-pagination; answerable: true

Expected answer points:

- after is a file_id cursor returning files after that file.
- order sorts by creation time, with asc as default and desc as the alternative.

Evidence:

- [api/list-files, lines 16–18](../materials/deepseek/md/api/list-files.md) — https://api-docs.deepseek.com/api/list-files
- [api/list-files, lines 28–34](../materials/deepseek/md/api/list-files.md) — https://api-docs.deepseek.com/api/list-files

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-pagination-keyword

What do after and order mean for GET /files, and what is the default order?

- Category: keyword; split: test; family: file-pagination; answerable: true

Expected answer points:

- after is a file_id cursor returning files after that file.
- order sorts by creation time, with asc as default and desc as the alternative.

Evidence:

- [api/list-files, lines 16–18](../materials/deepseek/md/api/list-files.md) — https://api-docs.deepseek.com/api/list-files
- [api/list-files, lines 28–34](../materials/deepseek/md/api/list-files.md) — https://api-docs.deepseek.com/api/list-files

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-list-size-semantic

How many stored files can I request in one page, and what page size is used if I omit it?

- Category: semantic; split: test; family: file-list-size; answerable: true

Expected answer points:

- The range is 1–1000 and the default is 1000.

Evidence:

- [api/list-files, lines 20–26](../materials/deepseek/md/api/list-files.md) — https://api-docs.deepseek.com/api/list-files
- [api/list-files, lines 20–24](../materials/deepseek/md/api/list-files.md) — https://api-docs.deepseek.com/api/list-files

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-list-size-keyword

What range and default apply to limit in the OpenAI-compatible GET /files endpoint?

- Category: keyword; split: test; family: file-list-size; answerable: true

Expected answer points:

- The range is 1–1000 and the default is 1000.

Evidence:

- [api/list-files, lines 20–26](../materials/deepseek/md/api/list-files.md) — https://api-docs.deepseek.com/api/list-files
- [api/list-files, lines 20–24](../materials/deepseek/md/api/list-files.md) — https://api-docs.deepseek.com/api/list-files

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-pagination-marker-semantic

How does a file listing tell me there are further results beyond the page I received?

- Category: semantic; split: dev; family: file-pagination-marker; answerable: true

Expected answer points:

- has_more indicates whether more files exist beyond the current page.

Evidence:

- [api/list-files, lines 106–108](../materials/deepseek/md/api/list-files.md) — https://api-docs.deepseek.com/api/list-files

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-pagination-marker-keyword

What does has_more mean in List Files?

- Category: keyword; split: dev; family: file-pagination-marker; answerable: true

Expected answer points:

- has_more indicates whether more files exist beyond the current page.

Evidence:

- [api/list-files, lines 106–108](../materials/deepseek/md/api/list-files.md) — https://api-docs.deepseek.com/api/list-files

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-inline-exclusive-semantic

Can one file content block include both an uploaded-file reference and inline image bytes, and when is a filename allowed?

- Category: semantic; split: test; family: file-inline-exclusive; answerable: true

Expected answer points:

- file_id and file_data are mutually exclusive; filename is allowed with file_data but not with file_id.

Evidence:

- [guides/files_api, lines 172–172](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-inline-exclusive-keyword

Explain file_id versus file_data and the filename restriction in a file block.

- Category: keyword; split: test; family: file-inline-exclusive; answerable: true

Expected answer points:

- file_id and file_data are mutually exclusive; filename is allowed with file_data but not with file_id.

Evidence:

- [guides/files_api, lines 172–172](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-ownership-semantic

Can I use an image uploaded through one API family with the other family, and what extra header is required for the latter?

- Category: semantic; split: dev; family: file-ownership; answerable: true

Expected answer points:

- Files belong to the API key and can be referenced from either API family; Anthropic /messages file references require anthropic-beta: files-api-2025-04-14.

Evidence:

- [guides/files_api, lines 168–168](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-ownership-keyword

Who owns uploaded files, and what header is required for file_id references from Anthropic /messages?

- Category: keyword; split: dev; family: file-ownership; answerable: true

Expected answer points:

- Files belong to the API key and can be referenced from either API family; Anthropic /messages file references require anthropic-beta: files-api-2025-04-14.

Evidence:

- [guides/files_api, lines 168–168](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-anthropic-file-path-semantic

A raw HTTP client and an SDK use the same Anthropic-compatible base address. Why does only the raw client need to add the version path?

- Category: semantic; split: test; family: anthropic-file-path; answerable: true

Expected answer points:

- The base URL is https://api.deepseek.com/anthropic.
- The SDK appends /v1 automatically; a plain HTTP client must use the full /anthropic/v1/ path.

Evidence:

- [guides/files_api, lines 178–178](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api
- [guides/files_api, lines 180–180](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-anthropic-file-path-keyword

What is the Anthropic Files API base_url, and who appends /v1?

- Category: keyword; split: test; family: anthropic-file-path; answerable: true

Expected answer points:

- The base URL is https://api.deepseek.com/anthropic.
- The SDK appends /v1 automatically; a plain HTTP client must use the full /anthropic/v1/ path.

Evidence:

- [guides/files_api, lines 178–178](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api
- [guides/files_api, lines 180–180](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-list-family-semantic

When switching the file listing client from the OpenAI interface to Anthropic, what happens to the cursor names and default page size?

- Category: semantic; split: dev; family: file-list-family; answerable: true

Expected answer points:

- OpenAI uses after; Anthropic uses mutually exclusive after_id/before_id.
- OpenAI defaults to 1000 and Anthropic to 20; both allow 1–1000.

Evidence:

- [guides/files_api, lines 184–193](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-list-family-keyword

Compare after with after_id/before_id and default limit across the two Files API families.

- Category: keyword; split: dev; family: file-list-family; answerable: true

Expected answer points:

- OpenAI uses after; Anthropic uses mutually exclusive after_id/before_id.
- OpenAI defaults to 1000 and Anthropic to 20; both allow 1–1000.

Evidence:

- [guides/files_api, lines 184–193](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-metadata-family-semantic

Which size-field name and creation-time representation change when I switch file metadata between the two interface families?

- Category: semantic; split: dev; family: file-metadata-family; answerable: true

Expected answer points:

- OpenAI uses bytes; Anthropic uses size_bytes.
- OpenAI created_at is Unix seconds; Anthropic created_at is an RFC 3339 string.

Evidence:

- [guides/files_api, lines 184–193](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-metadata-family-keyword

Compare bytes versus size_bytes and the created_at formats in the two Files APIs.

- Category: keyword; split: dev; family: file-metadata-family; answerable: true

Expected answer points:

- OpenAI uses bytes; Anthropic uses size_bytes.
- OpenAI created_at is Unix seconds; Anthropic created_at is an RFC 3339 string.

Evidence:

- [guides/files_api, lines 184–193](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-storage-limits-semantic

What limits apply to the length of image filenames, total stored space, and number of stored images?

- Category: semantic; split: dev; family: file-storage-limits; answerable: true

Expected answer points:

- Filename length is at most 512 characters.
- Storage is at most 25 GiB per user.
- At most 10000 files may be stored per user.

Evidence:

- [guides/files_api, lines 240–247](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-storage-limits-keyword

Give the Files API max filename length, max storage per user and max stored files per user.

- Category: keyword; split: dev; family: file-storage-limits; answerable: true

Expected answer points:

- Filename length is at most 512 characters.
- Storage is at most 25 GiB per user.
- At most 10000 files may be stored per user.

Evidence:

- [guides/files_api, lines 240–247](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-delete-semantic

How do I remove one uploaded file, and which response flag tells me whether it was deleted?

- Category: semantic; split: dev; family: file-delete; answerable: true

Expected answer points:

- Use DELETE /files/:file_id.
- deleted indicates whether the file was successfully deleted.

Evidence:

- [api/delete-file, lines 6–8](../materials/deepseek/md/api/delete-file.md) — https://api-docs.deepseek.com/api/delete-file
- [api/delete-file, lines 36–38](../materials/deepseek/md/api/delete-file.md) — https://api-docs.deepseek.com/api/delete-file

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-delete-keyword

What endpoint deletes file_id and what does the deleted boolean mean?

- Category: keyword; split: dev; family: file-delete; answerable: true

Expected answer points:

- Use DELETE /files/:file_id.
- deleted indicates whether the file was successfully deleted.

Evidence:

- [api/delete-file, lines 6–8](../materials/deepseek/md/api/delete-file.md) — https://api-docs.deepseek.com/api/delete-file
- [api/delete-file, lines 36–38](../materials/deepseek/md/api/delete-file.md) — https://api-docs.deepseek.com/api/delete-file

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-retrieve-semantic

How do I inspect information about a single stored image rather than list all images?

- Category: semantic; split: test; family: file-retrieve; answerable: true

Expected answer points:

- GET /files/:file_id returns information about the specified file.

Evidence:

- [api/retrieve-file, lines 6–8](../materials/deepseek/md/api/retrieve-file.md) — https://api-docs.deepseek.com/api/retrieve-file
- [api/retrieve-file, lines 10–10](../materials/deepseek/md/api/retrieve-file.md) — https://api-docs.deepseek.com/api/retrieve-file

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-file-retrieve-keyword

What does GET /files/:file_id return?

- Category: keyword; split: test; family: file-retrieve; answerable: true

Expected answer points:

- GET /files/:file_id returns information about the specified file.

Evidence:

- [api/retrieve-file, lines 6–8](../materials/deepseek/md/api/retrieve-file.md) — https://api-docs.deepseek.com/api/retrieve-file
- [api/retrieve-file, lines 10–10](../materials/deepseek/md/api/retrieve-file.md) — https://api-docs.deepseek.com/api/retrieve-file

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-vision-detection-semantic

If an image is mislabeled by its file extension or declared media type, what determines its actual format and which formats are accepted?

- Category: semantic; split: dev; family: vision-detection; answerable: true

Expected answer points:

- JPEG, PNG, GIF and WebP are supported; detection uses actual content rather than the filename or declared MIME type.

Evidence:

- [guides/vision, lines 8–8](../materials/deepseek/md/guides/vision.md) — https://api-docs.deepseek.com/guides/vision

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-vision-detection-keyword

Does Vision detect JPEG, PNG, GIF and WebP by content, filename, or MIME type?

- Category: keyword; split: dev; family: vision-detection; answerable: true

Expected answer points:

- JPEG, PNG, GIF and WebP are supported; detection uses actual content rather than the filename or declared MIME type.

Evidence:

- [guides/vision, lines 8–8](../materials/deepseek/md/guides/vision.md) — https://api-docs.deepseek.com/guides/vision

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-vision-url-semantic

I want the service to fetch an image from the web. What limits apply to the link length, download size, and download duration?

- Category: semantic; split: dev; family: vision-url; answerable: true

Expected answer points:

- A public image URL can be at most 8192 characters; the image at most 32 MiB; download must finish within 60 seconds.

Evidence:

- [guides/vision, lines 69–69](../materials/deepseek/md/guides/vision.md) — https://api-docs.deepseek.com/guides/vision

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-vision-url-keyword

What are the external http(s) image URL length, size and timeout limits?

- Category: keyword; split: dev; family: vision-url; answerable: true

Expected answer points:

- A public image URL can be at most 8192 characters; the image at most 32 MiB; download must finish within 60 seconds.

Evidence:

- [guides/vision, lines 69–69](../materials/deepseek/md/guides/vision.md) — https://api-docs.deepseek.com/guides/vision

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-vision-reuse-semantic

Repeatedly embedding the same large image bloats my requests. What alternative avoids resending its bytes and permits a larger image?

- Category: semantic; split: dev; family: vision-reuse; answerable: true

Expected answer points:

- Upload once and reuse file_id; this avoids repeated inline bytes and permits images up to 64 MiB rather than the 32 MiB inline limit.

Evidence:

- [guides/vision, lines 92–92](../materials/deepseek/md/guides/vision.md) — https://api-docs.deepseek.com/guides/vision

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-vision-reuse-keyword

Why use Files API file_id instead of inline base64, and what per-image size can file_id support?

- Category: keyword; split: dev; family: vision-reuse; answerable: true

Expected answer points:

- Upload once and reuse file_id; this avoids repeated inline bytes and permits images up to 64 MiB rather than the 32 MiB inline limit.

Evidence:

- [guides/vision, lines 92–92](../materials/deepseek/md/guides/vision.md) — https://api-docs.deepseek.com/guides/vision

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-responses-stream-end-semantic

How can my Responses stream reader distinguish a finished, cut-short, or failed reply? Should it wait for the old completion sentinel?

- Category: semantic; split: dev; family: responses-stream-end; answerable: true

Expected answer points:

- The terminal events are response.completed, response.incomplete and response.failed; there is no data: [DONE] message.

Evidence:

- [guides/responses_api, lines 33–33](../materials/deepseek/md/guides/responses_api.md) — https://api-docs.deepseek.com/guides/responses_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-responses-stream-end-keyword

Which terminal events replace data: [DONE] in the Responses API?

- Category: keyword; split: dev; family: responses-stream-end; answerable: true

Expected answer points:

- The terminal events are response.completed, response.incomplete and response.failed; there is no data: [DONE] message.

Evidence:

- [guides/responses_api, lines 33–33](../materials/deepseek/md/guides/responses_api.md) — https://api-docs.deepseek.com/guides/responses_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-responses-sequence-semantic

How does the Responses stream label events and give their ordering?

- Category: semantic; split: dev; family: responses-sequence; answerable: true

Expected answer points:

- event identifies event type and sequence_number increases monotonically.

Evidence:

- [guides/responses_api, lines 33–33](../materials/deepseek/md/guides/responses_api.md) — https://api-docs.deepseek.com/guides/responses_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-responses-sequence-keyword

What do event and sequence_number identify in a Responses API SSE stream?

- Category: keyword; split: dev; family: responses-sequence; answerable: true

Expected answer points:

- event identifies event type and sequence_number increases monotonically.

Evidence:

- [guides/responses_api, lines 33–33](../materials/deepseek/md/guides/responses_api.md) — https://api-docs.deepseek.com/guides/responses_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-responses-image-exclusive-semantic

Can an image input omit both its URL and stored-file reference, or supply both at once?

- Category: semantic; split: dev; family: responses-image-exclusive; answerable: true

Expected answer points:

- image_url and file_id are mutually exclusive; neither or both yields HTTP 400.

Evidence:

- [guides/responses_api, lines 103–103](../materials/deepseek/md/guides/responses_api.md) — https://api-docs.deepseek.com/guides/responses_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-responses-image-exclusive-keyword

What happens when input_image has neither or both image_url and file_id?

- Category: keyword; split: dev; family: responses-image-exclusive; answerable: true

Expected answer points:

- image_url and file_id are mutually exclusive; neither or both yields HTTP 400.

Evidence:

- [guides/responses_api, lines 103–103](../materials/deepseek/md/guides/responses_api.md) — https://api-docs.deepseek.com/guides/responses_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-responses-image-roles-semantic

May I place image input in a system or assistant message, or only in user-like messages and tool outputs?

- Category: semantic; split: test; family: responses-image-roles; answerable: true

Expected answer points:

- Images are allowed in user/developer messages and function_call_output/custom_tool_call_output; system or assistant images return 400.

Evidence:

- [guides/responses_api, lines 107–109](../materials/deepseek/md/guides/responses_api.md) — https://api-docs.deepseek.com/guides/responses_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-responses-image-roles-keyword

Which message roles and tool-output item types accept input_image in Responses?

- Category: keyword; split: test; family: responses-image-roles; answerable: true

Expected answer points:

- Images are allowed in user/developer messages and function_call_output/custom_tool_call_output; system or assistant images return 400.

Evidence:

- [guides/responses_api, lines 107–109](../materials/deepseek/md/guides/responses_api.md) — https://api-docs.deepseek.com/guides/responses_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-responses-state-semantic

Can the compatible Responses service resume a stored conversation just from a previous response identifier?

- Category: semantic; split: dev; family: responses-state; answerable: true

Expected answer points:

- previous_response_id and conversation are unsupported because the API is stateless.
- store is unsupported and the response carries store:false.

Evidence:

- [guides/responses_api, lines 117–146](../materials/deepseek/md/guides/responses_api.md) — https://api-docs.deepseek.com/guides/responses_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-responses-state-keyword

Are previous_response_id, conversation and store supported by DeepSeek Responses?

- Category: keyword; split: dev; family: responses-state; answerable: true

Expected answer points:

- previous_response_id and conversation are unsupported because the API is stateless.
- store is unsupported and the response carries store:false.

Evidence:

- [guides/responses_api, lines 117–146](../materials/deepseek/md/guides/responses_api.md) — https://api-docs.deepseek.com/guides/responses_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-responses-ignored-semantic

If my existing Responses client sends unsupported options, does that automatically make the request fail?

- Category: semantic; split: dev; family: responses-ignored; answerable: true

Expected answer points:

- Unsupported parameters are silently ignored and do not cause errors.

Evidence:

- [guides/responses_api, lines 148–148](../materials/deepseek/md/guides/responses_api.md) — https://api-docs.deepseek.com/guides/responses_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-responses-ignored-keyword

What happens to unsupported top-level Responses API parameters?

- Category: keyword; split: dev; family: responses-ignored; answerable: true

Expected answer points:

- Unsupported parameters are silently ignored and do not cause errors.

Evidence:

- [guides/responses_api, lines 148–148](../materials/deepseek/md/guides/responses_api.md) — https://api-docs.deepseek.com/guides/responses_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-responses-truncation-semantic

Can the service automatically trim an oversized conversation if I request truncation?

- Category: semantic; split: dev; family: responses-truncation; answerable: true

Expected answer points:

- truncation is unsupported; context-window overflow returns HTTP 400.

Evidence:

- [guides/responses_api, lines 117–146](../materials/deepseek/md/guides/responses_api.md) — https://api-docs.deepseek.com/guides/responses_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-responses-truncation-keyword

Is Responses truncation supported, and what happens when input exceeds the context window?

- Category: keyword; split: dev; family: responses-truncation; answerable: true

Expected answer points:

- truncation is unsupported; context-window overflow returns HTTP 400.

Evidence:

- [guides/responses_api, lines 117–146](../materials/deepseek/md/guides/responses_api.md) — https://api-docs.deepseek.com/guides/responses_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-responses-patch-semantic

Can I define an arbitrary custom tool name in this Responses-compatible service?

- Category: semantic; split: dev; family: responses-patch; answerable: true

Expected answer points:

- Only the apply_patch custom tool is supported; other custom names return 400.

Evidence:

- [guides/responses_api, lines 168–168](../materials/deepseek/md/guides/responses_api.md) — https://api-docs.deepseek.com/guides/responses_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-responses-patch-keyword

Which custom tool name is supported, and what happens to other custom names?

- Category: keyword; split: dev; family: responses-patch; answerable: true

Expected answer points:

- Only the apply_patch custom tool is supported; other custom names return 400.

Evidence:

- [guides/responses_api, lines 168–168](../materials/deepseek/md/guides/responses_api.md) — https://api-docs.deepseek.com/guides/responses_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-responses-parallel-semantic

Will disabling parallel function calls in my Responses request force calls to be serial?

- Category: semantic; split: dev; family: responses-parallel; answerable: true

Expected answer points:

- It is ignored; parallel tool calling is always enabled.

Evidence:

- [guides/responses_api, lines 117–146](../materials/deepseek/md/guides/responses_api.md) — https://api-docs.deepseek.com/guides/responses_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-responses-parallel-keyword

What happens to parallel_tool_calls in DeepSeek Responses?

- Category: keyword; split: dev; family: responses-parallel; answerable: true

Expected answer points:

- It is ignored; parallel tool calling is always enabled.

Evidence:

- [guides/responses_api, lines 117–146](../materials/deepseek/md/guides/responses_api.md) — https://api-docs.deepseek.com/guides/responses_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-responses-verbosity-semantic

Does the compatibility layer honor verbosity and reasoning-summary requests?

- Category: semantic; split: dev; family: responses-verbosity; answerable: true

Expected answer points:

- text.verbosity is accepted but has no effect.
- reasoning.summary is accepted but no summary is generated.

Evidence:

- [guides/responses_api, lines 117–146](../materials/deepseek/md/guides/responses_api.md) — https://api-docs.deepseek.com/guides/responses_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-responses-verbosity-keyword

How are text.verbosity and reasoning.summary handled by DeepSeek Responses?

- Category: keyword; split: dev; family: responses-verbosity; answerable: true

Expected answer points:

- text.verbosity is accepted but has no effect.
- reasoning.summary is accepted but no summary is generated.

Evidence:

- [guides/responses_api, lines 117–146](../materials/deepseek/md/guides/responses_api.md) — https://api-docs.deepseek.com/guides/responses_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-anthropic-model-map-semantic

My client insists on Claude model-name prefixes. Which DeepSeek backends do the larger and smaller Claude families select?

- Category: semantic; split: dev; family: anthropic-model-map; answerable: true

Expected answer points:

- claude-opus maps to deepseek-v4-pro.
- claude-haiku and claude-sonnet map to deepseek-flash.

Evidence:

- [guides/anthropic_api, lines 65–66](../materials/deepseek/md/guides/anthropic_api.md) — https://api-docs.deepseek.com/guides/anthropic_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-anthropic-model-map-keyword

How are claude-opus, claude-haiku and claude-sonnet model prefixes mapped?

- Category: keyword; split: dev; family: anthropic-model-map; answerable: true

Expected answer points:

- claude-opus maps to deepseek-v4-pro.
- claude-haiku and claude-sonnet map to deepseek-flash.

Evidence:

- [guides/anthropic_api, lines 65–66](../materials/deepseek/md/guides/anthropic_api.md) — https://api-docs.deepseek.com/guides/anthropic_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-anthropic-effort-semantic

Will the Anthropic compatibility layer use my explicit thinking-token budget and all output configuration options?

- Category: semantic; split: dev; family: anthropic-effort; answerable: true

Expected answer points:

- thinking is supported but budget_tokens is ignored.
- Only effort is supported within output_config.

Evidence:

- [guides/anthropic_api, lines 88–103](../materials/deepseek/md/guides/anthropic_api.md) — https://api-docs.deepseek.com/guides/anthropic_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-anthropic-effort-keyword

How are thinking.budget_tokens and output_config handled in the Anthropic API?

- Category: keyword; split: dev; family: anthropic-effort; answerable: true

Expected answer points:

- thinking is supported but budget_tokens is ignored.
- Only effort is supported within output_config.

Evidence:

- [guides/anthropic_api, lines 88–103](../materials/deepseek/md/guides/anthropic_api.md) — https://api-docs.deepseek.com/guides/anthropic_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-anthropic-metadata-semantic

Which user-specific metadata field survives the Anthropic compatibility layer?

- Category: semantic; split: dev; family: anthropic-metadata; answerable: true

Expected answer points:

- metadata.user_id is supported; other metadata fields are ignored.

Evidence:

- [guides/anthropic_api, lines 88–103](../materials/deepseek/md/guides/anthropic_api.md) — https://api-docs.deepseek.com/guides/anthropic_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-anthropic-metadata-keyword

Which metadata subfield is supported by the Anthropic API?

- Category: keyword; split: dev; family: anthropic-metadata; answerable: true

Expected answer points:

- metadata.user_id is supported; other metadata fields are ignored.

Evidence:

- [guides/anthropic_api, lines 88–103](../materials/deepseek/md/guides/anthropic_api.md) — https://api-docs.deepseek.com/guides/anthropic_api

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-concurrency-account-semantic

Can I multiply my simultaneous-request allowance by creating several API keys under the same account?

- Category: semantic; split: dev; family: concurrency-account; answerable: true

Expected answer points:

- Limits apply at account level regardless of API key.
- A request counts from being sent until the model response completes.

Evidence:

- [quick_start/rate_limit, lines 16–18](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-concurrency-account-keyword

Are concurrency limits per account or per API Key, and when does a request count as concurrent?

- Category: keyword; split: dev; family: concurrency-account; answerable: true

Expected answer points:

- Limits apply at account level regardless of API key.
- A request counts from being sent until the model response completes.

Evidence:

- [quick_start/rate_limit, lines 16–18](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-concurrency-values-semantic

How many requests can each current model handle at once for an account, and what happens if I exceed that?

- Category: semantic; split: dev; family: concurrency-values; answerable: true

Expected answer points:

- Flash allows 2500 and V4 Pro allows 500 concurrent requests.
- Exceeding the limit returns HTTP 429.

Evidence:

- [quick_start/rate_limit, lines 12–14](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit
- [quick_start/rate_limit, lines 16–18](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-concurrency-values-keyword

Give deepseek-flash and deepseek-v4-pro concurrency limits and the over-limit HTTP code.

- Category: keyword; split: dev; family: concurrency-values; answerable: true

Expected answer points:

- Flash allows 2500 and V4 Pro allows 500 concurrent requests.
- Exceeding the limit returns HTTP 429.

Evidence:

- [quick_start/rate_limit, lines 12–14](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit
- [quick_start/rate_limit, lines 16–18](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-concurrency-expansion-semantic

What should I do if my application needs more simultaneous requests, and is there an extra expansion fee?

- Category: semantic; split: dev; family: concurrency-expansion; answerable: true

Expected answer points:

- Submit a capacity expansion request; concurrency is matched to actual business needs and expansion has no additional cost.

Evidence:

- [quick_start/rate_limit, lines 10–10](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-concurrency-expansion-keyword

How do I request higher concurrency and what is the capacity-expansion cost?

- Category: keyword; split: dev; family: concurrency-expansion; answerable: true

Expected answer points:

- Submit a capacity expansion request; concurrency is matched to actual business needs and expansion has no additional cost.

Evidence:

- [quick_start/rate_limit, lines 10–10](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-user-isolation-semantic

How can I distinguish my application users for safety handling, cached context privacy, and scheduling under a shared account?

- Category: semantic; split: test; family: user-isolation; answerable: true

Expected answer points:

- user_id provides content safety isolation.
- It provides KVCache isolation for privacy management.
- It provides scheduling isolation.

Evidence:

- [quick_start/rate_limit, lines 26–30](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-user-isolation-keyword

List the three isolation functions of user_id.

- Category: keyword; split: test; family: user-isolation; answerable: true

Expected answer points:

- user_id provides content safety isolation.
- It provides KVCache isolation for privacy management.
- It provides scheduling isolation.

Evidence:

- [quick_start/rate_limit, lines 26–30](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-user-id-format-semantic

What characters and maximum length may I use for an application-user identifier, and should it contain private user details?

- Category: semantic; split: dev; family: user-id-format; answerable: true

Expected answer points:

- user_id must match [a-zA-Z0-9\-_]+, be at most 512 characters, and contain no user privacy information.

Evidence:

- [quick_start/rate_limit, lines 34–34](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-user-id-format-keyword

What regex, maximum length and privacy restriction apply to user_id?

- Category: keyword; split: dev; family: user-id-format; answerable: true

Expected answer points:

- user_id must match [a-zA-Z0-9\-_]+, be at most 512 characters, and contain no user privacy information.

Evidence:

- [quick_start/rate_limit, lines 34–34](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-keepalive-semantic

The server keeps the connection open but sends blank lines or comment-like events before answering. What are these, and how long can inference remain unstarted?

- Category: semantic; split: dev; family: keepalive; answerable: true

Expected answer points:

- Non-streaming uses empty lines; streaming uses SSE comments : keep-alive.
- The server closes the connection if inference has not started after 10 minutes.

Evidence:

- [quick_start/rate_limit, lines 90–91](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit
- [quick_start/rate_limit, lines 95–95](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-keepalive-keyword

What are non-streaming and SSE keep-alive payloads, and what is the no-inference timeout?

- Category: keyword; split: dev; family: keepalive; answerable: true

Expected answer points:

- Non-streaming uses empty lines; streaming uses SSE comments : keep-alive.
- The server closes the connection if inference has not started after 10 minutes.

Evidence:

- [quick_start/rate_limit, lines 90–91](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit
- [quick_start/rate_limit, lines 95–95](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-prices-units-semantic

Are the price-table amounts per request or per quantity of generated and supplied text?

- Category: semantic; split: dev; family: prices-units; answerable: true

Expected answer points:

- Prices are per 1M tokens and billing uses total input and output tokens.

Evidence:

- [quick_start/pricing, lines 6–6](../materials/deepseek/md/quick_start/pricing.md) — https://api-docs.deepseek.com/quick_start/pricing

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-prices-units-keyword

What unit do the prices use and which token directions are billed?

- Category: keyword; split: dev; family: prices-units; answerable: true

Expected answer points:

- Prices are per 1M tokens and billing uses total input and output tokens.

Evidence:

- [quick_start/pricing, lines 6–6](../materials/deepseek/md/quick_start/pricing.md) — https://api-docs.deepseek.com/quick_start/pricing

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-model-versions-semantic

According specifically to the captured Models & Pricing table, which model versions are listed for Flash and Pro?

- Category: semantic; split: dev; family: model-versions; answerable: true

Expected answer points:

- Flash is DeepSeek-V4.1-Flash and Pro is DeepSeek-V4-Pro-0813.

Evidence:

- [quick_start/pricing, lines 12–33](../materials/deepseek/md/quick_start/pricing.md) — https://api-docs.deepseek.com/quick_start/pricing

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-model-versions-keyword

Map deepseek-flash and deepseek-v4-pro to their MODEL VERSION values.

- Category: keyword; split: dev; family: model-versions; answerable: true

Expected answer points:

- Flash is DeepSeek-V4.1-Flash and Pro is DeepSeek-V4-Pro-0813.

Evidence:

- [quick_start/pricing, lines 12–33](../materials/deepseek/md/quick_start/pricing.md) — https://api-docs.deepseek.com/quick_start/pricing

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-context-output-semantic

How much context and how much maximum generated output do the two current models support?

- Category: semantic; split: dev; family: context-output; answerable: true

Expected answer points:

- Both list a 1M context length.
- Both list a maximum output of 384K.

Evidence:

- [quick_start/pricing, lines 12–33](../materials/deepseek/md/quick_start/pricing.md) — https://api-docs.deepseek.com/quick_start/pricing

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-context-output-keyword

What CONTEXT LENGTH and MAX OUTPUT are listed for Flash and V4 Pro?

- Category: keyword; split: dev; family: context-output; answerable: true

Expected answer points:

- Both list a 1M context length.
- Both list a maximum output of 384K.

Evidence:

- [quick_start/pricing, lines 12–33](../materials/deepseek/md/quick_start/pricing.md) — https://api-docs.deepseek.com/quick_start/pricing

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-peak-hours-semantic

When do higher token rates apply during the week, and do weekends or Chinese public holidays use those rates?

- Category: semantic; split: test; family: peak-hours; answerable: true

Expected answer points:

- Peak hours are 01:00–04:00 and 06:00–10:00 UTC Monday–Friday excluding Chinese public holidays; all other hours, weekends and holidays are off-peak; off-peak rates are half peak.

Evidence:

- [quick_start/pricing, lines 37–37](../materials/deepseek/md/quick_start/pricing.md) — https://api-docs.deepseek.com/quick_start/pricing

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-peak-hours-keyword

Give the UTC peak windows, applicable weekdays, holiday rule and off-peak discount.

- Category: keyword; split: test; family: peak-hours; answerable: true

Expected answer points:

- Peak hours are 01:00–04:00 and 06:00–10:00 UTC Monday–Friday excluding Chinese public holidays; all other hours, weekends and holidays are off-peak; off-peak rates are half peak.

Evidence:

- [quick_start/pricing, lines 37–37](../materials/deepseek/md/quick_start/pricing.md) — https://api-docs.deepseek.com/quick_start/pricing

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-balance-priority-semantic

If my account has both promotional credit and money I topped up, which is spent first?

- Category: semantic; split: dev; family: balance-priority; answerable: true

Expected answer points:

- The granted balance is used first when both granted and topped-up balances are available.

Evidence:

- [quick_start/pricing, lines 45–45](../materials/deepseek/md/quick_start/pricing.md) — https://api-docs.deepseek.com/quick_start/pricing

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-balance-priority-keyword

What is the deduction priority for granted balance versus topped-up balance?

- Category: keyword; split: dev; family: balance-priority; answerable: true

Expected answer points:

- The granted balance is used first when both granted and topped-up balances are available.

Evidence:

- [quick_start/pricing, lines 45–45](../materials/deepseek/md/quick_start/pricing.md) — https://api-docs.deepseek.com/quick_start/pricing

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-balance-api-semantic

Which request checks my account balance, and which flag indicates it is sufficient to make calls?

- Category: semantic; split: dev; family: balance-api; answerable: true

Expected answer points:

- Use GET /user/balance.
- is_available indicates whether the balance is sufficient for API calls.

Evidence:

- [api/get-user-balance, lines 6–8](../materials/deepseek/md/api/get-user-balance.md) — https://api-docs.deepseek.com/api/get-user-balance
- [api/get-user-balance, lines 18–20](../materials/deepseek/md/api/get-user-balance.md) — https://api-docs.deepseek.com/api/get-user-balance

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-balance-api-keyword

What endpoint returns balance information and what does is_available mean?

- Category: keyword; split: dev; family: balance-api; answerable: true

Expected answer points:

- Use GET /user/balance.
- is_available indicates whether the balance is sufficient for API calls.

Evidence:

- [api/get-user-balance, lines 6–8](../materials/deepseek/md/api/get-user-balance.md) — https://api-docs.deepseek.com/api/get-user-balance
- [api/get-user-balance, lines 18–20](../materials/deepseek/md/api/get-user-balance.md) — https://api-docs.deepseek.com/api/get-user-balance

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-balance-total-semantic

What does the available balance include, and what currency identifiers can the response use?

- Category: semantic; split: dev; family: balance-total; answerable: true

Expected answer points:

- total_balance includes granted and topped-up balances.
- Currency values are CNY and USD.

Evidence:

- [api/get-user-balance, lines 34–36](../materials/deepseek/md/api/get-user-balance.md) — https://api-docs.deepseek.com/api/get-user-balance
- [api/get-user-balance, lines 28–30](../materials/deepseek/md/api/get-user-balance.md) — https://api-docs.deepseek.com/api/get-user-balance

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-balance-total-keyword

Define total_balance and list currency values in Get User Balance.

- Category: keyword; split: dev; family: balance-total; answerable: true

Expected answer points:

- total_balance includes granted and topped-up balances.
- Currency values are CNY and USD.

Evidence:

- [api/get-user-balance, lines 34–36](../materials/deepseek/md/api/get-user-balance.md) — https://api-docs.deepseek.com/api/get-user-balance
- [api/get-user-balance, lines 28–30](../materials/deepseek/md/api/get-user-balance.md) — https://api-docs.deepseek.com/api/get-user-balance

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-models-list-semantic

How do I discover available model identifiers and find out which organization owns each model?

- Category: semantic; split: dev; family: models-list; answerable: true

Expected answer points:

- GET /models lists models.
- id is the model identifier usable in endpoints.
- owned_by identifies the owning organization.

Evidence:

- [api/list-models, lines 6–8](../materials/deepseek/md/api/list-models.md) — https://api-docs.deepseek.com/api/list-models
- [api/list-models, lines 30–32](../materials/deepseek/md/api/list-models.md) — https://api-docs.deepseek.com/api/list-models
- [api/list-models, lines 40–42](../materials/deepseek/md/api/list-models.md) — https://api-docs.deepseek.com/api/list-models

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-models-list-keyword

What endpoint lists models, and what do id and owned_by represent?

- Category: keyword; split: dev; family: models-list; answerable: true

Expected answer points:

- GET /models lists models.
- id is the model identifier usable in endpoints.
- owned_by identifies the owning organization.

Evidence:

- [api/list-models, lines 6–8](../materials/deepseek/md/api/list-models.md) — https://api-docs.deepseek.com/api/list-models
- [api/list-models, lines 30–32](../materials/deepseek/md/api/list-models.md) — https://api-docs.deepseek.com/api/list-models
- [api/list-models, lines 40–42](../materials/deepseek/md/api/list-models.md) — https://api-docs.deepseek.com/api/list-models

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-text-token-estimate-semantic

Can I calculate exact billed usage just by counting English letters, or is that only an estimate?

- Category: semantic; split: dev; family: text-token-estimate; answerable: true

Expected answer points:

- An English character is approximately 0.3 token; a Chinese character approximately 0.6 token.
- Ratios vary with tokenization; the model-returned usage is authoritative.

Evidence:

- [quick_start/token_usage, lines 10–11](../materials/deepseek/md/quick_start/token_usage.md) — https://api-docs.deepseek.com/quick_start/token_usage
- [quick_start/token_usage, lines 13–13](../materials/deepseek/md/quick_start/token_usage.md) — https://api-docs.deepseek.com/quick_start/token_usage

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-text-token-estimate-keyword

What approximate token ratios are given for English and Chinese characters, and what is the source of truth?

- Category: keyword; split: dev; family: text-token-estimate; answerable: true

Expected answer points:

- An English character is approximately 0.3 token; a Chinese character approximately 0.6 token.
- Ratios vary with tokenization; the model-returned usage is authoritative.

Evidence:

- [quick_start/token_usage, lines 10–11](../materials/deepseek/md/quick_start/token_usage.md) — https://api-docs.deepseek.com/quick_start/token_usage
- [quick_start/token_usage, lines 13–13](../materials/deepseek/md/quick_start/token_usage.md) — https://api-docs.deepseek.com/quick_start/token_usage

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-tokenizer-download-semantic

Where can I find the offline token-counting demonstration package linked by the documentation?

- Category: semantic; split: dev; family: tokenizer-download; answerable: true

Expected answer points:

- The linked package is https://cdn.deepseek.com/api-docs/deepseek_v4_tokenizer.zip.

Evidence:

- [quick_start/token_usage, lines 19–19](../materials/deepseek/md/quick_start/token_usage.md) — https://api-docs.deepseek.com/quick_start/token_usage

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-tokenizer-download-keyword

What is the URL behind deepseek_tokenizer.zip on the token usage page?

- Category: keyword; split: dev; family: tokenizer-download; answerable: true

Expected answer points:

- The linked package is https://cdn.deepseek.com/api-docs/deepseek_v4_tokenizer.zip.

Evidence:

- [quick_start/token_usage, lines 19–19](../materials/deepseek/md/quick_start/token_usage.md) — https://api-docs.deepseek.com/quick_start/token_usage

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-vision-detail-semantic

I need cheaper coarse visual understanding rather than fine image detail. Which setting resizes the image, and how?

- Category: semantic; split: test; family: vision-detail; answerable: true

Expected answer points:

- low downsizes to 512×512.
- high and original preserve the image; auto is currently equivalent to original.

Evidence:

- [guides/vision, lines 128–133](../materials/deepseek/md/guides/vision.md) — https://api-docs.deepseek.com/guides/vision

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-vision-detail-keyword

What do detail=low, high, original, and auto do in the Vision guide?

- Category: keyword; split: test; family: vision-detail; answerable: true

Expected answer points:

- low downsizes to 512×512.
- high and original preserve the image; auto is currently equivalent to original.

Evidence:

- [guides/vision, lines 128–133](../materials/deepseek/md/guides/vision.md) — https://api-docs.deepseek.com/guides/vision

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-vision-token-cap-semantic

Would a much larger image necessarily cost more image tokens after resizing, and are images in a batch counted together?

- Category: semantic; split: dev; family: vision-token-cap; answerable: true

Expected answer points:

- The upper bound is 1024 tokens per image; 2000×2000 and 5000×5000 examples use the same count after resizing, and each image is counted independently.

Evidence:

- [guides/vision, lines 163–163](../materials/deepseek/md/guides/vision.md) — https://api-docs.deepseek.com/guides/vision

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-vision-token-cap-keyword

What is the current per-image token upper bound, and how are multiple images counted?

- Category: keyword; split: dev; family: vision-token-cap; answerable: true

Expected answer points:

- The upper bound is 1024 tokens per image; 2000×2000 and 5000×5000 examples use the same count after resizing, and each image is counted independently.

Evidence:

- [guides/vision, lines 163–163](../materials/deepseek/md/guides/vision.md) — https://api-docs.deepseek.com/guides/vision

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-vision-batch-limits-semantic

How do the image-count and aggregate-size limits change when I include stored-file references?

- Category: semantic; split: dev; family: vision-batch-limits; answerable: true

Expected answer points:

- At most 600 images per request.
- The aggregate limit is 64 MiB without file_id images and up to 200 MiB including them.

Evidence:

- [guides/vision, lines 171–180](../materials/deepseek/md/guides/vision.md) — https://api-docs.deepseek.com/guides/vision

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-vision-batch-limits-keyword

Give max images per request and total image size with and without file_id images.

- Category: keyword; split: dev; family: vision-batch-limits; answerable: true

Expected answer points:

- At most 600 images per request.
- The aggregate limit is 64 MiB without file_id images and up to 200 MiB including them.

Evidence:

- [guides/vision, lines 171–180](../materials/deepseek/md/guides/vision.md) — https://api-docs.deepseek.com/guides/vision

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-vision-dimension-semantic

What image-side length is allowed for a small batch versus a batch of at least fifteen images?

- Category: semantic; split: dev; family: vision-dimension; answerable: true

Expected answer points:

- The general limit is 8192 px per side, reduced to 4096 px per side with 15 or more images.

Evidence:

- [guides/vision, lines 171–180](../materials/deepseek/md/guides/vision.md) — https://api-docs.deepseek.com/guides/vision

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-vision-dimension-keyword

What is the max image dimension for 14 versus 15 images in one request?

- Category: keyword; split: dev; family: vision-dimension; answerable: true

Expected answer points:

- The general limit is 8192 px per side, reduced to 4096 px per side with 15 or more images.

Evidence:

- [guides/vision, lines 171–180](../materials/deepseek/md/guides/vision.md) — https://api-docs.deepseek.com/guides/vision

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-error-400-semantic

My request body has the wrong shape. Which error and corrective action should I expect?

- Category: semantic; split: test; family: error-400; answerable: true

Expected answer points:

- HTTP 400 (Invalid Format): Invalid request body format. Modify the request body according to the error hints.

Evidence:

- [quick_start/error_codes, lines 10–10](../materials/deepseek/md/quick_start/error_codes.md) — https://api-docs.deepseek.com/quick_start/error_codes

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-error-400-keyword

In the Error Codes table, what causes HTTP 400 (Invalid Format) and what is its solution?

- Category: keyword; split: test; family: error-400; answerable: true

Expected answer points:

- HTTP 400 (Invalid Format): Invalid request body format. Modify the request body according to the error hints.

Evidence:

- [quick_start/error_codes, lines 10–10](../materials/deepseek/md/quick_start/error_codes.md) — https://api-docs.deepseek.com/quick_start/error_codes

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-error-401-semantic

My credential is wrong. Which error identifies that and what should I check?

- Category: semantic; split: dev; family: error-401; answerable: true

Expected answer points:

- HTTP 401 (Authentication Fails): Authentication fails due to the wrong API key. Check the API key, or create one if needed.

Evidence:

- [quick_start/error_codes, lines 11–11](../materials/deepseek/md/quick_start/error_codes.md) — https://api-docs.deepseek.com/quick_start/error_codes

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-error-401-keyword

In the Error Codes table, what causes HTTP 401 (Authentication Fails) and what is its solution?

- Category: keyword; split: dev; family: error-401; answerable: true

Expected answer points:

- HTTP 401 (Authentication Fails): Authentication fails due to the wrong API key. Check the API key, or create one if needed.

Evidence:

- [quick_start/error_codes, lines 11–11](../materials/deepseek/md/quick_start/error_codes.md) — https://api-docs.deepseek.com/quick_start/error_codes

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-error-402-semantic

My account has no funds left. Which error applies and what is the remedy?

- Category: semantic; split: dev; family: error-402; answerable: true

Expected answer points:

- HTTP 402 (Insufficient Balance): You have run out of balance. Check the balance and add funds through Top up.

Evidence:

- [quick_start/error_codes, lines 12–12](../materials/deepseek/md/quick_start/error_codes.md) — https://api-docs.deepseek.com/quick_start/error_codes

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-error-402-keyword

In the Error Codes table, what causes HTTP 402 (Insufficient Balance) and what is its solution?

- Category: keyword; split: dev; family: error-402; answerable: true

Expected answer points:

- HTTP 402 (Insufficient Balance): You have run out of balance. Check the balance and add funds through Top up.

Evidence:

- [quick_start/error_codes, lines 12–12](../materials/deepseek/md/quick_start/error_codes.md) — https://api-docs.deepseek.com/quick_start/error_codes

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-error-422-semantic

The request parameters are invalid. Which error applies and how should I fix it?

- Category: semantic; split: dev; family: error-422; answerable: true

Expected answer points:

- HTTP 422 (Invalid Parameters): Your request contains invalid parameters. Modify request parameters according to the error hints.

Evidence:

- [quick_start/error_codes, lines 13–13](../materials/deepseek/md/quick_start/error_codes.md) — https://api-docs.deepseek.com/quick_start/error_codes

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-error-422-keyword

In the Error Codes table, what causes HTTP 422 (Invalid Parameters) and what is its solution?

- Category: keyword; split: dev; family: error-422; answerable: true

Expected answer points:

- HTTP 422 (Invalid Parameters): Your request contains invalid parameters. Modify request parameters according to the error hints.

Evidence:

- [quick_start/error_codes, lines 13–13](../materials/deepseek/md/quick_start/error_codes.md) — https://api-docs.deepseek.com/quick_start/error_codes

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-error-429-semantic

I am sending requests too quickly. Which error applies and what does the guide suggest?

- Category: semantic; split: dev; family: error-429; answerable: true

Expected answer points:

- HTTP 429 (Rate Limit Reached): You are sending requests too quickly. Pace requests reasonably; the page also suggests temporarily using another provider.

Evidence:

- [quick_start/error_codes, lines 14–14](../materials/deepseek/md/quick_start/error_codes.md) — https://api-docs.deepseek.com/quick_start/error_codes

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-error-429-keyword

In the Error Codes table, what causes HTTP 429 (Rate Limit Reached) and what is its solution?

- Category: keyword; split: dev; family: error-429; answerable: true

Expected answer points:

- HTTP 429 (Rate Limit Reached): You are sending requests too quickly. Pace requests reasonably; the page also suggests temporarily using another provider.

Evidence:

- [quick_start/error_codes, lines 14–14](../materials/deepseek/md/quick_start/error_codes.md) — https://api-docs.deepseek.com/quick_start/error_codes

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-error-500-semantic

The service has an internal fault that persists. Which error and follow-up does the guide describe?

- Category: semantic; split: test; family: error-500; answerable: true

Expected answer points:

- HTTP 500 (Server Error): Our server encounters an issue. Retry after a brief wait and contact support if it persists.

Evidence:

- [quick_start/error_codes, lines 15–15](../materials/deepseek/md/quick_start/error_codes.md) — https://api-docs.deepseek.com/quick_start/error_codes

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-error-500-keyword

In the Error Codes table, what causes HTTP 500 (Server Error) and what is its solution?

- Category: keyword; split: test; family: error-500; answerable: true

Expected answer points:

- HTTP 500 (Server Error): Our server encounters an issue. Retry after a brief wait and contact support if it persists.

Evidence:

- [quick_start/error_codes, lines 15–15](../materials/deepseek/md/quick_start/error_codes.md) — https://api-docs.deepseek.com/quick_start/error_codes

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-error-503-semantic

The service is overloaded by traffic. Which error applies and what should I do?

- Category: semantic; split: test; family: error-503; answerable: true

Expected answer points:

- HTTP 503 (Server Overloaded): The server is overloaded due to high traffic. Retry after a brief wait.

Evidence:

- [quick_start/error_codes, lines 16–16](../materials/deepseek/md/quick_start/error_codes.md) — https://api-docs.deepseek.com/quick_start/error_codes

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-error-503-keyword

In the Error Codes table, what causes HTTP 503 (Server Overloaded) and what is its solution?

- Category: keyword; split: test; family: error-503; answerable: true

Expected answer points:

- HTTP 503 (Server Overloaded): The server is overloaded due to high traffic. Retry after a brief wait.

Evidence:

- [quick_start/error_codes, lines 16–16](../materials/deepseek/md/quick_start/error_codes.md) — https://api-docs.deepseek.com/quick_start/error_codes

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-price-cache-hit-offpeak

According specifically to the captured Models & Pricing table, what are the off-peak cache hit 1m input tokens prices for deepseek-flash and deepseek-v4-pro?

- Category: numeric; split: dev; family: price-cache-hit-offpeak; answerable: true

Expected answer points:

- Per 1M tokens, the table lists Flash at $0.003 and Pro at $0.022.

Evidence:

- [quick_start/pricing, lines 12–33](../materials/deepseek/md/quick_start/pricing.md) — https://api-docs.deepseek.com/quick_start/pricing

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-price-cache-hit-peak

According specifically to the captured Models & Pricing table, what are the peak cache hit 1m input tokens prices for deepseek-flash and deepseek-v4-pro?

- Category: numeric; split: dev; family: price-cache-hit-peak; answerable: true

Expected answer points:

- Per 1M tokens, the table lists Flash at $0.006 and Pro at $0.044.

Evidence:

- [quick_start/pricing, lines 12–33](../materials/deepseek/md/quick_start/pricing.md) — https://api-docs.deepseek.com/quick_start/pricing

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-price-cache-miss-offpeak

According specifically to the captured Models & Pricing table, what are the off-peak cache miss 1m input tokens prices for deepseek-flash and deepseek-v4-pro?

- Category: numeric; split: dev; family: price-cache-miss-offpeak; answerable: true

Expected answer points:

- Per 1M tokens, the table lists Flash at $0.15 and Pro at $0.66.

Evidence:

- [quick_start/pricing, lines 12–33](../materials/deepseek/md/quick_start/pricing.md) — https://api-docs.deepseek.com/quick_start/pricing

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-price-cache-miss-peak

According specifically to the captured Models & Pricing table, what are the peak cache miss 1m input tokens prices for deepseek-flash and deepseek-v4-pro?

- Category: numeric; split: dev; family: price-cache-miss-peak; answerable: true

Expected answer points:

- Per 1M tokens, the table lists Flash at $0.3 and Pro at $1.32.

Evidence:

- [quick_start/pricing, lines 12–33](../materials/deepseek/md/quick_start/pricing.md) — https://api-docs.deepseek.com/quick_start/pricing

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-price-output-offpeak

According specifically to the captured Models & Pricing table, what are the off-peak 1m output tokens prices for deepseek-flash and deepseek-v4-pro?

- Category: numeric; split: dev; family: price-output-offpeak; answerable: true

Expected answer points:

- Per 1M tokens, the table lists Flash at $0.6 and Pro at $1.98.

Evidence:

- [quick_start/pricing, lines 12–33](../materials/deepseek/md/quick_start/pricing.md) — https://api-docs.deepseek.com/quick_start/pricing

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-price-output-peak

According specifically to the captured Models & Pricing table, what are the peak 1m output tokens prices for deepseek-flash and deepseek-v4-pro?

- Category: numeric; split: dev; family: price-output-peak; answerable: true

Expected answer points:

- Per 1M tokens, the table lists Flash at $1.2 and Pro at $3.96.

Evidence:

- [quick_start/pricing, lines 12–33](../materials/deepseek/md/quick_start/pricing.md) — https://api-docs.deepseek.com/quick_start/pricing

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-price-arithmetic-flash

Using the captured Flash table rates, calculate the cost of 1M cache-miss input tokens plus 1M output tokens, all off-peak. Ignore any other usage.

- Category: numeric; split: dev; family: price-arithmetic-flash; answerable: true

Expected answer points:

- Input costs $0.15 and output costs $0.60, for $0.75 total.

Evidence:

- [quick_start/pricing, lines 12–33](../materials/deepseek/md/quick_start/pricing.md) — https://api-docs.deepseek.com/quick_start/pricing

Scoring: Derive 1×0.15 + 1×0.60 = 0.75 USD from the table. Arithmetic is an inference, not a quoted result. Do not apply Pro rates.

## ds-history-news0725

According to the historical API Upgrade announcement, how many functions could Function Calling support in one call, and were parallel calls supported?

- Category: historical; split: dev; family: history-news0725; answerable: true

Expected answer points:

- Up to 128 functions per call and parallel function calls were supported.

Evidence:

- [news/news0725, lines 46–46](../materials/deepseek/md/news/news0725.md) — https://api-docs.deepseek.com/news/news0725

Scoring: Answer only the named historical announcement. Treat performance claims as claims made by the publisher, not independently verified benchmarks or current service guarantees.

## ds-history-news0802

What input-position requirement did the historical Context Caching on Disk announcement specify, and did matching text in the middle qualify?

- Category: historical; split: test; family: history-news0802; answerable: true

Expected answer points:

- Identical prefixes starting at token zero qualified; partial matches in the middle did not.

Evidence:

- [news/news0802, lines 22–22](../materials/deepseek/md/news/news0802.md) — https://api-docs.deepseek.com/news/news0802

Scoring: Answer only the named historical announcement. Treat performance claims as claims made by the publisher, not independently verified benchmarks or current service guarantees.

## ds-history-news0905

Which two model versions were combined to create DeepSeek-V2.5 in its release announcement?

- Category: historical; split: test; family: history-news0905; answerable: true

Expected answer points:

- DeepSeek-V2-0628 and DeepSeek-Coder-V2-0724.

Evidence:

- [news/news0905, lines 6–6](../materials/deepseek/md/news/news0905.md) — https://api-docs.deepseek.com/news/news0905

Scoring: Answer only the named historical announcement. Treat performance claims as claims made by the publisher, not independently verified benchmarks or current service guarantees.

## ds-history-news1120

In the R1-Lite-Preview announcement, were API access and open-source models already available or described as coming soon?

- Category: historical; split: dev; family: history-news1120; answerable: true

Expected answer points:

- Open-source models and the API were described as coming soon.

Evidence:

- [news/news1120, lines 10–10](../materials/deepseek/md/news/news1120.md) — https://api-docs.deepseek.com/news/news1120

Scoring: Answer only the named historical announcement. Treat performance claims as claims made by the publisher, not independently verified benchmarks or current service guarantees.

## ds-history-news1210

What happened to the V2.5 series with the release of DeepSeek-V2.5-1210?

- Category: historical; split: test; family: history-news1210; answerable: true

Expected answer points:

- The V2.5 series came to an end.

Evidence:

- [news/news1210, lines 16–16](../materials/deepseek/md/news/news1210.md) — https://api-docs.deepseek.com/news/news1210

Scoring: Answer only the named historical announcement. Treat performance claims as claims made by the publisher, not independently verified benchmarks or current service guarantees.

## ds-history-news1226

In the original V3 introduction, how many total MoE and activated parameters were reported?

- Category: historical; split: dev; family: history-news1226; answerable: true

Expected answer points:

- 671B total MoE parameters and 37B activated parameters.

Evidence:

- [news/news1226, lines 21–23](../materials/deepseek/md/news/news1226.md) — https://api-docs.deepseek.com/news/news1226

Scoring: Answer only the named historical announcement. Treat performance claims as claims made by the publisher, not independently verified benchmarks or current service guarantees.

## ds-history-news250115

Which model powered the initially introduced DeepSeek App, and did that announcement say it was free?

- Category: historical; split: dev; family: history-news250115; answerable: true

Expected answer points:

- It was powered by DeepSeek-V3 and described as free to use.

Evidence:

- [news/news250115, lines 6–6](../materials/deepseek/md/news/news250115.md) — https://api-docs.deepseek.com/news/news250115
- [news/news250115, lines 8–8](../materials/deepseek/md/news/news250115.md) — https://api-docs.deepseek.com/news/news250115

Scoring: Answer only the named historical announcement. Treat performance claims as claims made by the publisher, not independently verified benchmarks or current service guarantees.

## ds-history-news250120

According to the original DeepSeek-R1 release announcement, which API model name selected R1?

- Category: historical; split: dev; family: history-news250120; answerable: true

Expected answer points:

- The model name was deepseek-reasoner.

Evidence:

- [news/news250120, lines 60–60](../materials/deepseek/md/news/news250120.md) — https://api-docs.deepseek.com/news/news250120

Scoring: Answer only the named historical announcement. Treat performance claims as claims made by the publisher, not independently verified benchmarks or current service guarantees.

## ds-history-news250325

Which license did the DeepSeek-V3-0324 announcement say the models were released under?

- Category: historical; split: dev; family: history-news250325; answerable: true

Expected answer points:

- The MIT License.

Evidence:

- [news/news250325, lines 14–17](../materials/deepseek/md/news/news250325.md) — https://api-docs.deepseek.com/news/news250325

Scoring: Answer only the named historical announcement. Treat performance claims as claims made by the publisher, not independently verified benchmarks or current service guarantees.

## ds-history-news250528

Which structured-output and tool features were announced for DeepSeek-R1-0528?

- Category: historical; split: dev; family: history-news250528; answerable: true

Expected answer points:

- JSON output and function calling.

Evidence:

- [news/news250528, lines 14–14](../materials/deepseek/md/news/news250528.md) — https://api-docs.deepseek.com/news/news250528

Scoring: Answer only the named historical announcement. Treat performance claims as claims made by the publisher, not independently verified benchmarks or current service guarantees.

## ds-history-news250821

In the V3.1 announcement, which model aliases selected non-thinking and thinking modes?

- Category: historical; split: test; family: history-news250821; answerable: true

Expected answer points:

- deepseek-chat selected non-thinking; deepseek-reasoner selected thinking.

Evidence:

- [news/news250821, lines 20–20](../materials/deepseek/md/news/news250821.md) — https://api-docs.deepseek.com/news/news250821
- [news/news250821, lines 22–22](../materials/deepseek/md/news/news250821.md) — https://api-docs.deepseek.com/news/news250821

Scoring: Answer only the named historical announcement. Treat performance claims as claims made by the publisher, not independently verified benchmarks or current service guarantees.

## ds-history-news250922

Which two user-visible problem areas did the V3.1-Terminus announcement emphasize improving?

- Category: historical; split: dev; family: history-news250922; answerable: true

Expected answer points:

- Language consistency and Code Agent/Search Agent performance.

Evidence:

- [news/news250922, lines 12–12](../materials/deepseek/md/news/news250922.md) — https://api-docs.deepseek.com/news/news250922
- [news/news250922, lines 14–14](../materials/deepseek/md/news/news250922.md) — https://api-docs.deepseek.com/news/news250922

Scoring: Answer only the named historical announcement. Treat performance claims as claims made by the publisher, not independently verified benchmarks or current service guarantees.

## ds-history-news250929

What attention mechanism debuted in V3.2-Exp, and on which model was it built?

- Category: historical; split: dev; family: history-news250929; answerable: true

Expected answer points:

- DeepSeek Sparse Attention (DSA), built on V3.1-Terminus.

Evidence:

- [news/news250929, lines 8–8](../materials/deepseek/md/news/news250929.md) — https://api-docs.deepseek.com/news/news250929

Scoring: Answer only the named historical announcement. Treat performance claims as claims made by the publisher, not independently verified benchmarks or current service guarantees.

## ds-history-news260424

In the V4 Preview announcement, what total and active parameter counts were given for Pro and Flash?

- Category: historical; split: dev; family: history-news260424; answerable: true

Expected answer points:

- Pro: 1.6T total and 49B active; Flash: 284B total and 13B active.

Evidence:

- [news/news260424, lines 8–8](../materials/deepseek/md/news/news260424.md) — https://api-docs.deepseek.com/news/news260424
- [news/news260424, lines 10–10](../materials/deepseek/md/news/news260424.md) — https://api-docs.deepseek.com/news/news260424

Scoring: Answer only the named historical announcement. Treat performance claims as claims made by the publisher, not independently verified benchmarks or current service guarantees.

## ds-history-news260813

When did the V4-Pro GA announcement say its new peak/off-peak pricing would take effect?

- Category: historical; split: dev; family: history-news260813; answerable: true

Expected answer points:

- 16:00 UTC on August 16, 2026.

Evidence:

- [news/news260813, lines 26–26](../materials/deepseek/md/news/news260813.md) — https://api-docs.deepseek.com/news/news260813

Scoring: Answer only the named historical announcement. Treat performance claims as claims made by the publisher, not independently verified benchmarks or current service guarantees.

## ds-history-news260821

What per-image token cap was advertised in the historical V4-Flash-Vision-Exp announcement?

- Category: historical; split: dev; family: history-news260821; answerable: true

Expected answer points:

- Up to 384 tokens per image, at V4-Flash pricing.

Evidence:

- [news/news260821, lines 34–34](../materials/deepseek/md/news/news260821.md) — https://api-docs.deepseek.com/news/news260821

Scoring: Answer only the named historical announcement. Treat performance claims as claims made by the publisher, not independently verified benchmarks or current service guarantees.

## ds-history-news260910

What total and input/output active parameter counts were reported for V4.1-Flash?

- Category: historical; split: dev; family: history-news260910; answerable: true

Expected answer points:

- 552B total MoE parameters; 8B active for input and 16B active for output.

Evidence:

- [news/news260910, lines 18–18](../materials/deepseek/md/news/news260910.md) — https://api-docs.deepseek.com/news/news260910
- [news/news260910, lines 20–20](../materials/deepseek/md/news/news260910.md) — https://api-docs.deepseek.com/news/news260910

Scoring: Answer only the named historical announcement. Treat performance claims as claims made by the publisher, not independently verified benchmarks or current service guarantees.

## ds-terminus-expiry-semantic

What temporary service address was offered for the older comparison model, and when was its availability stated to end?

- Category: semantic; split: dev; family: terminus-expiry; answerable: true

Expected answer points:

- The temporary base URL was https://api.deepseek.com/v3.1_terminus_expires_on_20251015; availability ended October 15, 2025 at 15:59 UTC.

Evidence:

- [guides/comparison_testing, lines 8–8](../materials/deepseek/md/guides/comparison_testing.md) — https://api-docs.deepseek.com/guides/comparison_testing

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-terminus-expiry-keyword

What are the V3.1-Terminus comparison base_url and expiry time in the historical guide?

- Category: keyword; split: dev; family: terminus-expiry; answerable: true

Expected answer points:

- The temporary base URL was https://api.deepseek.com/v3.1_terminus_expires_on_20251015; availability ended October 15, 2025 at 15:59 UTC.

Evidence:

- [guides/comparison_testing, lines 8–8](../materials/deepseek/md/guides/comparison_testing.md) — https://api-docs.deepseek.com/guides/comparison_testing

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-faq-top-up

How can I add funds online and verify the payment result?

- Category: semantic; split: test; family: faq-top-up; answerable: true

Expected answer points:

- Online top-up supports PayPal, bank card, Alipay or WeChat Pay through Top Up; results appear on Billing.

Evidence:

- [faq-api/top-up, lines 6–6](../materials/deepseek/md/faq-api/top-up.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/top-up

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-faq-balance-error

Why might my top-up appear missing after I log in under a different method?

- Category: semantic; split: dev; family: faq-balance-error; answerable: true

Expected answer points:

- It usually means a different account was topped up; try the original Google/email login and check top-up records.

Evidence:

- [faq-api/balance-error, lines 6–6](../materials/deepseek/md/faq-api/balance-error.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/balance-error
- [faq-api/balance-error, lines 8–10](../materials/deepseek/md/faq-api/balance-error.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/balance-error

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-faq-balance-validity

Will money I topped up disappear just because a period of time has passed?

- Category: semantic; split: dev; family: faq-balance-validity; answerable: true

Expected answer points:

- Top-up balances do not expire.

Evidence:

- [faq-api/balance-validity, lines 6–6](../materials/deepseek/md/faq-api/balance-validity.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/balance-validity

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-faq-refund-policy

How do refund procedures differ for online payments and corporate bank transfers?

- Category: semantic; split: dev; family: faq-refund-policy; answerable: true

Expected answer points:

- Unused balances can be refunded; online payments use Billing then Refunds, while corporate transfers require a Refund Request ticket.

Evidence:

- [faq-api/refund-policy, lines 6–6](../materials/deepseek/md/faq-api/refund-policy.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/refund-policy
- [faq-api/refund-policy, lines 8–9](../materials/deepseek/md/faq-api/refund-policy.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/refund-policy

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-faq-invoice-request

Where does the API FAQ tell me to request an invoice?

- Category: semantic; split: test; family: faq-invoice-request; answerable: true

Expected answer points:

- Log in to the Platform, go to Billing and click Invoices.

Evidence:

- [faq-api/invoice-request, lines 6–6](../materials/deepseek/md/faq-api/invoice-request.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/invoice-request

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-faq-invoice-details

How can I add usage details to an invoice according to the API FAQ?

- Category: semantic; split: dev; family: faq-invoice-details; answerable: true

Expected answer points:

- Go to Billing, click Invoices, and enter the relevant information in the Remarks field.

Evidence:

- [faq-api/invoice-details, lines 6–6](../materials/deepseek/md/faq-api/invoice-details.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/invoice-details

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-faq-key-usage

How do I inspect usage for an individual API key in the platform?

- Category: semantic; split: dev; family: faq-key-usage; answerable: true

Expected answer points:

- Open Usage, then select the time range and API key to filter usage.

Evidence:

- [faq-api/key-usage, lines 8–10](../materials/deepseek/md/faq-api/key-usage.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/key-usage

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-faq-key-revoke

What should I do immediately if an API key is exposed, and what application change follows?

- Category: semantic; split: test; family: faq-key-revoke; answerable: true

Expected answer points:

- Revoke the compromised key immediately, then create a new key and replace it in the application.

Evidence:

- [faq-api/key-revoke, lines 6–6](../materials/deepseek/md/faq-api/key-revoke.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/key-revoke
- [faq-api/key-revoke, lines 8–12](../materials/deepseek/md/faq-api/key-revoke.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/key-revoke

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-faq-cooperation-agreement

Can an enterprise negotiate changes to the standard cooperation agreement described in the FAQ?

- Category: semantic; split: dev; family: faq-cooperation-agreement; answerable: true

Expected answer points:

- No. It is a standard framework agreement and cannot be modified.

Evidence:

- [faq-api/cooperation-agreement, lines 8–8](../materials/deepseek/md/faq-api/cooperation-agreement.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/cooperation-agreement

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-faq-rate-limits

Do higher-rate-limit needs require buying one of several API pricing tiers?

- Category: semantic; split: dev; family: faq-rate-limits; answerable: true

Expected answer points:

- The FAQ describes unified pricing with no tiered pricing; higher rate limits are requested through an expansion application.

Evidence:

- [faq-api/rate-limits, lines 6–6](../materials/deepseek/md/faq-api/rate-limits.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/rate-limits
- [faq-api/rate-limits, lines 8–8](../materials/deepseek/md/faq-api/rate-limits.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/rate-limits

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-faq-verification-failure

What are the common causes of real-name verification failing in the API FAQ?

- Category: semantic; split: dev; family: faq-verification-failure; answerable: true

Expected answer points:

- Too many accounts bound to one ID, or too many consecutive incorrect ID-number entries causing temporary verification lockout.

Evidence:

- [faq-api/verification-failure, lines 8–9](../materials/deepseek/md/faq-api/verification-failure.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/verification-failure

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-faq-verification-types

Does personal versus enterprise real-name verification change user benefits?

- Category: semantic; split: test; family: faq-verification-types; answerable: true

Expected answer points:

- There is currently no difference in user benefits.

Evidence:

- [faq-api/verification-types, lines 6–6](../materials/deepseek/md/faq-api/verification-types.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/verification-types

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-faq-verification-update

Can I upgrade personal verification to enterprise verification without losing my balance?

- Category: semantic; split: dev; family: faq-verification-update; answerable: true

Expected answer points:

- Yes; updating verification does not affect the account balance.

Evidence:

- [faq-api/verification-update, lines 6–6](../materials/deepseek/md/faq-api/verification-update.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/verification-update
- [faq-api/verification-update, lines 10–10](../materials/deepseek/md/faq-api/verification-update.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/verification-update

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-faq-verification-change

Can an enterprise-verified account be converted back to a personal account?

- Category: semantic; split: dev; family: faq-verification-change; answerable: true

Expected answer points:

- No, an enterprise-verified account cannot be changed to a personal account.

Evidence:

- [faq-api/verification-change, lines 6–6](../materials/deepseek/md/faq-api/verification-change.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/verification-change

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-faq-verification-name

After a registered company-name update, which company names may fund transfers and which may appear on invoices?

- Category: semantic; split: dev; family: faq-verification-name; answerable: true

Expected answer points:

- Transfers may use either the new or former company name; invoices can only use the new company name.

Evidence:

- [faq-api/verification-name, lines 10–10](../materials/deepseek/md/faq-api/verification-name.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/verification-name

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-faq-keep-alive

Does receiving empty lines while waiting mean the API has returned an empty final JSON answer?

- Category: semantic; split: test; family: faq-keep-alive; answerable: true

Expected answer points:

- No; empty lines are a non-streaming keep-alive mechanism and do not affect parsing of the eventual JSON body.

Evidence:

- [faq-api/keep-alive, lines 8–9](../materials/deepseek/md/faq-api/keep-alive.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/keep-alive
- [faq-api/keep-alive, lines 11–11](../materials/deepseek/md/faq-api/keep-alive.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/keep-alive

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-exact-1

What is the setup command documented for Hermes Agent?

- Category: keyword; split: dev; family: integration-hermes; answerable: true

Expected answer points:

- hermes setup

Evidence:

- [quick_start/agent_integrations/hermes, lines 28–34](../materials/deepseek/md/quick_start/agent_integrations/hermes.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/hermes

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-exact-2

Which command initializes nanobot configuration?

- Category: keyword; split: dev; family: integration-nanobot; answerable: true

Expected answer points:

- nanobot onboard

Evidence:

- [quick_start/agent_integrations/nanobot, lines 39–41](../materials/deepseek/md/quick_start/agent_integrations/nanobot.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/nanobot

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-exact-3

What configuration path does the nanobot guide give for Linux and macOS?

- Category: keyword; split: dev; family: integration-nanobot; answerable: true

Expected answer points:

- ~/.nanobot/config.json

Evidence:

- [quick_start/agent_integrations/nanobot, lines 45–46](../materials/deepseek/md/quick_start/agent_integrations/nanobot.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/nanobot

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-exact-4

What minimum recommended OpenCode version is stated in the integration guide?

- Category: keyword; split: dev; family: integration-opencode; answerable: true

Expected answer points:

- v1.18.30

Evidence:

- [quick_start/agent_integrations/opencode, lines 10–10](../materials/deepseek/md/quick_start/agent_integrations/opencode.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/opencode

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-exact-5

Which slash command opens the provider connection flow in OpenCode?

- Category: keyword; split: dev; family: integration-opencode; answerable: true

Expected answer points:

- /connect

Evidence:

- [quick_start/agent_integrations/opencode, lines 12–13](../materials/deepseek/md/quick_start/agent_integrations/opencode.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/opencode

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-exact-6

What npm package installs the documented Kilo Code CLI?

- Category: keyword; split: dev; family: integration-kilo_code; answerable: true

Expected answer points:

- @kilocode/cli

Evidence:

- [quick_start/agent_integrations/kilo_code, lines 13–15](../materials/deepseek/md/quick_start/agent_integrations/kilo_code.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/kilo_code

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-exact-7

What slash command opens the model selector in Kilo Code?

- Category: keyword; split: dev; family: integration-kilo_code; answerable: true

Expected answer points:

- /models

Evidence:

- [quick_start/agent_integrations/kilo_code, lines 39–44](../materials/deepseek/md/quick_start/agent_integrations/kilo_code.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/kilo_code

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-exact-8

What minimum Node.js version is required for the manual Langcli installation?

- Category: keyword; split: dev; family: integration-langcli; answerable: true

Expected answer points:

- Node.js 20 or later

Evidence:

- [quick_start/agent_integrations/langcli, lines 28–28](../materials/deepseek/md/quick_start/agent_integrations/langcli.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/langcli

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-exact-9

Which npm package does the manual Langcli installation use?

- Category: keyword; split: dev; family: integration-langcli; answerable: true

Expected answer points:

- langcli-com

Evidence:

- [quick_start/agent_integrations/langcli, lines 30–32](../materials/deepseek/md/quick_start/agent_integrations/langcli.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/langcli

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-1

What local address and port does the AstrBot integration guide use for the Web UI?

- Category: keyword; split: dev; family: integration-astrbot; answerable: true

Expected answer points:

- http://localhost:6185

Evidence:

- [quick_start/agent_integrations/astrbot, lines 50–52](../materials/deepseek/md/quick_start/agent_integrations/astrbot.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/astrbot

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-2

Which two commands initialize and start AstrBot?

- Category: keyword; split: dev; family: integration-astrbot; answerable: true

Expected answer points:

- astrbot init initializes it; astrbot run starts it.

Evidence:

- [quick_start/agent_integrations/astrbot, lines 26–29](../materials/deepseek/md/quick_start/agent_integrations/astrbot.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/astrbot

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-3

What value is assigned to CLAUDE_CODE_AUTO_COMPACT_WINDOW in the Claude Code guide?

- Category: keyword; split: dev; family: integration-claude_code; answerable: true

Expected answer points:

- 786432

Evidence:

- [quick_start/agent_integrations/claude_code, lines 14–24](../materials/deepseek/md/quick_start/agent_integrations/claude_code.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-4

What value does the Claude Code configuration give ANTHROPIC_DEFAULT_HAIKU_MODEL?

- Category: keyword; split: dev; family: integration-claude_code; answerable: true

Expected answer points:

- deepseek-flash

Evidence:

- [quick_start/agent_integrations/claude_code, lines 14–24](../materials/deepseek/md/quick_start/agent_integrations/claude_code.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-5

According to the DeepSeek integration guide, what does wire_api = "responses" select?

- Category: keyword; split: dev; family: integration-codex; answerable: true

Expected answer points:

- It selects the Responses API protocol.

Evidence:

- [quick_start/agent_integrations/codex, lines 207–218](../materials/deepseek/md/quick_start/agent_integrations/codex.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/codex

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-6

Where does the DeepSeek Codex setup script back up the existing configuration?

- Category: keyword; split: dev; family: integration-codex; answerable: true

Expected answer points:

- ~/.codex/backup-deepseek/

Evidence:

- [quick_start/agent_integrations/codex, lines 32–35](../materials/deepseek/md/quick_start/agent_integrations/codex.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/codex

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-7

Which provider type must GitHub Copilot CLI use, and why does the OpenAI type fail?

- Category: keyword; split: dev; family: integration-copilot_cli; answerable: true

Expected answer points:

- Use anthropic; the OpenAI integration fails to replay reasoning_content in thinking mode, causing HTTP 400.

Evidence:

- [quick_start/agent_integrations/copilot_cli, lines 8–8](../materials/deepseek/md/quick_start/agent_integrations/copilot_cli.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/copilot_cli

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-8

Does COPILOT_OFFLINE=true prevent prompts from reaching DeepSeek?

- Category: keyword; split: dev; family: integration-copilot_cli; answerable: true

Expected answer points:

- No. Prompts still reach api.deepseek.com; it only blocks GitHub API calls.

Evidence:

- [quick_start/agent_integrations/copilot_cli, lines 87–87](../materials/deepseek/md/quick_start/agent_integrations/copilot_cli.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/copilot_cli

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-9

What values does the guide set for COPILOT_PROVIDER_MAX_PROMPT_TOKENS and COPILOT_PROVIDER_MAX_OUTPUT_TOKENS?

- Category: keyword; split: dev; family: integration-copilot_cli; answerable: true

Expected answer points:

- 840000 and 128000, respectively.

Evidence:

- [quick_start/agent_integrations/copilot_cli, lines 59–62](../materials/deepseek/md/quick_start/agent_integrations/copilot_cli.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/copilot_cli

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-10

What Linux/macOS configuration file path is given for Crush?

- Category: keyword; split: dev; family: integration-crush; answerable: true

Expected answer points:

- ~/.config/crush/crush.json

Evidence:

- [quick_start/agent_integrations/crush, lines 29–30](../materials/deepseek/md/quick_start/agent_integrations/crush.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/crush

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-11

What provider type does the Crush JSON example configure for DeepSeek?

- Category: keyword; split: dev; family: integration-crush; answerable: true

Expected answer points:

- openai-compat

Evidence:

- [quick_start/agent_integrations/crush, lines 32–59](../materials/deepseek/md/quick_start/agent_integrations/crush.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/crush

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-12

Where does the Deep Code guide place its settings file?

- Category: keyword; split: dev; family: integration-deepcode; answerable: true

Expected answer points:

- ~/.deepcode/settings.json

Evidence:

- [quick_start/agent_integrations/deepcode, lines 27–27](../materials/deepseek/md/quick_start/agent_integrations/deepcode.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/deepcode

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-13

What is the project-level Agent Skills discovery path in Deep Code?

- Category: keyword; split: dev; family: integration-deepcode; answerable: true

Expected answer points:

- ./.deepcode/skills/<name>/SKILL.md

Evidence:

- [quick_start/agent_integrations/deepcode, lines 80–81](../materials/deepseek/md/quick_start/agent_integrations/deepcode.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/deepcode

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-14

Where does the GitHub Copilot extension guide say it stores the API key?

- Category: keyword; split: dev; family: integration-github_copilot; answerable: true

Expected answer points:

- In the OS keychain, not on disk.

Evidence:

- [quick_start/agent_integrations/github_copilot, lines 21–23](../materials/deepseek/md/quick_start/agent_integrations/github_copilot.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/github_copilot

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-15

Which command chooses the extension model used to describe images before sending their description to DeepSeek?

- Category: keyword; split: dev; family: integration-github_copilot; answerable: true

Expected answer points:

- DeepSeek: Set Vision Proxy Model

Evidence:

- [quick_start/agent_integrations/github_copilot, lines 42–42](../materials/deepseek/md/quick_start/agent_integrations/github_copilot.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/github_copilot

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-16

What models file does the Oh My Pi integration guide require?

- Category: keyword; split: dev; family: integration-oh_my_pi; answerable: true

Expected answer points:

- ~/.omp/agent/models.yml

Evidence:

- [quick_start/agent_integrations/oh_my_pi, lines 20–20](../materials/deepseek/md/quick_start/agent_integrations/oh_my_pi.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/oh_my_pi

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-17

Does an Oh My Pi compat block merge into the built-in block or replace it?

- Category: keyword; split: dev; family: integration-oh_my_pi; answerable: true

Expected answer points:

- It replaces the entire built-in block, so specify all compatibility fields.

Evidence:

- [quick_start/agent_integrations/oh_my_pi, lines 132–132](../materials/deepseek/md/quick_start/agent_integrations/oh_my_pi.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/oh_my_pi

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-18

Which command returns an existing OpenClaw installation to configuration?

- Category: keyword; split: dev; family: integration-openclaw; answerable: true

Expected answer points:

- openclaw onboard --install-daemon

Evidence:

- [quick_start/agent_integrations/openclaw, lines 12–14](../materials/deepseek/md/quick_start/agent_integrations/openclaw.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/openclaw

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-19

Which command opens the OpenClaw Web UI?

- Category: keyword; split: dev; family: integration-openclaw; answerable: true

Expected answer points:

- openclaw dashboard

Evidence:

- [quick_start/agent_integrations/openclaw, lines 56–58](../materials/deepseek/md/quick_start/agent_integrations/openclaw.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/openclaw

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-20

What is the Linux/macOS custom model catalog path for Pi?

- Category: keyword; split: dev; family: integration-pi_mono; answerable: true

Expected answer points:

- ~/.pi/agent/models.json

Evidence:

- [quick_start/agent_integrations/pi_mono, lines 33–34](../materials/deepseek/md/quick_start/agent_integrations/pi_mono.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/pi_mono

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-21

Which exact compatibility key does Pi use to preserve reasoning on assistant messages?

- Category: keyword; split: dev; family: integration-pi_mono; answerable: true

Expected answer points:

- requiresReasoningContentOnAssistantMessages

Evidence:

- [quick_start/agent_integrations/pi_mono, lines 36–98](../materials/deepseek/md/quick_start/agent_integrations/pi_mono.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/pi_mono

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-22

What slash command and tab are used to configure a custom model in Qoder CLI?

- Category: keyword; split: dev; family: integration-qoder; answerable: true

Expected answer points:

- Use /model and its Custom tab/wizard.

Evidence:

- [quick_start/agent_integrations/qoder, lines 68–70](../materials/deepseek/md/quick_start/agent_integrations/qoder.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/qoder

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-23

Does a Qoder custom model consume Qoder Credits?

- Category: keyword; split: dev; family: integration-qoder; answerable: true

Expected answer points:

- No; custom-model usage is billed directly to the DeepSeek API account.

Evidence:

- [quick_start/agent_integrations/qoder, lines 8–11](../materials/deepseek/md/quick_start/agent_integrations/qoder.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/qoder

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-24

Where does the first-run Reasonix wizard persist its key configuration?

- Category: keyword; split: dev; family: integration-reasonix; answerable: true

Expected answer points:

- ~/.reasonix/config.json

Evidence:

- [quick_start/agent_integrations/reasonix, lines 15–15](../materials/deepseek/md/quick_start/agent_integrations/reasonix.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/reasonix

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-25

How do /pro and /preset max differ in Reasonix?

- Category: keyword; split: dev; family: integration-reasonix; answerable: true

Expected answer points:

- /pro selects Pro for the next turn; /preset max selects Pro for the entire session.

Evidence:

- [quick_start/agent_integrations/reasonix, lines 24–24](../materials/deepseek/md/quick_start/agent_integrations/reasonix.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/reasonix

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-26

What encoding must the WorkBuddy/CodeBuddy models.json use?

- Category: keyword; split: dev; family: integration-workbuddy; answerable: true

Expected answer points:

- UTF-8 without BOM.

Evidence:

- [quick_start/agent_integrations/workbuddy, lines 57–57](../materials/deepseek/md/quick_start/agent_integrations/workbuddy.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/workbuddy

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-integration-detail-27

What exact endpoint does the WorkBuddy/CodeBuddy model JSON example put in url?

- Category: keyword; split: dev; family: integration-workbuddy; answerable: true

Expected answer points:

- https://api.deepseek.com/v1/chat/completions

Evidence:

- [quick_start/agent_integrations/workbuddy, lines 36–55](../materials/deepseek/md/quick_start/agent_integrations/workbuddy.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/workbuddy

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-chat-stop-limit-semantic

How many different strings may I ask the chat service to stop at?

- Category: semantic; split: dev; family: chat-stop-limit; answerable: true

Expected answer points:

- At most 16 stop sequences.

Evidence:

- [api/create-chat-completion, lines 280–286](../materials/deepseek/md/api/create-chat-completion.md) — https://api-docs.deepseek.com/api/create-chat-completion

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-chat-stop-limit-keyword

What is the maximum number of stop sequences for Chat Completions?

- Category: keyword; split: dev; family: chat-stop-limit; answerable: true

Expected answer points:

- At most 16 stop sequences.

Evidence:

- [api/create-chat-completion, lines 280–286](../materials/deepseek/md/api/create-chat-completion.md) — https://api-docs.deepseek.com/api/create-chat-completion

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-chat-logprob-semantic

What must I turn on before requesting probabilities for alternative output tokens, and how many alternatives are allowed?

- Category: semantic; split: dev; family: chat-logprob; answerable: true

Expected answer points:

- top_logprobs allows 0–20 and requires logprobs:true.

Evidence:

- [api/create-chat-completion, lines 434–438](../materials/deepseek/md/api/create-chat-completion.md) — https://api-docs.deepseek.com/api/create-chat-completion

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-chat-logprob-keyword

What range and logprobs prerequisite apply to top_logprobs?

- Category: keyword; split: dev; family: chat-logprob; answerable: true

Expected answer points:

- top_logprobs allows 0–20 and requires logprobs:true.

Evidence:

- [api/create-chat-completion, lines 434–438](../materials/deepseek/md/api/create-chat-completion.md) — https://api-docs.deepseek.com/api/create-chat-completion

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-chat-usage-chunk-semantic

Where should a streaming chat client read final usage if there is no separate usage-only event?

- Category: semantic; split: dev; family: chat-usage-chunk; answerable: true

Expected answer points:

- The last chunk before [DONE] carries full-request usage; there is no separate usage-only chunk, and choices has one element with no new content and a non-null finish_reason.

Evidence:

- [api/create-chat-completion, lines 310–314](../materials/deepseek/md/api/create-chat-completion.md) — https://api-docs.deepseek.com/api/create-chat-completion

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-chat-usage-chunk-keyword

What is the final Chat Completions usage chunk shape before data: [DONE]?

- Category: keyword; split: dev; family: chat-usage-chunk; answerable: true

Expected answer points:

- The last chunk before [DONE] carries full-request usage; there is no separate usage-only chunk, and choices has one element with no new content and a non-null finish_reason.

Evidence:

- [api/create-chat-completion, lines 310–314](../materials/deepseek/md/api/create-chat-completion.md) — https://api-docs.deepseek.com/api/create-chat-completion

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-chat-finish-reasons-semantic

How can I tell whether generation was cut short because inference resources were insufficient or because it was interrupted?

- Category: semantic; split: dev; family: chat-finish-reasons; answerable: true

Expected answer points:

- insufficient_system_resource means interrupted for insufficient inference-system resources; aborted means generation was interrupted.

Evidence:

- [api/create-chat-completion, lines 477–481](../materials/deepseek/md/api/create-chat-completion.md) — https://api-docs.deepseek.com/api/create-chat-completion

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-chat-finish-reasons-keyword

Define finish_reason values insufficient_system_resource and aborted.

- Category: keyword; split: dev; family: chat-finish-reasons; answerable: true

Expected answer points:

- insufficient_system_resource means interrupted for insufficient inference-system resources; aborted means generation was interrupted.

Evidence:

- [api/create-chat-completion, lines 477–481](../materials/deepseek/md/api/create-chat-completion.md) — https://api-docs.deepseek.com/api/create-chat-completion

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-chat-length-reason-semantic

How can I distinguish an answer naturally finishing from one stopping because its generation budget was exhausted?

- Category: semantic; split: dev; family: chat-length-reason; answerable: true

Expected answer points:

- stop means a natural stopping point or provided stop sequence; length means the requested maximum number of tokens was reached.

Evidence:

- [api/create-chat-completion, lines 477–481](../materials/deepseek/md/api/create-chat-completion.md) — https://api-docs.deepseek.com/api/create-chat-completion

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-chat-length-reason-keyword

Compare finish_reason="stop" with finish_reason="length" in Chat Completions.

- Category: keyword; split: dev; family: chat-length-reason; answerable: true

Expected answer points:

- stop means a natural stopping point or provided stop sequence; length means the requested maximum number of tokens was reached.

Evidence:

- [api/create-chat-completion, lines 477–481](../materials/deepseek/md/api/create-chat-completion.md) — https://api-docs.deepseek.com/api/create-chat-completion

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-cross-history-stream

I need a multi-turn chat whose answer arrives incrementally. What history must I send, and which request option enables streaming?

- Category: multi_document; split: test; family: cross-history-stream; answerable: true

Expected answer points:

- Send concatenated previous history because chat is stateless.
- Set stream to true.

Evidence:

- [guides/multi_round_chat, lines 8–8](../materials/deepseek/md/guides/multi_round_chat.md) — https://api-docs.deepseek.com/guides/multi_round_chat
- [index, lines 27–27](../materials/deepseek/md/index.md) — https://api-docs.deepseek.com/

Scoring: All requested parts must be supported. Cite evidence from the relevant API families; do not substitute a similar field from another interface.

## ds-cross-json-strict

How does enabling JSON Output differ from enabling strict tool argument schemas?

- Category: multi_document; split: dev; family: cross-json-strict; answerable: true

Expected answer points:

- JSON Output uses response_format json_object plus the word json and an example in the prompt.
- Strict tool calls use the beta URL, strict:true on functions, and server schema validation.

Evidence:

- [guides/json_mode, lines 14–17](../materials/deepseek/md/guides/json_mode.md) — https://api-docs.deepseek.com/guides/json_mode
- [guides/tool_calls, lines 98–100](../materials/deepseek/md/guides/tool_calls.md) — https://api-docs.deepseek.com/guides/tool_calls

Scoring: All requested parts must be supported. Cite evidence from the relevant API families; do not substitute a similar field from another interface.

## ds-cross-fim-prefix

Compare filling a code gap with continuing an assistant prefix: how do their inputs differ, and what beta address do both use?

- Category: multi_document; split: dev; family: cross-fim-prefix; answerable: true

Expected answer points:

- FIM takes a prefix and optional suffix and fills the middle.
- Chat prefix completion continues the last assistant message with prefix:true.
- Both use https://api.deepseek.com/beta.

Evidence:

- [guides/fim_completion, lines 6–6](../materials/deepseek/md/guides/fim_completion.md) — https://api-docs.deepseek.com/guides/fim_completion
- [guides/chat_prefix_completion, lines 10–11](../materials/deepseek/md/guides/chat_prefix_completion.md) — https://api-docs.deepseek.com/guides/chat_prefix_completion

Scoring: All requested parts must be supported. Cite evidence from the relevant API families; do not substitute a similar field from another interface.

## ds-cross-fim-thinking

Can I use the advertised 384K maximum output for a thinking-mode FIM request?

- Category: multi_document; split: dev; family: cross-fim-thinking; answerable: true

Expected answer points:

- No; the pricing table restricts FIM to non-thinking mode.
- The FIM guide separately limits FIM output to 4K tokens.

Evidence:

- [quick_start/pricing, lines 25–25](../materials/deepseek/md/quick_start/pricing.md) — https://api-docs.deepseek.com/quick_start/pricing
- [guides/fim_completion, lines 10–11](../materials/deepseek/md/guides/fim_completion.md) — https://api-docs.deepseek.com/guides/fim_completion

Scoring: All requested parts must be supported. Cite evidence from the relevant API families; do not substitute a similar field from another interface.

## ds-cross-cache-billing

How do I inspect cache reuse counters and determine which wallet balance is charged first?

- Category: multi_document; split: dev; family: cross-cache-billing; answerable: true

Expected answer points:

- usage exposes prompt_cache_hit_tokens and prompt_cache_miss_tokens.
- Granted balance is deducted before topped-up balance.

Evidence:

- [guides/kv_cache, lines 89–89](../materials/deepseek/md/guides/kv_cache.md) — https://api-docs.deepseek.com/guides/kv_cache
- [guides/kv_cache, lines 91–91](../materials/deepseek/md/guides/kv_cache.md) — https://api-docs.deepseek.com/guides/kv_cache
- [quick_start/pricing, lines 45–45](../materials/deepseek/md/quick_start/pricing.md) — https://api-docs.deepseek.com/quick_start/pricing

Scoring: All requested parts must be supported. Cite evidence from the relevant API families; do not substitute a similar field from another interface.

## ds-cross-cache-isolation

Can I segregate cached contexts for users of my application, and does caching guarantee identical generated answers?

- Category: multi_document; split: test; family: cross-cache-isolation; answerable: true

Expected answer points:

- Use user_id for KVCache isolation.
- No; caching only matches input prefixes, while output is still generated and can vary.

Evidence:

- [quick_start/rate_limit, lines 26–30](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit
- [guides/kv_cache, lines 95–95](../materials/deepseek/md/guides/kv_cache.md) — https://api-docs.deepseek.com/guides/kv_cache

Scoring: All requested parts must be supported. Cite evidence from the relevant API families; do not substitute a similar field from another interface.

## ds-cross-files-big-image

An image is 40 MiB. Why is an external URL unsuitable, and how can I supply it through the documented image APIs?

- Category: multi_document; split: dev; family: cross-files-big-image; answerable: true

Expected answer points:

- An external-URL image is limited to 32 MiB.
- Upload it through the Files API, which allows 64 MiB, then reference file_id.

Evidence:

- [guides/vision, lines 69–69](../materials/deepseek/md/guides/vision.md) — https://api-docs.deepseek.com/guides/vision
- [guides/files_api, lines 21–21](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api
- [guides/files_api, lines 150–150](../materials/deepseek/md/guides/files_api.md) — https://api-docs.deepseek.com/guides/files_api

Scoring: All requested parts must be supported. Cite evidence from the relevant API families; do not substitute a similar field from another interface.

## ds-cross-stream-protocol

How does the terminal marker for Chat Completions streaming differ from that of Responses streaming?

- Category: multi_document; split: dev; family: cross-stream-protocol; answerable: true

Expected answer points:

- Chat Completions uses data: [DONE], with final usage in the preceding chunk.
- Responses ends with response.completed, response.incomplete or response.failed and has no [DONE].

Evidence:

- [api/create-chat-completion, lines 310–314](../materials/deepseek/md/api/create-chat-completion.md) — https://api-docs.deepseek.com/api/create-chat-completion
- [guides/responses_api, lines 33–33](../materials/deepseek/md/guides/responses_api.md) — https://api-docs.deepseek.com/guides/responses_api

Scoring: All requested parts must be supported. Cite evidence from the relevant API families; do not substitute a similar field from another interface.

## ds-cross-key-leak-balance

If an API key leaks and I want to protect it and check funds, what does the FAQ recommend and which API endpoint checks balance?

- Category: multi_document; split: dev; family: cross-key-leak-balance; answerable: true

Expected answer points:

- Immediately revoke the compromised key and replace it with a new key.
- Use GET /user/balance.

Evidence:

- [faq-api/key-revoke, lines 6–6](../materials/deepseek/md/faq-api/key-revoke.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/key-revoke
- [faq-api/key-revoke, lines 8–12](../materials/deepseek/md/faq-api/key-revoke.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/key-revoke
- [api/get-user-balance, lines 6–8](../materials/deepseek/md/api/get-user-balance.md) — https://api-docs.deepseek.com/api/get-user-balance

Scoring: All requested parts must be supported. Cite evidence from the relevant API families; do not substitute a similar field from another interface.

## ds-cross-pay-refund

Does a top-up expire, and where is an unused online-payment balance refunded?

- Category: multi_document; split: dev; family: cross-pay-refund; answerable: true

Expected answer points:

- Top-up balances do not expire.
- Unused balances can be refunded through Billing then Refunds for online payments.

Evidence:

- [faq-api/balance-validity, lines 6–6](../materials/deepseek/md/faq-api/balance-validity.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/balance-validity
- [faq-api/refund-policy, lines 6–6](../materials/deepseek/md/faq-api/refund-policy.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/refund-policy
- [faq-api/refund-policy, lines 8–9](../materials/deepseek/md/faq-api/refund-policy.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/refund-policy

Scoring: All requested parts must be supported. Cite evidence from the relevant API families; do not substitute a similar field from another interface.

## ds-cross-copilot-cot

Why does the Copilot CLI guide require the Anthropic provider, and how does the reasoning guide explain the underlying failure?

- Category: multi_document; split: dev; family: cross-copilot-cot; answerable: true

Expected answer points:

- Its OpenAI integration does not replay reasoning_content, so the guide requires anthropic.
- Tool-carrying thinking requests require all prior reasoning_content; incorrect replay returns 400.

Evidence:

- [quick_start/agent_integrations/copilot_cli, lines 8–8](../materials/deepseek/md/quick_start/agent_integrations/copilot_cli.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/copilot_cli
- [guides/thinking_mode, lines 132–132](../materials/deepseek/md/guides/thinking_mode.md) — https://api-docs.deepseek.com/guides/thinking_mode

Scoring: All requested parts must be supported. Cite evidence from the relevant API families; do not substitute a similar field from another interface.

## ds-cross-api-user-id

Where do the OpenAI Chat SDK and Anthropic SDK place the business-user identifier?

- Category: multi_document; split: test; family: cross-api-user-id; answerable: true

Expected answer points:

- OpenAI Chat SDK puts user_id inside extra_body.
- Anthropic supports metadata.user_id while ignoring other metadata fields.

Evidence:

- [quick_start/rate_limit, lines 50–50](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit
- [guides/anthropic_api, lines 88–103](../materials/deepseek/md/guides/anthropic_api.md) — https://api-docs.deepseek.com/guides/anthropic_api

Scoring: All requested parts must be supported. Cite evidence from the relevant API families; do not substitute a similar field from another interface.

## ds-conflict-pro-routing

Does this snapshot consistently identify which model serves deepseek-v4-pro requests? Compare the pricing table with the September 10, 2026 announcement.

- Category: source_conflict; split: dev; family: conflict-pro-routing; answerable: true

Expected answer points:

- The pricing table lists DeepSeek-V4-Pro-0813 for deepseek-v4-pro.
- The September 10 announcement says all Pro requests route to V4.1-Flash at Flash rates starting September 14, 2026 at 04:00 UTC.
- The changelog adds a decision to continue V4 Pro service after September 14 with billing unchanged, explaining why the older announcement should not be treated as the final status.

Evidence:

- [quick_start/pricing, lines 12–33](../materials/deepseek/md/quick_start/pricing.md) — https://api-docs.deepseek.com/quick_start/pricing
- [news/news260910, lines 50–50](../materials/deepseek/md/news/news260910.md) — https://api-docs.deepseek.com/news/news260910
- [updates, lines 40–40](../materials/deepseek/md/updates.md) — https://api-docs.deepseek.com/updates

Scoring: A passing answer explicitly states the disagreement or historical change and attributes each claim to its page/date. Do not silently choose one source or invent a reconciliation. This snapshot cannot independently verify live routing.

## ds-conflict-image-tokens

Why should I not reuse the old Vision-Exp announcement value as the current image-token cap?

- Category: source_conflict; split: dev; family: conflict-image-tokens; answerable: true

Expected answer points:

- The historical Vision-Exp announcement says up to 384 tokens per image.
- The captured Vision guide states a 1024-token cap per image.

Evidence:

- [news/news260821, lines 34–34](../materials/deepseek/md/news/news260821.md) — https://api-docs.deepseek.com/news/news260821
- [guides/vision, lines 163–163](../materials/deepseek/md/guides/vision.md) — https://api-docs.deepseek.com/guides/vision

Scoring: A passing answer explicitly states the disagreement or historical change and attributes each claim to its page/date. Do not silently choose one source or invent a reconciliation. This snapshot cannot independently verify live routing.

## ds-conflict-concurrency

An old caching announcement says there are no concurrency or rate limits. Does that agree with the captured rate-limit guide?

- Category: source_conflict; split: dev; family: conflict-concurrency; answerable: true

Expected answer points:

- The historical caching announcement claimed no concurrency or rate limits.
- The captured rate-limit page lists Flash 2500, Pro 500 and HTTP 429 when limits are exceeded.

Evidence:

- [news/news0802, lines 84–84](../materials/deepseek/md/news/news0802.md) — https://api-docs.deepseek.com/news/news0802
- [quick_start/rate_limit, lines 12–14](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit
- [quick_start/rate_limit, lines 16–18](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit

Scoring: A passing answer explicitly states the disagreement or historical change and attributes each claim to its page/date. Do not silently choose one source or invent a reconciliation. This snapshot cannot independently verify live routing.

## ds-conflict-offpeak

Did the end of off-peak discounts announced in 2025 mean there are no off-peak prices in the captured 2026 pricing table?

- Category: source_conflict; split: dev; family: conflict-offpeak; answerable: true

Expected answer points:

- V3.1 announced off-peak discounts would end September 5, 2025 at 16:00 UTC.
- The captured pricing page has off-peak rates equal to half the peak rates.

Evidence:

- [news/news250821, lines 64–64](../materials/deepseek/md/news/news250821.md) — https://api-docs.deepseek.com/news/news250821
- [quick_start/pricing, lines 37–37](../materials/deepseek/md/quick_start/pricing.md) — https://api-docs.deepseek.com/quick_start/pricing

Scoring: A passing answer explicitly states the disagreement or historical change and attributes each claim to its page/date. Do not silently choose one source or invent a reconciliation. This snapshot cannot independently verify live routing.

## ds-conflict-effort-xhigh

Does xhigh mean the same thing in the general reasoning-effort mapping and in the Oh My Pi configuration example?

- Category: source_conflict; split: dev; family: conflict-effort-xhigh; answerable: true

Expected answer points:

- The general guide maps xhigh to high.
- The Oh My Pi configuration maps its xhigh selector to max.

Evidence:

- [guides/thinking_mode, lines 18–26](../materials/deepseek/md/guides/thinking_mode.md) — https://api-docs.deepseek.com/guides/thinking_mode
- [quick_start/agent_integrations/oh_my_pi, lines 95–95](../materials/deepseek/md/quick_start/agent_integrations/oh_my_pi.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/oh_my_pi

Scoring: A passing answer explicitly states the disagreement or historical change and attributes each claim to its page/date. Do not silently choose one source or invent a reconciliation. This snapshot cannot independently verify live routing.

## ds-unanswerable-personal-key

What is my actual DeepSeek API key?

- Category: unanswerable; split: test; family: unanswerable-personal-key; answerable: false

Expected answer points:

- The public documentation cannot reveal the user's actual API key.

Related background (not positive evidence):

- [index, lines 12–12](../materials/deepseek/md/index.md) — https://api-docs.deepseek.com/

Scoring: Explicitly acknowledge missing evidence and do not invent the requested specifics. A relevant procedure may be offered. context_evidence is related background, NOT proof of corpus-wide absence and NOT a positive retrieval target.

## ds-unanswerable-personal-balance

How many US dollars are currently left in my personal account?

- Category: unanswerable; split: dev; family: unanswerable-personal-balance; answerable: false

Expected answer points:

- The snapshot contains endpoint documentation and examples, not the user's live balance.

Related background (not positive evidence):

- [api/get-user-balance, lines 10–10](../materials/deepseek/md/api/get-user-balance.md) — https://api-docs.deepseek.com/api/get-user-balance

Scoring: Explicitly acknowledge missing evidence and do not invent the requested specifics. A relevant procedure may be offered. context_evidence is related background, NOT proof of corpus-wide absence and NOT a positive retrieval target.

## ds-unanswerable-refund-arrival

What exact calendar date will my submitted refund reach my bank?

- Category: unanswerable; split: dev; family: unanswerable-refund-arrival; answerable: false

Expected answer points:

- No user-specific refund settlement date is present.

Related background (not positive evidence):

- [faq-api/refund-policy, lines 6–6](../materials/deepseek/md/faq-api/refund-policy.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/refund-policy

Scoring: Explicitly acknowledge missing evidence and do not invent the requested specifics. A relevant procedure may be offered. context_evidence is related background, NOT proof of corpus-wide absence and NOT a positive retrieval target.

## ds-unanswerable-private-file

What is inside my uploaded file file-api-PRIVATE-NOT-IN-CORPUS?

- Category: unanswerable; split: dev; family: unanswerable-private-file; answerable: false

Expected answer points:

- The private file contents are unavailable in this documentation snapshot.

Related background (not positive evidence):

- [api/retrieve-file, lines 10–10](../materials/deepseek/md/api/retrieve-file.md) — https://api-docs.deepseek.com/api/retrieve-file

Scoring: Explicitly acknowledge missing evidence and do not invent the requested specifics. A relevant procedure may be offered. context_evidence is related background, NOT proof of corpus-wide absence and NOT a positive retrieval target.

## ds-unanswerable-latency-guarantee

What contractual P99 response-latency SLA does DeepSeek guarantee for my account?

- Category: unanswerable; split: dev; family: unanswerable-latency-guarantee; answerable: false

Expected answer points:

- The captured docs do not provide this account-specific contractual P99 SLA.

Related background (not positive evidence):

- [quick_start/rate_limit, lines 86–86](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit

Scoring: Explicitly acknowledge missing evidence and do not invent the requested specifics. A relevant procedure may be offered. context_evidence is related background, NOT proof of corpus-wide absence and NOT a positive retrieval target.

## ds-unanswerable-uptime

What exact uptime percentage did the API achieve yesterday?

- Category: unanswerable; split: test; family: unanswerable-uptime; answerable: false

Expected answer points:

- Yesterday's measured uptime is not recorded in this frozen corpus.

Related background (not positive evidence):

- [quick_start/error_codes, lines 15–15](../materials/deepseek/md/quick_start/error_codes.md) — https://api-docs.deepseek.com/quick_start/error_codes

Scoring: Explicitly acknowledge missing evidence and do not invent the requested specifics. A relevant procedure may be offered. context_evidence is related background, NOT proof of corpus-wide absence and NOT a positive retrieval target.

## ds-unanswerable-future-pricing

What will Flash output tokens cost exactly one year after this snapshot?

- Category: unanswerable; split: dev; family: unanswerable-future-pricing; answerable: false

Expected answer points:

- Future pricing is not specified and cannot be inferred from present rates.

Related background (not positive evidence):

- [quick_start/pricing, lines 47–47](../materials/deepseek/md/quick_start/pricing.md) — https://api-docs.deepseek.com/quick_start/pricing

Scoring: Explicitly acknowledge missing evidence and do not invent the requested specifics. A relevant procedure may be offered. context_evidence is related background, NOT proof of corpus-wide absence and NOT a positive retrieval target.

## ds-unanswerable-pro-launch

Give the exact public launch timestamp of V4.1-Pro, including seconds.

- Category: unanswerable; split: dev; family: unanswerable-pro-launch; answerable: false

Expected answer points:

- The announcement mentions V4.1-Pro but does not state an exact launch timestamp.

Related background (not positive evidence):

- [news/news260910, lines 50–50](../materials/deepseek/md/news/news260910.md) — https://api-docs.deepseek.com/news/news260910

Scoring: Explicitly acknowledge missing evidence and do not invent the requested specifics. A relevant procedure may be offered. context_evidence is related background, NOT proof of corpus-wide absence and NOT a positive retrieval target.

## ds-unanswerable-weights-secret

What is the private training-data record for my email address?

- Category: unanswerable; split: dev; family: unanswerable-weights-secret; answerable: false

Expected answer points:

- No user-specific training-data records are present in the public API docs.

Related background (not positive evidence):

- [index, lines 6–6](../materials/deepseek/md/index.md) — https://api-docs.deepseek.com/

Scoring: Explicitly acknowledge missing evidence and do not invent the requested specifics. A relevant procedure may be offered. context_evidence is related background, NOT proof of corpus-wide absence and NOT a positive retrieval target.

## ds-unanswerable-embedding-endpoint

What exact DeepSeek embeddings endpoint and vector dimension are specified in this corpus?

- Category: unanswerable; split: dev; family: unanswerable-embedding-endpoint; answerable: false

Expected answer points:

- This captured corpus does not document an embeddings endpoint and its vector dimension.

Related background (not positive evidence):

- [api/deepseek-api, lines 1–1](../materials/deepseek/md/api/deepseek-api.md) — https://api-docs.deepseek.com/api/deepseek-api

Scoring: Explicitly acknowledge missing evidence and do not invent the requested specifics. A relevant procedure may be offered. context_evidence is related background, NOT proof of corpus-wide absence and NOT a positive retrieval target.

## ds-unanswerable-ocr-accuracy

What exact OCR accuracy will Flash achieve on my unseen scanned invoice?

- Category: unanswerable; split: test; family: unanswerable-ocr-accuracy; answerable: false

Expected answer points:

- No accuracy result for that unseen image is supplied.

Related background (not positive evidence):

- [guides/vision, lines 6–6](../materials/deepseek/md/guides/vision.md) — https://api-docs.deepseek.com/guides/vision

Scoring: Explicitly acknowledge missing evidence and do not invent the requested specifics. A relevant procedure may be offered. context_evidence is related background, NOT proof of corpus-wide absence and NOT a positive retrieval target.

## ds-unanswerable-token-exact

Exactly how many tokens will my private 200-page document use?

- Category: unanswerable; split: dev; family: unanswerable-token-exact; answerable: false

Expected answer points:

- The document is unavailable and rough character ratios cannot determine an exact count.

Related background (not positive evidence):

- [quick_start/token_usage, lines 13–13](../materials/deepseek/md/quick_start/token_usage.md) — https://api-docs.deepseek.com/quick_start/token_usage

Scoring: Explicitly acknowledge missing evidence and do not invent the requested specifics. A relevant procedure may be offered. context_evidence is related background, NOT proof of corpus-wide absence and NOT a positive retrieval target.

## ds-unanswerable-quota-approved

Has DeepSeek approved my capacity expansion request?

- Category: unanswerable; split: dev; family: unanswerable-quota-approved; answerable: false

Expected answer points:

- The docs describe requesting expansion, not this user's approval status.

Related background (not positive evidence):

- [quick_start/rate_limit, lines 10–10](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit

Scoring: Explicitly acknowledge missing evidence and do not invent the requested specifics. A relevant procedure may be offered. context_evidence is related background, NOT proof of corpus-wide absence and NOT a positive retrieval target.

## ds-unanswerable-deleted-restoration

Which documented endpoint restores an already deleted file?

- Category: unanswerable; split: dev; family: unanswerable-deleted-restoration; answerable: false

Expected answer points:

- No restore-deleted-file endpoint is documented in the captured corpus.

Related background (not positive evidence):

- [api/delete-file, lines 10–10](../materials/deepseek/md/api/delete-file.md) — https://api-docs.deepseek.com/api/delete-file

Scoring: Explicitly acknowledge missing evidence and do not invent the requested specifics. A relevant procedure may be offered. context_evidence is related background, NOT proof of corpus-wide absence and NOT a positive retrieval target.

## ds-unanswerable-schema-secret

What is the internal implementation code of DeepSeek's JSON-schema validator?

- Category: unanswerable; split: dev; family: unanswerable-schema-secret; answerable: false

Expected answer points:

- The validator's internal source code is not included.

Related background (not positive evidence):

- [guides/tool_calls, lines 98–100](../materials/deepseek/md/guides/tool_calls.md) — https://api-docs.deepseek.com/guides/tool_calls

Scoring: Explicitly acknowledge missing evidence and do not invent the requested specifics. A relevant procedure may be offered. context_evidence is related background, NOT proof of corpus-wide absence and NOT a positive retrieval target.

## ds-unanswerable-cache-clock

At exactly what timestamp will my specific cached prefix be evicted?

- Category: unanswerable; split: test; family: unanswerable-cache-clock; answerable: false

Expected answer points:

- The docs give best-effort behavior and a usual range, not a per-prefix eviction timestamp.

Related background (not positive evidence):

- [guides/kv_cache, lines 101–101](../materials/deepseek/md/guides/kv_cache.md) — https://api-docs.deepseek.com/guides/kv_cache

Scoring: Explicitly acknowledge missing evidence and do not invent the requested specifics. A relevant procedure may be offered. context_evidence is related background, NOT proof of corpus-wide absence and NOT a positive retrieval target.

## ds-unanswerable-key-transaction

Which of my API keys caused the largest charge this morning?

- Category: unanswerable; split: dev; family: unanswerable-key-transaction; answerable: false

Expected answer points:

- User-specific usage logs are not present; the FAQ only describes how to inspect them.

Related background (not positive evidence):

- [faq-api/key-usage, lines 8–10](../materials/deepseek/md/faq-api/key-usage.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/key-usage

Scoring: Explicitly acknowledge missing evidence and do not invent the requested specifics. A relevant procedure may be offered. context_evidence is related background, NOT proof of corpus-wide absence and NOT a positive retrieval target.

## ds-unanswerable-server-region

Which physical server and rack processed my last request?

- Category: unanswerable; split: dev; family: unanswerable-server-region; answerable: false

Expected answer points:

- No user request trace or physical server/rack assignment is available.

Related background (not positive evidence):

- [api/create-chat-completion, lines 10–10](../materials/deepseek/md/api/create-chat-completion.md) — https://api-docs.deepseek.com/api/create-chat-completion

Scoring: Explicitly acknowledge missing evidence and do not invent the requested specifics. A relevant procedure may be offered. context_evidence is related background, NOT proof of corpus-wide absence and NOT a positive retrieval target.

## ds-unanswerable-refund-approved

Was my refund approved or rejected?

- Category: unanswerable; split: dev; family: unanswerable-refund-approved; answerable: false

Expected answer points:

- The public refund procedure does not reveal the user's refund status.

Related background (not positive evidence):

- [faq-api/refund-policy, lines 6–6](../materials/deepseek/md/faq-api/refund-policy.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/refund-policy

Scoring: Explicitly acknowledge missing evidence and do not invent the requested specifics. A relevant procedure may be offered. context_evidence is related background, NOT proof of corpus-wide absence and NOT a positive retrieval target.

## ds-unanswerable-benchmark-our-app

What accuracy and P95 latency did this KnowledgeBase project achieve on these DeepSeek questions?

- Category: unanswerable; split: dev; family: unanswerable-benchmark-our-app; answerable: false

Expected answer points:

- These source documents contain no measured KnowledgeBase evaluation results.

Related background (not positive evidence):

- [index, lines 6–6](../materials/deepseek/md/index.md) — https://api-docs.deepseek.com/

Scoring: Explicitly acknowledge missing evidence and do not invent the requested specifics. A relevant procedure may be offered. context_evidence is related background, NOT proof of corpus-wide absence and NOT a positive retrieval target.

## ds-sample-curl-auth

Which environment-variable name is interpolated in the Authorization header of the curl chat sample?

- Category: keyword; split: dev; family: samples-chat_curl; answerable: true

Expected answer points:

- DEEPSEEK_API_KEY

Evidence:

- [api_samples/chat_curl, lines 6–20](../materials/deepseek/md/api_samples/chat_curl.md) — https://api-docs.deepseek.com/api_samples/chat_curl

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-sample-node-result

Which JavaScript property expression is printed as the answer in chat_nodejs?

- Category: keyword; split: test; family: samples-chat_nodejs; answerable: true

Expected answer points:

- completion.choices[0].message.content

Evidence:

- [api_samples/chat_nodejs, lines 25–26](../materials/deepseek/md/api_samples/chat_nodejs.md) — https://api-docs.deepseek.com/api_samples/chat_nodejs

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-sample-python-result

Which Python expression is printed as the answer in chat_python?

- Category: keyword; split: dev; family: samples-chat_python; answerable: true

Expected answer points:

- response.choices[0].message.content

Evidence:

- [api_samples/chat_python, lines 26–27](../materials/deepseek/md/api_samples/chat_python.md) — https://api-docs.deepseek.com/api_samples/chat_python

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-sample-nonstream-cot

Which response expression reads reasoning in the non-streaming thinking example?

- Category: keyword; split: dev; family: samples-thinking_mode_api_example_non_streaming; answerable: true

Expected answer points:

- response.choices[0].message.reasoning_content

Evidence:

- [api_samples/thinking_mode_api_example_non_streaming, lines 19–20](../materials/deepseek/md/api_samples/thinking_mode_api_example_non_streaming.md) — https://api-docs.deepseek.com/api_samples/thinking_mode_api_example_non_streaming

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-sample-stream-cot

Which delta expression is accumulated as reasoning in the streaming example?

- Category: keyword; split: dev; family: samples-thinking_mode_api_example_streaming; answerable: true

Expected answer points:

- chunk.choices[0].delta.reasoning_content

Evidence:

- [api_samples/thinking_mode_api_example_streaming, lines 23–27](../materials/deepseek/md/api_samples/thinking_mode_api_example_streaming.md) — https://api-docs.deepseek.com/api_samples/thinking_mode_api_example_streaming

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-sample-tool-stop

In the thinking tool-call sample, what condition ends the sub-turn loop?

- Category: semantic; split: dev; family: samples-thinking_mode_api_example_tool_call; answerable: true

Expected answer points:

- The loop stops when tool_calls is None.

Evidence:

- [api_samples/thinking_mode_api_example_tool_call, lines 51–79](../materials/deepseek/md/api_samples/thinking_mode_api_example_tool_call.md) — https://api-docs.deepseek.com/api_samples/thinking_mode_api_example_tool_call

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-sample-output-date

What get_date result is printed in Turn 1.1 of the captured sample output?

- Category: keyword; split: dev; family: samples-thinking_mode_api_example_tool_call_output; answerable: true

Expected answer points:

- 2026-04-19

Evidence:

- [api_samples/thinking_mode_api_example_tool_call_output, lines 6–11](../materials/deepseek/md/api_samples/thinking_mode_api_example_tool_call_output.md) — https://api-docs.deepseek.com/api_samples/thinking_mode_api_example_tool_call_output

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-fim-echo

Can echo be combined with suffix or logprobs in FIM Completion?

- Category: keyword; split: dev; family: fim-echo; answerable: true

Expected answer points:

- No. echo cannot be combined with suffix or logprobs.

Evidence:

- [api/create-completion, lines 29–31](../materials/deepseek/md/api/create-completion.md) — https://api-docs.deepseek.com/api/create-completion

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-fim-logprobs

Why can a FIM token logprob result contain up to logprobs+1 entries?

- Category: keyword; split: dev; family: fim-logprobs; answerable: true

Expected answer points:

- The sampled token is always returned alongside the most likely alternatives, so the result can contain logprobs+1 entries.

Evidence:

- [api/create-completion, lines 33–37](../materials/deepseek/md/api/create-completion.md) — https://api-docs.deepseek.com/api/create-completion

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-responses-required-input

Must both input and instructions be supplied to POST /responses?

- Category: keyword; split: dev; family: responses-required-input; answerable: true

Expected answer points:

- No; at least one of input and instructions is required.

Evidence:

- [api/create-response, lines 36–36](../materials/deepseek/md/api/create-response.md) — https://api-docs.deepseek.com/api/create-response

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-responses-developer

How does the Responses API interpret developer message roles?

- Category: keyword; split: test; family: responses-developer; answerable: true

Expected answer points:

- developer is treated as user.

Evidence:

- [api/create-response, lines 50–54](../materials/deepseek/md/api/create-response.md) — https://api-docs.deepseek.com/api/create-response

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-faq-destination

Where does the captured documentation FAQ landing page send English readers?

- Category: keyword; split: test; family: faq-destination; answerable: true

Expected answer points:

- https://static.deepseek.com/faq/index.html?lang=en#/category/4

Evidence:

- [faq, lines 6–6](../materials/deepseek/md/faq.md) — https://api-docs.deepseek.com/faq

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-coding-guide-opencode

What minimum OpenCode version does the combined Integrate with AI Tools page recommend, specifically?

- Category: keyword; split: dev; family: coding-guide-opencode; answerable: true

Expected answer points:

- v1.14.24

Evidence:

- [guides/coding_agents, lines 75–75](../materials/deepseek/md/guides/coding_agents.md) — https://api-docs.deepseek.com/guides/coding_agents

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-news-route-anomaly

In the frozen snapshot, what content is actually captured at /news/news251201 rather than an original V3.2 announcement?

- Category: source_conflict; split: dev; family: news-route-anomaly; answerable: true

Expected answer points:

- It contains Your First API Call and the current introductory API instructions.

Evidence:

- [news/news251201, lines 1–1](../materials/deepseek/md/news/news251201.md) — https://api-docs.deepseek.com/news/news251201

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-updates-pro

What decision about V4 Pro after September 14, 2026 is recorded in the captured Change Log?

- Category: historical; split: dev; family: updates-pro; answerable: true

Expected answer points:

- Continue providing V4 Pro API services after September 14 with billing unchanged.

Evidence:

- [updates, lines 40–40](../materials/deepseek/md/updates.md) — https://api-docs.deepseek.com/updates

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-updates-hle-footnote

In the V4.1-Flash Change Log entry, what does the asterisk on HLE 39.1 mean?

- Category: historical; split: dev; family: updates-hle-footnote; answerable: true

Expected answer points:

- It was tested only on the pure-text subset of the HLE benchmark.

Evidence:

- [updates, lines 34–34](../materials/deepseek/md/updates.md) — https://api-docs.deepseek.com/updates

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-opaque-call-date

Which function is associated with call_00_kw66qNnNto11bSfJVIdlV5Oo in the sample transcript?

- Category: keyword; split: dev; family: samples-thinking_mode_api_example_tool_call_output; answerable: true

Expected answer points:

- get_date

Evidence:

- [api_samples/thinking_mode_api_example_tool_call_output, lines 6–11](../materials/deepseek/md/api_samples/thinking_mode_api_example_tool_call_output.md) — https://api-docs.deepseek.com/api_samples/thinking_mode_api_example_tool_call_output

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-opaque-call-hangzhou

Which city and date occur in the arguments of call_00_H2SCW6136vWJGq9SQlBuhVt4?

- Category: keyword; split: dev; family: samples-thinking_mode_api_example_tool_call_output; answerable: true

Expected answer points:

- Hangzhou and 2026-04-20.

Evidence:

- [api_samples/thinking_mode_api_example_tool_call_output, lines 13–17](../materials/deepseek/md/api_samples/thinking_mode_api_example_tool_call_output.md) — https://api-docs.deepseek.com/api_samples/thinking_mode_api_example_tool_call_output

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-opaque-call-guangzhou

Which city and date occur in the arguments of call_00_8URkLt5NjmNkVKhDmMcNq9Mo?

- Category: keyword; split: dev; family: samples-thinking_mode_api_example_tool_call_output; answerable: true

Expected answer points:

- Guangzhou and 2026-04-20.

Evidence:

- [api_samples/thinking_mode_api_example_tool_call_output, lines 24–28](../materials/deepseek/md/api_samples/thinking_mode_api_example_tool_call_output.md) — https://api-docs.deepseek.com/api_samples/thinking_mode_api_example_tool_call_output

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-keyword-csv-amount

Which CSV file in the exported usage ZIP contains usage details by API key?

- Category: keyword; split: dev; family: keyword-csv-amount; answerable: true

Expected answer points:

- The file titled amount.

Evidence:

- [faq-api/key-usage, lines 8–10](../materials/deepseek/md/faq-api/key-usage.md) — https://static.deepseek.com/faq/index.html?lang=en#/question/key-usage

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-keyword-regex-length

For user_id matching [a-zA-Z0-9\-_]+, what maximum length is documented?

- Category: keyword; split: dev; family: keyword-regex-length; answerable: true

Expected answer points:

- 512 characters.

Evidence:

- [quick_start/rate_limit, lines 34–34](../materials/deepseek/md/quick_start/rate_limit.md) — https://api-docs.deepseek.com/quick_start/rate_limit

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-keyword-compat-spelling

What does requiresAssistantContentForToolCalls ensure, according to the Oh My Pi table?

- Category: keyword; split: dev; family: keyword-compat-spelling; answerable: true

Expected answer points:

- Tool-call messages have non-null content.

Evidence:

- [quick_start/agent_integrations/oh_my_pi, lines 103–107](../materials/deepseek/md/quick_start/agent_integrations/oh_my_pi.md) — https://api-docs.deepseek.com/quick_start/agent_integrations/oh_my_pi

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.

## ds-keyword-file-prefix

What exact prefix identifies an uploaded file ID in the Upload File API?

- Category: keyword; split: dev; family: keyword-file-prefix; answerable: true

Expected answer points:

- file-api-

Evidence:

- [api/create-file, lines 48–50](../materials/deepseek/md/api/create-file.md) — https://api-docs.deepseek.com/api/create-file

Scoring: Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.
