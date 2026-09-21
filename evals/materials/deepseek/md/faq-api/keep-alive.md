# Why does the API keep returning empty lines?

Source: https://static.deepseek.com/faq/index.html?lang=en#/question/keep-alive
Captured: 2026-09-21T20:08:01.336Z

After your request is sent, it may sometimes take a while to receive a response from the server. During this period, your HTTP request will remain connected, and you may continuously receive contents in the following formats:

- Non-streaming requests: Continuously return empty lines
- Streaming requests: Continuously return SSE keep-alive comments (`: keep-alive`)

These contents do not affect the parsing of the JSON body of the response. If you are parsing the HTTP responses yourself, please ensure to handle these empty lines or comments appropriately.

If the request has not started inference after 10 minutes, the server will close the connection.
