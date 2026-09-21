# V3.1-Terminus Comparison Testing

Source: https://api-docs.deepseek.com/guides/comparison_testing
Captured: 2026-09-21T19:37:50.577Z

As an experimental version, although DeepSeek-V3.2-Exp has been validated for effectiveness on public evaluation sets, it still requires broader and larger-scale testing in real user scenarios to identify potential issues in certain long-tail use cases. To facilitate comparative testing by users, we have temporarily retained additional API access interfaces for V3.1-Terminus.

Users can simply modify the `base_url` to `"https://api.deepseek.com/v3.1_terminus_expires_on_20251015"` to access V3.1-Terminus, with pricing consistent with V3.2-Exp. This endpoint will remain available until October 15, 2025, 15:59 UTC.

We sincerely encourage users to provide valuable feedback during comparative testing via the following link:<br>
[https://feedback.deepseek.com/dsa](https://trtgsjkv6r.feishu.cn/share/base/form/shrcnRyOUMl0z2Jo8aK3RqccLIB)

* * *

## How to Conduct Comparison Testing

You can control which model version to access by modifying the `base_url`:

-   When using the **original method** to access the API, you will reach the **DeepSeek-V3.2-Exp** model
-   When you **set `base_url="https://api.deepseek.com/v3.1_terminus_expires_on_20251015"`**, you are accessing the **`DeepSeek-V3.1-Terminus`** model.

The correspondence between `base_url` settings and specific model versions is shown in the table below:

| API Type | base\_url Setting | Model Version |
| --- | --- | --- |
| OpenAI | `https://api.deepseek.com` | DeepSeek-V3.2-Exp |
| Anthropic | `https://api.deepseek.com/anthropic` | DeepSeek-V3.2-Exp |
| OpenAI | `https://api.deepseek.com/v3.1_terminus_expires_on_20251015` | DeepSeek-V3.1-Terminus |
| Anthropic | `https://api.deepseek.com/v3.1_terminus_expires_on_20251015/anthropic` | DeepSeek-V3.1-Terminus |

* * *

## Usage Examples

### Accessing V3.1-Terminus via OpenAI-Compatible API

#### Invoke The API

```bash
curl https://api.deepseek.com/v3.1_terminus_expires_on_20251015/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${DEEPSEEK_API_KEY}" \
  -d '{
        "model": "deepseek-chat",
        "messages": [
          {"role": "system", "content": "You are a helpful assistant."},
          {"role": "user", "content": "Hello!"}
        ],
        "stream": false
      }'
```

#### Sample Output

```json
{
    ... ...
    "model": "deepseek-v3.1-terminus",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you today?"
            },
            "logprobs": null,
            "finish_reason": "stop"
        }
    ],
    ... ...
}
```

#### Invoke The API

```python
# Please install OpenAI SDK first: `pip3 install openai`
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com/v3.1_terminus_expires_on_20251015")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
    ],
    stream=False
)

print(f"Model is: {response.model}")
print(f"Output is: {response.choices[0].message.content}")
```

#### Sample Output

```bash
Model is: deepseek-v3.1-terminus
Output is: Hello! How can I help you today?
```

#### Invoke The API

```javascript
// Please install OpenAI SDK first: `npm install openai`

import OpenAI from "openai";

const openai = new OpenAI({
        baseURL: 'https://api.deepseek.com/v3.1_terminus_expires_on_20251015',
        apiKey: process.env.DEEPSEEK_API_KEY,
});

async function main() {
  const completion = await openai.chat.completions.create({
    messages: [
      { role: "system", content: "You are a helpful assistant." },
      { role: "user", content: "Hello!."}
    ],
    model: "deepseek-chat",
  });

  console.log("Model is:", completion.model)
  console.log("Output is:", completion.choices[0].message.content);
}

main();
```

#### Sample Output

```bash
Model is: deepseek-v3.1-terminus
Output is: Hello! How can I help you today?
```

As shown in the sample output, **you can verify whether the called model is V3.1-Terminus by checking the `model` field in the API response.**

* * *

### Accessing V3.1-Terminus via Claude Code

When setting up Claude Code environment variables, you need to modify the `ANTHROPIC_BASE_URL` environment variable to access the DeepSeek-V3.1-Terminus model:

```bash
export ANTHROPIC_BASE_URL=https://api.deepseek.com/v3.1_terminus_expires_on_20251015/anthropic
```

For complete configuration instructions, please refer to the [Anthropic API Guide](https://api-docs.deepseek.com/guides/anthropic_api).
