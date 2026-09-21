# Using the Anthropic API

Source: https://api-docs.deepseek.com/guides/anthropic_api
Captured: 2026-09-21T19:37:14.264Z

To meet the demand for using the Anthropic API ecosystem, our API has added support for the Anthropic API format, with the `base_url` being `https://api.deepseek.com/anthropic`.

With simple configuration, you can integrate the capabilities of DeepSeek into the Anthropic API ecosystem.

* * *

## Use DeepSeek in Claude Code

Please refer to [Integrate with Claude Code](https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code).

## Invoke DeepSeek Model via Anthropic API

1.  Install Anthropic SDK

```text
pip install anthropic
```

2.  Config Environment Variables

```text
export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
export ANTHROPIC_API_KEY=${YOUR_API_KEY}
```

3.  Invoke the API

```text
import anthropic

client = anthropic.Anthropic()

message = client.messages.create(
    model="deepseek-flash",
    max_tokens=1000,
    system="You are a helpful assistant.",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Hi, how are you?"
                }
            ]
        }
    ]
)
print(message.content)
```

**Note:** When you pass an unsupported model name to DeepSeek's Anthropic API, the API backend will automatically map it to the `deepseek-flash` model.

* * *

## Anthropic Model Mapping

When you use the Anthropic API, we map the Claude model names you pass in:

-   Models starting with claude-opus are mapped to `deepseek-v4-pro`
-   Models starting with claude-haiku or claude-sonnet are mapped to `deepseek-flash`

The claude-opus mapping points to `deepseek-v4-pro`, which is billed at the V4 Pro price.

With this mapping, when using the developer mode of the new Claude Desktop APP, you can bypass the APP's model name restrictions by simply changing the base\_url and api\_key to connect to DeepSeek models.

* * *

## Anthropic API Compatibility Details

This section lists the compatibility details of the DeepSeek API with the Anthropic API. For the full Anthropic API format definition, please refer to the [official Anthropic API reference](https://platform.claude.com/docs/en/api/python/beta/messages/create).

### HTTP Header

| Field | Support Status |
| --- | --- |
| anthropic-beta | Ignored for `/messages`; required (`files-api-2025-04-14`) for Files API endpoints — see [Files API](https://api-docs.deepseek.com/guides/files_api#anthropic-compatible-files-api) |
| anthropic-version | Ignored |
| x-api-key | Fully Supported |

### Simple Fields

| Field | Support Status |
| --- | --- |
| model | Use DeepSeek Model Instead |
| max\_tokens | Fully Supported |
| container | Ignored |
| mcp\_servers | Ignored |
| metadata | `user_id` is supported, others are ignored  <br>Please refer to [Rate Limit & Isolation](https://api-docs.deepseek.com/quick_start/rate_limit) for more information about `user_id` parameter. |
| service\_tier | Ignored |
| stop\_sequences | Fully Supported |
| stream | Fully Supported |
| system | Fully Supported |
| temperature | Fully Supported (range \[0.0 ~ 2.0\]) |
| thinking | Supported (`budget_tokens` is ignored) |
| output\_config | Only `effort` is supported |
| top\_k | Ignored |
| top\_p | Only takes effect in thinking mode (with a lower bound of `0.95`); in non-thinking mode it is fixed at `1.0` |

### Tool Fields

#### tools

| Field | Support Status |
| --- | --- |
| name | Fully Supported |
| input\_schema | Fully Supported |
| description | Fully Supported |
| cache\_control | Ignored |

#### tool\_choice

| Value | Support Status |
| --- | --- |
| none | Fully Supported |
| auto | Supported (`disable_parallel_tool_use` is ignored) |
| any | Supported (`disable_parallel_tool_use` is ignored) |
| tool | Supported (`disable_parallel_tool_use` is ignored) |

### Message Fields

| Field | Variant | Sub-Field | Support Status |
| --- | --- | --- | --- |
| content | string |  | Fully Supported |
| content | array, type="text" | text | Fully Supported |
| content | array, type="text" | cache\_control | Ignored |
| content | array, type="text" | citations | Ignored |
| content | array, type="image" | source | Supported. `source.type` can be base64 (media types: jpeg, png, gif, webp), url, or file (the file variant requires the header `anthropic-beta: files-api-2025-04-14`) |
| content | array, type = "document" |  | Not Supported |
| content | array, type = "search\_result" |  | Not Supported |
| content | array, type = "thinking" |  | Supported |
| content | array, type="redacted\_thinking" |  | Not Supported |
| content | array, type = "tool\_use" | id | Fully Supported |
| content | array, type = "tool\_use" | input | Fully Supported |
| content | array, type = "tool\_use" | name | Fully Supported |
| content | array, type = "tool\_use" | cache\_control | Ignored |
| content | array, type = "tool\_result" | tool\_use\_id | Fully Supported |
| content | array, type = "tool\_result" | content | Fully Supported |
| content | array, type = "tool\_result" | cache\_control | Ignored |
| content | array, type = "tool\_result" | is\_error | Ignored |
| content | array, type = "server\_tool\_use" |  | Supported |
| content | array, type = "web\_search\_tool\_result" |  | Supported |
| content | array, type = "code\_execution\_tool\_result" |  | Not Supported |
| content | array, type = "mcp\_tool\_use" |  | Not Supported |
| content | array, type = "mcp\_tool\_result" |  | Not Supported |
| content | array, type = "container\_upload" |  | Not Supported |
