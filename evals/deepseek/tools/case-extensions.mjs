export function extend({add,pair,docs,cases,evidence}) {
  pair('text-token-estimate','quick_start/token_usage',
    'Can I calculate exact billed usage just by counting English letters, or is that only an estimate?',
    'What approximate token ratios are given for English and Chinese characters, and what is the source of truth?',
    [['An English character is approximately 0.3 token; a Chinese character approximately 0.6 token.',['1 English character','1 Chinese character']],['Ratios vary with tokenization; the model-returned usage is authoritative.','However, due to the different tokenization']],['0.3','0.6']);
  pair('tokenizer-download','quick_start/token_usage',
    'Where can I find the offline token-counting demonstration package linked by the documentation?',
    'What is the URL behind deepseek_tokenizer.zip on the token usage page?',
    [['The linked package is https://cdn.deepseek.com/api-docs/deepseek_v4_tokenizer.zip.','deepseek_v4_tokenizer.zip']],['deepseek_v4_tokenizer.zip']);
  pair('vision-detail','guides/vision',
    'I need cheaper coarse visual understanding rather than fine image detail. Which setting resizes the image, and how?',
    'What do detail=low, high, original, and auto do in the Vision guide?',
    [['low downsizes to 512×512.','| `low` |'],['high and original preserve the image; auto is currently equivalent to original.',['| `high` |','| `original` |','| `auto` |']]],['512','original']);
  pair('vision-token-cap','guides/vision',
    'Would a much larger image necessarily cost more image tokens after resizing, and are images in a batch counted together?',
    'What is the current per-image token upper bound, and how are multiple images counted?',
    [['The upper bound is 1024 tokens per image; 2000×2000 and 5000×5000 examples use the same count after resizing, and each image is counted independently.','As a result, there is an upper bound']],['1024']);
  pair('vision-batch-limits','guides/vision',
    'How do the image-count and aggregate-size limits change when I include stored-file references?',
    'Give max images per request and total image size with and without file_id images.',
    [['At most 600 images per request.','| Max images per request |'],['The aggregate limit is 64 MiB without file_id images and up to 200 MiB including them.','| Max total image size per request |']],['600','64','200','MiB']);
  pair('vision-dimension','guides/vision',
    'What image-side length is allowed for a small batch versus a batch of at least fifteen images?',
    'What is the max image dimension for 14 versus 15 images in one request?',
    [['The general limit is 8192 px per side, reduced to 4096 px per side with 15 or more images.','| Max image dimension |']],['8192','4096']);

  const errors = [
    ['400','Invalid Format','Invalid request body format.','Modify the request body according to the error hints.','My request body has the wrong shape. Which error and corrective action should I expect?'],
    ['401','Authentication Fails','Authentication fails due to the wrong API key.','Check the API key, or create one if needed.','My credential is wrong. Which error identifies that and what should I check?'],
    ['402','Insufficient Balance','You have run out of balance.','Check the balance and add funds through Top up.','My account has no funds left. Which error applies and what is the remedy?'],
    ['422','Invalid Parameters','Your request contains invalid parameters.','Modify request parameters according to the error hints.','The request parameters are invalid. Which error applies and how should I fix it?'],
    ['429','Rate Limit Reached','You are sending requests too quickly.','Pace requests reasonably; the page also suggests temporarily using another provider.','I am sending requests too quickly. Which error applies and what does the guide suggest?'],
    ['500','Server Error','Our server encounters an issue.','Retry after a brief wait and contact support if it persists.','The service has an internal fault that persists. Which error and follow-up does the guide describe?'],
    ['503','Server Overloaded','The server is overloaded due to high traffic.','Retry after a brief wait.','The service is overloaded by traffic. Which error applies and what should I do?'],
  ];
  for(const [code,label,cause,solution,question] of errors) pair(`error-${code}`,'quick_start/error_codes',question,
    `In the Error Codes table, what causes HTTP ${code} (${label}) and what is its solution?`,
    [[`HTTP ${code} (${label}): ${cause} ${solution}`,cause]],[code]);

  // Price questions explicitly target table cells, since a later announcement
  // disagrees with the current table about Pro routing and billing.
  const priceRows = [
    ['cache-hit-offpeak','1M INPUT TOKENS','CACHE HIT','OFF-PEAK','$0.003','$0.022'],
    ['cache-hit-peak','1M INPUT TOKENS','CACHE HIT','PEAK','$0.006','$0.044'],
    ['cache-miss-offpeak','1M INPUT TOKENS','CACHE MISS','OFF-PEAK','$0.15','$0.66'],
    ['cache-miss-peak','1M INPUT TOKENS','CACHE MISS','PEAK','$0.3','$1.32'],
    ['output-offpeak','1M OUTPUT TOKENS','','OFF-PEAK','$0.6','$1.98'],
    ['output-peak','1M OUTPUT TOKENS','','PEAK','$1.2','$3.96']
  ];
  for(const [id,kind,cache,tier,flash,pro] of priceRows) {
    const row = docs.get('quick_start/pricing').text.split('\n').find(line=>line.startsWith('| PRICING')&&line.includes(kind)&&line.includes(cache)&&line.includes(`| ${tier} |`));
    add(`price-${id}`,'numeric','quick_start/pricing',`According specifically to the captured Models & Pricing table, what are the ${tier.toLowerCase()} ${cache ? cache.toLowerCase()+' ' : ''}${kind.toLowerCase()} prices for deepseek-flash and deepseek-v4-pro?`,
      [[`Per 1M tokens, the table lists Flash at ${flash} and Pro at ${pro}.`,row]],{exact:[flash,pro],family:`price-${id}`});
  }
  add('price-arithmetic-flash','numeric','quick_start/pricing','Using the captured Flash table rates, calculate the cost of 1M cache-miss input tokens plus 1M output tokens, all off-peak. Ignore any other usage.',
    [['Input costs $0.15 and output costs $0.60, for $0.75 total.',[
      docs.get('quick_start/pricing').text.split('\n').find(x=>x.startsWith('| PRICING')&&x.includes('CACHE MISS')&&x.includes('OFF-PEAK')),
      docs.get('quick_start/pricing').text.split('\n').find(x=>x.startsWith('| PRICING')&&x.includes('OUTPUT TOKENS')&&x.includes('OFF-PEAK'))]]],{difficulty:'hard',notes:'Derive 1×0.15 + 1×0.60 = 0.75 USD from the table. Arithmetic is an inference, not a quoted result. Do not apply Pro rates.'});

  const history = [
    ['news0725','According to the historical API Upgrade announcement, how many functions could Function Calling support in one call, and were parallel calls supported?','Up to 128 functions per call and parallel function calls were supported.','Function Calling supports multiple functions'],
    ['news0802','What input-position requirement did the historical Context Caching on Disk announcement specify, and did matching text in the middle qualify?','Identical prefixes starting at token zero qualified; partial matches in the middle did not.','only requests with identical prefixes'],
    ['news0905','Which two model versions were combined to create DeepSeek-V2.5 in its release announcement?','DeepSeek-V2-0628 and DeepSeek-Coder-V2-0724.','a powerful combination of DeepSeek-V2-0628'],
    ['news1120','In the R1-Lite-Preview announcement, were API access and open-source models already available or described as coming soon?','Open-source models and the API were described as coming soon.','Open-source models & API coming soon'],
    ['news1210','What happened to the V2.5 series with the release of DeepSeek-V2.5-1210?','The V2.5 series came to an end.','the V2.5 series comes to an end'],
    ['news1226','In the original V3 introduction, how many total MoE and activated parameters were reported?','671B total MoE parameters and 37B activated parameters.',['671B MoE parameters','37B activated parameters']],
    ['news250115','Which model powered the initially introduced DeepSeek App, and did that announcement say it was free?','It was powered by DeepSeek-V3 and described as free to use.',['Powered by world-class DeepSeek-V3','FREE to use']],
    ['news250120','According to the original DeepSeek-R1 release announcement, which API model name selected R1?','The model name was deepseek-reasoner.','model=deepseek-reasoner'],
    ['news250325','Which license did the DeepSeek-V3-0324 announcement say the models were released under?','The MIT License.','Models are now released under the MIT License'],
    ['news250528','Which structured-output and tool features were announced for DeepSeek-R1-0528?','JSON output and function calling.','Supports JSON output & function calling'],
    ['news250821','In the V3.1 announcement, which model aliases selected non-thinking and thinking modes?','deepseek-chat selected non-thinking; deepseek-reasoner selected thinking.',['deepseek-chat → non-thinking mode','deepseek-reasoner → thinking mode']],
    ['news250922','Which two user-visible problem areas did the V3.1-Terminus announcement emphasize improving?','Language consistency and Code Agent/Search Agent performance.',['Language consistency:','Agent upgrades:']],
    ['news250929','What attention mechanism debuted in V3.2-Exp, and on which model was it built?','DeepSeek Sparse Attention (DSA), built on V3.1-Terminus.','Built on V3.1-Terminus'],
    ['news260424','In the V4 Preview announcement, what total and active parameter counts were given for Pro and Flash?','Pro: 1.6T total and 49B active; Flash: 284B total and 13B active.',['1.6T total / 49B active','284B total / 13B active']],
    ['news260813','When did the V4-Pro GA announcement say its new peak/off-peak pricing would take effect?','16:00 UTC on August 16, 2026.','New pricing takes effect at 16:00 UTC'],
    ['news260821','What per-image token cap was advertised in the historical V4-Flash-Vision-Exp announcement?','Up to 384 tokens per image, at V4-Flash pricing.','Images are tokenized for billing: up to 384'],
    ['news260910','What total and input/output active parameter counts were reported for V4.1-Flash?','552B total MoE parameters; 8B active for input and 16B active for output.',['552B-parameter MoE','just 8B active parameters for input']],
  ];
  for(const [id,q,a,n] of history) add(`history-${id}`,'historical',`news/${id}`,q,[[a,n]],{tags:['historical_scope'],notes:'Answer only the named historical announcement. Treat performance claims as claims made by the publisher, not independently verified benchmarks or current service guarantees.'});

  pair('terminus-expiry','guides/comparison_testing',
    'What temporary service address was offered for the older comparison model, and when was its availability stated to end?',
    'What are the V3.1-Terminus comparison base_url and expiry time in the historical guide?',
    [['The temporary base URL was https://api.deepseek.com/v3.1_terminus_expires_on_20251015; availability ended October 15, 2025 at 15:59 UTC.','Users can simply modify']],['v3.1_terminus_expires_on_20251015','15:59']);

  const faq = [
    ['top-up','How can I add funds online and verify the payment result?','Online top-up supports PayPal, bank card, Alipay or WeChat Pay through Top Up; results appear on Billing.','You can top up online'],
    ['balance-error','Why might my top-up appear missing after I log in under a different method?','It usually means a different account was topped up; try the original Google/email login and check top-up records.',['it usually means','If you have a Google or email login']],
    ['balance-validity','Will money I topped up disappear just because a period of time has passed?','Top-up balances do not expire.','Top-up balances do not expire.'],
    ['refund-policy','How do refund procedures differ for online payments and corporate bank transfers?','Unused balances can be refunded; online payments use Billing then Refunds, while corporate transfers require a Refund Request ticket.',['Unused balances','**Online Payment:**','**Corporate Bank Transfer:**']],
    ['invoice-request','Where does the API FAQ tell me to request an invoice?','Log in to the Platform, go to Billing and click Invoices.','Log in to the Platform, go to'],
    ['invoice-details','How can I add usage details to an invoice according to the API FAQ?','Go to Billing, click Invoices, and enter the relevant information in the Remarks field.','Log in to the Platform, go to'],
    ['key-usage','How do I inspect usage for an individual API key in the platform?','Open Usage, then select the time range and API key to filter usage.',['Log in to the Platform and go to','Select your desired time range']],
    ['key-revoke','What should I do immediately if an API key is exposed, and what application change follows?','Revoke the compromised key immediately, then create a new key and replace it in the application.',['revoking the compromised key immediately','After revocation, please create']],
    ['cooperation-agreement','Can an enterprise negotiate changes to the standard cooperation agreement described in the FAQ?','No. It is a standard framework agreement and cannot be modified.','The agreement is a standard framework agreement'],
    ['rate-limits','Do higher-rate-limit needs require buying one of several API pricing tiers?','The FAQ describes unified pricing with no tiered pricing; higher rate limits are requested through an expansion application.',['There is a unified pricing standard','If you need higher rate limits']],
    ['verification-failure','What are the common causes of real-name verification failing in the API FAQ?','Too many accounts bound to one ID, or too many consecutive incorrect ID-number entries causing temporary verification lockout.',['The number of accounts bound','The ID number has been entered']],
    ['verification-types','Does personal versus enterprise real-name verification change user benefits?','There is currently no difference in user benefits.','There is currently no difference'],
    ['verification-update','Can I upgrade personal verification to enterprise verification without losing my balance?','Yes; updating verification does not affect the account balance.',['Yes, you can update','The change will not affect']],
    ['verification-change','Can an enterprise-verified account be converted back to a personal account?','No, an enterprise-verified account cannot be changed to a personal account.','An Enterprise Verified Account cannot'],
    ['verification-name','After a registered company-name update, which company names may fund transfers and which may appear on invoices?','Transfers may use either the new or former company name; invoices can only use the new company name.','After the update, you can continue'],
    ['keep-alive','Does receiving empty lines while waiting mean the API has returned an empty final JSON answer?','No; empty lines are a non-streaming keep-alive mechanism and do not affect parsing of the eventual JSON body.',['Non-streaming','These contents do not affect']],
  ];
  for(const [id,q,a,n] of faq) add(`faq-${id}`,'semantic',`faq-api/${id}`,q,[[a,n]],{family:`faq-${id}`});

  // Exact lookup cases preserve opaque strings, versions and config paths.
  const integrations = [
    ['hermes','What is the setup command documented for Hermes Agent?','hermes setup','hermes setup'],
    ['nanobot','Which command initializes nanobot configuration?','nanobot onboard','nanobot onboard'],
    ['nanobot','What configuration path does the nanobot guide give for Linux and macOS?','~/.nanobot/config.json','~/.nanobot/config.json'],
    ['opencode','What minimum recommended OpenCode version is stated in the integration guide?','v1.18.30','v1.18.30'],
    ['opencode','Which slash command opens the provider connection flow in OpenCode?','/connect','Type `/connect`'],
    ['kilo_code','What npm package installs the documented Kilo Code CLI?','@kilocode/cli','npm install -g @kilocode/cli'],
    ['kilo_code','What slash command opens the model selector in Kilo Code?','/models','Type `/models`'],
    ['langcli','What minimum Node.js version is required for the manual Langcli installation?','Node.js 20 or later','Node.js 20 or later'],
    ['langcli','Which npm package does the manual Langcli installation use?','langcli-com','npm i -g langcli-com']
  ];
  integrations.forEach(([id,q,a,n],i)=>add(`integration-exact-${i+1}`,'keyword',`quick_start/agent_integrations/${id}`,q,[[a,n]],{family:`integration-${id}`,exact:[a],tags:['identifier_sensitive']}));

  // Additional suites are maintained separately for easy review.
  return import('./case-suites.mjs').then(module=>module.extend({add,pair,docs,cases,evidence}));
}
