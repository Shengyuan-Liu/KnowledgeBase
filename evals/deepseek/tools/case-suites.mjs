export function extend({add,pair,docs,cases,evidence}) {
  const integrations = [
    ['astrbot','What local address and port does the AstrBot integration guide use for the Web UI?','http://localhost:6185','http://localhost:6185'],
    ['astrbot','Which two commands initialize and start AstrBot?','astrbot init initializes it; astrbot run starts it.','astrbot init #'],
    ['claude_code','What value is assigned to CLAUDE_CODE_AUTO_COMPACT_WINDOW in the Claude Code guide?','786432','export CLAUDE_CODE_AUTO_COMPACT_WINDOW=786432'],
    ['claude_code','What value does the Claude Code configuration give ANTHROPIC_DEFAULT_HAIKU_MODEL?','deepseek-flash','export ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-flash'],
    ['codex','According to the DeepSeek integration guide, what does wire_api = "responses" select?','It selects the Responses API protocol.','| `wire_api` in'],
    ['codex','Where does the DeepSeek Codex setup script back up the existing configuration?','~/.codex/backup-deepseek/','is backed up to'],
    ['copilot_cli','Which provider type must GitHub Copilot CLI use, and why does the OpenAI type fail?','Use anthropic; the OpenAI integration fails to replay reasoning_content in thinking mode, causing HTTP 400.','Use `anthropic` as the provider type'],
    ['copilot_cli','Does COPILOT_OFFLINE=true prevent prompts from reaching DeepSeek?','No. Prompts still reach api.deepseek.com; it only blocks GitHub API calls.','offline mode only blocks'],
    ['copilot_cli','What values does the guide set for COPILOT_PROVIDER_MAX_PROMPT_TOKENS and COPILOT_PROVIDER_MAX_OUTPUT_TOKENS?','840000 and 128000, respectively.','export COPILOT_PROVIDER_MAX_PROMPT_TOKENS=840000'],
    ['crush','What Linux/macOS configuration file path is given for Crush?','~/.config/crush/crush.json','~/.config/crush/crush.json'],
    ['crush','What provider type does the Crush JSON example configure for DeepSeek?','openai-compat','"type": "openai-compat"'],
    ['deepcode','Where does the Deep Code guide place its settings file?','~/.deepcode/settings.json','Create `~/.deepcode/settings.json`'],
    ['deepcode','What is the project-level Agent Skills discovery path in Deep Code?','./.deepcode/skills/<name>/SKILL.md','**Project-level:**'],
    ['github_copilot','Where does the GitHub Copilot extension guide say it stores the API key?','In the OS keychain, not on disk.','The key is stored securely'],
    ['github_copilot','Which command chooses the extension model used to describe images before sending their description to DeepSeek?','DeepSeek: Set Vision Proxy Model','DeepSeek: Set Vision Proxy Model'],
    ['oh_my_pi','What models file does the Oh My Pi integration guide require?','~/.omp/agent/models.yml','Create `~/.omp/agent/models.yml`'],
    ['oh_my_pi','Does an Oh My Pi compat block merge into the built-in block or replace it?','It replaces the entire built-in block, so specify all compatibility fields.','`compat` replaces the built-in block wholesale'],
    ['openclaw','Which command returns an existing OpenClaw installation to configuration?','openclaw onboard --install-daemon','openclaw onboard --install-daemon'],
    ['openclaw','Which command opens the OpenClaw Web UI?','openclaw dashboard','openclaw dashboard'],
    ['pi_mono','What is the Linux/macOS custom model catalog path for Pi?','~/.pi/agent/models.json','~/.pi/agent/models.json'],
    ['pi_mono','Which exact compatibility key does Pi use to preserve reasoning on assistant messages?','requiresReasoningContentOnAssistantMessages','"requiresReasoningContentOnAssistantMessages": true'],
    ['qoder','What slash command and tab are used to configure a custom model in Qoder CLI?','Use /model and its Custom tab/wizard.','Type `/model` in the CLI'],
    ['qoder','Does a Qoder custom model consume Qoder Credits?','No; custom-model usage is billed directly to the DeepSeek API account.','**Custom models**:'],
    ['reasonix','Where does the first-run Reasonix wizard persist its key configuration?','~/.reasonix/config.json','persists it to `~/.reasonix/config.json`'],
    ['reasonix','How do /pro and /preset max differ in Reasonix?','/pro selects Pro for the next turn; /preset max selects Pro for the entire session.','Type `/pro` inside the TUI'],
    ['workbuddy','What encoding must the WorkBuddy/CodeBuddy models.json use?','UTF-8 without BOM.','Save `models.json` as UTF-8 without BOM'],
    ['workbuddy','What exact endpoint does the WorkBuddy/CodeBuddy model JSON example put in url?','https://api.deepseek.com/v1/chat/completions','"url": "https://api.deepseek.com/v1/chat/completions"']
  ];
  integrations.forEach(([id,q,a,n],i)=>add(`integration-detail-${i+1}`,'keyword',`quick_start/agent_integrations/${id}`,q,[[a,n]],{family:`integration-${id}`,tags:['identifier_sensitive','page_specific_configuration']}));

  pair('chat-stop-limit','api/create-chat-completion',
    'How many different strings may I ask the chat service to stop at?',
    'What is the maximum number of stop sequences for Chat Completions?',
    [['At most 16 stop sequences.','Up to 16 sequences']],['16']);
  pair('chat-logprob','api/create-chat-completion',
    'What must I turn on before requesting probabilities for alternative output tokens, and how many alternatives are allowed?',
    'What range and logprobs prerequisite apply to top_logprobs?',
    [['top_logprobs allows 0–20 and requires logprobs:true.','An integer between 0 and 20']],['20','logprobs']);
  pair('chat-usage-chunk','api/create-chat-completion',
    'Where should a streaming chat client read final usage if there is no separate usage-only event?',
    'What is the final Chat Completions usage chunk shape before data: [DONE]?',
    [['The last chunk before [DONE] carries full-request usage; there is no separate usage-only chunk, and choices has one element with no new content and a non-null finish_reason.','Either way, the last chunk before']],['usage','finish_reason']);
  pair('chat-finish-reasons','api/create-chat-completion',
    'How can I tell whether generation was cut short because inference resources were insufficient or because it was interrupted?',
    'Define finish_reason values insufficient_system_resource and aborted.',
    [['insufficient_system_resource means interrupted for insufficient inference-system resources; aborted means generation was interrupted.','The reason the model stopped generating tokens.']],['insufficient_system_resource','aborted']);
  pair('chat-length-reason','api/create-chat-completion',
    'How can I distinguish an answer naturally finishing from one stopping because its generation budget was exhausted?',
    'Compare finish_reason="stop" with finish_reason="length" in Chat Completions.',
    [['stop means a natural stopping point or provided stop sequence; length means the requested maximum number of tokens was reached.','The reason the model stopped generating tokens.']],['stop','length']);

  const cross = (id,q,points,notes) => add(id,'multi_document',null,q,points,{difficulty:'hard',notes:notes || 'All requested parts must be supported. Cite evidence from the relevant API families; do not substitute a similar field from another interface.'});
  cross('cross-history-stream','I need a multi-turn chat whose answer arrives incrementally. What history must I send, and which request option enables streaming?',[
    ['Send concatenated previous history because chat is stateless.','API is a "stateless" API','guides/multi_round_chat'],
    ['Set stream to true.','you can set the `stream` parameter','index']]);
  cross('cross-json-strict','How does enabling JSON Output differ from enabling strict tool argument schemas?',[
    ['JSON Output uses response_format json_object plus the word json and an example in the prompt.',['Set the `response_format`','Include the word "json"'],'guides/json_mode'],
    ['Strict tool calls use the beta URL, strict:true on functions, and server schema validation.',['Use `base_url=','all `function` need','The server will validate'],'guides/tool_calls']]);
  cross('cross-fim-prefix','Compare filling a code gap with continuing an assistant prefix: how do their inputs differ, and what beta address do both use?',[
    ['FIM takes a prefix and optional suffix and fills the middle.','users can provide a prefix and a suffix','guides/fim_completion'],
    ['Chat prefix completion continues the last assistant message with prefix:true.','users must ensure','guides/chat_prefix_completion'],
    ['Both use https://api.deepseek.com/beta.','The user needs to set','guides/chat_prefix_completion']]);
  cross('cross-fim-thinking','Can I use the advertised 384K maximum output for a thinking-mode FIM request?',[
    ['No; the pricing table restricts FIM to non-thinking mode.','Non-thinking mode only','quick_start/pricing'],
    ['The FIM guide separately limits FIM output to 4K tokens.','The max tokens of FIM','guides/fim_completion']]);
  cross('cross-cache-billing','How do I inspect cache reuse counters and determine which wallet balance is charged first?',[
    ['usage exposes prompt_cache_hit_tokens and prompt_cache_miss_tokens.',['`prompt_cache_hit_tokens`:','`prompt_cache_miss_tokens`:'],'guides/kv_cache'],
    ['Granted balance is deducted before topped-up balance.','The expense = number of tokens','quick_start/pricing']]);
  cross('cross-cache-isolation','Can I segregate cached contexts for users of my application, and does caching guarantee identical generated answers?',[
    ['Use user_id for KVCache isolation.','**KVCache Isolation:**','quick_start/rate_limit'],
    ['No; caching only matches input prefixes, while output is still generated and can vary.','The hard disk cache only matches','guides/kv_cache']]);
  cross('cross-files-big-image','An image is 40 MiB. Why is an external URL unsuitable, and how can I supply it through the documented image APIs?',[
    ['An external-URL image is limited to 32 MiB.','Pass a publicly accessible','guides/vision'],
    ['Upload it through the Files API, which allows 64 MiB, then reference file_id.',['A single file may be at most','Reference the returned `file_id`'],'guides/files_api']]);
  cross('cross-stream-protocol','How does the terminal marker for Chat Completions streaming differ from that of Responses streaming?',[
    ['Chat Completions uses data: [DONE], with final usage in the preceding chunk.','Either way, the last chunk before','api/create-chat-completion'],
    ['Responses ends with response.completed, response.incomplete or response.failed and has no [DONE].','Set `stream: true`','guides/responses_api']]);
  cross('cross-key-leak-balance','If an API key leaks and I want to protect it and check funds, what does the FAQ recommend and which API endpoint checks balance?',[
    ['Immediately revoke the compromised key and replace it with a new key.',['revoking the compromised key immediately','After revocation, please create'],'faq-api/key-revoke'],
    ['Use GET /user/balance.','GET /user/balance','api/get-user-balance']]);
  cross('cross-pay-refund','Does a top-up expire, and where is an unused online-payment balance refunded?',[
    ['Top-up balances do not expire.','Top-up balances do not expire.','faq-api/balance-validity'],
    ['Unused balances can be refunded through Billing then Refunds for online payments.',['Unused balances','**Online Payment:**'],'faq-api/refund-policy']]);
  cross('cross-copilot-cot','Why does the Copilot CLI guide require the Anthropic provider, and how does the reasoning guide explain the underlying failure?',[
    ['Its OpenAI integration does not replay reasoning_content, so the guide requires anthropic.','Use `anthropic` as the provider type','quick_start/agent_integrations/copilot_cli'],
    ['Tool-carrying thinking requests require all prior reasoning_content; incorrect replay returns 400.','Please note that for requests carrying','guides/thinking_mode']]);
  cross('cross-api-user-id','Where do the OpenAI Chat SDK and Anthropic SDK place the business-user identifier?',[
    ['OpenAI Chat SDK puts user_id inside extra_body.','you need to place the `user_id` parameter','quick_start/rate_limit'],
    ['Anthropic supports metadata.user_id while ignoring other metadata fields.','| metadata |','guides/anthropic_api']]);

  const conflict = (id,q,points) => add(id,'source_conflict',null,q,points,{difficulty:'hard',tags:['conflicting_sources'],notes:'A passing answer explicitly states the disagreement or historical change and attributes each claim to its page/date. Do not silently choose one source or invent a reconciliation. This snapshot cannot independently verify live routing.'});
  conflict('conflict-pro-routing','Does this snapshot consistently identify which model serves deepseek-v4-pro requests? Compare the pricing table with the September 10, 2026 announcement.',[
    ['The pricing table lists DeepSeek-V4-Pro-0813 for deepseek-v4-pro.','| MODEL VERSION |','quick_start/pricing'],
    ['The September 10 announcement says all Pro requests route to V4.1-Flash at Flash rates starting September 14, 2026 at 04:00 UTC.','Starting at 04:00 UTC on Sept 14','news/news260910'],
    ['The changelog adds a decision to continue V4 Pro service after September 14 with billing unchanged, explaining why the older announcement should not be treated as the final status.','In response to user demand, we have decided','updates']]);
  conflict('conflict-image-tokens','Why should I not reuse the old Vision-Exp announcement value as the current image-token cap?',[
    ['The historical Vision-Exp announcement says up to 384 tokens per image.','Images are tokenized for billing: up to 384','news/news260821'],
    ['The captured Vision guide states a 1024-token cap per image.','As a result, there is an upper bound','guides/vision']]);
  conflict('conflict-concurrency','An old caching announcement says there are no concurrency or rate limits. Does that agree with the captured rate-limit guide?',[
    ['The historical caching announcement claimed no concurrency or rate limits.','with no limits on concurrency or rate','news/news0802'],
    ['The captured rate-limit page lists Flash 2500, Pro 500 and HTTP 429 when limits are exceeded.',['| Concurrency Limit |','when the concurrency limit is exceeded'],'quick_start/rate_limit']]);
  conflict('conflict-offpeak','Did the end of off-peak discounts announced in 2025 mean there are no off-peak prices in the captured 2026 pricing table?',[
    ['V3.1 announced off-peak discounts would end September 5, 2025 at 16:00 UTC.','New pricing starts & off-peak discounts end','news/news250821'],
    ['The captured pricing page has off-peak rates equal to half the peak rates.','Off-peak rates are half','quick_start/pricing']]);
  conflict('conflict-effort-xhigh','Does xhigh mean the same thing in the general reasoning-effort mapping and in the Oh My Pi configuration example?',[
    ['The general guide maps xhigh to high.','| xhigh |','guides/thinking_mode'],
    ['The Oh My Pi configuration maps its xhigh selector to max.','Maps OMP\'s `xhigh` to DeepSeek\'s `max`','quick_start/agent_integrations/oh_my_pi']]);

  const absent = [
    ['personal-key','What is my actual DeepSeek API key?','The public documentation cannot reveal the user\'s actual API key.','index','apply for an'],
    ['personal-balance','How many US dollars are currently left in my personal account?','The snapshot contains endpoint documentation and examples, not the user\'s live balance.','api/get-user-balance','Get user current balance'],
    ['refund-arrival','What exact calendar date will my submitted refund reach my bank?','No user-specific refund settlement date is present.','faq-api/refund-policy','Unused balances'],
    ['private-file','What is inside my uploaded file file-api-PRIVATE-NOT-IN-CORPUS?','The private file contents are unavailable in this documentation snapshot.','api/retrieve-file','Returns information'],
    ['latency-guarantee','What contractual P99 response-latency SLA does DeepSeek guarantee for my account?','The captured docs do not provide this account-specific contractual P99 SLA.','quick_start/rate_limit','Request Keep-Alive Mechanism'],
    ['uptime','What exact uptime percentage did the API achieve yesterday?','Yesterday\'s measured uptime is not recorded in this frozen corpus.','quick_start/error_codes','Our server encounters'],
    ['future-pricing','What will Flash output tokens cost exactly one year after this snapshot?','Future pricing is not specified and cannot be inferred from present rates.','quick_start/pricing','Product prices may vary'],
    ['pro-launch','Give the exact public launch timestamp of V4.1-Pro, including seconds.','The announcement mentions V4.1-Pro but does not state an exact launch timestamp.','news/news260910','until V4.1-Pro launches'],
    ['weights-secret','What is the private training-data record for my email address?','No user-specific training-data records are present in the public API docs.','index','The DeepSeek API uses'],
    ['embedding-endpoint','What exact DeepSeek embeddings endpoint and vector dimension are specified in this corpus?','This captured corpus does not document an embeddings endpoint and its vector dimension.','api/deepseek-api','DeepSeek API'],
    ['ocr-accuracy','What exact OCR accuracy will Flash achieve on my unseen scanned invoice?','No accuracy result for that unseen image is supplied.','guides/vision','The `deepseek-flash` model accepts images'],
    ['token-exact','Exactly how many tokens will my private 200-page document use?','The document is unavailable and rough character ratios cannot determine an exact count.','quick_start/token_usage','However, due to the different tokenization'],
    ['quota-approved','Has DeepSeek approved my capacity expansion request?','The docs describe requesting expansion, not this user\'s approval status.','quick_start/rate_limit','If you need higher concurrency'],
    ['deleted-restoration','Which documented endpoint restores an already deleted file?','No restore-deleted-file endpoint is documented in the captured corpus.','api/delete-file','Deletes a file.'],
    ['schema-secret','What is the internal implementation code of DeepSeek\'s JSON-schema validator?','The validator\'s internal source code is not included.','guides/tool_calls','The server will validate'],
    ['cache-clock','At exactly what timestamp will my specific cached prefix be evicted?','The docs give best-effort behavior and a usual range, not a per-prefix eviction timestamp.','guides/kv_cache','Cache construction takes seconds'],
    ['key-transaction','Which of my API keys caused the largest charge this morning?','User-specific usage logs are not present; the FAQ only describes how to inspect them.','faq-api/key-usage','Select your desired time range'],
    ['server-region','Which physical server and rack processed my last request?','No user request trace or physical server/rack assignment is available.','api/create-chat-completion','Creates a model response'],
    ['refund-approved','Was my refund approved or rejected?','The public refund procedure does not reveal the user\'s refund status.','faq-api/refund-policy','Unused balances'],
    ['benchmark-our-app','What accuracy and P95 latency did this KnowledgeBase project achieve on these DeepSeek questions?','These source documents contain no measured KnowledgeBase evaluation results.','index','The DeepSeek API uses']
  ];
  for(const [id,q,point,doc,needle] of absent) {
    const ref = evidence(doc,needle,1);
    ref.supports_answer_points = [];
    cases.push({id:`ds-unanswerable-${id}`,corpus_id:cases[0].corpus_id,family_id:`unanswerable-${id}`,
      split:absent.findIndex(x=>x[0]===id)%5===0?'test':'dev',category:'unanswerable',difficulty:'hard',question:q,answerable:false,
      expected_answer_points:[point],evidence:[],context_evidence:[ref],exact_answer_tokens:[],tags:['abstention'],
      scoring_notes:'Explicitly acknowledge missing evidence and do not invent the requested specifics. A relevant procedure may be offered. context_evidence is related background, NOT proof of corpus-wide absence and NOT a positive retrieval target.'});
  }

  const focused = [
    ['sample-curl-auth','keyword','api_samples/chat_curl','Which environment-variable name is interpolated in the Authorization header of the curl chat sample?','DEEPSEEK_API_KEY','Authorization: Bearer ${DEEPSEEK_API_KEY}'],
    ['sample-node-result','keyword','api_samples/chat_nodejs','Which JavaScript property expression is printed as the answer in chat_nodejs?','completion.choices[0].message.content','console.log(completion.choices[0].message.content)'],
    ['sample-python-result','keyword','api_samples/chat_python','Which Python expression is printed as the answer in chat_python?','response.choices[0].message.content','print(response.choices[0].message.content)'],
    ['sample-nonstream-cot','keyword','api_samples/thinking_mode_api_example_non_streaming','Which response expression reads reasoning in the non-streaming thinking example?','response.choices[0].message.reasoning_content','reasoning_content = response.choices[0].message.reasoning_content'],
    ['sample-stream-cot','keyword','api_samples/thinking_mode_api_example_streaming','Which delta expression is accumulated as reasoning in the streaming example?','chunk.choices[0].delta.reasoning_content','reasoning_content += chunk.choices[0].delta.reasoning_content'],
    ['sample-tool-stop','semantic','api_samples/thinking_mode_api_example_tool_call','In the thinking tool-call sample, what condition ends the sub-turn loop?','The loop stops when tool_calls is None.','if tool_calls is None:'],
    ['sample-output-date','keyword','api_samples/thinking_mode_api_example_tool_call_output','What get_date result is printed in Turn 1.1 of the captured sample output?','2026-04-19','tool result for get_date: 2026-04-19'],
    ['fim-echo','keyword','api/create-completion','Can echo be combined with suffix or logprobs in FIM Completion?','No. echo cannot be combined with suffix or logprobs.','Echo back the prompt'],
    ['fim-logprobs','keyword','api/create-completion','Why can a FIM token logprob result contain up to logprobs+1 entries?','The sampled token is always returned alongside the most likely alternatives, so the result can contain logprobs+1 entries.','Include the log probabilities on the'],
    ['responses-required-input','keyword','api/create-response','Must both input and instructions be supplied to POST /responses?','No; at least one of input and instructions is required.','At least one of `input` and `instructions`'],
    ['responses-developer','keyword','api/create-response','How does the Responses API interpret developer message roles?','developer is treated as user.','The role of the message author. `developer`'],
    ['faq-destination','keyword','faq','Where does the captured documentation FAQ landing page send English readers?','https://static.deepseek.com/faq/index.html?lang=en#/category/4','If you are not redirected'],
    ['coding-guide-opencode','keyword','guides/coding_agents','What minimum OpenCode version does the combined Integrate with AI Tools page recommend, specifically?','v1.14.24','version number is >= v1.14.24'],
    ['news-route-anomaly','source_conflict','news/news251201','In the frozen snapshot, what content is actually captured at /news/news251201 rather than an original V3.2 announcement?','It contains Your First API Call and the current introductory API instructions.','Your First API Call'],
    ['updates-pro','historical','updates','What decision about V4 Pro after September 14, 2026 is recorded in the captured Change Log?','Continue providing V4 Pro API services after September 14 with billing unchanged.','In response to user demand, we have decided'],
    ['updates-hle-footnote','historical','updates','In the V4.1-Flash Change Log entry, what does the asterisk on HLE 39.1 mean?','It was tested only on the pure-text subset of the HLE benchmark.','Tested only on the pure-text subset'],
    ['opaque-call-date','keyword','api_samples/thinking_mode_api_example_tool_call_output','Which function is associated with call_00_kw66qNnNto11bSfJVIdlV5Oo in the sample transcript?','get_date','call_00_kw66qNnNto11bSfJVIdlV5Oo'],
    ['opaque-call-hangzhou','keyword','api_samples/thinking_mode_api_example_tool_call_output','Which city and date occur in the arguments of call_00_H2SCW6136vWJGq9SQlBuhVt4?','Hangzhou and 2026-04-20.','call_00_H2SCW6136vWJGq9SQlBuhVt4'],
    ['opaque-call-guangzhou','keyword','api_samples/thinking_mode_api_example_tool_call_output','Which city and date occur in the arguments of call_00_8URkLt5NjmNkVKhDmMcNq9Mo?','Guangzhou and 2026-04-20.','call_00_8URkLt5NjmNkVKhDmMcNq9Mo'],
    ['keyword-csv-amount','keyword','faq-api/key-usage','Which CSV file in the exported usage ZIP contains usage details by API key?','The file titled amount.','the file titled **amount**'],
    ['keyword-regex-length','keyword','quick_start/rate_limit','For user_id matching [a-zA-Z0-9\\-_]+, what maximum length is documented?','512 characters.','The `user_id` parameter must be a string'],
    ['keyword-compat-spelling','keyword','quick_start/agent_integrations/oh_my_pi','What does requiresAssistantContentForToolCalls ensure, according to the Oh My Pi table?','Tool-call messages have non-null content.','| `requiresAssistantContentForToolCalls: true`'],
    ['keyword-file-prefix','keyword','api/create-file','What exact prefix identifies an uploaded file ID in the Upload File API?','file-api-','The file identifier, of the form `file-api-...`']
  ];
  for(const [id,category,doc,q,a,n] of focused) add(id,category,doc,q,[[a,n]],{family:doc.startsWith('api_samples/')?'samples-'+doc.split('/')[1]:id,tags:['page_specific']});
}
