import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const base = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const corpus = path.resolve(base,'../materials/deepseek');
const manifest = JSON.parse(fs.readFileSync(path.join(corpus,'manifest.json'),'utf8'));
const docs = new Map(manifest.documents.map(doc => [doc.id,{...doc,text:fs.readFileSync(path.join(corpus,doc.file),'utf8')} ]));
const cases = [];
const hash = text => createHash('sha256').update(text).digest('hex');

function evidence(docId, needle, point) {
  const doc = docs.get(docId);
  if (!doc) throw new Error(`Missing document ${docId}`);
  const at = doc.text.indexOf(needle);
  if (at < 0) throw new Error(`Missing evidence in ${docId}: ${needle}`);
  // Use a paragraph or a single table row, not the entire source document.
  const table = doc.text.slice(doc.text.lastIndexOf('\n',at)+1,at).startsWith('|');
  const delimiter = table ? '\n' : '\n\n';
  const previous = doc.text.lastIndexOf(delimiter,at);
  let start = previous < 0 ? 0 : previous + delimiter.length;
  if (docId.startsWith('api/')) {
    const fields = [...doc.text.slice(0,at).matchAll(/^\*\*(?!Possible|Default|Schema|Important|required|nullable)([^*\n]+)\*\*/gm)];
    const field = fields.at(-1);
    if (field && at-field.index < 400) start = Math.min(start,field.index);
  }
  const next = doc.text.indexOf(delimiter,at+needle.length);
  const end = next < 0 ? doc.text.length : next;
  const quote = doc.text.slice(start,end).trimEnd();
  const exactEnd = start + quote.length;
  return {file:`materials/deepseek/${doc.txt_file}`,md_file:`materials/deepseek/${doc.file}`,
    source_url:doc.source_url,document_id:docId,
    line:doc.text.slice(0,start).split('\n').length,end_line:doc.text.slice(0,exactEnd).split('\n').length,
    start_offset:[...doc.text.slice(0,start)].length,end_offset:[...doc.text.slice(0,exactEnd)].length,
    quote,supports_answer_points:[point]};
}

function add(id, category, doc, question, points, options={}) {
  const refs = [];
  points.forEach(([answer,needle,source],i) => {
    for (const n of Array.isArray(needle) ? needle : [needle]) {
      const ref = evidence(source || doc,n,i+1);
      const prior = refs.find(e=>e.file===ref.file&&e.start_offset===ref.start_offset&&e.end_offset===ref.end_offset);
      if (prior) {if(!prior.supports_answer_points.includes(i+1))prior.supports_answer_points.push(i+1);}
      else refs.push(ref);
    }
  });
  const family_id = options.family || id;
  cases.push({id:`ds-${id}`,corpus_id:manifest.corpus_id,family_id,category,
    split:parseInt(hash(family_id).slice(0,8),16)%5===0?'test':'dev',
    difficulty:options.difficulty || (category==='multi_document'?'hard':'medium'),
    question,answerable:true,expected_answer_points:points.map(p=>p[0]),evidence:refs,
    exact_answer_tokens:options.exact || [],tags:options.tags || [],
    scoring_notes:options.notes || 'Judge factual meaning and completeness; accept equivalent wording and supported alternative passages. Exact identifiers, numbers, units and API-family distinctions must remain correct.'});
}

function pair(id,doc,semantic,keyword,points,exact=[]) {
  add(`${id}-semantic`,'semantic',doc,semantic,points,{family:id});
  add(`${id}-keyword`,'keyword',doc,keyword,points,{family:id,exact,tags:['identifier_sensitive']});
}

// Hand-authored fact families: two distinct query styles share one split.
pair('base-url','index',
  'I have a client for an OpenAI-shaped service and another for an Anthropic-shaped service. Where should each connect to DeepSeek?',
  'What are the documented base_url values for the OpenAI and Anthropic API formats?',
  [['Use https://api.deepseek.com for the OpenAI format.','base\\_url (OpenAI)'],['Use https://api.deepseek.com/anthropic for the Anthropic format.','base\\_url (Anthropic)']],['https://api.deepseek.com','https://api.deepseek.com/anthropic']);
pair('retired-aliases','index',
  'If I keep using either of the older Flash model names, do I still get the retired model and its old billing?',
  'How are deepseek-v4-flash and deepseek-v4-flash-vision-exp requests served and billed in this snapshot?',
  [['Both legacy names remain accepted, but their retired models are replaced by DeepSeek-V4.1-Flash and billed at the Flash price.','The legacy names']],['DeepSeek-V4.1-Flash']);
pair('thinking-default','guides/thinking_mode',
  'Will the service reason before answering if I do not explicitly choose a reasoning setting, and how much effort does it use?',
  'What are the default thinking mode and default effort?',
  [['Thinking is enabled by default and the default effort is high.','Thinking mode is enabled by default']],['high']);
pair('effort-mapping','guides/thinking_mode',
  'My client offers the very small, middle, extra-high and ultra reasoning presets. How are those translated by DeepSeek?',
  'Map minimal, medium, xhigh, and ultra to actual DeepSeek reasoning efforts.',
  [['minimal maps to low.','| minimal |'],['medium and xhigh both map to high.',['| medium |','| xhigh |']],['ultra maps to max.','| ultra |']],['low','high','max']);
pair('thinking-sdk','guides/thinking_mode',
  'How should I pass the extra switch that turns reasoning on when using the Python chat client?',
  'Where must thinking be placed in an OpenAI SDK Chat Completion request?',
  [['Place the thinking parameter inside extra_body.','you need to pass the `thinking` parameter within `extra_body`']],['extra_body']);
pair('ignored-sampling','guides/thinking_mode',
  'My attempts to change randomness and repetition penalties seem ineffective during reasoning. Is this expected or an invalid request?',
  'What happens to temperature, presence_penalty and frequency_penalty in thinking mode?',
  [['These parameters have no effect in thinking mode, but setting them does not trigger an error for compatibility.','Thinking mode does not support']],['temperature','presence_penalty','frequency_penalty']);
pair('top-p','guides/thinking_mode',
  'What happens if I ask for a nucleus sampling value below the allowed reasoning threshold, or set it with reasoning off?',
  'Explain top_p=0.5 in thinking mode and top_p in non-thinking mode.',
  [['Thinking mode clamps values below 0.95 to 0.95; non-thinking mode fixes top_p at 1.0 and ignores the supplied value.','`top_p` only takes effect']],['0.95','1.0']);
pair('cot-without-tools','guides/thinking_mode',
  'For a reasoning conversation without any tool definitions, must I resend earlier reasoning, and does it consume context if I do?',
  'What happens to reasoning_content when a subsequent request does not carry tools?',
  [['It need not be passed back; if supplied it is ignored and is not concatenated into the context.','If the request **does not carry the `tools` parameter**']],['reasoning_content']);
pair('cot-with-tools','guides/thinking_mode',
  'I use reasoning with tools. Must I preserve earlier reasoning even on turns that did not invoke a function, and what happens if I omit it?',
  'When tools is present, what reasoning_content must be passed back and what error can omission cause?',
  [['Fully pass back reasoning_content in all subsequent requests, including turns with no tool call; incorrect omission returns a 400 error.','Please note that for requests carrying']],['reasoning_content','400']);
pair('json-setup','guides/json_mode',
  'I need a machine-readable object rather than free-form prose. What output setting and prompt instructions are required?',
  'How do response_format, json in the prompt, and the example format enable JSON Output?',
  [['Set response_format to {"type":"json_object"}.','Set the `response_format`'],['Include the word json in a system or user prompt and provide an example of the desired JSON format.','Include the word "json"']],['response_format','json_object']);
pair('json-truncation','guides/json_mode',
  'How can I avoid a structured response ending halfway through, and what does the guide suggest for an occasional blank result?',
  'What do the JSON Output notes say about max_tokens and empty content?',
  [['Set max_tokens reasonably to avoid truncating the JSON.','Set the `max_tokens`'],['Empty content can occur; try modifying the prompt.','may occasionally return empty content']],['max_tokens']);
pair('cache-default','guides/kv_cache',
  'Do I have to add special cache-management code before repeated prompts benefit from stored context?',
  'Is DeepSeek Context Caching on Disk enabled by default?',
  [['Disk context caching is enabled by default for all users and requires no code modification.','enabled by default for all users']]);
pair('cache-full-unit','guides/kv_cache',
  'Is sharing just any initial text enough for a cache hit, or does a complete previously stored unit have to match?',
  'What must fully match a persisted cache prefix unit for a cache hit?',
  [['The matching prefix must already have been persisted, and a subsequent request must fully match a complete cache prefix unit.','A cache hit requires']],['cache prefix unit']);
pair('cache-abac','guides/kv_cache',
  'Three requests begin with the same section but have different endings. Why might only the third reuse that common section?',
  'Explain cache hits for A+B, then A+C, then A+D in the documented Example 2.',
  [['A+C does not fully match the A+B unit; detecting shared A causes A to be persisted, so A+D can then hit A.','Example 2: A user']]);
pair('cache-counters','guides/kv_cache',
  'Which response counters tell me how much input reused stored computation and how much did not?',
  'Define prompt_cache_hit_tokens and prompt_cache_miss_tokens in usage.',
  [['prompt_cache_hit_tokens counts input tokens that hit the cache.','`prompt_cache_hit_tokens`:'],['prompt_cache_miss_tokens counts input tokens that missed the cache.','`prompt_cache_miss_tokens`:']],['prompt_cache_hit_tokens','prompt_cache_miss_tokens']);
pair('cache-randomness','guides/kv_cache',
  'Does reusing cached input force the service to return an identical answer on every request?',
  'Does the hard disk cache cache generated output or only the input prefix?',
  [['The cache matches only the input prefix; output is still generated by inference and can be random.','The hard disk cache only matches']]);
pair('cache-lifetime','guides/kv_cache',
  'Can I rely on stored context always being present, and when may unused cache disappear?',
  'What are the cache hit guarantee, construction time and usual cache eviction interval?',
  [['Cache is best effort, with no guaranteed 100% hit rate.','"best-effort"'],['Construction takes seconds; unused cache is normally cleared within hours to days.','Cache construction takes seconds']]);
pair('stateless-chat','guides/multi_round_chat',
  'The model forgets the earlier exchange when I send only my next question. What conversation data should my client resend?',
  'Is /chat/completions stateful, and what history must be sent on each request?',
  [['The API is stateless; the client must concatenate and send all prior conversation history with each request.','API is a "stateless" API']]);
pair('prefix-setup','guides/chat_prefix_completion',
  'I want the assistant to continue a beginning I supply. Which final message and endpoint configuration enable this?',
  'For Chat Prefix Completion, what role, prefix flag, and base_url are required?',
  [['The last message must have role assistant and prefix set to True.','users must ensure'],['Use https://api.deepseek.com/beta.','The user needs to set']],['assistant','prefix','https://api.deepseek.com/beta']);
pair('fim-purpose','guides/fim_completion',
  'I know the beginning and end of a code fragment and want the missing middle filled in. Which feature does that, and is the ending mandatory?',
  'What does FIM completion accept as prefix and suffix, and is suffix optional?',
  [['FIM completes content between a prefix and optional suffix, often for text or code completion.','users can provide a prefix and a suffix']],['FIM']);
pair('fim-limit','guides/fim_completion',
  'What generation cap and service address should I use for filling a gap inside a code fragment?',
  'What are the FIM completion max tokens and beta base_url?',
  [['The maximum is 4K tokens.','The max tokens of FIM'],['Use https://api.deepseek.com/beta.','The user needs to set']],['4K','https://api.deepseek.com/beta']);
pair('tools-execution','guides/tool_calls',
  'When the assistant asks for weather through a function, does DeepSeek actually run my weather lookup?',
  'Who implements and executes get_weather in the Tool Calls example?',
  [['The user/client must provide and execute the function; the model itself does not execute specific functions.','the functionality of the `get_weather` function']],['get_weather']);
pair('tool-insertion','guides/tool_calls',
  'My agent wants to insert a tool exchange it created itself into the middle of history. Which interface families permit that?',
  'Compare mid-conversation inserted tool calls in Anthropic, Responses and Chat Completion APIs.',
  [['Anthropic and Responses support inserted tool calls and system messages.','The [Anthropic API]'],['Chat Completion supports inserted system messages but not inserted tool calls.','The Chat Completion API does not support']]);
pair('strict-enable','guides/tool_calls',
  'How do I force generated function arguments to follow my schema, and will an unsupported schema be accepted?',
  'What base_url and strict property are needed for strict Tool Calls, and how is the schema checked?',
  [['Use the beta base URL and strict:true on every function.',['Use `base_url=','all `function` need']],['The server validates the schema and returns an error for invalid or unsupported schema definitions.','The server will validate']],['https://api.deepseek.com/beta','strict']);
pair('strict-object','guides/tool_calls',
  'In strict function definitions, may I leave some object properties optional or allow unlisted fields?',
  'What required and additionalProperties rules apply to every strict-mode object?',
  [['All properties must be required and additionalProperties must be false.','All properties of every `object`']],['required','additionalProperties','false']);
pair('strict-string','guides/tool_calls',
  'Can strict function schemas constrain strings by a regular expression and length bounds equally?',
  'Are pattern, minLength and maxLength supported for strict-mode strings?',
  [['pattern is supported.','`pattern`: Uses regular expressions'],['minLength and maxLength are unsupported.',['`minLength`','`maxLength`']]],['pattern','minLength','maxLength']);
pair('strict-array','guides/tool_calls',
  'Can a strict tool schema enforce the smallest and largest permitted number of list elements?',
  'Are minItems and maxItems supported in strict-mode arrays?',
  [['minItems and maxItems are unsupported.',['minItems','maxItems']]],['minItems','maxItems']);
pair('strict-ref','guides/tool_calls',
  'How does this guide spell the reusable schema-definition key and the key that refers to it?',
  'In this documentation, what do $def and $ref do? Preserve the documented spelling.',
  [['$def defines reusable modules; $ref references them and can also define recursive structures.','You can use `$def`']],['$def','$ref']);

pair('file-upload','guides/files_api',
  'I want to upload an image once and reuse it later. What request encoding, endpoint and purpose value should I use?',
  'What are the upload method/path, Content-Type and purpose for the Files API?',
  [['Use multipart/form-data with POST /files.','Upload a file with a'],['Set purpose to user_data.','| `purpose` | Yes |']],['POST /files','multipart/form-data','user_data']);
pair('file-upload-limit','guides/files_api',
  'How large can an uploaded image be, and how long can its upload take?',
  'What are the maximum Files API upload size and upload duration?',
  [['The file limit is 64 MiB and upload must complete within 10 minutes.','A single file may be at most']],['64','MiB','10']);
pair('file-expiry','guides/files_api',
  'How do I make an image expire automatically, and how do I keep it permanently instead?',
  'What anchor and seconds range does expires_after require, and what does omitting both fields do?',
  [['Use expires_after[anchor]=created_at together with expires_after[seconds].','| `expires_after[anchor]`'],['The lifetime range is 3600 to 2592000 seconds; omitting both fields keeps the file permanently.','| `expires_after[seconds]`']],['created_at','3600','2592000']);
pair('file-expiry-result','api/create-file',
  'Will every upload response include an expiration timestamp even if I chose permanent storage?',
  'When is expires_at present in the Upload File response?',
  [['expires_at is present only when expiration was set at upload time.','Only present when an expiration']],['expires_at']);
pair('file-pagination','api/list-files',
  'How can I request the next batch of uploaded files and choose their creation-time ordering?',
  'What do after and order mean for GET /files, and what is the default order?',
  [['after is a file_id cursor returning files after that file.','A `file_id` cursor'],['order sorts by creation time, with asc as default and desc as the alternative.','Sort order by creation time.']],['after','asc','desc']);
pair('file-list-size','api/list-files',
  'How many stored files can I request in one page, and what page size is used if I omit it?',
  'What range and default apply to limit in the OpenAI-compatible GET /files endpoint?',
  [['The range is 1–1000 and the default is 1000.',['The number of files to return.','**Default value:** `1000`']]],['1000']);
pair('file-pagination-marker','api/list-files',
  'How does a file listing tell me there are further results beyond the page I received?',
  'What does has_more mean in List Files?',
  [['has_more indicates whether more files exist beyond the current page.','Whether there are more files beyond']],['has_more']);
pair('file-inline-exclusive','guides/files_api',
  'Can one file content block include both an uploaded-file reference and inline image bytes, and when is a filename allowed?',
  'Explain file_id versus file_data and the filename restriction in a file block.',
  [['file_id and file_data are mutually exclusive; filename is allowed with file_data but not with file_id.','A `file` block can also carry']],['file_id','file_data','filename']);
pair('file-ownership','guides/files_api',
  'Can I use an image uploaded through one API family with the other family, and what extra header is required for the latter?',
  'Who owns uploaded files, and what header is required for file_id references from Anthropic /messages?',
  [['Files belong to the API key and can be referenced from either API family; Anthropic /messages file references require anthropic-beta: files-api-2025-04-14.','Files belong to your API key']],['anthropic-beta','files-api-2025-04-14']);
pair('anthropic-file-path','guides/files_api',
  'A raw HTTP client and an SDK use the same Anthropic-compatible base address. Why does only the raw client need to add the version path?',
  'What is the Anthropic Files API base_url, and who appends /v1?',
  [['The base URL is https://api.deepseek.com/anthropic.','same file operations are also available'],['The SDK appends /v1 automatically; a plain HTTP client must use the full /anthropic/v1/ path.','The endpoints are served under']],['/anthropic/v1/']);
pair('file-list-family','guides/files_api',
  'When switching the file listing client from the OpenAI interface to Anthropic, what happens to the cursor names and default page size?',
  'Compare after with after_id/before_id and default limit across the two Files API families.',
  [['OpenAI uses after; Anthropic uses mutually exclusive after_id/before_id.','| List pagination |'],['OpenAI defaults to 1000 and Anthropic to 20; both allow 1–1000.','| List `limit` |']],['after','after_id','before_id','1000','20']);
pair('file-metadata-family','guides/files_api',
  'Which size-field name and creation-time representation change when I switch file metadata between the two interface families?',
  'Compare bytes versus size_bytes and the created_at formats in the two Files APIs.',
  [['OpenAI uses bytes; Anthropic uses size_bytes.','| File object size field |'],['OpenAI created_at is Unix seconds; Anthropic created_at is an RFC 3339 string.','| `created_at` |']],['bytes','size_bytes','RFC 3339']);
pair('file-storage-limits','guides/files_api',
  'What limits apply to the length of image filenames, total stored space, and number of stored images?',
  'Give the Files API max filename length, max storage per user and max stored files per user.',
  [['Filename length is at most 512 characters.','| Max filename length |'],['Storage is at most 25 GiB per user.','| Max storage per user |'],['At most 10000 files may be stored per user.','| Max number of stored files per user |']],['512','25','GiB','10000']);
pair('file-delete','api/delete-file',
  'How do I remove one uploaded file, and which response flag tells me whether it was deleted?',
  'What endpoint deletes file_id and what does the deleted boolean mean?',
  [['Use DELETE /files/:file_id.','DELETE /files/:file_id'],['deleted indicates whether the file was successfully deleted.','Whether the file was successfully deleted.']],['DELETE','deleted']);
pair('file-retrieve','api/retrieve-file',
  'How do I inspect information about a single stored image rather than list all images?',
  'What does GET /files/:file_id return?',
  [['GET /files/:file_id returns information about the specified file.',['GET /files/:file_id','Returns information about a specific file.']]],['GET /files/']);

pair('vision-detection','guides/vision',
  'If an image is mislabeled by its file extension or declared media type, what determines its actual format and which formats are accepted?',
  'Does Vision detect JPEG, PNG, GIF and WebP by content, filename, or MIME type?',
  [['JPEG, PNG, GIF and WebP are supported; detection uses actual content rather than the filename or declared MIME type.','Supported image formats:']],['JPEG','PNG','GIF','WebP']);
pair('vision-url','guides/vision',
  'I want the service to fetch an image from the web. What limits apply to the link length, download size, and download duration?',
  'What are the external http(s) image URL length, size and timeout limits?',
  [['A public image URL can be at most 8192 characters; the image at most 32 MiB; download must finish within 60 seconds.','Pass a publicly accessible']],['8192','32','MiB','60']);
pair('vision-reuse','guides/vision',
  'Repeatedly embedding the same large image bloats my requests. What alternative avoids resending its bytes and permits a larger image?',
  'Why use Files API file_id instead of inline base64, and what per-image size can file_id support?',
  [['Upload once and reuse file_id; this avoids repeated inline bytes and permits images up to 64 MiB rather than the 32 MiB inline limit.','Upload an image once with']],['file_id','64','MiB']);

pair('responses-stream-end','guides/responses_api',
  'How can my Responses stream reader distinguish a finished, cut-short, or failed reply? Should it wait for the old completion sentinel?',
  'Which terminal events replace data: [DONE] in the Responses API?',
  [['The terminal events are response.completed, response.incomplete and response.failed; there is no data: [DONE] message.','Set `stream: true`']],['response.completed','response.incomplete','response.failed']);
pair('responses-sequence','guides/responses_api',
  'How does the Responses stream label events and give their ordering?',
  'What do event and sequence_number identify in a Responses API SSE stream?',
  [['event identifies event type and sequence_number increases monotonically.','Set `stream: true`']],['sequence_number']);
pair('responses-image-exclusive','guides/responses_api',
  'Can an image input omit both its URL and stored-file reference, or supply both at once?',
  'What happens when input_image has neither or both image_url and file_id?',
  [['image_url and file_id are mutually exclusive; neither or both yields HTTP 400.','`image_url` and `file_id` are mutually exclusive']],['400','image_url','file_id']);
pair('responses-image-roles','guides/responses_api',
  'May I place image input in a system or assistant message, or only in user-like messages and tool outputs?',
  'Which message roles and tool-output item types accept input_image in Responses?',
  [['Images are allowed in user/developer messages and function_call_output/custom_tool_call_output; system or assistant images return 400.','Images are allowed only in']],['user','developer','function_call_output','custom_tool_call_output','400']);
pair('responses-state','guides/responses_api',
  'Can the compatible Responses service resume a stored conversation just from a previous response identifier?',
  'Are previous_response_id, conversation and store supported by DeepSeek Responses?',
  [['previous_response_id and conversation are unsupported because the API is stateless.',['| `previous_response_id` |','| `conversation` |']],['store is unsupported and the response carries store:false.','| `store` |']],['previous_response_id','store']);
pair('responses-ignored','guides/responses_api',
  'If my existing Responses client sends unsupported options, does that automatically make the request fail?',
  'What happens to unsupported top-level Responses API parameters?',
  [['Unsupported parameters are silently ignored and do not cause errors.','Unsupported parameters are **silently ignored**']]);
pair('responses-truncation','guides/responses_api',
  'Can the service automatically trim an oversized conversation if I request truncation?',
  'Is Responses truncation supported, and what happens when input exceeds the context window?',
  [['truncation is unsupported; context-window overflow returns HTTP 400.','| `truncation` |']],['400']);
pair('responses-patch','guides/responses_api',
  'Can I define an arbitrary custom tool name in this Responses-compatible service?',
  'Which custom tool name is supported, and what happens to other custom names?',
  [['Only the apply_patch custom tool is supported; other custom names return 400.','Only `{"type": "custom", "name": "apply_patch"}`']],['apply_patch','400']);
pair('responses-parallel','guides/responses_api',
  'Will disabling parallel function calls in my Responses request force calls to be serial?',
  'What happens to parallel_tool_calls in DeepSeek Responses?',
  [['It is ignored; parallel tool calling is always enabled.','| `parallel_tool_calls` |']],['parallel_tool_calls']);
pair('responses-verbosity','guides/responses_api',
  'Does the compatibility layer honor verbosity and reasoning-summary requests?',
  'How are text.verbosity and reasoning.summary handled by DeepSeek Responses?',
  [['text.verbosity is accepted but has no effect.','| `text` |'],['reasoning.summary is accepted but no summary is generated.','| `reasoning` |']],['verbosity','summary']);

pair('anthropic-model-map','guides/anthropic_api',
  'My client insists on Claude model-name prefixes. Which DeepSeek backends do the larger and smaller Claude families select?',
  'How are claude-opus, claude-haiku and claude-sonnet model prefixes mapped?',
  [['claude-opus maps to deepseek-v4-pro.','Models starting with claude-opus'],['claude-haiku and claude-sonnet map to deepseek-flash.','Models starting with claude-haiku']],['deepseek-v4-pro','deepseek-flash']);
pair('anthropic-effort','guides/anthropic_api',
  'Will the Anthropic compatibility layer use my explicit thinking-token budget and all output configuration options?',
  'How are thinking.budget_tokens and output_config handled in the Anthropic API?',
  [['thinking is supported but budget_tokens is ignored.','| thinking |'],['Only effort is supported within output_config.','| output\\_config |']],['budget_tokens','effort']);
pair('anthropic-metadata','guides/anthropic_api',
  'Which user-specific metadata field survives the Anthropic compatibility layer?',
  'Which metadata subfield is supported by the Anthropic API?',
  [['metadata.user_id is supported; other metadata fields are ignored.','| metadata |']],['user_id']);

pair('concurrency-account','quick_start/rate_limit',
  'Can I multiply my simultaneous-request allowance by creating several API keys under the same account?',
  'Are concurrency limits per account or per API Key, and when does a request count as concurrent?',
  [['Limits apply at account level regardless of API key.','Concurrency limits are calculated'],['A request counts from being sent until the model response completes.','A request counts as one concurrent connection']]);
pair('concurrency-values','quick_start/rate_limit',
  'How many requests can each current model handle at once for an account, and what happens if I exceed that?',
  'Give deepseek-flash and deepseek-v4-pro concurrency limits and the over-limit HTTP code.',
  [['Flash allows 2500 and V4 Pro allows 500 concurrent requests.','| Concurrency Limit |'],['Exceeding the limit returns HTTP 429.','when the concurrency limit is exceeded']],['2500','500','429']);
pair('concurrency-expansion','quick_start/rate_limit',
  'What should I do if my application needs more simultaneous requests, and is there an extra expansion fee?',
  'How do I request higher concurrency and what is the capacity-expansion cost?',
  [['Submit a capacity expansion request; concurrency is matched to actual business needs and expansion has no additional cost.','If you need higher concurrency']]);
pair('user-isolation','quick_start/rate_limit',
  'How can I distinguish my application users for safety handling, cached context privacy, and scheduling under a shared account?',
  'List the three isolation functions of user_id.',
  [['user_id provides content safety isolation.','**Content Safety Isolation:**'],['It provides KVCache isolation for privacy management.','**KVCache Isolation:**'],['It provides scheduling isolation.','**Scheduling Isolation:**']],['user_id']);
pair('user-id-format','quick_start/rate_limit',
  'What characters and maximum length may I use for an application-user identifier, and should it contain private user details?',
  'What regex, maximum length and privacy restriction apply to user_id?',
  [['user_id must match [a-zA-Z0-9\\-_]+, be at most 512 characters, and contain no user privacy information.','The `user_id` parameter must be a string']],['512']);
pair('keepalive','quick_start/rate_limit',
  'The server keeps the connection open but sends blank lines or comment-like events before answering. What are these, and how long can inference remain unstarted?',
  'What are non-streaming and SSE keep-alive payloads, and what is the no-inference timeout?',
  [['Non-streaming uses empty lines; streaming uses SSE comments : keep-alive.',['Non-streaming requests:','Streaming requests:']],['The server closes the connection if inference has not started after 10 minutes.','If the request has not started inference']],[': keep-alive','10']);

pair('prices-units','quick_start/pricing',
  'Are the price-table amounts per request or per quantity of generated and supplied text?',
  'What unit do the prices use and which token directions are billed?',
  [['Prices are per 1M tokens and billing uses total input and output tokens.','The prices listed below are in units']],['1M']);
pair('model-versions','quick_start/pricing',
  'According specifically to the captured Models & Pricing table, which model versions are listed for Flash and Pro?',
  'Map deepseek-flash and deepseek-v4-pro to their MODEL VERSION values.',
  [['Flash is DeepSeek-V4.1-Flash and Pro is DeepSeek-V4-Pro-0813.','| MODEL VERSION |']],['DeepSeek-V4.1-Flash','DeepSeek-V4-Pro-0813']);
pair('context-output','quick_start/pricing',
  'How much context and how much maximum generated output do the two current models support?',
  'What CONTEXT LENGTH and MAX OUTPUT are listed for Flash and V4 Pro?',
  [['Both list a 1M context length.','| CONTEXT LENGTH |'],['Both list a maximum output of 384K.','| MAX OUTPUT |']],['1M','384K']);
pair('peak-hours','quick_start/pricing',
  'When do higher token rates apply during the week, and do weekends or Chinese public holidays use those rates?',
  'Give the UTC peak windows, applicable weekdays, holiday rule and off-peak discount.',
  [['Peak hours are 01:00–04:00 and 06:00–10:00 UTC Monday–Friday excluding Chinese public holidays; all other hours, weekends and holidays are off-peak; off-peak rates are half peak.','Off-peak rates are half']],['01:00','04:00','06:00','10:00','UTC']);
pair('balance-priority','quick_start/pricing',
  'If my account has both promotional credit and money I topped up, which is spent first?',
  'What is the deduction priority for granted balance versus topped-up balance?',
  [['The granted balance is used first when both granted and topped-up balances are available.','The expense = number of tokens']]);
pair('balance-api','api/get-user-balance',
  'Which request checks my account balance, and which flag indicates it is sufficient to make calls?',
  'What endpoint returns balance information and what does is_available mean?',
  [['Use GET /user/balance.','GET /user/balance'],['is_available indicates whether the balance is sufficient for API calls.','Whether the user\'s balance is sufficient']],['GET /user/balance','is_available']);
pair('balance-total','api/get-user-balance',
  'What does the available balance include, and what currency identifiers can the response use?',
  'Define total_balance and list currency values in Get User Balance.',
  [['total_balance includes granted and topped-up balances.','The total available balance'],['Currency values are CNY and USD.','[`CNY`, `USD`']],['total_balance','CNY','USD']);
pair('models-list','api/list-models',
  'How do I discover available model identifiers and find out which organization owns each model?',
  'What endpoint lists models, and what do id and owned_by represent?',
  [['GET /models lists models.','GET /models'],['id is the model identifier usable in endpoints.','The model identifier,'],['owned_by identifies the owning organization.','The organization that owns']],['GET /models','owned_by']);

// More families, cross-document cases and operational suites are appended below.
await import('./case-extensions.mjs').then(module => module.extend({add,pair,docs,cases,evidence}));

// Conversation fixtures are development material. Keep their reused fact
// families out of the reserved split even when the initial hash chose test.
const conversationDevelopmentFamilies=new Set(['balance-priority','vision-dimension','faq-balance-validity','fim-purpose','integration-oh_my_pi']);
for(const test of cases)if(conversationDevelopmentFamilies.has(test.family_id))test.split='dev';

fs.writeFileSync(path.join(base,'cases.jsonl'),cases.map(c=>JSON.stringify(c)).join('\n')+'\n');
for (const split of ['dev','test']) fs.writeFileSync(path.join(base,`${split}.jsonl`),cases.filter(c=>c.split===split).map(c=>JSON.stringify(c)).join('\n')+'\n');
const counts = field => Object.fromEntries([...new Set(cases.map(c=>c[field]))].sort().map(key=>[key,cases.filter(c=>c[field]===key).length]));
const coverage = manifest.documents.map(doc=>({document_id:doc.id,case_ids:cases.filter(c=>[...(c.evidence||[]),...(c.context_evidence||[])].some(e=>e.document_id===doc.id)).map(c=>c.id)}));
fs.writeFileSync(path.join(base,'coverage.json'),JSON.stringify({corpus_id:manifest.corpus_id,total_cases:cases.length,by_category:counts('category'),by_split:counts('split'),by_difficulty:counts('difficulty'),answerable:cases.filter(c=>c.answerable).length,unanswerable:cases.filter(c=>!c.answerable).length,documents:coverage},null,2)+'\n');
fs.writeFileSync(path.join(base,'cases.md'),'# DeepSeek documentation evaluation cases\n\nGenerated from hand-authored case definitions. Evidence offsets and lines refer to the frozen corpus. Do not ingest this file.\n\n'+cases.map(c=>`## ${c.id}\n\n${c.question}\n\n- Category: ${c.category}; split: ${c.split}; family: ${c.family_id}; answerable: ${c.answerable}\n\nExpected answer points:\n\n${c.expected_answer_points.map(p=>'- '+p).join('\n')}\n\n${c.answerable?'Evidence':'Related background (not positive evidence)'}:\n\n${[...(c.evidence||[]),...(c.context_evidence||[])].map(e=>`- [${e.document_id}, lines ${e.line}–${e.end_line}](../${e.md_file}) — ${e.source_url}`).join('\n')}\n\nScoring: ${c.scoring_notes}\n`).join('\n'));
console.log(JSON.stringify({cases:cases.length,categories:counts('category'),splits:counts('split')},null,2));
