# Delete File

Source: https://api-docs.deepseek.com/api/delete-file
Captured: 2026-09-21T19:37:05.229Z

```
DELETE /files/:file_id
```

Deletes a file.

## Request

Path Parameters

**file\_id** stringrequired

The ID of the file to delete.

## Responses

OK, returns the deletion status.

**Schema**

**id** stringrequired

The ID of the deleted file.

**object** stringrequired

**Possible values:** \[`file`\]

The object type, which is always `file`.

**deleted** booleanrequired

Whether the file was successfully deleted.

```json
{
  "id": "string",
  "object": "file",
  "deleted": true
}
```

```json
{
  "id": "file-api-0a1b2c3d4e5f60718293a4b5c6d7e8f9",
  "object": "file",
  "deleted": true
}
```
