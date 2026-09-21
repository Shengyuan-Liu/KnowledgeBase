# Lists Models

Source: https://api-docs.deepseek.com/api/list-models
Captured: 2026-09-21T19:37:07.555Z

```
GET /models
```

Lists the currently available models, and provides basic information about each one such as the owner and availability. Check [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing) for our currently supported models.

## Responses

OK, returns A list of models

**Schema**

**object** stringrequired

**Possible values:** \[`list`\]

**data**

Model\[\]

required

-   Array \[

**id** stringrequired

The model identifier, which can be referenced in the API endpoints.

**object** stringrequired

**Possible values:** \[`model`\]

The object type, which is always "model".

**owned\_by** stringrequired

The organization that owns the model.

-   \]

```json
{
  "object": "list",
  "data": [
    {
      "id": "string",
      "object": "model",
      "owned_by": "string"
    }
  ]
}
```

```json
{
  "object": "list",
  "data": [
    {
      "id": "deepseek-flash",
      "object": "model",
      "owned_by": "deepseek"
    },
    {
      "id": "deepseek-v4-pro",
      "object": "model",
      "owned_by": "deepseek"
    }
  ]
}
```
